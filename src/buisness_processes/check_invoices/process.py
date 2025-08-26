"""
Модуль: process.py
Описание: Процесс проверки накладных из Excel-файла.

Назначение:
- Управление полным циклом проверки:
  - Загрузка номеров через FileHandler,
  - Фильтрация по бизнес-правилам,
  - Группировка по регионам,
  - Последовательный запуск поиска для каждого региона,
  - Сохранение промежуточных и финальных результатов через Reporter.
- Поддержка двух режимов:
  - "full": полная проверка исходного файла
  - "update": обновление существующего отчёта (только not_found)
- Не зависеть от деталей работы с Excel.
- Использовать FileHandler как единый интерфейс к файлам.

Архитектурная роль:
- Оркестратор: управляет жизненным циклом проверки.
- Координирует: FileHandler → InvoiceSearchOperation → Reporter.
- Не знает, как читать/писать Excel — только что и когда.

Зависимости:
- InvoiceSearchOperation (операция поиска)
- Logger (логирование)
- FileHandler (работа с Excel)
- ReporterOfCheckInvoiceProcess (генерация отчёта)
- models.invoice: Invoice, InvoiceFactory, FilterInvoices
"""

from datetime import datetime
from typing import List

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
    - file_handler (FileHandler): Для загрузки и сохранения Excel
    - factory (InvoiceFactory): Для создания объектов Invoice
    - filter (FilterInvoices): Для фильтрации по бизнес-правилам
    - reporter (ReporterOfCheckInvoiceProcess): Для генерации отчёта
    - invoices (List[Invoice]): Список накладных для проверки
    - config (Config): Конфигурация приложения
    """

    def __init__(self, logger: Logger, config: Config):
        self.logger = logger
        self.config = config
        self.file_handler = None
        self.factory = InvoiceFactory()
        self.filter = FilterInvoices()
        self.reporter = None
        self.invoices = []

    def run(self, file_path: str, mode: str = "full"):
        """
        Запускает процесс проверки накладных в указанном режиме.

        Поддерживаемые режимы:
        - "full": полная проверка всех накладных из исходного файла
        - "update": обновление существующего отчёта — проверяются только not_found

        Args:
            file_path (str): Путь к файлу:
                - Если mode="full": исходный Excel (например, "мой куб GC")
                - Если mode="update": существующий отчёт (report_of_checking_invoices.xlsx)
            mode (str): Режим выполнения. По умолчанию "full".

        Returns:
            None

        Исключения:
            - Логируются через self.logger
            - При ошибках чтения/записи — процесс частично сохраняет результаты

        Примеры:
            # Полная проверка
            process.run("data/invoices.xlsx", mode="full")

            # Обновление отчёта
            process.run("data/report_of_checking_invoices.xlsx", mode="update")
        """
        start_time = datetime.now()
        self.logger.info(f"🚀 Запуск процесса — {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

        try:
            # === Определяем режим выполнения ===
            if mode == "update":
                self._run_update_mode(file_path)
            else:
                self._run_full_mode(file_path)

        except Exception as e:
            self.logger.error(f"❌ Критическая ошибка в процессе: {e}")
        finally:
            end_time = datetime.now()
            duration = end_time - start_time
            self.logger.info(f"⏱️ Время выполнения: {duration}")

    def _run_full_mode(self, file_path: str):
        """
        Режим: полная проверка всех накладных из исходного файла.

        Шаги:
        1. Инициализируем FileHandler
        2. Читаем накладные с листов: "мой куб GC", "мой куб BF", "мой куб PU"
        3. Фильтруем по бизнес-правилам (например, ISA > 0)
        4. Создаём объекты Invoice
        5. Проверяем по регионам
        6. Генерируем отчёт
        """
        self.logger.info("🔄 Режим: полная проверка")

        # 1. Инициализация
        self.file_handler = FileHandler(file_path, self.logger)

        # 2. Чтение данных со всех листов
        raw_data = []
        for sheet_name in ["мой куб GC", "мой куб BF", "мой куб PU"]:
            try:
                data = self.file_handler.read_invoices(sheet_name)
                self.logger.info(f"✅ Прочитано {len(data)} накладных с листа '{sheet_name}'")
                raw_data.extend(data)
            except Exception as e:
                self.logger.warning(f"⚠️ Ошибка при чтении листа '{sheet_name}': {e}")

        if not raw_data:
            self.logger.warning("⚠️ Нет данных для обработки")
            return

        # 3. Фильтрация
        filtered_data = self.filter.filter_invoices(raw_data)
        self.logger.info(f"📊 Фильтрация: {len(raw_data)} → {len(filtered_data)} накладных")

        # 4. Создание объектов Invoice
        self.invoices = self.factory.create_invoices(filtered_data)
        self.logger.info(f"📦 Подготовлено {len(self.invoices)} накладных для проверки")

        # 5. Проверка по регионам
        data_for_report = []
        self._process_region("siberia", data_for_report)
        self._process_region("ural", data_for_report)

        # 6. Генерация отчёта
        self._generate_report(file_path, data_for_report, is_update=False)

    def _run_update_mode(self, report_path: str):
        """
        Режим: обновление существующего отчёта.

        Логика:
        1. Читаем отчёт, оставляем только накладные со статусом "not_found"
        2. Создаём объекты Invoice
        3. Проверяем их заново
        4. Перезаписываем тот же файл с обновлёнными статусами

        Преимущество: не проверяем уже найденные накладные.
        """
        self.logger.info("🔄 Режим: обновление отчёта")

        # 1. Инициализация
        self.file_handler = FileHandler(report_path, self.logger)

        # 2. Чтение только not_found накладных из отчёта
        raw_data = self.file_handler.read_existing_report(report_path)
        if not raw_data:
            self.logger.warning("⚠️ Нет накладных для обновления (все найдены)")
            return

        # 3. Создание объектов Invoice
        self.invoices = self.factory.create_invoices(raw_data)
        self.logger.info(f"📦 Подготовлено {len(self.invoices)} накладных для повторной проверки")

        # 4. Проверка по регионам
        data_for_report = []
        self._process_region("siberia", data_for_report)
        self._process_region("ural", data_for_report)

        # 5. Обновление отчёта
        self._generate_report(report_path, data_for_report, is_update=True)

    def _process_region(self, region: str, data_for_report: List):
        """
        Проверяет накладные для указанного региона.

        Args:
            region (str): "siberia" или "ural"
            data_for_report (List): Список для добавления результатов
        """
        filtered_invoices = [inv for inv in self.invoices if inv.region == region]
        if not filtered_invoices:
            self.logger.info(f"✅ {region.upper()}: нет накладных для проверки")
            return

        self.logger.info(f"🔍 Начинаем проверку региона: {region.upper()} ({len(filtered_invoices)} накладных)")

        operator = InvoiceSearchOperation(region, self.logger, self.config)
        operator.start()
        try:
            for invoice in filtered_invoices:
                checked_invoice = operator.check_invoice(invoice)
                data_for_report.append(checked_invoice)
        finally:
            operator.close()

        self.logger.info(f"✅ Регион {region.upper()} проверен")

    def _generate_report(self, source_path: str, data_for_report: List, is_update: bool):
        """
        Генерирует или обновляет отчёт.

        Args:
            source_path (str): Путь к исходному файлу или отчёту
            data_for_report (List): Список CheckedInvoice
            is_update (bool): True — обновление, False — новый отчёт
        """
        # Путь к отчёту
        report_path = "data/report_of_checking_invoices.xlsx"

        self.reporter = ReporterOfCheckInvoiceProcess(
            file_name=report_path,
            data=data_for_report,
            logger=self.logger
        )

        if is_update:
            self.reporter.update_report(report_path, data_for_report)
            self.logger.info(f"✅ Отчёт обновлён: {report_path}")
        else:
            self.reporter.create_report()
            self.logger.info(f"✅ Отчёт создан: {report_path}")

        # Открываем отчёт
        self.reporter.open_report()