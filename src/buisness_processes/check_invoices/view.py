"""
Модуль: view.py
Описание: Минималистичный GUI для запуска проверки накладных.
Функционал: выбрать файл → нажать "Запустить"
"""

# --- Стандартная библиотека ---
import os

# --- PyQt5 ---
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFileDialog,
    QFrame,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

# --- Локальные импорты ---
from src.core.logger import Logger
from src.core.config import Config
from src.buisness_processes.check_invoices.process import InvoiceCheckerProcess


class CheckInvoicesView(QWidget):
    """
    Виджет: выбор файла Excel → запуск проверки.
    Никакой лишней функциональности.
    """

    def __init__(self, logger: Logger, config: Config):
        super().__init__()
        self.logger = logger
        self.config = config
        self.process = InvoiceCheckerProcess(logger, config)

        # === Атрибуты UI ===
        self.file_path = None
        self.navigation_button = None
        self.file_label = None
        self.run_button = None

        # === Кнопка навигации ===
        self.navigation_button = self.get_navigation_button()

        # === Инициализация интерфейса ===
        self._setup_ui()
        self._connect_signals()

        # === Начальное состояние ===
        self.run_button.setEnabled(False)

    def get_navigation_button(self) -> QPushButton:
        """
        Возвращает стилизованную кнопку для бокового меню.
        Согласована со стилем 'Настройки'.
        """
        button = QPushButton("📦 Проверка накладных")
        button.setCheckable(True)
        button.setToolTip("Запустить процесс проверки накладных из Excel")
        button.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 12px 15px;
                font-size: 14px;
                font-weight: 500;
                border: none;
                background-color: #f0f0f0;
                color: #202124;
                border-radius: 8px;
                margin: 4px 8px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QPushButton:checked {
                background-color: #4285f4;
                color: white;
                font-weight: 600;
            }
            QPushButton:checked:hover {
                background-color: #3367d6;
            }
            QPushButton:pressed {
                background-color: #3367d6;
            }
        """)
        button.setCursor(Qt.PointingHandCursor)
        return button

    def _setup_ui(self):
        """Настраивает интерфейс: заголовок, выбор файла, кнопка запуска."""
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(25, 25, 25, 25)
        self.setLayout(layout)

        # === Заголовок ===
        title = QLabel("📦 Проверка накладных")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title.setStyleSheet("color: #1a73e8; margin-bottom: 10px;")
        layout.addWidget(title)

        subtitle = QLabel("Выберите файл и запустите проверку.")
        subtitle.setStyleSheet("color: #5f6368; font-size: 12px;")
        layout.addWidget(subtitle)

        # === Разделитель ===
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("background-color: #dadce0; height: 1px;")
        layout.addWidget(line)

        # === Блок выбора файла ===
        file_layout = QHBoxLayout()
        self.file_label = QLabel("📁 Файл не выбран")
        self.file_label.setStyleSheet("color: #5f6368; font-style: italic;")

        browse_btn = QPushButton("📂 Выбрать файл")
        browse_btn.setObjectName("browse_file_button")
        browse_btn.setCursor(Qt.PointingHandCursor)
        browse_btn.setStyleSheet("""
            QPushButton {
                background-color: #1a73e8;
                color: white;
                padding: 10px 16px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1765cc;
            }
        """)

        file_layout.addWidget(self.file_label)
        file_layout.addStretch()
        file_layout.addWidget(browse_btn)
        layout.addLayout(file_layout)

        # === Крупная кнопка запуска ===
        self.run_button = QPushButton("▶️ Запустить проверку")
        self.run_button.setObjectName("run_process_button")
        self.run_button.setCursor(Qt.PointingHandCursor)
        self.run_button.setStyleSheet("""
            QPushButton {
                background-color: #34a853;
                color: white;
                padding: 16px 24px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 16px;
                min-height: 60px;
                margin-top: 15px;
            }
            QPushButton:hover {
                background-color: #2e9147;
            }
            QPushButton:disabled {
                background-color: #dadce0;
                color: #9aa0a6;
            }
        """)
        layout.addWidget(self.run_button)

        # === Растяжка вниз ===
        layout.addStretch()

    def _connect_signals(self):
        """Подключает сигналы к обработчикам."""
        # Кнопка "Выбрать файл"
        browse_btn = self.findChild(QPushButton, "browse_file_button")
        if browse_btn:
            browse_btn.clicked.connect(self._on_browse_file)
        else:
            self.logger.error("❌ Кнопка 'Выбрать файл' не найдена")

        # Кнопка "Запустить проверку"
        self.run_button.clicked.connect(self._on_run_process)

    def _on_browse_file(self):
        """Обработчик выбора файла."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите Excel-файл",
            "",
            "Excel Files (*.xlsx);;All Files (*)"
        )
        if not file_path:
            return

        if not os.path.exists(file_path):
            self.logger.error(f"❌ Файл не существует: {file_path}")
            return

        self.file_path = file_path
        filename = os.path.basename(file_path)
        self.file_label.setText(f"✅ Выбран файл: <b>{filename}</b>")
        self.file_label.setStyleSheet("color: #34a853; font-size: 13px;")
        self.run_button.setEnabled(True)
        self.logger.info(f"📎 Выбран файл: {filename}")

    def _on_run_process(self):
        """Запуск процесса проверки."""
        if not self.file_path:
            self.logger.error("❌ Файл не выбран. Невозможно запустить проверку.")
            return

        try:
            self.logger.info(f"🚀 Запуск проверки: {os.path.basename(self.file_path)}")
            self.process.run(self.file_path)
            self.logger.info("✅ Проверка завершена. Отчёт открыт.")
        except Exception as e:
            self.logger.error(f"❌ Ошибка при выполнении процесса: {e}")

    def activate(self):
        self.logger.info("Вкладка 'Проверка накладных' активирована")

    def deactivate(self):
        self.logger.info("Вкладка 'Проверка накладных' деактивирована")