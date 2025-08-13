"""
Модуль: logger.py

Класс Logger — централизованное логирование в GUI и в файл.

Поддерживает:
- Вывод в текстовое поле (QTextEdit).
- Запись в файл (если включено в настройках).
- Автогенерацию имени файла при старте.
- Цветные метки: [INFO], [ERROR], [WARN].
"""

import os
from datetime import datetime
from PyQt5.QtCore import QObject, pyqtSignal


class Logger(QObject):
    """
    Класс логирования.

    Поддерживает:
    - Вывод в GUI (через сигнал).
    - Запись в файл.
    - Динамическое включение/отключение записи в файл.
    """

    # Сигнал для обновления GUI (потокобезопасно)
    log_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.log_file_path = None
        self._file_enabled = False
        self._file_handle = None

        # Автосоздание папки и файла
        self._setup_log_file()

    def _setup_log_file(self):
        """Создаёт папку logs и генерирует имя файла с меткой времени."""
        log_dir = "logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.log_file_path = os.path.join(log_dir, f"log_{timestamp}.txt")

        try:
            self._file_handle = open(self.log_file_path, "w", encoding="utf-8")
            self.log(f"Лог-файл создан: {self.log_file_path}")
        except Exception as e:
            print(f"[Logger] Ошибка при создании файла: {e}")

    def enable_file_logging(self, enabled: bool):
        """Включает или отключает запись в файл."""
        self._file_enabled = enabled
        if enabled:
            self.log("Запись логов в файл ВКЛЮЧЕНА")
        else:
            self.log("Запись логов в файл ВЫКЛЮЧЕНА")

    def _write_to_file(self, message: str):
        """Записывает сообщение в файл, если разрешено."""
        if self._file_enabled and self._file_handle and not self._file_handle.closed:
            self._file_handle.write(message + "\n")
            self._file_handle.flush()  # немедленная запись

    def _format_message(self, level: str, message: str) -> str:
        """Форматирует сообщение с временем и уровнем."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        return f"[{timestamp}] [{level}] {message}"

    def log(self, message: str):
        """Логирует сообщение как INFO."""
        formatted = self._format_message("INFO", message)
        self.log_signal.emit(formatted)
        self._write_to_file(formatted)

    def warn(self, message: str):
        """Логирует предупреждение."""
        formatted = self._format_message("WARN", message)
        self.log_signal.emit(formatted)
        self._write_to_file(formatted)

    def error(self, message: str):
        """Логирует ошибку."""
        formatted = self._format_message("ERROR", message)
        self.log_signal.emit(formatted)
        self._write_to_file(formatted)

    def close(self):
        """Закрывает файл лога."""
        if self._file_handle and not self._file_handle.closed:
            self._file_handle.close()