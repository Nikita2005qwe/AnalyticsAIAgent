"""
Класс: Logger
Описание: Централизованный, расширяемый логгер приложения с поддержкой:
- Записи в файл (для долгосрочного хранения),
- Отправки событий в GUI (через сигналы),
- Уровней логирования (DEBUG, INFO, WARNING, ERROR),
- Работы в режиме «синглтон» (один экземпляр на всё приложение).

Назначение:
- Регистрировать все важные события: старт, ошибки, прогресс процессов.
- Обеспечивать **видимость** логов для пользователя через `LogWidget`.
- Позволять **анализировать** происходящее даже после закрытия приложения (через файл).
- Быть **независимым от UI**, но **интегрироваться с ним** при необходимости.

Архитектурная роль:
- Ядро системы логирования.
- «Издатель» событий: рассылает логи всем подписчикам (например, `LogWidget`).
- Не зависит от PyQt напрямую, но может подключать обработчики из UI.
Версия: v0.1
Автор: Боряков
Дата: 21.08.2025
Статус: Разработан
"""

import logging
import os
import sys
from typing import Optional
from src.core.signals import log_signal

class Logger:
    _instance: Optional['Logger'] = None  # Статический экземпляр (синглтон)
    _log_buffer = []  # Буфер для логов до подключения GUI

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, log_file: str = "logs/app.log", level: str = "INFO"):
        """
        Инициализирует логгер. Не вызывается напрямую — используй get_instance().

        Args:
            log_file (str): Путь к файлу, куда будут писаться логи.
            level (str): Уровень логирования: 'DEBUG', 'INFO', 'WARNING', 'ERROR'.

        Пример:
            logger = Logger.get_instance(log_file="logs/session_2025-04-05.log", level="DEBUG")

        Важно:
        - Конструктор защищён от повторного вызова (паттерн Синглтон).
        - Все классы приложения должны использовать Logger.get_instance().
        """
        self._gui_handler = None
        if hasattr(self, 'initialized') and self.initialized:
            return

            # Создаём логгер
        self.logger = logging.getLogger("AnalyticsAIAgent")
        self.logger.setLevel(getattr(logging, level.upper()))
        self.logger.handlers.clear()  # Убираем дубли

        # Формат
        formatter = logging.Formatter('%(asctime)s — %(levelname)s — %(message)s')

        # File Handler
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        # GUI Handler — только добавляем в логгер, не подключаем сигнал
        gui_handler = logging.StreamHandler()
        gui_handler.setFormatter(formatter)
        self.logger.addHandler(gui_handler)

        # Заменяем emit, чтобы отправлять в сигнал
        def emit_via_signal(record):
            log_signal.log.emit(record.levelname, record.getMessage())

        gui_handler.emit = emit_via_signal

        # Восстанавливаем буфер
        for level, msg in self._log_buffer:
            getattr(self.logger, level.lower())(msg)
        self._log_buffer.clear()

        # Флаг инициализации
        self.initialized = True

    def _emit_log(self, level, message):
        log_signal.log.emit(level, message)

    @classmethod
    def log_before_gui(cls, level: str, message: str):
        """Сохраняет лог в буфер до инициализации GUI"""
        cls._log_buffer.append((level, message))

    @classmethod
    def get_instance(cls, log_file: str = "logs/app.log", level: str = "INFO") -> 'Logger':
        """
        Возвращает единственный экземпляр Logger (синглтон).

        Args:
            log_file (str): Путь к файлу логов (используется при первом создании).
            level (str): Уровень логирования.

        Returns:
            Logger: Единственный экземпляр.

        Шаги:
        1. Если _instance не существует:
           - Создать новый Logger с указанными параметрами.
        2. Вернуть существующий _instance.
        3. Если уровень изменился — обновить уровень (опционально, можно игнорировать).

        Примеры использования:
            # В Application
            logger = Logger.get_instance()

            # В CheckInvoicesProcess
            logger = Logger.get_instance()
            logger.info("Начало проверки накладных...")

            # В FileService
            logger.error("Не удалось прочитать файл: invalid.xlsx")
        """
        if cls._instance is None:
            cls(log_file, level)
        return cls._instance

    def _setup_file_handler(self, log_file: str):
        """
        Настраивает запись логов в файл.

        Args:
            log_file (str): Полный путь к файлу логов.

        Шаги:
        1. Создать директорию (например, 'logs/'), если не существует.
        2. Создать FileHandler, который будет писать в указанный файл.
        3. Установить формат: "[УРОВЕНЬ] Время — Сообщение"
        4. Добавить обработчик к self._logger.

        Формат сообщения:
            "[INFO] 2025-04-05 14:30:22 — Файл успешно загружен"

        Примечание:
        - Это основной способ долгосрочного хранения логов.
        - Даже если GUI скрыт — всё равно пишется в файл.
        """
        log_path = os.path.abspath(log_file)
        log_dir = os.path.dirname(log_path)

        # Явно создаём директорию
        try:
            os.makedirs(log_dir, exist_ok=True)
        except Exception as e:
            print(f"❌ Не удалось создать директорию логов: {log_dir} — {e}", file=sys.stderr)
            raise

        # Теперь создаём FileHandler
        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        formatter = logging.Formatter(
            fmt="[%(levelname)s] %(asctime)s — %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

    def setup_gui_handler(self, target_signal=log_signal):
        """
        Подключает обработчик, который отправляет логи в GUI.

        Args:
            target_signal: Объект с сигналом .log(level, message).
                         По умолчанию — глобальный log_signal из core.signals.

        Шаги:
        1. Создать GUIHandler (logging.Handler).
        2. В emit(record):
           - level = record.levelname
           - message = record.getMessage()
           - target_signal.log.emit(level, message)
        3. Добавить обработчик к self._logger.

        Пример:
            logger = Logger.get_instance()
            logger.setup_gui_handler()  # использует глобальный сигнал

        Преимущество:
        - Можно передать кастомный сигнал для тестов.
        - Всё приложение использует один канал.
        """
        class GUIHandler(logging.Handler):
            def __init__(self, signal):
                super().__init__()
                self.signal = signal

            def emit(self, record):
                try:
                    msg = self.format(record)
                    # Мы хотим только level и message, как в сигнале
                    level = record.levelname
                    message = record.getMessage()
                    self.signal.log.emit(level, message)
                except Exception:
                    self.handleError(record)

        if self._gui_handler is None:
            self._gui_handler = GUIHandler(target_signal)
            self._gui_handler.setFormatter(
                logging.Formatter("%(levelname)s — %(message)s")
            )
            self.logger.addHandler(self._gui_handler)

    def debug(self, message: str):
        """
        Логирует отладочное сообщение.

        Args:
            message (str): Текст сообщения.

        Используется для:
        - Детального отслеживания шагов (например, "Начало проверки накладной 12345")
        - Вывода промежуточных данных (например, "Фильтр ISA: значение = 1200")
        - Отладки алгоритмов

        Пример:
            logger.debug(f"Обработка строки {row_index} из Excel")

        Выводится:
            - В файл
            - В GUI (если подключён)
        """
        self.logger.debug(message)

    def info(self, message: str):
        """
        Логирует информационное сообщение.

        Args:
            message (str): Текст сообщения.

        Используется для:
        - Старт/стоп процессов
        - Успешная загрузка файла
        - Авторизация в DMS
        - Прогресс: "Проверено 50 из 100 накладных"

        Пример:
            logger.info("Процесс проверки накладных завершён")
        """
        self.logger.info(message)

    def warning(self, message: str):
        """
        Логирует предупреждение (не критичная ошибка).

        Args:
            message (str): Текст сообщения.

        Используется для:
        - Накладная не найдена
        - Пустое значение в SFA
        - Пропущенная строка в Excel
        - Временная ошибка сети (повторная попытка)

        Пример:
            logger.warning(f"Накладная {number} не найдена в DMS")
        """
        self.logger.warning(message)


    def error(self, message: str):
        """
        Логирует критическую ошибку.

        Args:
            message (str): Текст сообщения.

        Используется для:
        - Сбой авторизации
        - Ошибка чтения файла
        - Исключение в процессе
        - Недоступность DMS

        Пример:
            logger.error("Не удалось войти в DMS: неверный пароль")

        Важно:
        - Такие ошибки должны быть видны пользователю.
        - Должны сохраняться в файл и отображаться в LogWidget.
        """
        self.logger.error(message)
