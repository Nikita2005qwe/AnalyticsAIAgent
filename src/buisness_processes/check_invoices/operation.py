"""
Модуль: operation.py
Описание: Операция поиска накладной в системе.

Назначение:
- Выполнить сценарий: авторизация → навигация → поиск → результат.
- Работать в рамках **одной сессии браузера** на весь процесс.
- Использовать Page Objects (`LoginPage`, `InvoicesPage` и др.).
- Использовать **доменную модель** `Invoice` для валидации и логики.
- Быть **конкретной**, но **не привязанной к названию системы**.

Архитектурная роль:
- Атомарная операция: "найти накладную".
- Часть процесса `InvoiceCheckerProcess`.
- Не знает о Excel, файлах, UI.

Зависимости:
- Selenium WebDriver
- Page Objects: `LoginPage`, `MainPage`, `SubsystemsPage`, `DistributorPanelPage`, `InvoicesPage`
- models.invoice: Invoice, InvoiceFactory, should_process, get_region_by_prefix
- Logger — для логирования хода выполнения
"""

# --- Импорты из стандартной библиотеки ---
from typing import Tuple, Optional

from numpy.ma.core import logical_not
# --- Импорты из сторонних библиотек ---
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait

# --- Импорты из src ---
from src.pages.dms.main_page import MainPage
from src.pages.dms.login_page import LoginPage
from src.pages.dms.subsystems_page import SubsystemsPage
from src.pages.dms.distributor_panel_page import DistributorPanelPage
from src.pages.dms.invoices_page import InvoicesPage

# --- Импорты из моделей ---
from src.models.invoice.invoice import Invoice, CheckedInvoice, CheckStatus

# --- Импорты из core ---
from src.core.logger import Logger
from src.core.config import Config

