"""
Модуль: application.py

Класс Application — основа графического интерфейса AI-агента для аналитика.
Является точкой входа в GUI и координирует взаимодействие пользователя с бизнес-логикой приложения.

Отвечает за:
- Создание и настройку главного окна приложения
- Организацию интерфейса по вкладкам (Управление ТО, загрузка данных и др.)
- Обработку пользовательских действий: создание и перепривязку торговых точек
- Вывод результатов операций и ошибок в лог-область

Основные компоненты:
- Главное окно на базе QMainWindow
- Вкладки: «Управление ТО», «Загрузка данных» и др.
- Поля ввода и кнопки для ручного и массового ввода данных
- Обработчики событий: _on_create_single, _on_reassign_single, _on_bulk_reassign и др.
- Интеграция с PointManager для выполнения бизнес-операций

Зависимости:
- PyQt5 — реализация графического интерфейса
- src.business.point_manager.PointManager — выполнение операций с торговыми точками
"""

import sys
from typing import Any, Dict, List
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QLineEdit,
    QTabWidget,
    QFileDialog,
    QFrame,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

# Временная заглушка — будет заменена на реальный PointManager
class PointManager:
    """Заглушка для бизнес-логики. Пока эмулирует создание и перепривязку ТО."""
    def create_trade_points(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        return {"success": len(data), "errors": []}

    def reassign_esr_bulk(self, point_ids: List[str], new_esr: str) -> Dict[str, Any]:
        return {"success": len(point_ids), "failed": 0, "new_esr": new_esr}


class Application:
    """Основной класс GUI-приложения — AI-агент для аналитика."""

    def __init__(self):
        """Инициализирует приложение и настраивает интерфейс."""
        self.qt_app = QApplication(sys.argv)
        self.main_window = QMainWindow()
        self.main_window.setWindowTitle("🧠 AI-Агент для Аналитика")
        self.main_window.resize(1100, 750)

        # Инициализация бизнес-логики
        self.point_manager = PointManager()

        # Элементы интерфейса
        self.log_area: QTextEdit
        self.bulk_input: QTextEdit

        self._setup_ui()

    def _setup_ui(self):
        """Создаёт и размещает все элементы интерфейса."""
        central_widget = QWidget()
        self.main_window.setCentralWidget(central_widget)
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

        # --- Вкладка: Управление ТО ---
        tab_to = self._create_trade_point_tab()
        tabs.addTab(tab_to, "Управление ТО")

        # --- Вкладка: Загрузка данных ---
        tab_data = self._create_data_tab()
        tabs.addTab(tab_data, "Загрузка данных")

        layout.addWidget(tabs)

        # --- Лог ---
        layout.addWidget(QLabel("Лог операций:"))
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setStyleSheet("background-color: #f8f9fa; font-family: 'Courier';")
        self.log_area.setMaximumHeight(200)
        layout.addWidget(self.log_area)

        central_widget.setLayout(layout)

    def _create_trade_point_tab(self) -> QWidget:
        """Создаёт вкладку для управления торговыми точками."""
        tab = QWidget()
        layout = QVBoxLayout()

        # --- Создание одной ТО ---
        layout.addWidget(QLabel("🔹 Создать одну торговую точку"))
        grid = self._create_input_grid(
            fields=["Контрагент", "Адрес", "Тип ТТ", "Специализация", "Местонахождение", "Площадь", "код территории привязки", "Название сети"],
            prefix="create_"
        )
        layout.addLayout(grid)

        btn_create_single = QPushButton("➕ Создать точку")
        btn_create_single.clicked.connect(self._on_create_single)
        layout.addWidget(btn_create_single)

        # --- Массовое создание ---
        layout.addWidget(QLabel("\n🔹 Массовое создание из JSON"))
        self.bulk_input = QTextEdit()
        self.bulk_input.setPlaceholderText('Список ТО в формате JSON:\n[{"Контрагент": "...", "Адрес": "...", ...}]')
        self.bulk_input.setMaximumHeight(120)
        layout.addWidget(self.bulk_input)

        btn_bulk_create = QPushButton("📁 Создать из JSON")
        btn_bulk_create.clicked.connect(self._on_bulk_create)
        layout.addWidget(btn_bulk_create)

        # --- Перепривязка ---
        layout.addWidget(QLabel("\n🔹 Перепривязать ТО к новому ESR"))
        reassign_layout = QHBoxLayout()
        self.le_reassign_esr = QLineEdit()
        self.le_reassign_esr.setPlaceholderText("Новый код территории привязки (ESR)")
        reassign_layout.addWidget(self.le_reassign_esr)
        btn_reassign = QPushButton("🔄 Перепривязать все")
        btn_reassign.clicked.connect(self._on_reassign_bulk)
        reassign_layout.addWidget(btn_reassign)
        layout.addLayout(reassign_layout)

        tab.setLayout(layout)
        return tab

    def _create_data_tab(self) -> QWidget:
        """Создаёт вкладку для загрузки данных."""
        tab = QWidget()
        layout = QVBoxLayout()

        layout.addWidget(QLabel("📥 Загрузка данных из 1С"))
        layout.addWidget(QLabel("Здесь можно загрузить JSON, экспортированный из 1С."))

        btn_load_json = QPushButton("📂 Загрузить JSON из 1С")
        btn_load_json.clicked.connect(self._on_load_json)
        layout.addWidget(btn_load_json)

        self.label_file_status = QLabel("Файл не загружен")
        layout.addWidget(self.label_file_status)

        tab.setLayout(layout)
        return tab

    def _create_input_grid(self, fields: List[str], prefix: str) -> QVBoxLayout:
        """Создаёт сетку полей ввода."""
        layout = QVBoxLayout()
        grid = QHBoxLayout()
        col1 = QVBoxLayout()
        col2 = QVBoxLayout()

        self._input_fields = {}

        for i, field in enumerate(fields):
            label = QLabel(f"{field}:")
            line_edit = QLineEdit()
            line_edit.setPlaceholderText(f"Введите {field.lower()}")
            self._input_fields[f"{prefix}{field}"] = line_edit

            (col1 if i % 2 == 0 else col2).addWidget(label)
            (col1 if i % 2 == 0 else col2).addWidget(line_edit)

        grid.addLayout(col1)
        grid.addLayout(col2)
        layout.addLayout(grid)
        return layout

    def _on_create_single(self):
        """
        
        Обработчик создания одной торговой точки.
        
        Тут будет расположена логика создания точки.
        """
        data = {}
        for key, field in self._input_fields.items():
            if key.startswith("create_"):
                value = field.text().strip()
                if not value:
                    self._log(f"⚠️ Не заполнено поле: {key[7:]}")
                    return
                data[key[7:]] = value

        try:
            result = self.point_manager.create_trade_points([data])
            self._log(f"✅ Успешно создана ТО: {data['Контрагент']} → {data['Адрес']}")
        except Exception as e:
            self._log(f"❌ Ошибка при создании: {e}")

    def _on_bulk_create(self):
        """
        Обработчик массового создания из JSON.
        
        Используем эту функцию для обращения к классам программы, реализующим бизнес логику создания ТТ
        """
        json_text = self.bulk_input.toPlainText().strip()
        if not json_text:
            self._log("⚠️ JSON пуст")
            return

        try:
            import json
            data_list = json.loads(json_text)
            if not isinstance(data_list, list):
                raise ValueError("Ожидается список объектов")
            result = self.point_manager.create_trade_points(data_list)
            self._log(f"✅ Создано {result['success']} точек. Ошибок: {len(result['errors'])}")
        except Exception as e:
            self._log(f"❌ Ошибка в JSON или данных: {e}")

    def _on_reassign_bulk(self):
        """
        Обработчик массовой перепривязки.
        
        
        Обращаемся к данному методу для массовой перепривязки территории ESR для списка торговых точек у которых указан GUID
        """
        new_esr = self.le_reassign_esr.text().strip()
        if not new_esr:
            self._log("⚠️ Укажите новый код территории привязки (ESR)")
            return

        try:
            # Пока заглушка — в реальности список ID может быть из таблицы или файла
            mock_ids = ["T001", "T002"]  # Пример
            result = self.point_manager.reassign_esr_bulk(mock_ids, new_esr)
            self._log(f"🔄 Перепривязано {result['success']} точек к ESR: {new_esr}")
        except Exception as e:
            self._log(f"❌ Ошибка при перепривязке: {e}")

    def _on_load_json(self):
        """
        Загрузка JSON-файла из 1С.
        
        
        """
        file_path, _ = QFileDialog.getOpenFileName(
            self.main_window,
            "Загрузить JSON из 1С",
            "",
            "JSON Files (*.json);;All Files (*)"
        )
        if file_path:
            self.label_file_status.setText(f"✅ Загружено: {file_path.split('/')[-1]}")
            self._log(f"📥 Загружен файл: {file_path}")
        else:
            self.label_file_status.setText("❌ Загрузка отменена")

    def _log(self, message: str):
        """
        Добавляет сообщение в лог с временной меткой.
        
        Функция которую нужно перенести в отдельный класс Logger
        """
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_area.append(f"[{timestamp}] {message}")

    def run(self):
        """Запускает приложение."""
        self.main_window.show()
        sys.exit(self.qt_app.exec_())