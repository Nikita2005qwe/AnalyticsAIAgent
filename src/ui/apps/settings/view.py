"""
Модуль: view.py
Класс: SettingsAppView

Описание: Виджет вкладки "Настройки" — позволяет управлять параметрами приложения.

Назначение:
- Отображать ключевые настройки (например, 'full_log')
- Предоставлять кнопку "Сохранить"
- Вызывать config.save() при сохранении
- Быть частью главного окна как вкладка

Архитектурная роль:
- UI-интерфейс для редактирования config
- Не содержит логики сохранения — только вызывает config.save()
- Получает config и logger через DI

Версия: v0.1
Автор: Боряков
Дата: 21.08.2025
Статус: Разработан
"""

# --- Стандартная библиотека ---
from typing import Any

# --- PyQt5 ---
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QCheckBox,
    QPushButton,
    QFrame, QLineEdit
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

# --- Локальные импорты ---
from src.core.config import Config
from src.core.logger import Logger


class SettingsAppView(QWidget):
    """
    Виджет вкладки "Настройки".

    Атрибуты:
    - config (Config): объект конфигурации
    - logger (Logger): глобальный логгер
    - full_log_checkbox (QCheckBox): чекбокс для опции 'full_log'
    """

    def __init__(self, logger: Logger, config: Config):
        """
        Инициализирует вкладку "Настройки".

        Args:
            config (Config): объект конфигурации
            logger (Logger): глобальный логгер

        Шаги:
        1. Сохранить config и logger
        2. Вызвать super().__init__()
        3. Вызвать self._setup_ui()
        4. Вызвать self._load_settings() — загрузить текущие значения
        5. Вызвать self._connect_signals() — подключить события

        Примечание:
        - Все настройки читаются из config.get(key)
        - При старте отображаются текущие значения
        """
        super().__init__()
        self.config = config
        self.logger = logger

        self.full_log_checkbox = None

        self._setup_ui()
        self._load_settings()
        self._connect_signals()
        self.logger.info("Вкладка 'Настройки': инициализирована")

    def _setup_ui(self):
        """
        Настраивает визуальный интерфейс.
        """
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # === Заголовок ===
        title = QLabel("⚙️ Настройки приложения")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        title.setAlignment(Qt.AlignLeft)
        layout.addWidget(title)

        # === Разделитель ===
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)

        # === Полный лог ===
        self.full_log_checkbox = QCheckBox("Включить полное логирование")
        layout.addWidget(self.full_log_checkbox)
        # Чекбокс "Развернуть"
        self.maximized_checkbox = QCheckBox("Запускать развёрнутым")
        layout.addWidget(self.maximized_checkbox)

        # === Размер окна ===
        size_label = QLabel("Размер окна (ширина x высота):")
        layout.addWidget(size_label)

        # Поле для ширины
        width_input = QLineEdit()
        width_input.setText(str(self.config.get("window_size", [1920, 1080])[0]))
        width_input.setFixedWidth(80)
        layout.addWidget(width_input)

        # Поле для высоты
        height_input = QLineEdit()
        height_input.setText(str(self.config.get("window_size", [1920, 1080])[1]))
        height_input.setFixedWidth(80)
        layout.addWidget(height_input)

        # === Кнопка "Сохранить" ===
        save_btn = QPushButton("💾 Сохранить настройки")
        save_btn.setFixedWidth(300)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        layout.addWidget(save_btn)
        layout.addStretch()  # Растягивает вниз

        self.setLayout(layout)

        # Сохраняем ссылки
        self.save_button = save_btn
        self.width_input = width_input
        self.height_input = height_input

    def _load_settings(self):
        """
        Загружает текущие настройки из config и отображает их в интерфейсе.
        """
        full_log = self.config.get("full_log", False)
        self.maximized_checkbox.setChecked(self.config.get("maximized", False))
        self.full_log_checkbox.setChecked(full_log)

    def _connect_signals(self):
        """
        Подключает сигналы к обработчикам.
        """
        self.save_button.clicked.connect(self._on_save_clicked)

    def _on_save_clicked(self):
        """
        Обработчик нажатия кнопки "Сохранить".
        """
        # 1. Считываем значения
        full_log = self.full_log_checkbox.isChecked()
        width = int(self.width_input.text())
        height = int(self.height_input.text())
        maximized = self.maximized_checkbox.isChecked()

        # 2. Сохраняем в config
        self.config.set("full_log", full_log)
        self.config.set("window_size", [width, height])
        self.config.set("maximized", maximized)

        # 3. Сохраняем в файл
        try:
            self.config.save()
            self.logger.info(f"Настройки сохранены: full_log={full_log}, window_size=({width}, {height})")

            # 4. Применяем изменения
            self.config.apply_settings()

        except Exception as e:
            self.logger.error(f"Ошибка при сохранении настроек: {e}")

    def get_navigation_button(self) -> QPushButton:
        """
        Возвращает стилизованную кнопку для бокового меню.
        Согласована со стилем 'Проверка накладных'.
        """
        btn = QPushButton("⚙️ Настройки")
        btn.setCheckable(True)
        btn.setToolTip("Открыть настройки приложения")
        btn.setStyleSheet("""
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
        btn.setCursor(Qt.PointingHandCursor)
        return btn