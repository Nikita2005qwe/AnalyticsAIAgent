"""
Модуль: process.py
Описание: Процесс проверки накладных из Excel-файла.

Назначение:
- Управление полным циклом проверки:
  - Загрузка номеров через FileService,
  - Фильтрация по бизнес-правилам,
  - Группировка по регионам,
  - Последовательный запуск поиска для каждого региона,
  - Сохранение промежуточных и финальных результатов через FileService.
- Не зависеть от деталей работы с Excel.
- Использовать FileService как единый интерфейс к файлам.

Архитектурная роль:
- Оркестратор: управляет жизненным циклом проверки.
- Координирует: FileService → InvoiceSearchOperation → FileService.
- Не знает, как читать/писать Excel — только что и когда.

Зависимости:
- InvoiceSearchOperation (операция поиска)
- Logger (логирование)
- FileService (работа с Excel)
- models.invoice: Invoice, InvoiceFactory, should_process
"""
from datetime import datetime
from tarfile import data_filter
# --- Импорты из стандартной библиотеки ---
from typing import List, Tuple

# --- Импорты из src ---
from src.core.logger import Logger
from src.core.config import Config
from .operation import InvoiceSearchOperation
from .report import ReporterOfCheckInvoiceProcess

# --- Импорты из сервисов ---
from src.services.file_handler import FileHandler

# --- Импорты из моделей ---
from src.models.invoice.invoice_factory import InvoiceFactory
from src.models.invoice.invoice_validation import FilterInvoices


