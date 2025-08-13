from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox
from src.core.logger import Logger


class SettingsWidget(QWidget):
    """
    Вкладка "Настройки" — позволяет управлять поведением логирования.
    """

    def __init__(self, logger: Logger):
        super().__init__()
        self.logger = logger
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.addStretch()

        # Заголовок
        title = self._create_title("⚙️ Настройки приложения")
        layout.addWidget(title)

        # Раздел: Логирование
        log_group = self._create_log_settings()
        layout.addLayout(log_group)

        layout.addStretch()
        self.setLayout(layout)

    def _create_title(self, text: str) -> QLabel:
        """Создаёт заголовок."""
        label = QLabel(text)
        label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50;")
        return label

    def _create_log_settings(self) -> QVBoxLayout:
        """Группа настроек логирования."""
        layout = QVBoxLayout()

        label = QLabel("Логирование")
        label.setStyleSheet("font-weight: bold;")
        layout.addWidget(label)

        self.chk_file_log = QCheckBox("Записывать логи в файл")
        self.chk_file_log.setChecked(False)
        self.chk_file_log.stateChanged.connect(self._on_toggle_file_log)
        layout.addWidget(self.chk_file_log)

        return layout

    def _on_toggle_file_log(self, state):
        """Обработчик изменения состояния чекбокса."""
        self.logger.enable_file_logging(state == 2)  # 2 = checked