"""
Модуль: view.py

Графический интерфейс для проверки накладных.
Позволяет:
- Выбрать Excel-файл.
- Выбрать лист из списка.
- Запустить проверку.
- Просмотреть лог.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QFileDialog
)
from PyQt5.QtCore import Qt

# Импорт процесса
from src.buisness_processes.check_invoices.process import InvoiceCheckerProcess
from src.core.logger import Logger

class CheckInvoicesWidget(QWidget):
    """
    Виджет для проверки накладных.
    """

    # Допустимые листы
    AVAILABLE_SHEETS = ["выгрузка_GC", "выгрузка_BF", "выгрузка_PU"]

    def __init__(self, logger: Logger):
        """
        :param logger: Экземпляр класса Logger - логирует результаты исполнения операций и процессов
        """
        super().__init__()
        self.logger = logger
        self.file_path = None
        self.process = InvoiceCheckerProcess(logger=self.logger)
        self._setup_ui()

    def _setup_ui(self):
        """Создаёт интерфейс."""
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)
        layout.setSpacing(12)

        # Заголовок
        title = QLabel("📦 Проверка накладных (Сибирь / Урал)")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #2c3e50; margin-bottom: 8px;")
        layout.addWidget(title)

        # Выбор файла
        file_layout = QHBoxLayout()
        self.file_label = QLabel("Файл не выбран")
        self.file_label.setStyleSheet("color: #7f8c8d; font-style: italic;")
        btn_browse = QPushButton("📂 Выбрать файл")
        btn_browse.clicked.connect(self._on_browse_file)
        file_layout.addWidget(self.file_label)
        file_layout.addWidget(btn_browse)
        layout.addLayout(file_layout)

        # Выбор листа
        sheet_layout = QHBoxLayout()
        sheet_layout.addWidget(QLabel("Лист:"))
        self.sheet_combo = QComboBox()
        self.sheet_combo.addItems(self.AVAILABLE_SHEETS)
        sheet_layout.addWidget(self.sheet_combo)
        layout.addLayout(sheet_layout)

        # Кнопка запуска
        self.btn_run = QPushButton("▶️ Запустить проверку")
        self.btn_run.clicked.connect(self._on_run_process)
        self.btn_run.setEnabled(False)
        layout.addWidget(self.btn_run)

        self.setLayout(layout)

    def _on_browse_file(self):
        """Обработчик выбора файла."""
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите Excel-файл с накладными",
            "",
            "Excel Files (*.xlsx)"
        )
        if path:
            self.file_path = path
            short_name = path.split("/")[-1]
            self.file_label.setText(f"✅ {short_name}")
            self.btn_run.setEnabled(True)
            self.logger.log(f"📎 Выбран файл: {short_name}")
        else:
            self.file_label.setText("Файл не выбран")
            self.btn_run.setEnabled(False)

    def _on_run_process(self):
        """Запуск процесса проверки."""
        if not self.file_path:
            self.logger.error("⚠️ Файл не выбран.")
            return

        sheet_name = self.sheet_combo.currentText()
        self.logger.log(f"🚀 Запуск проверки: лист='{sheet_name}'")

        try:
            results = self.process.run(self.file_path, sheet_name)

            found = sum(1 for _, f, s in results if s == "found")
            not_found = sum(1 for _, f, s in results if s == "not_found")
            errors = sum(1 for _, f, s in results if s in ("unknown", "error"))

            self.logger.log(f"✅ Готово: найдено={found}, не найдено={not_found}, ошибки={errors}")
            self.logger.log(f"🎨 Результаты сохранены в файл: {self.file_path}")

        except Exception as e:
            self.logger.error(f"❌ Ошибка при выполнении: {e}")