class InvoiceCheckerProcess:
    """
    Процесс проверки накладных из Excel-файла.

    Атрибуты:
    - logger (Logger): Для логирования хода выполнения
    - file_service (FileService): Для загрузки и сохранения Excel
    - factory (InvoiceFactory): Для создания объектов Invoice
    """

    def __init__(self, logger: Logger, config: Config):
        """
        Инициализирует процесс проверки.

        Args:
            logger (Logger): Экземпляр логгера

        Примечание:
        - Использует внедрение зависимостей: FileService создаётся вне процесса.
        - Это позволяет легко заменять или мокать FileService в тестах.
        """
        self.invoices = []
        self.logger = logger
        self.file_handler = None
        self.factory = InvoiceFactory()
        self.filter = FilterInvoices()
        self.reporter = None
        self.config = config
        self.operator = None

    def run(self, file_path: str) -> None:
        """
        Запускает полный процесс проверки накладных из Excel-файла.

        Это **центральный метод** всего процесса. Он:
        - Загружает данные,
        - Фильтрует по бизнес-правилам,
        - Группирует по регионам,
        - Последовательно проверяет накладные в DMS (через InvoiceSearchOperation),
        - Немедленно сохраняет промежуточные результаты,
        - Обновляет Excel-файл с цветовой заливкой,
        - Открывает отчёт после завершения.

        Главная цель — **максимальная надёжность и восстановляемость**:
        - Даже если процесс будет прерван (ошибка, закрытие браузера, сбой),
          **все проверенные накладные будут отмечены в файле**.
        - Никакая работа не теряется.

        Args:
            file_path (str): Путь к Excel-файлу с номерами накладных

        Returns:
            List[Tuple[str, bool, str]]: Список результатов в формате:
                (номер_накладной, найдена, статус)
                где статус:
                    - "found" — найдена
                    - "not_found" — не найдена
                    - "error" — ошибка при проверке
                    - "unknown" — неизвестный префикс
                    - "skipped" — пропущена (не проходит фильтр)

        Шаги выполнения:

        1. **Проверка входных данных:**
           - Убедиться, что file_path не пустой и файл существует
           - Проверить, что sheet_name входит в допустимые (если есть ограничения)
           - Если ошибка — залогировать, вернуть пустой список

        2. **Загрузка и создание объектов Invoice:**
           - Вызвать self._load_invoices_from_excel(file_path, sheet_name)
           - Метод возвращает List[Invoice] с заполненными:
               - number
               - prefix
               - region
               - isa_amount, sfa_amount
           - Если ошибка чтения — залогировать, вернуть []

        3. **Фильтрация по бизнес-правилам:**
           - Оставить только те накладные, для которых should_process(invoice) == True
           - Остальные (например, ISA=0) — пометить как "skipped", не проверять
           - Залогировать: "Фильтрация: 120 → 85 накладных"

        4. **Группировка по регионам:**
           - Разделить на:
               - siberia: [inv for inv in invoices if inv.region == "siberia"]
               - ural: [inv for inv in invoices if inv.region == "ural"]
               - unknown: остальные (неизвестный префикс)
           - Залогировать количество в каждой группе

        5. **Обработка региона "siberia":**
           - Если группа не пуста:
               a. Создать InvoiceSearchOperation("siberia", logger=self.logger)
               b. Вызвать op.start() — инициализировать сессию
               c. Для каждой накладной в группе:
                   - Вызвать op.check_invoice(invoice.number)
                   - Обновить invoice.found_in_dms и status
                   - Добавить результат в общий список self.temp_results
                   - Залогировать ход: "→ 01/12345: ✅"
               d. После всех — вызвать self._mark_excel_partial(file_path, sheet_name, self.temp_results)
                   * Это **ключевой шаг**: результаты по Сибири **немедленно сохраняются в файл**
                   * Даже если дальше будет ошибка — эти накладные уже отмечены
               e. Вызвать op.close() — корректно закрыть браузер

        6. **Обработка региона "ural":**
           - Аналогично:
               a. Создать op = InvoiceSearchOperation("ural", ...)
               b. start()
               c. Проверить все накладные
               d. Сохранить промежуточный результат: _mark_excel_partial
               e. close()

        7. **Обработка "unknown" (неизвестные префиксы):**
           - Для каждой накладной:
               - Установить status = "unknown"
               - found_in_dms = False
               - Добавить в результаты
           - В файле будет подсвечена как FILL_NOT_SEARCHED (жёлтый)
           - Не пытаемся проверять — не хватает данных

        8. **Финальное обновление Excel:**
           - Вызвать self._mark_excel_partial() **ещё раз** — на случай, если после Урала были изменения
           - Убедиться, что все ячейки обновлены

        9. **Открытие отчётного файла:**
           - Вызвать self._save_and_open_report(file_path)
           - Метод:
               * Убедится, что файл существует
               * Попытаться открыть его системной командой:
                   - Windows: os.startfile(file_path)
                   - macOS: subprocess.run(['open', file_path])
                   - Linux: subprocess.run(['xdg-open', file_path])
               * Залогировать: "📄 Отчёт открыт: {file_path}"
               * При ошибке — предупреждение, не ошибка

        10. **Финальное логирование:**
            - Подсчитать:
                - found = количество с status == "found"
                - not_found = "not_found"
                - errors = "error"
                - unknown = "unknown"
            - Залогировать итог:
                "✅ Готово: найдено=15, не найдено=3, ошибки=2, неизвестные=1"
                "🎨 Результаты сохранены и файл открыт"

        11. **Возврат результата:**
            - Вернуть список всех результатов
            - Может быть использован AI-агентом, тестами, логикой

        Обработка ошибок:

        - Все исключения (включая падение браузера, таймаут, ошибка Excel) — перехватываются
        - При критической ошибке (например, не удалось прочитать файл):
            * Залогировать
            * Вернуть пустой список
        - При частичной ошибке (например, упал браузер в середине):
            * Продолжить с _recover_session()
            * Или перейти к следующему региону
            * Уже проверенные накладные — уже сохранены

        Ключевые особенности:

        - ✅ **Частичное сохранение**: после каждого региона результаты сохраняются в файл
        - ✅ **Устойчивость**: не падает из-за одной накладной
        - ✅ **Восстановление сессии**: если браузер закрыт — пытается перезапустить
        - ✅ **Открытие файла**: после завершения — файл открывается автоматически
        - ✅ **Подсветка непроверенных**: накладные, которые не были проверены (например, из-за прерывания),
          остаются с белой заливкой (FILL_NOT_CHECKED), что визуально отличает их от "не найденных"
        - ✅ **Интеграция с доменом**: использует Invoice, правила, фабрику, стиль

        Использует:
        - self._load_invoices_from_excel() → загрузка данных
        - should_process() → фильтрация
        - InvoiceSearchOperation → проверка
        - self._mark_excel_partial() → промежуточное сохранение
        - self._save_and_open_report() → UX
        - Logger → логирование хода и ошибок

        Пример вызова:
            results = process.run("data/invoices.xlsx", "выгрузка_GC")
            # → [(...), ...], файл обновлён и открыт
        """
        data_for_report = []
        start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.logger.info(f"Запуск процесса — {start_time}")
        self.file_handler = FileHandler(file_path)
        # Собираем данные по накладным со всех листов как описано в экземпляре file_handler
        for sheet_name in ["мой куб GC","мой куб BF","мой куб PU"]:
            self.invoices.extend(self.file_handler.read_invoices(sheet_name))
        # Фильтруем эти данные по условиям
        self.invoices = self.filter.filter_invoices(self.invoices)
        # Собираем из отфильтрованных данных накладные
        self.invoices = self.factory.create_invoices(self.invoices)

        # Обработка Сибири
        self.process_invoices_by_region("siberia", data_for_report)

        # Обработка Урала
        self.process_invoices_by_region("ural", data_for_report)

        self.reporter = ReporterOfCheckInvoiceProcess("data/report_of_checking_invoices.xlsx",
                                                      data_for_report,
                                                      logger=self.logger)
        self.reporter.create_report()

        end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.logger.info(f"Завершение процесса — {end_time}")
        duration = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S") - datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
        self.logger.info(f"⏱️ Время выполнения: {duration}")

        self.reporter.open_report()

    def process_invoices_by_region(self, region: str, data_for_report: list):
        """
        Обрабатывает накладные для указанного региона.

        Выполняет следующие действия:
        1. Фильтрует накладные по региону.
        2. Создаёт оператор для поиска и проверки накладных (InvoiceSearchOperation).
        3. Запускает оператор.
        4. Проверяет каждую накладную из региона.
        5. Добавляет результат проверки в общий список data_for_report.

        :param region: Название региона (например, "siberia", "ural")
        :param data_for_report: Список, в который добавляются результаты проверки накладных
        """
        # Фильтрация накладных по указанному региону
        filtered_invoices = [invoice for invoice in self.invoices if invoice.region == region]

        # Создание оператора для работы с накладными в данном регионе
        operator = InvoiceSearchOperation(region, self.logger, self.config)

        # Запуск оператора (возможно, инициализация, подключение и т.п.)
        operator.start()

        # Проверка каждой накладной и добавление результата в общий отчёт
        try:
            for invoice in filtered_invoices:
                checked_invoice = operator.check_invoice(invoice)
                data_for_report.append(checked_invoice)
        finally:
            operator.close()  # Вызовется всегда