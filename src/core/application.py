"""
Модуль: application.py

Основное GUI-приложение — AI-агент для аналитика.
Поддерживает динамическое добавление вкладок через фабрику.
"""

import sys
from typing import List, Type
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit, QTabWidget, QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


# --- Интерфейс для вкладок ---
class TabInterface:
    @staticmethod
    def create_widget(log_callback) -> QWidget:
        raise NotImplementedError


# --- Заглушка бизнес-логики (временно) ---
class PointManager:
    def create_trade_points(self, data): return {"success": len(data), "errors": []}
    def reassign_esr_bulk(self, ids, esr): return {"success": len(ids), "new_esr": esr}


class Application:
    def __init__(self):
        """Инициализация приложения."""
        self.qt_app = QApplication(sys.argv)
        self.main_window = QMainWindow()
        self.main_window.setWindowTitle("🧠 AI-Агент для Аналитика")
        self.main_window.resize(1100, 750)

        self.point_manager = PointManager()
        self.tabs_registry: List[Type[TabInterface]] = []
        self._register_tabs()
        self._setup_ui()

    def _register_tabs(self):
        """Регистрирует все вкладки."""
        from src.buisness_processes.check_invoices.view import CheckInvoicesWidget

        class CheckInvoicesTab(TabInterface):
            @staticmethod
            def create_widget(log_callback):
                return CheckInvoicesWidget(log_callback=log_callback)

        self.tabs_registry.append(CheckInvoicesTab)

        # Сюда можно добавить другие вкладки в будущем
        # class CreateTradePointsTab(TabInterface): ...
        # self.tabs_registry.append(CreateTradePointsTab)

    def _setup_ui(self):
        """Создаёт интерфейс."""
        central = QWidget()
        self.main_window.setCentralWidget(central)
        layout = QVBoxLayout()

        # Заголовок
        title = QLabel("AI-Агент для Аналитика")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setStyleSheet("color: #2c3e50; margin: 10px;")
        layout.addWidget(title)

        # Разделитель
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)

        # Вкладки
        tabs = QTabWidget()

        # Статические вкладки (пример)
        tabs.addTab(self._create_trade_point_tab(), "Управление ТО")
        tabs.addTab(self._create_data_tab(), "Загрузка данных")

        # Лог
        layout.addWidget(QLabel("Лог операций:"))
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setStyleSheet("background-color: #f8f9fa; font-family: 'Courier'; font-size: 12px;")
        self.log_area.setMaximumHeight(200)
        layout.addWidget(self.log_area)

        # Динамические вкладки
        for tab_class in self.tabs_registry:
            try:
                widget = tab_class.create_widget(log_callback=self._log)
                tab_name = self._get_tab_name(tab_class)
                tabs.addTab(widget, tab_name)
                self._log(f"📌 Вкладка добавлена: {tab_name}")
            except Exception as e:
                self._log(f"❌ Ошибка при создании вкладки: {e}")

        layout.addWidget(tabs)



        central.setLayout(layout)

    def _get_tab_name(self, tab_class: Type[TabInterface]) -> str:
        """Определяет имя вкладки по классу."""
        name = tab_class.__name__
        if "CheckInvoices" in name: return "Проверка накладных"
        if "CreateTradePoints" in name: return "Создание ТТ"
        return name.replace("Tab", "").replace("Widget", "")

    # --- Примеры вкладок (можно оставить или удалить) ---
    def _create_trade_point_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("🔹 Управление торговыми точками (заглушка)"))
        btn = QPushButton("Пример кнопки")
        btn.clicked.connect(lambda: self._log("Кнопка нажата"))
        layout.addWidget(btn)
        tab.setLayout(layout)
        return tab

    def _create_data_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("📥 Загрузка данных (заглушка)"))
        btn = QPushButton("Загрузить JSON")
        btn.clicked.connect(lambda: self._log("Загрузка JSON"))
        layout.addWidget(btn)
        tab.setLayout(layout)
        return tab

    def _log(self, message: str):
        """Добавляет сообщение в лог с временем."""
        from datetime import datetime
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_area.append(f"[{ts}] {message}")

    def run(self):
        """Запускает приложение."""
        self.main_window.show()
        sys.exit(self.qt_app.exec_())