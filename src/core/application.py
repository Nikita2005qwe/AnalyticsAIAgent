"""
Модуль: application.py
Класс: Application

Описание: Главный класс приложения, отвечающий за инициализацию, настройку и запуск всех компонентов.

Назначение:
- Загрузка конфигурации (настройки, .env)
- Инициализация логгера
- Создание главного окна (с вкладками)
- Регистрация всех бизнес-процессов (view-виджетов)
- Запуск GUI

Архитектурная роль:
- Точка входа в приложение
- Координатор между слоями: core, ui, business_processes
- Централизованное управление жизненным циклом

Версия: v0.1
Автор: Боряков
Дата: 21.08.2025
Статус: Разработан
"""

# --- Стандартная библиотека ---
import sys

from PyQt5.QtGui import QKeySequence
# --- PyQt5 ---
from PyQt5.QtWidgets import (
    QApplication,  # Основной класс для запуска GUI-приложения
    QMessageBox, QShortcut  # Диалоговое окно для отображения ошибок
)

# --- Локальные импорты из проекта ---
from src.core.config import Config      # Хранилище настроек и секретов
from src.core.logger import Logger      # Глобальный логгер с поддержкой GUI и файла
from src.core.shortcuts import ShortcutManager
from src.ui.main_window import MainWindow  # Главное окно с вкладками и боковым меню


