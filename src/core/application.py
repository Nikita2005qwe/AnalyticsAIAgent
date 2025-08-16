# src/core/application.py

"""
Модуль: application.py

Основное GUI-приложение — AI-агент для аналитика.

Особенности:
- Полноэкранный режим.
- Централизованное логирование через Logger.
- Вкладка "Настройки" с опцией записи логов в файл.
- Масштабируемая фабрика вкладок.
- Чёткое разделение на мелкие методы.
"""

import sys
from typing import List, Type
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTextEdit, QTabWidget, QFrame, QDesktopWidget
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
# Локальные модули
from src.core.logger import Logger
from src.core.settings_widget import SettingsWidget


class TabInterface:
    @staticmethod
    def create_widget(logger) -> QWidget:
        raise NotImplementedError


class PointManager:
    def create_trade_points(self, data): return {"success": len(data), "errors": []}
    def reassign_esr_bulk(self, ids, esr): return {"success": len(ids), "new_esr": esr}


class Application:
    def __init__(self):
        """Инициализация приложения: создаёт логгер, окно, компоненты."""
        self.qt_app = QApplication(sys.argv)
        # --- 1. Включаем поддержку высокого DPI ---
        if hasattr(Qt, 'AA_EnableHighDpiScaling'):
            self.qt_app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
            self.qt_app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

        # --- 2. Получаем размер экрана ---
        screen = QDesktopWidget().screenGeometry()
        self.screen_width = screen.width()
        self.screen_height = screen.height()

        # --- 3. Определяем масштабный коэффициент ---
        # База — Full HD (1920x1080), на нём UI выглядит нормально
        base_width = 1920
        base_height = 1080
        self.scale_factor = max(self.screen_width / base_width, self.screen_height / base_height)

        # Пример: на 2880x1920 → scale_factor ≈ 1.5–2.0
        print(f"Экран: {self.screen_width}x{self.screen_height}, масштаб: {self.scale_factor:.2f}x")

        # --- 4. Устанавливаем глобальный шрифт с масштабированием ---
        base_font_size = 20
        scaled_font_size = int(base_font_size * self.scale_factor)
        font = QFont("Segoe UI", scaled_font_size)
        font.setBold(False)
        self.qt_app.setFont(font)

        # --- 5. Устанавливаем стили с масштабированием ---
        self.qt_app.setStyleSheet(self._get_global_style())

        # --- 6. Создаём главное окно ---
        self.main_window = QMainWindow()
        self.main_window.setWindowTitle("AI-Агент для Аналитика")
        self.main_window.resize(int(1100 * self.scale_factor), int(750 * self.scale_factor))
        self.main_window.showMaximized()  # можно убрать, если хочешь точный размер

        self.logger = Logger()  # Центральный логгер
        self.point_manager = PointManager()
        self.tabs_registry: List[Type[TabInterface]] = []
        self._register_tabs()

        self.log_area = None  # будет создано позже
        self._setup_ui()

    def _register_tabs(self):
        """Регистрирует все вкладки."""
        from src.buisness_processes.check_invoices.view import CheckInvoicesWidget

        class CheckInvoicesTab(TabInterface):
            @staticmethod
            def create_widget(logger):
                return CheckInvoicesWidget(logger=logger)

        class SettingsTab(TabInterface):
            @staticmethod
            def create_widget(logger):
                return SettingsWidget(logger=logger)

        self.tabs_registry.append(CheckInvoicesTab)
        self.tabs_registry.append(SettingsTab)

    def _setup_ui(self):
        """Создаёт весь интерфейс."""
        central = QWidget()
        self.main_window.setCentralWidget(central)
        layout = QVBoxLayout()

        layout.addWidget(self._create_title())
        layout.addWidget(self._create_separator())
        layout.addLayout(self._create_tabs_layout())
        layout.addWidget(self._create_log_label())
        layout.addWidget(self._create_log_area())

        central.setLayout(layout)

    def _create_title(self) -> QLabel:
        """Создаёт заголовок приложения."""
        title = QLabel("AI-Агент для Аналитика")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Arial", 3, QFont.Bold))
        title.setStyleSheet("color: #2c3e50; margin: 10px;")
        return title

    def _create_separator(self) -> QFrame:
        """Создаёт горизонтальную линию."""
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        return line

    def _create_tabs_layout(self) -> QHBoxLayout:
        """Создаёт вкладки."""
        tabs = QTabWidget()

        # Статические вкладки (пример)
        tabs.addTab(self._create_placeholder_tab("Управление ТО"), "Управление ТО")
        tabs.addTab(self._create_placeholder_tab("Загрузка данных"), "Загрузка данных")

        # Динамические вкладки
        for tab_class in self.tabs_registry:
            try:
                widget = tab_class.create_widget(logger=self.logger)
                tab_name = self._get_tab_name(tab_class)
                tabs.addTab(widget, tab_name)
                self.logger.log(f"📌 Вкладка добавлена: {tab_name}")
            except Exception as e:
                self.logger.error(f"❌ Ошибка при создании вкладки: {e}")

        layout = QHBoxLayout()
        layout.addWidget(tabs)
        return layout

    def _create_placeholder_tab(self, title: str) -> QWidget:
        """Создаёт заглушку для временных вкладок."""
        tab = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(QLabel(f"🔹 {title} (заглушка)"))
        tab.setLayout(layout)
        return tab

    def _get_tab_name(self, tab_class: Type[TabInterface]) -> str:
        if "CheckInvoices" in tab_class.__name__: return "Проверка накладных"
        if "Settings" in tab_class.__name__: return "Настройки"
        return tab_class.__name__.replace("Tab", "").replace("Widget", "")

    def _create_log_label(self) -> QLabel:
        """Создаёт метку для лога."""
        return QLabel("Лог операций:")

    def _create_log_area(self) -> QTextEdit:
        """Создаёт текстовое поле для лога."""
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setStyleSheet("background-color: #f8f9fa; font-family: 'Courier'; font-size: 12px;")
        self.log_area.setMaximumHeight(200)

        # Подключаем сигнал логгера
        self.logger.log_signal.connect(self.log_area.append)

        return self.log_area

    def _get_global_style(self) -> str:
        # Базовые размеры в "условных единицах", масштабируются
        def px(size: int) -> str:
            return f"{int(size * self.scale_factor)}px"

        return f"""
        * {{
            font-family: 'Segoe UI', 'Arial', sans-serif;
            font-size: {px(14)};
        }}

        QLabel {{
            font-size: {px(35)};
            color: #2c3e50;
        }}

        QLabel#title {{
            font-size: {px(35)};
            font-weight: bold;
            color: #1a3b5d;
        }}

        QPushButton {{
            background-color: #3498db;
            color: white;
            border: none;
            padding: {px(12)} {px(20)};
            border-radius: {px(8)};
            font-size: {px(30)};
            font-weight: bold;
            min-height: {px(10)};
        }}

        QPushButton:hover {{
            background-color: #2980b9;
        }}

        QPushButton:pressed {{
            background-color: #1f618d;
        }}

        QTabBar::tab {{
            background-color: #bdc3c7;
            color: #2c3e50;
            padding: {px(12)} {px(20)};
            margin: {px(2)};
            border-top-left-radius: {px(6)};
            border-top-right-radius: {px(6)};
            font-size: {px(14)};
            min-width: {px(120)};
            min-height: {px(40)};
        }}

        QTabBar::tab:selected {{
            background-color: #3498db;
            color: white;
        }}

        QCheckBox {{
            spacing: {px(8)};
            font-size: {px(14)};
        }}

        QCheckBox::indicator {{
            width: {px(18)};
            height: {px(18)};
        }}

        QTextEdit {{
            background-color: #ffffff;
            border: 1px solid #dcdde1;
            border-radius: {px(6)};
            font-family: 'Courier New', monospace;
            font-size: {px(12)};
            padding: {px(8)};
            min-height: {px(100)};
        }}

        QComboBox {{
            padding: {px(8)} {px(12)};
            border: 1px solid #bdc3c7;
            border-radius: {px(6)};
            min-height: {px(36)};
            font-size: {px(14)};
        }}

        QComboBox::drop-down {{
            width: {px(30)};
            border-left: 1px solid #bdc3c7;
        }}
        """

    def run(self):
        """Запускает приложение."""
        self.main_window.show()
        try:
            sys.exit(self.qt_app.exec_())
        finally:
            self.logger.close()