"""
Модуль: main_window.py
Класс: MainWindow

Описание: Главное окно приложения, представляющее собой контейнер с вкладками (tabbed interface).

Назначение:
- Центральный контейнер для всех виджетов-процессов (например, "Проверка накладных", "Задачи").
- Обеспечивает навигацию между вкладками.
- Управляет внешним видом окна: заголовок, размер, иконка, стили.

Архитектурная роль:
- UI-координатор: отображает зарегистрированные виджеты как вкладки.
- Часть слоя `ui`, не содержит бизнес-логики.
- Получает виджеты от `Application` и добавляет их через `add_tab()`.

Версия: v0.1
Автор: Боряков
Дата: 21.08.2025
Статус: Полностью готов
"""

# --- Стандартная библиотека ---
from typing import Optional
import os

# --- PyQt5 ---
from PyQt5.QtWidgets import (
    QMainWindow,  # Базовый класс для главного окна приложения
    QTabWidget,  # Виджет с вкладками — основа интерфейса
    QWidget,  # Базовый контейнер для UI-элементов
    QVBoxLayout,  # Вертикальная компоновка
    QHBoxLayout,  # Горизонтальная компоновка
    QMessageBox,  # Диалоговые окна (например, подтверждение выхода)
    QFrame,  # Лёгкий контейнер для группировки
    QScrollArea, QSizePolicy, QSplitter, QPushButton  # Для прокрутки длинного списка (например, боковое меню)
)
from PyQt5.QtGui import QIcon  # Для установки иконки приложения
from PyQt5.QtCore import Qt, pyqtSignal  # Qt — флаги, pyqtSignal — для будущих расширений

# --- Локальные импорты из проекта ---
from src.core.logger import Logger  # Глобальный логгер приложения
from src.ui.log_widget import LogWidget