class Application:
    """
    Главный класс приложения — точка входа и координатор всех компонентов.

    Атрибуты:
    - config (Config): объект конфигурации (настройки, API-ключи)
    - logger (Logger): глобальный логгер для записи событий
    - main_window (MainWindow): главное окно приложения с вкладками
    - widgets (dict): реестр всех зарегистрированных виджетов: {название: экземпляр}
    - qt_app (QApplication): экземпляр PyQt-приложения (создаётся в run)

    Архитектурная роль:
    - Управляет жизненным циклом приложения
    - Последовательно инициализирует core-компоненты
    - Регистрирует все UI-виджеты
    - Обеспечивает централизованное логирование и обработку ошибок
    """

    def __init__(self):
        """
        Инициализирует приложение.

        Шаги:
        1. Установить self.config = None — будет создан в setup_config()
        2. Установить self.logger = None — будет создан в setup_logger()
        3. Установить self.main_window = None — будет создан в setup_main_window()
        4. Установить self.widgets = {} — реестр всех зарегистрированных виджетов
        5. Установить self.qt_app = None — будет создан в run()

        Примечание:
        - Application не принимает параметров — он сам создаёт все зависимости
        - Порядок инициализации строго определён: Config → Logger → MainWindow → виджеты
        - Использует принцип DI (Dependency Injection) — передаёт зависимости в виджеты
        """
        self.config = None
        self.logger = None
        self.main_window = None
        self.widgets = {}
        self.qt_app = None
        self.shortcut_manager = None  # ← новый атрибут

    def setup_config(self):
        """
        Загружает и инициализирует конфигурацию приложения.

        Шаги:
        1. Создать экземпляр Config с временным logger=None
        2. Создать необходимые директории: config/, logs/, temp/
        3. Загрузить настройки из config/settings.json
           - Если файл не существует — создать дефолтный
        4. Загрузить переменные окружения из .env
           - Если .env нет — предупредить, но продолжить
        5. Проверить наличие обязательных секретов (например, DMS_LOGIN, CRM_PASSWORD)
        6. Сохранить объект в self.config

        Примечание:
        - Config — центральное хранилище: GUI-настройки, пути, секреты
        - Использует .env для хранения чувствительных данных (не в JSON)
        - Дефолтный config создаётся при первом запуске
        """
        try:
            # Шаг 1: Создать экземпляр Config
            self.config = Config(logger=None)

            # Шаг 2: Создать директории
            self.config.ensure_directories()

            # Шаг 3: Загрузить настройки из JSON
            self.config.load()

            # Логирование будет позже, после инициализации Logger
        except Exception as e:
            # На этом этапе logger ещё не готов — используем print
            print(f"❌ Ошибка при инициализации Config: {e}", file=sys.stderr)
            raise

    def setup_logger(self):
        """
        Инициализирует глобальный логгер.

        Шаги:
        1. Получить путь к файлу логов из self.config.get("log_file", "logs/app.log")
        2. Определить уровень логирования:
           - Если config.get("full_log") == True → DEBUG
           - Иначе → INFO
        3. Создать экземпляр Logger с помощью Logger.get_instance()
        4. Сохранить в self.logger
        5. Залогировать старт: "Application started. Version 0.4"

        Примечание:
        - Logger — синглтон, используется всеми компонентами приложения
        - Поддерживает запись в файл и отправку событий в GUI (через сигнал)
        - Уровень логирования зависит от настроек, а не жёстко закодирован
        """
        # Шаг 1: Получить путь к файлу логов
        log_file = self.config.get("log_file", "logs/app.log")

        # Шаг 2: Определить уровень логирования
        level = "DEBUG" if self.config.get("full_log", False) else "INFO"

        # Шаг 3: Создать экземпляр Logger
        self.logger = Logger.get_instance(log_file=log_file, level=level)

        # Шаг 5: Залогировать старт
        self.logger.info("Application started. Version 0.4")

    def setup_main_window(self):
        """
        Создаёт и настраивает главное окно приложения.

        Шаги:
        1. Создать экземпляр MainWindow, передав logger
        2. Вызвать main_window.setup_ui() с параметрами:
           - icon_file_name: путь к иконке (из config или дефолтный)
           - style_file: путь к QSS-стилям
        3. Сохранить ссылку в self.main_window

        Примечание:
        - MainWindow должен поддерживать добавление вкладок через add_tab(title, widget)
        - Использует боковое меню для навигации между процессами
        - Поддерживает темы и иконки
        """
        # Шаг 1: Создать экземпляр MainWindow
        self.main_window = MainWindow(logger=self.logger)
        window_size = self.config.get("window_size", [1920, 1080])
        full_screen = self.config.get("full_screen", True)
        maximized = self.config.get("maximized", True)
        # Шаг 2: Настроить UI
        self.main_window.setup_ui(
            icon_file_name=self.config.get("icon_path", "assets/icon.png"),
            style_file=self.config.get("style_file", "styles/app.qss"),
            initial_size=window_size,
            full_screen=full_screen,
            maximized=maximized
        )

    def register_business_processes(self):
        """
        Регистрирует все вкладки приложения, описанные в конфигурации.

        Это ключевой метод, который связывает:
        - декларативную конфигурацию (config.json)
        - динамическую загрузку модулей (import)
        - создание UI-виджетов
        - добавление вкладок в главное окно

        Назначение:
        - Централизованно зарегистрировать все view-компоненты (вкладки)
        - Поддерживать гибкость: новые вкладки добавляются только в config.json
        - Не требовать правки кода при добавлении нового процесса
        - Обеспечить единый способ инициализации всех виджетов

        Архитектурная роль:
        - Мост между конфигурацией и UI
        - Реализует паттерн: "Координатор + декларация"
        - Поддерживает расширяемость без изменения кода

        Зависимости:
        - src.core.config.Config — для получения списка вкладок
        - src.ui.main_window.MainWindow — для добавления вкладок
        - PyQt5.QtWidgets.QWidget — базовый класс для всех view
        - Динамические импорты: __import__, getattr
        """

        # === 2. Получаем конфигурацию вкладок из Config ===
        # Метод get_tab_config() возвращает словарь:
        # {
        #   "check_invoices": {
        #     "title": "Проверка накладных",
        #     "type": "business_process",
        #     "module": "check_invoices",
        #     "class": "CheckInvoicesView"
        #   },
        #   ...
        # }
        tab_config = self.config.get_tab_config()

        # === 3. Получаем порядок вкладок ===
        # tab_order — список ключей, определяющий порядок отображения
        # Пример: ["check_invoices", "settings", "ai_chat"]
        # Если не задан — возвращаем все ключи из tabs
        order = self.config.get_tab_order()

        # === 4. Основной цикл: регистрация каждой вкладки ===
        for key in order:
            # Шаг 4.1: Проверяем, описана ли вкладка в config.tabs
            if key not in tab_config:
                self.logger.warning(f"Вкладка '{key}' указана в tab_order, но не описана в tabs. Пропущено.")
                continue

            # Шаг 4.2: Получаем мета-данные вкладки
            tab_info = tab_config[key]
            title = tab_info["title"]  # Отображаемое название
            tab_type = tab_info["type"]  # Тип: business_process / internal_app
            module_name = tab_info["module"]  # Имя модуля (папки)
            class_name = tab_info["class"]  # Имя класса в модуле

            try:
                # === 5. Определяем путь к модулю в зависимости от типа ===
                if tab_type == "business_process":
                    # Бизнес-процессы: src.business_processes.<module>.view
                    module_path = f"src.buisness_processes.{module_name}.view"
                elif tab_type == "internal_app":
                    # Встроенные приложения: src.ui.apps.<module>.view
                    module_path = f"src.ui.apps.{module_name}.view"
                else:
                    raise ValueError(f"Неизвестный тип вкладки: '{tab_type}'. "
                                     f"Ожидалось: 'business_process' или 'internal_app'")

                # === 6. Динамически импортируем модуль ===
                # __import__ загружает модуль по строке
                # fromlist=[class_name] — гарантирует, что вернётся именно модуль view
                module = __import__(module_path, fromlist=[class_name])

                # === 7. Получаем класс из модуля по имени ===
                # Например: getattr(module, "CheckInvoicesView")
                view_class = getattr(module, class_name)

                # === 8. Создаём экземпляр виджета ===
                # Все view-классы должны иметь интерфейс:
                # __init__(config: Config, logger: Logger)
                widget = view_class(self.logger, self.config)

                # Получаем кнопку навигации
                nav_button = widget.get_navigation_button()
                nav_button.setCheckable(True)

                # Подключаем сигнал: при клике — показать виджет
                # Замыкание, чтобы захватить widget
                nav_button.clicked.connect(
                    lambda checked, w=widget: self.main_window.switch_to(w)
                )

                # Добавляем кнопку в боковое меню
                self.main_window.sidebar_layout.addWidget(nav_button)

                # === 10. Сохраняем ссылку в реестре Application ===
                # Нужно для дальнейшего доступа (например, навигация, активация)
                self.widgets[title] = widget

                # === 11. Логируем успешную регистрацию ===
                self.logger.info(f"Виджет зарегистрирован: {title}")

            # === 12. Обработка ошибок ===
            except ModuleNotFoundError as e:
                # Модуль не найден — возможно, папка отсутствует
                self.logger.error(f"Модуль не найден для вкладки '{title}' ({key}): {e}")

            except AttributeError as e:
                # Класс не найден в модуле — опечатка в class_name или нет класса
                self.logger.error(f"Класс '{class_name}' не найден в модуле '{module_path}': {e}")

            except TypeError as e:
                # Ошибка при создании экземпляра — неправильные аргументы в __init__
                self.logger.error(f"Ошибка инициализации виджета '{title}': {e}. "
                                  f"Проверьте сигнатуру __init__(config, logger)")

            except Exception as e:
                # Любая другая ошибка (например, ошибка в __init__ виджета)
                self.logger.error(f"Неизвестная ошибка при создании виджета '{title}': {e}")

        # === 13. Финальное логирование ===
        self.logger.info(f"Регистрация вкладок завершена. Зарегистрировано: {len(self.widgets)} виджетов")

    def on_config_changed(self, key: str, value):
        if key == "full_log":
            self.main_window.show_logs_panel(value)
        elif key == 'window_mode':
            if value["maximized"]:
                self.main_window.showMaximized()  # ← Приоритет: развёрнутое окно
            else:
                self.main_window.showNormal()
                self.main_window.resize(*value["window_size"])  # ← Только если не maximized

    def run(self):
        """
        Запускает приложение: инициализирует все компоненты и показывает главное окно.

        Шаги:
        1. Вызвать setup_config()
        2. Вызвать setup_logger()
        3. Передать настоящий logger в config.set_logger()
        4. Вызвать setup_main_window()
        5. Вызвать register_business_processes()
        6. Вызвать build_navigation()
        7. Создать QApplication
        8. Показать главное окно
        9. Запустить цикл событий: app.exec_()

        Обработка ошибок:
        - Если на любом этапе произошла ошибка:
          * Залогировать её через self.logger (если доступен)
          * Показать QMessageBox с текстом ошибки
          * Завершить приложение с кодом 1
        """
        try:
            # Шаг 1
            self.setup_config()

            # Шаг 2
            self.setup_logger()

            # Шаг 3
            self.config.set_logger(self.logger)
            self.config.config_changed.connect(self.on_config_changed)
            # Шаг 4
            self.qt_app = QApplication(sys.argv)
            self.setup_main_window()
            self.main_window.application = self  # ← для switch_to

            # Шаг 5
            # === 5. Зарегистрировать виджеты ===
            self.register_business_processes()

            # === Инициализация ShortcutManager ===
            self.shortcut_manager = ShortcutManager(
                self.main_window,
                self.logger,
                self.config,
                self.widgets.get("Настройки"),
                self.widgets.get("Проверка накладных")
            )

            # === Подключаем переключение контекста ===
            # При смене вкладки — уведомляем ShortcutManager
            def on_tab_switch(widget):
                if hasattr(self, 'shortcut_manager'):
                    self.shortcut_manager.on_widget_activated(widget)

            # Оборачиваем switch_to, чтобы добавить колбэк
            original_switch = self.main_window.switch_to

            def wrapped_switch(widget):
                original_switch(widget)
                on_tab_switch(widget)

            self.main_window.switch_to = wrapped_switch

            # После setup_main_window() и до main_window.show()
            self.main_window.show_logs_panel(self.config.get("full_log", False))
            # Шаг 7-9
            self.main_window.show()
            self.logger.info("GUI запущен")

            sys.exit(self.qt_app.exec_())

        except Exception as e:
            # Если logger уже инициализирован — логируем
            if self.logger:
                self.logger.error(f"Фатальная ошибка при запуске: {e}")
            else:
                print(f"❌ Фатальная ошибка: {e}", file=sys.stderr)

            # Пытаемся показать QMessageBox
            try:
                app = QApplication(sys.argv)
                msg_box = QMessageBox()
                msg_box.setWindowTitle("Ошибка запуска")
                msg_box.setText(f"Приложение не может быть запущено:\n{e}")
                msg_box.setIcon(QMessageBox.Critical)
                msg_box.exec_()
            except:
                pass  # Если и GUI не запустится — ничего не поделать

            sys.exit(1)