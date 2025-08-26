"""
Модуль: shortcuts.py
Класс: ShortcutManager

Описание: Централизованный менеджер горячих клавиш (макросов) для приложения.

Назначение:
- Регистрация и управление глобальными комбинациями клавиш (Ctrl+Y, Ctrl+S и т.д.)
- Обеспечение контекстной активации (например, Ctrl+S работает только в настройках)
- Предотвращение конфликтов между шорткатами
- Поддержка динамического включения/выключения

Архитектурная роль:
- Связующее звено между UI и бизнес-логикой по управлению клавишами
- Не зависит от конкретных виджетов напрямую, но может их проверять
- Инжектируется в Application как сервис
Версия: v0.2
Автор: Боряков
Дата: 25.08.2025
Статус: Разработан
"""

from PyQt5.QtWidgets import QShortcut
from PyQt5.QtGui import QKeySequence
from PyQt5.QtCore import QObject

from src.core.config import Config
from src.core.logger import Logger
from typing import TYPE_CHECKING, Optional, Dict, Any

if TYPE_CHECKING:
    from src.ui.main_window import MainWindow
    from src.ui.apps.settings.view import SettingsAppView
    from src.buisness_processes.check_invoices.view import CheckInvoicesView


class ShortcutManager(QObject):
    """
    Менеджер горячих клавиш приложения.

    Атрибуты:
    - main_window (MainWindow): ссылка на главное окно (для установки шорткатов)
    - settings_widget (SettingsAppView): ссылка на вкладку настроек (для контекста)
    - check_invoices_widget (CheckInvoicesView): ссылка на вкладку проверки (для контекста)
    - config (Config): опционально — для кастомных шорткатов в будущем
    - shortcuts (list): список всех зарегистрированных шорткатов
    - context_widgets (dict): сопоставление виджетов и их контекстных шорткатов
    """

    def __init__(self, main_window, logger: Logger, config: Config, settings_widget=None, check_invoices_widget=None):
        super().__init__()
        self.logger = logger
        self.main_window = main_window
        self.settings_widget = settings_widget
        self.check_invoices_widget = check_invoices_widget
        self.config = config
        self.shortcuts = []
        self.context_widgets = {}

        # Регистрируем контекстные виджеты
        if self.check_invoices_widget:
            self.context_widgets[self.check_invoices_widget] = []

        self._setup_shortcuts()

    def _setup_shortcuts(self):
        """Регистрирует все глобальные и контекстные шорткаты."""
        # === Глобальные шорткаты ===
        self._add_shortcut("Ctrl+Y", self._on_open_settings, "Открыть вкладку 'Настройки'")
        self._add_shortcut("Ctrl+Q", self._on_quit_application, "Выйти из приложения")

        # === Контекстный шорткат: Ctrl+I → Проверка накладных ===
        self._add_shortcut("Ctrl+I", self._on_open_check_invoices, "Перейти к проверке накладных")

        # === Контекстные шорткаты: активны только при активации виджета ===

        # --- 1. Для вкладки "Проверка накладных" ---
        if self.check_invoices_widget:
            self._add_context_shortcut(
                widget=self.check_invoices_widget,
                key_sequence="Ctrl+F",
                callback=self._on_browse_file,
                description="Выбрать Excel-файл с накладными"
            )
            self._add_context_shortcut(
                widget=self.check_invoices_widget,
                key_sequence="Ctrl+E",
                callback=self._on_run_process,
                description="Запустить проверку накладных"
            )
            self._add_context_shortcut(
                widget=self.check_invoices_widget,
                key_sequence="Ctrl+R",
                callback=self._on_update_report,
                description="Обновить существующий отчёт"
            )

        # --- 2. Для вкладки "Настройки" ---
        if self.settings_widget:
            self._add_context_shortcut(
                widget=self.settings_widget,
                key_sequence="Ctrl+S",
                callback=self._on_save_settings,
                description="Сохранить настройки"
            )

    def _add_shortcut(self, key_sequence: str, callback, description: str = ""):
        """Унифицированное добавление глобального шортката."""
        shortcut = QShortcut(QKeySequence(key_sequence), self.main_window)
        shortcut.activated.connect(callback)
        shortcut.setEnabled(True)

        shortcut_item = {
            "shortcut": shortcut,
            "key": key_sequence,
            "callback": callback,
            "description": description,
            "context": None  # глобальный
        }
        self.shortcuts.append(shortcut_item)
        self.logger.info(f"⚡ Шорткат зарегистрирован: {key_sequence} → {description}")

    def _add_context_shortcut(self, widget, key_sequence: str, callback, description: str = ""):
        """Добавляет контекстный шорткат, который активен только при активации виджета."""
        shortcut = QShortcut(QKeySequence(key_sequence), self.main_window)
        shortcut.activated.connect(callback)
        shortcut.setEnabled(False)  # изначально отключён

        shortcut_item = {
            "shortcut": shortcut,
            "key": key_sequence,
            "callback": callback,
            "description": description,
            "context": widget
        }
        self.shortcuts.append(shortcut_item)

        # Сохраняем для быстрого доступа
        if widget not in self.context_widgets:
            self.context_widgets[widget] = []
        self.context_widgets[widget].append(shortcut_item)

    def _on_open_settings(self):
        """Ctrl+Y: открывает вкладку 'Настройки'."""
        if self.settings_widget:
            self.main_window.switch_to(self.settings_widget)

    def _on_open_check_invoices(self):
        """Ctrl+I: открывает вкладку 'Проверка накладных'."""
        if self.check_invoices_widget:
            self.main_window.switch_to(self.check_invoices_widget)

    def _on_browse_file(self):
        """Ctrl+F: вызывает выбор файла (только если активна вкладка проверки)."""
        if self._is_active(self.check_invoices_widget):
            self.check_invoices_widget._on_browse_file()

    def _on_run_process(self):
        """Ctrl+E: запускает проверку (только если активна вкладка проверки)."""
        if self._is_active(self.check_invoices_widget):
            self.check_invoices_widget._on_run_process()

    def _on_update_report(self):
        """Ctrl+R: запускает обновление загруженного отчёта (только если активна вкладка проверки)."""
        if self.check_invoices_widget:
            self.check_invoices_widget._on_update_report()

    def _on_save_settings(self):
        """Ctrl+S: сохраняет настройки (только если активна вкладка настроек)."""
        if self._is_active(self.settings_widget):
            self.settings_widget._on_save_clicked()

    def _on_quit_application(self):
        """Ctrl+Q: закрывает приложение."""
        self.main_window.close()

    def _is_active(self, widget) -> bool:
        """Проверяет, активен ли виджет."""
        return self.main_window.current_widget() == widget

    def on_widget_activated(self, widget):
        """
        Вызывается при активации вкладки.
        Включает контекстные шорткаты для этого виджета.
        """
        # Сначала отключаем все контекстные
        self._deactivate_all_context_shortcuts()

        # Включаем для текущего
        if widget in self.context_widgets:
            for item in self.context_widgets[widget]:
                item["shortcut"].setEnabled(True)

    def _deactivate_all_context_shortcuts(self):
        """Отключает все контекстные шорткаты."""
        for item in self.shortcuts:
            if item["context"] is not None:
                item["shortcut"].setEnabled(False)

    def get_shortcuts_info(self):
        """Возвращает список всех шорткатов (для отладки или справки)."""
        return [
            {"Клавиши": s["key"], "Описание": s["description"], "Тип": "Контекстный" if s["context"] else "Глобальный"}
            for s in self.shortcuts
        ]

    def disconnect_all(self):
        """Отключает все шорткаты (например, при деинициализации)."""
        for item in self.shortcuts:
            try:
                item["shortcut"].activated.disconnect()
            except:
                pass
        self.shortcuts.clear()
        self.context_widgets.clear()