class InvoiceSearchOperation:
    """
    Операция поиска накладной в системе.

    Каждый экземпляр — **одна сессия браузера** для одного региона.
    Используется в процессе проверки нескольких накладных.

    Атрибуты:
    - region (str): "siberia" или "ural"
    - driver (WebDriver): Управляет браузером
    - logger (Logger): Для логирования хода выполнения
    - factory (InvoiceFactory): Для создания объектов Invoice
    - main_page (MainPage): Главная страница
    - login_page (LoginPage): Страница входа
    - subsystems_page (SubsystemsPage): Страница подсистем
    - distributor_panel (DistributorPanelPage): Панель дистрибьютора
    - invoices_page (InvoicesPage): Страница поиска накладных
    - _initialized (bool): Флаг — сессия запущена
    """

    # Сопоставление региона → переменные окружения
    CREDENTIALS = {
        "siberia": ("DMS_USERNAME_SIB", "DMS_PASSWORD_SIB"),
        "ural": ("DMS_USERNAME_URAL", "DMS_PASSWORD_URAL"),
    }

    def __init__(self, region: str, logger: Logger, config: Config):
        """
        Создаёт операцию для указанного региона.

        Args:
            region (str): "siberia" или "ural"
            logger (Logger): Экземпляр логгера для записи событий

        Raises:
            ValueError: Если регион не поддерживается

        Примечание:
        - Логин/пароль берутся из .env по ключам, зависящим от региона.
        - Драйвер создаётся только при первом вызове check_invoice().
        - Все Page Objects инициализируются при старте.
        - Использует InvoiceFactory для создания Invoice.
        """
        self.region = region.lower()
        if self.region not in self.CREDENTIALS:
            raise ValueError(f"Не известный регион {region}")
        self.logger = logger
        self.driver = None
        self.invoices_page: Optional[InvoicesPage] = None
        self._initialized = False
        self.config = config

    def check_invoice(self, invoice: Invoice) -> CheckedInvoice:
        """
        Проверяет, найдена ли накладная в системе.

        Основная цель — вернуть **однозначный результат** (True/False), даже если:
        - Браузер был закрыт вручную,
        - Произошёл таймаут,
        - Сессия устарела.

        Метод спроектирован как **устойчивый к сбоям**: он не должен останавливать весь процесс
        из-за одной накладной. Всё, что невозможно проверить — помечается как ошибка,
        но процесс продолжается.

        Args:


        Returns:
            bool:
                - True — накладная найдена (хотя бы на одной площадке)
                - False — не найдена или произошла ошибка

        Шаги выполнения:

        1. **Создание доменного объекта:**
           - Вызвать self.factory.from_number(invoice_number)
           - Получить Invoice с заполненными:
               - number
               - prefix
               - region (по префиксу)
           - Если префикс не распознан — залогировать "⚠️ Неизвестный префикс: {prefix}",
             добавить в статистику, вернуть False

        2. **Проверка бизнес-условий:**
           - Вызвать should_process(invoice)
           - Если False (например, ISA=0 или SFA пусто) — залогировать "🟡 Пропущена (не проходит фильтр)",
             вернуть False
           - Это предотвращает бессмысленные запросы

        3. **Проверка соответствия региона:**
           - Убедиться, что invoice.region == self.region
           - Если нет — залогировать "⚠️ Регион не совпадает: ожидается {self.region}, найден {invoice.region}"
             и вернуть False
           - Это гарантирует, что накладная из Урала не проверяется в сессии Сибири

        4. **Восстановление сессии (если нужно):**
           - Вызвать self._is_driver_alive()
           - Если драйвер не отвечает (например, пользователь закрыл браузер):
               * Залогировать "⚠️ Браузер закрыт. Попытка восстановления сессии..."
               * Вызвать self._recover_session()
               * Если не удалось — вернуть False, залогировать "❌ Не удалось восстановить сессию"
           - Это позволяет продолжить проверку после случайного закрытия окна

        5. **Переключение на основной город:**
           - Определить город по префиксу (get_city_by_prefix)
           - Вызвать self._switch_to_city(city)
           - Если не удалось — вернуть False, залогировать ошибку

        6. **Выполнение поиска:**
           - Залогировать "🔍 Поиск накладной: {invoice_number}"
           - Вызвать self.invoices_page.perform_search(invoice_number)
           - Дождаться результата: self.invoices_page.wait_for_search_result(timeout=15)
           - Если таймаут — залогировать "⏰ Таймаут поиска", вернуть False

        7. **Анализ результата:**
           - Вызвать self.invoices_page.is_empty()
           - Если False (таблица не пуста) → накладная найдена → вернуть True
           - Если True (пусто) → перейти к шагу 8

        8. **Попытка на альтернативной площадке (если есть):**
           - Проверить, есть ли alternative_city в данных префикса
           - Если есть:
               * Переключиться на alternative_city
               * Повторить поиск (шаги 6–7)
               * Если найдена — вернуть True
           - Если нет — оставить как "не найдена"

        9. **Логирование результата:**
           - Залогировать:
               - "✅ {number}: найдена" — если True
               - "❌ {number}: не найдена" — если False и нет ошибки
               - "⚠️ {number}: ошибка — {сообщение}" — если было исключение
           - Использует self.logger.log() — результат виден в реальном времени

        10. **Возврат результата:**
            - Возвращает bool, который будет использован в процессе
              для обновления статуса и подсветки в Excel

        Логирование:
        - Все действия логируются: старт, поиск, результат, ошибки
        - Сообщения понятны пользователю (эмодзи, краткость)
        - Ошибки не останавливают процесс — только помечаются

        Обработка исключений:
        - Все исключения (TimeoutException, StaleElement, ConnectionError и др.)
          перехватываются, логируются, и метод возвращает False
        - Это предотвращает падение всего процесса из-за одной накладной

        Raises:
            Никаких исключений не выбрасывает — всегда возвращает bool.
            Внутренние ошибки логируются, но не прерывают выполнение.

        Важные особенности:
        - **Не прерывает процесс при ошибке** — продолжает проверку остальных
        - **Работает с живым браузером** — если закрыт, пытается перезапустить
        - **Использует доменную модель** — Invoice, правила, фабрику
        - **Готов к прерываниям** — даже если упадёт, частичный результат будет сохранён в процессе

        Использует:
        - InvoiceFactory.from_number() → создание объекта
        - should_process() → фильтрация
        - get_city_by_prefix() → определение города
        - _is_driver_alive() и _recover_session() → устойчивость
        - InvoicesPage.perform_search(), wait_for_search_result(), is_empty() → поиск
        - Logger.log() → отображение хода

        Пример использования в процессе:
            found = operation.check_invoice("01/12345")
            # → True/False, всегда
            :param invoice:
        """
        if not self._initialized:
            self.start()
        try:
            # Переключаемся на нужный город
            self._switch_to_city(invoice.delivery_city)
            # Вводим в поле поиска номер
            self.invoices_page.perform_search(invoice.number)
            # Ожидаем результат
            self.invoices_page.wait_for_search_result()
            # Проверяем статус накладной
            status = CheckStatus.FOUND if not self.invoices_page.is_empty() else CheckStatus.NOT_FOUND
            # Возвращаем накладную со статусом для дальнейшего отчёта
            return CheckedInvoice(invoice=invoice, status=status)
        except Exception as e:
            # Логируем результат, если произошла ошибка на одном из этапов
            self.logger.error(f"Ошибка {e}")
            return CheckedInvoice(invoice=invoice, status=CheckStatus.ERROR)

    def start(self):
        """
        Инициализирует сессию:
        1. Запускает браузер
        2. Открывает главную страницу
        3. Принимает попап региона
        4. Переходит на страницу входа
        5. Авторизуется под пользователем региона
        6. Переходит в панель дистрибьютора
        7. Переходит в раздел "документы"
        8. Дожидается загрузки структуры организации

        Шаги:
        1. Получить логин/пароль из .env с помощью os.getenv()
        2. Создать экземпляр WebDriver (Chrome)
        3. Максимизировать окно
        4. Создать Page Objects:
           - MainPage
           - LoginPage
           - SubsystemsPage
           - DistributorPanelPage
           - InvoicesPage
        5. Выполнить последовательность переходов:
           - main_page.open() → accept_region_popup() → go_to_login_page()
           - login_page.login(username, password)
           - subsystems_page.go_to_distributor_panel()
           - distributor_panel.go_to_section("documents")
        6. Дождаться, что invoices_page.is_loaded() и структура загружена
        7. Установить флаг _initialized = True

        Логирование:
        - Перед каждым шагом — записать в logger.log()
        - При ошибке — logger.error(), затем _safe_quit()

        Raises:
            RuntimeError: Если инициализация не удалась
        """
        if self._initialized:
            return
        try:
            username_key, password_key = self.CREDENTIALS[self.region]
            username = self.config.get_secret(username_key)
            password = self.config.get_secret(password_key)
            if not password:
                raise RuntimeError(f"Данные не заданы Логин: {username}, Пароль: {password}")
            self.logger.info(f"Запуск DMS для региона {self.region}")
            # --- НАЧАЛО: Создание драйвера с опциями ---
            options = webdriver.ChromeOptions()
            options.add_argument("--start-maximized")
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")  # 🔴 КРИТИЧЕСКИ ВАЖНО
            options.add_argument("--disable-dev-shm-usage")  # 🔴 Для стабильности в Windows
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-popup-blocking")
            options.add_argument("--disable-blink-features=AutomationControlled")

            self.driver = webdriver.Chrome(options=options)
            self.driver.maximize_window()

            # Твой стиль, но исправленный: список действий с описанием
            steps = [
                ("Открытие главной страницы", MainPage, lambda p: p.open()),
                ("Принятие региона", MainPage, lambda p: p.accept_region_popup()),
                ("Переход на страницу входа", MainPage, lambda p: p.go_to_login_page()),

                ("Авторизация", LoginPage, lambda p: p.login(username, password)),

                ("Переход в панель дистрибьютора", SubsystemsPage, lambda p: p.go_to_distributor_panel()),

                ("Переход в раздел 'Документы'", DistributorPanelPage, lambda p: p.go_to_section("documents")),
            ]

            for description, PageClass, action in steps:
                self.logger.info(f"➡️ {description}")
                try:
                    page = PageClass(self.driver)
                    action(page)
                except Exception as e:
                    self.logger.error(f"❌ Ошибка на шаге '{description}': {e}")
                    raise

            # Отдельно сохраняем последнюю страницу
            self.invoices_page = InvoicesPage(self.driver)
            if self.invoices_page.is_loaded():
                self._initialized = True
                self.logger.info("Сессия DMS успешно запущена")
                return
            raise TimeoutError("Загрузка таблицы с накладными долгая")

        except TimeoutError as e:
            self.logger.error("Загрузка таблицы с накладными долгая, повторная попытка")
            self.start()
        except Exception as e:
            self._safe_quit()
            raise RuntimeError(f"Ошибка при запуске DMS ({e})")

    def close(self):
        """
        Корректно закрывает браузер и очищает ресурсы.

        Вызывается после завершения проверки всех накладных региона.
        Передаёт управление _safe_quit().
        """
        self._safe_quit()


    def _switch_to_city(self, city: str):
        """
        Переключает текущую площадку на указанную.

        Args:
            city (str): Город ("Красноярск", "Челябинск" и т.д.)

        Шаги:
        1. Получить текущую структуру через invoices_page.get_current_orgstructure()
        2. Если не совпадает с ожидаемой — вызвать invoices_page.select_orgstructure_by_city(city)
        3. Дождаться обновления страницы (например, через ожидание исчезновения лоадера)

        Логирование:
        - Записать: "Переключение на площадку: {city}"

        Примечание:
        - Использует InvoicesPage.select_orgstructure_by_city()
        """
        expected = f"ООО «Континент» ({city})"
        try:
            current = self.invoices_page.get_current_orgstructure()
            if current == expected:
                return

            self.logger.info(f"🔄 Переключение на площадку: {city}")
            self.invoices_page.select_orgstructure_by_city(city)

            # Ждём обновления (можно улучшить через ожидание лоадера)
            # Простая задержка или ожидание смены текста
            WebDriverWait(self.driver, 10).until(
                lambda d: self.invoices_page.get_current_orgstructure() == expected
            )
        except RuntimeError as e:
            self.logger.error(f"Новое направление не было выбрано")

    def _recover_session(self):
        """
        Пытается восстановить сессию:
        1. Закрывает старый driver (если есть)
        2. Вызывает start() заново

        Используется, если driver умер.
        """
        self._safe_quit()
        self.start()

    def _safe_quit(self):
        """
        Безопасно завершает драйвер, даже если произошла ошибка.

        Шаги:
        1. Если driver существует — вызвать driver.quit()
        2. Перехватить исключения (например, таймаут)
        3. Обнулить driver, invoices_page, _initialized
        4. Залогировать: "Сессия закрыта"

        Примечание:
        - Вызывается из close() и при ошибках в start()
        """
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None
        self.invoices_page = None
        self._initialized = False