"""
Класс: LogWidget
Описание: Виджет для отображения логов приложения в реальном времени.

Назначение:
- Показывать логи, генерируемые `Logger`, в графическом интерфейсе.
- Позволять пользователю:
  - Просматривать логи (даже если виджет был скрыт ранее),
  - Копировать текст (например, для отчёта или диагностики),
  - Видеть цветовую индикацию уровней (INFO, WARNING, ERROR),
  - Управлять авто-прокруткой.
- Работать в фоне: логи **сохраняются в буфер**, даже если виджет скрыт.
- Быть частью главного окна (например, как вкладка или панель).

Архитектурная роль:
- Подписчик на события логгера (паттерн **Observer**).
- UI-компонент, не отвечающий за логику, а только за **отображение**.
- Связующее звено между `Logger` (core) и пользователем.

Версия: v0.1
Автор: Боряков
Дата: 21.08.2025
Статус: Полностью готов
"""

from PyQt5.QtWidgets import QWidget, QTextEdit, QVBoxLayout, QCheckBox, QAction, QMenu
from PyQt5.QtCore import pyqtSignal, QObject, Qt
from src.core.signals import log_signal


class LogWidget(QWidget):
    def __init__(self):
        """
        Инициализирует виджет для отображения логов.

        Атрибуты:
        - text_edit (QTextEdit): Поле с логами (только для чтения).
        - auto_scroll (QCheckBox): Включает/выключает авто-прокрутку.
        - log_signal (LogSignal): Сигнал, на который подписывается виджет.
        - log_buffer (list): Хранит все логи (даже при скрытии).
        - is_visible (bool): Флаг — виден ли виджет в данный момент.
        """
        super().__init__()
        self.text_edit = None
        self.auto_scroll = None
        self.log_signal = log_signal
        self.log_buffer = []
        self.is_visible = False
        self.setup_ui()
        self.connect_signals()

    def setup_ui(self):
        """
        Настраивает визуальную часть виджета.

        Шаги:
        1. Создать QVBoxLayout как основной layout.
        2. Создать QTextEdit:
           - Установить read-only (только для чтения),
           - Отключить перенос строк (word wrap),
           - Настроить моноширинный шрифт (например, 'Consolas', 'Courier New').
        3. Создать QCheckBox с текстом "Авто-прокрутка" — включена по умолчанию.
        4. Добавить контекстное меню:
           - "Копировать" → вызывает copy_logs()
           - "Очистить" → вызывает clear_logs()
        5. Добавить элементы в layout:
           - Сначала text_edit,
           - Затем auto_scroll.
        6. Применить layout к виджету.

        Примечание:
        - QTextEdit идеален: поддерживает HTML, цвета, прокрутку, копирование.
        - Моноширинный шрифт улучшает читаемость логов.
        """
        layout = QVBoxLayout()
        layout.setSpacing(6)
        layout.setContentsMargins(6, 6, 6, 6)

        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setWordWrapMode(False)
        self.text_edit.setFontFamily("Consolas")
        self.text_edit.setFontPointSize(10)

        self.auto_scroll = QCheckBox("Авто-прокрутка")
        self.auto_scroll.setChecked(True)

        layout.addWidget(self.text_edit)
        layout.addWidget(self.auto_scroll)
        self.setLayout(layout)

    def connect_signals(self):
        """
        Подключает сигналы к слотам.

        Шаги:
        1. Подключить self.log_signal.log к self.on_log_received.
        2. Подключить контекстное меню:
           - При ПКМ: показать меню с действиями "Копировать", "Очистить".
        3. Убедиться, что сигналы не подключаются повторно (защита от дублей).

        Пример:
            self.log_signal.log.connect(self.on_log_received)
            self.text_edit.setContextMenuPolicy(Qt.CustomContextMenu)
            self.text_edit.customContextMenuRequested.connect(self.show_context_menu)
        """
        self.log_signal.log.connect(self.on_log_received)
        self.text_edit.setContextMenuPolicy(Qt.CustomContextMenu)
        self.text_edit.customContextMenuRequested.connect(self.show_context_menu)


    def on_log_received(self, level: str, message: str):
        """
        Обрабатывает новое сообщение лога.

        Args:
            level (str): Уровень лога — 'DEBUG', 'INFO', 'WARNING', 'ERROR'
            message (str): Текст сообщения

        Шаги:
        1. Добавить кортеж (level, message, timestamp) в self.log_buffer.
        2. Определить цвет в зависимости от уровня:
           - DEBUG: серый (#888888)
           - INFO: чёрный (#000000)
           - WARNING: оранжевый (#FF8C00)
           - ERROR: красный (#FF0000)
        3. Сформировать строку в формате HTML:
           <span style="color: #FF0000">[ERROR] 14:30:22 — Сбой авторизации</span>
        4. Добавить строку в text_edit.
        5. Если auto_scroll включён — прокрутить вниз.

        Примечание:
        - Даже если виджет скрыт — логи всё равно попадают в буфер.
        - При открытии виджета можно отобразить всю историю.
        """
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")

        self.log_buffer.append((level, message, timestamp))

        color = {
            "DEBUG": "#888888",
            "INFO": "#000000",
            "WARNING": "#FF8C00",
            "ERROR": "#FF0000",
            "CRITICAL": "#B22222"
        }.get(level, "#000000")

        log_entry = f'<span style="color:{color};">[{level}] {timestamp} — {message}</span>'
        self.text_edit.append(log_entry)

        if self.auto_scroll.isChecked():
            scrollbar = self.text_edit.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

    def restore_buffer(self):
        """Восстанавливает логи из глобального буфера Logger"""
        try:
            from src.core.logger import Logger
            for level, msg in Logger._log_buffer:
                self.on_log_received(level, msg)
        except:
            pass

    def show_context_menu(self, pos):
        """
        Показывает контекстное меню при клике правой кнопкой.

        Args:
            pos (QPoint): Позиция клика.

        Шаги:
        1. Создать QMenu.
        2. Добавить действия:
           - "Копировать" → вызывает self.copy_logs()
           - "Очистить" → вызывает self.clear_logs()
        3. Показать меню в позиции pos.

        Примечание:
        - Можно добавить "Сохранить как..." в будущем.
        """
        menu = QMenu(self)
        copy_action = QAction("Копировать", self)
        clear_action = QAction("Очистить", self)

        copy_action.triggered.connect(self.copy_logs)
        clear_action.triggered.connect(self.clear_logs)

        menu.addAction(copy_action)
        menu.addAction(clear_action)
        menu.exec_(self.text_edit.mapToGlobal(pos))

    def copy_logs(self):
        """
        Копирует весь текст из text_edit в буфер обмена.

        Шаги:
        1. Выделить весь текст: text_edit.selectAll()
        2. Скопировать: text_edit.copy()
        3. Снять выделение: text_edit.moveCursor(QTextCursor.End)

        Пример использования:
        - Пользователь нашёл ошибку → копирует лог → отправляет разработчику.
        """
        self.text_edit.selectAll()
        self.text_edit.copy()
        cursor = self.text_edit.textCursor()
        cursor.clearSelection()
        self.text_edit.setTextCursor(cursor)

    def clear_logs(self):
        """
        Очищает текстовое поле и буфер логов.

        Шаги:
        1. Спросить подтверждение: "Очистить все логи?" (QMessageBox).
        2. Если да:
           - Очистить text_edit
           - Очистить self.log_buffer
        3. Залогировать действие: "Логи очищены пользователем"

        Примечание:
        - Очистка не влияет на файл логов — они остаются на диске.
        """
        from PyQt5.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self,
            "Очистка логов",
            "Вы действительно хотите очистить все логи?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.text_edit.clear()
            self.log_buffer.clear()

    def showEvent(self, event):
        """
        Вызывается при отображении виджета (например, при переходе на вкладку).

        Args:
            event (QShowEvent): Событие показа.

        Шаги:
        1. Установить self.is_visible = True.
        2. (Опционально) Прокрутить вниз, если auto_scroll включён.
        3. Вызвать super().showEvent(event).

        Примечание:
        - Можно использовать для отложенной загрузки истории.
        """
        self.is_visible = True
        if self.auto_scroll.isChecked():
            self.text_edit.verticalScrollBar().setValue(self.text_edit.verticalScrollBar().maximum())
        super().showEvent(event)