class MainWindow(QMainWindow):
    """
    Главное окно приложения — контейнер с вкладками и боковым меню.

    Атрибуты:
    - tab_widget (QTabWidget): центральный виджет, отображающий вкладки
    - sidebar_layout (QVBoxLayout): контейнер для кнопок навигации (боковое меню)
    - _logger (Logger): экземпляр логгера для отчёта о событиях (например, "Вкладка добавлена")

    Архитектурные принципы:
    - Не хранит реестр виджетов (self.tabs удалён) — использует QTabWidget как источник истины
    - Получает виджеты от Application через add_tab()
    - Предоставляет методы для активации, получения и удаления вкладок
    - Поддерживает боковое меню для навигации
    """

    def __init__(self, logger: Logger):
        """
        Инициализирует главное окно с центральным QTabWidget.

        Args:
            logger (Logger): Экземпляр глобального логгера для записи событий

        Шаги:
        1. Вызвать super().__init__() — инициализация QMainWindow
        2. Установить self._logger = logger — для логирования действий
        3. Инициализировать self.tab_widget = None — будет создан в setup_ui
        4. Инициализировать self.sidebar_layout = None — будет создан в setup_ui

        Примечание:
        - MainWindow не знает о бизнес-логике, только отображает вкладки
        - Все виджеты добавляются через add_tab() из Application
        - Использует QTabWidget как единственный источник истины о вкладках
        """
        super().__init__()
        self._current_widget = None
        self.splitter = None
        self.log_widget = None
        self.sidebar_layout = None
        self.central_widget = None
        self.central_layout = None
        self._logger = logger

    def setup_ui(
        self,
        icon_file_name: str = "assets/icon.png",
        style_file: str = "styles/app.qss",
        initial_size: list = None,
        full_screen: bool = False,
        maximized: bool = False):
        """
        Настраивает визуальную часть главного окна.

        Args:
            icon_file_name (str): Путь к файлу иконки приложения
            style_file (str): Путь к QSS-файлу со стилями

        Шаги:
        1. Установить заголовок окна: "AI-агент для аналитика"
        2. Установить минимальный размер: 1920x1080 (подходит для Full HD)
        3. Создать главный layout: QHBoxLayout — для горизонтального разделения
        4. Создать контейнер-виджет и установить его как центральный
        5. Создать боковое меню (sidebar):
           - QWidget с фиксированной шириной 250px
           - QVBoxLayout для размещения кнопок навигации
           - Отступы: 8px
        6. Создать центральный QTabWidget:
           - setTabsClosable(False) — вкладки нельзя закрывать
           - setMovable(True) — можно перетаскивать
        7. Разместить sidebar и tab_widget в главном layout:
           - sidebar — слева
           - tab_widget — растягивается на оставшееся пространство
        8. Установить иконку приложения, если файл существует
        9. Применить QSS-стили из файла
        10. Залогировать успешную настройку UI

        Примечание:
        - QTabWidget — родной элемент PyQt5, идеально подходит для многостраничного интерфейса.
        - Можно позже добавить контекстное меню (ПКМ по вкладке → закрыть, обновить).
        - sidebar_layout будет использоваться Application для добавления кнопок навигации
        """
        self.setWindowTitle("AI-агент для аналитика")
        # 🔹 Гарантированно устанавливаем размер
        size = initial_size if initial_size and len(initial_size) == 2 else [1920, 1080]

        if maximized:
            self.resize(size[0], size[1])  # ← нужен resize ДО showMaximized()
            self.showMaximized()
        else:
            self.resize(size[0], size[1])
            self.setMinimumSize(1200, 800)
        # === Главный layout (вертикальный) ===
        main_layout = QVBoxLayout()
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # === Горизонтальный сплит: sidebar + central ===
        split_layout = QHBoxLayout()
        split_widget = QWidget()
        split_widget.setLayout(split_layout)
        main_layout.addWidget(split_widget)

        # === Боковое меню (слева) ---
        sidebar_widget = QWidget()
        sidebar_widget.setFixedWidth(250)
        sidebar_widget.setStyleSheet("background-color: #f0f0f0; border-right: 1px solid #ccc;")
        self.sidebar_layout = QVBoxLayout()
        self.sidebar_layout.setAlignment(Qt.AlignLeft)  # ← Выравнивание по левому краю
        self.sidebar_layout.setSpacing(6)  # Расстояние между кнопками
        self.sidebar_layout.setContentsMargins(8, 8, 8, 8)
        sidebar_widget.setLayout(self.sidebar_layout)
        split_layout.addWidget(sidebar_widget)

        # --- 2. Центральный контейнер с layout'ом ---
        central_container = QWidget()
        self.central_layout = QVBoxLayout()
        self.central_layout.setContentsMargins(0, 0, 0, 0)
        self.central_layout.setSpacing(0)
        central_container.setLayout(self.central_layout)
        central_container.setStyleSheet("background-color: white;")
        split_layout.addWidget(central_container)

        # === 3. Окно логов (снизу, под всем) ===
        self.log_widget = LogWidget()
        self.log_widget.setMaximumHeight(600)  # Максимум, до которого можно растянуть
        self.log_widget.setMinimumHeight(400)  # Минимум

        # === Разделитель: верхняя часть + логи ===
        self.splitter = QSplitter(Qt.Vertical)
        self.splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #e0e0e0;
                height: 10px;
                border-top: 1px solid #cccccc;
                border-bottom: 1px solid #cccccc;
            }
            QSplitter::handle:hover {
                background-color: #d0d0d0;
            }
        """)
        # Верхняя часть (sidebar + центральный контейнер)
        top_widget = QWidget()
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.addWidget(split_widget)
        top_widget.setLayout(top_layout)

        # Добавляем в сплиттер
        self.splitter.addWidget(top_widget)
        self.splitter.addWidget(self.log_widget)

        # === 2. Устанавливаем начальные размеры: логи — 500px (максимум)
        self.splitter.setSizes([self.height() - 500, 500])
        # Важно: чтобы панель логов не "схлопывалась"
        self.splitter.setChildrenCollapsible(False)

        # Добавляем сплиттер в основной layout
        main_layout.addWidget(self.splitter)
        # === Иконка и стили ===
        if os.path.exists(icon_file_name):
            try:
                self.setWindowIcon(QIcon(icon_file_name))
            except Exception as e:
                self._logger.warning(f"Иконка не загружена: {e}")

        self._apply_styles(style_file)
        self._logger.info("Главное окно: UI настроено")

    def show_logs_panel(self, visible: bool):
        """Показывает или скрывает панель логов"""
        self.log_widget.setVisible(visible)
        # Можно управлять размерами
        if visible:
            sizes = self.splitter.sizes()
            if sum(sizes) > 0:
                total = sum(sizes)
                self.splitter.setSizes([int(total * 0.7), int(total * 0.3)])
                
    def _apply_styles(self, style_file: str):
        """
        Применяет QSS-стили из файла, если он существует.

        Args:
            style_file (str): Путь к файлу стилей

        Шаги:
        1. Попытаться открыть файл в кодировке UTF-8
        2. Прочитать содержимое и применить через setStyleSheet()
        3. Залогировать успешную загрузку
        4. Если файл не найден — предупредить
        5. При других ошибках — залогировать ошибку

        Примечание:
        - QSS (Qt Style Sheets) — аналог CSS для PyQt
        - Стили могут задавать цвета, шрифты, отступы, эффекты
        - Позволяет легко менять внешний вид без изменения кода
        """
        try:
            with open(style_file, "r", encoding="utf-8") as f:
                style_content = f.read()
            self.setStyleSheet(style_content)
            self._logger.info(f"Стили загружены из {style_file}")
        except FileNotFoundError:
            self._logger.warning(f"Файл стилей {style_file} не найден. Используются стили по умолчанию.")
        except Exception as e:
            self._logger.error(f"Ошибка при загрузке стилей: {e}")

    def switch_to(self, widget: QWidget):
        """
        Переключает центральный виджет на указанный, сохраняя структуру интерфейса.
        Также снимает состояние 'checked' со всех кнопок навигации и устанавливает на текущую.

        Args:
            widget (QWidget): новый виджет для отображения (например, SettingsAppView)

        Шаги:
        1. Проверить, есть ли уже виджет в central_layout
        2. Если есть — удалить его из layout (через setParent(None))
        3. Добавить новый виджет в central_layout
        4. Найти navigation_button у нового виджета (если есть) и установить checked=True
        5. Снять checked со всех остальных кнопок в sidebar_layout
        6. Залогировать смену виджета

        Примечание:
        - Это гарантирует, что только одна кнопка в боковом меню будет активной
        - Улучшает UX: пользователь всегда видит, какая вкладка открыта
        """
        # Удаляем старый виджет из layout
        if self.central_layout.count() > 0:
            old_widget = self.central_layout.itemAt(0).widget()
            if old_widget:
                old_widget.setParent(None)

        # Добавляем новый
        self.central_layout.addWidget(widget)
        self._current_widget = widget

        # === Управление состоянием кнопок навигации ===
        # Снимаем checked со всех кнопок
        for i in range(self.sidebar_layout.count()):
            item = self.sidebar_layout.itemAt(i)
            if item and item.widget():
                btn = item.widget()
                if isinstance(btn, QPushButton) and btn.isCheckable():
                    btn.setChecked(False)

        # Устанавливаем checked на текущую кнопку
        if hasattr(widget, 'navigation_button') and widget.navigation_button:
            widget.navigation_button.setChecked(True)
        
    def current_widget(self):
        """Возвращает текущий активный виджет."""
        return self._current_widget

    def closeEvent(self, event):
        """
        Обрабатывает событие закрытия окна.

        Args:
            event (QCloseEvent): Событие закрытия

        Шаги:
        1. Залогировать событие: "Приложение закрывается..."
        2. Показать QMessageBox с подтверждением выхода
        3. Если пользователь подтвердил — принять событие
        4. Иначе — отклонить

        Примечание:
        - Предотвращает случайное закрытие приложения
        - В будущем можно расширить: проверка активных процессов, сохранение состояния
        - Является стандартным поведением для GUI-приложений
        - Обеспечивает пользовательский контроль над выходом
        """
        self._logger.info("Приложение закрывается...")

        reply = QMessageBox.question(
            self,
            "Подтверждение выхода",
            "Вы действительно хотите закрыть приложение?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            event.accept()
            self._logger.info("Приложение закрыто пользователем")
        else:
            event.ignore()
            self._logger.info("Закрытие отменено пользователем")