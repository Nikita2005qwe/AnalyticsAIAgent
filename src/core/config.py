"""
Класс: Config
Описание: Централизованное хранилище конфигурации приложения.

Назначение:
- Загрузка настроек из:
  - JSON-файла (пользовательские настройки: GUI, поведение)
  - .env-файла (секреты: API-ключи, логины, пароли)
  - Значений по умолчанию (если нет внешних источников)
- Предоставление настроек всем компонентам приложения.
- Сохранение изменённых настроек (например, из вкладки "Настройки").

Архитектурная роль:
- Единый источник конфигурации.
- Изолирует чувствительные данные (через .env).
- Поддерживает runtime-изменения (например, включить полный лог).

Версия: v0.1
Автор: Боряков
Дата: 21.08.2025
Статус: Разработан
"""
import sys

from PyQt5.QtCore import pyqtSignal, QObject

from src.core.logger import Logger
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional
from dotenv import load_dotenv


class Config(QObject):

    config_changed = pyqtSignal(str, object)

    def __init__(self, logger: Optional[Logger]):
        """
        Инициализирует конфигурацию.

        Атрибуты:
        - config_path (Path): Путь к JSON-файлу с настройками (например, 'config/settings.json')
        - env_path (Path): Путь к .env-файлу (например, '.env')
        - logger (Logger): Экземпляр класса Logger, для логирования изменений и ошибок
        - data (dict): Основной словарь с настройками (GUI, поведение)
        - secrets (dict): Словарь с секретами из .env (не сохраняется в JSON)
        """
        super().__init__()
        self.config_path: Path = Path("config/settings.json")
        self.env_path: Path = Path(".env")
        self.logger = logger
        self.data: Dict[str, Any] = {}
        self.secrets: Dict[str, str] = {}

        self._log_buffer = []
        if not self.logger:
            from src.core.logger import Logger
            Logger.log_before_gui("info", "Config: Logger ещё не готов — логирую в буфер")

        # Если logger уже есть — сбросить буфер
        if self.logger:
            self._flush_buffer()

    def load(self):
        """
        Загружает все настройки: из JSON и .env.

        Returns:
            None

        Шаги:
        1. Создать директорию config/, если не существует.
        2. Если config/settings.json существует:
           - Загрузить в self.data
        3. Если нет — создать дефолтный config с настройками по умолчанию.
        4. Если .env существует:
           - Загрузить переменные окружения через dotenv
           - Сохранить нужные ключи (например, DMS_LOGIN, OPEN_ROUTER_API_KEY) в self.secrets
        5. Если .env нет — предупредить в логах, но продолжить (если не критично).

        Пример содержимого settings.json:
            {
                "full_log": false,
                "window_size": [1000, 700],
            }

        Пример .env:
            # Сибирь
            DMS_USERNAME_SIB=user123
            DMS_PASSWORD_SIB=pass456

            # Урал
            DMS_USERNAME_URAL=user123
            DMS_PASSWORD_URAL=pass456123

            # Базовый URL DMS
            DMS_BASE_URL="https://goodfood.shop/"

            CRM_BASE_URL="https://crm.nestle.ru/"

            CRM_USERNAME="CRM_USERNAME"
            CRM_PASSWORD="CRM_PASSWORD"

            OPEN_ROUTER_API_KEY=sk-...

        Важно:
        - secrets не сохраняются в JSON и не отображаются в GUI напрямую.
        - Все пути нормализуются через Path.
        """
        # Шаг 1: Создать директорию config/, если не существует
        self.config_path.parent.mkdir(exist_ok=True)

        # Шаг 2-3: Загрузить JSON или создать дефолтный
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
                self.log("info", f"Конфигурация загружена из {self.config_path}")
            except (json.JSONDecodeError, OSError) as e:
                self.log("error", f"Ошибка чтения settings.json: {e}. Создаём дефолтный конфиг.")
                self.create_default_config()
        else:
            self.create_default_config()
            self.log("info", f"Файл {self.config_path} не найден. Создан дефолтный конфиг.")

        # Шаг 4-5: Загрузить .env, если существует
        if self.env_path.exists():
            load_dotenv(self.env_path)
            # Ключи, которые мы хотим извлечь как секреты
            secret_keys = [
                "DMS_USERNAME_SIB", "DMS_PASSWORD_SIB",
                "DMS_USERNAME_URAL", "DMS_PASSWORD_URAL",
                "DMS_BASE_URL",
                "CRM_BASE_URL", "CRM_USERNAME", "CRM_PASSWORD",
                "OPEN_ROUTER_API_KEY"
            ]
            for key in secret_keys:
                value = os.getenv(key)
                if value is not None:
                    # Убираем кавычки и лишние пробелы
                    self.secrets[key] = value.strip().strip('"\'')
            self.log("info",f"Секреты загружены из {self.env_path}")
        else:
            self.log("warning",f"Файл {self.env_path} не найден. Продолжаем без секретов (если не критично).")

    def save(self):
        """
        Сохраняет пользовательские настройки в JSON-файл.

        Returns:
            None

        Шаги:
        1. Убедиться, что директория config/ существует.
        2. Записать self.data в config/settings.json в формате JSON.
        3. Не сохранять self.secrets — они управляются через .env.
        Только вот как мне сохранять пароли, которые ввёл пользователь, пока использовал приложение

        Примечание:
        - Вызывается при закрытии приложения или при нажатии "Сохранить" в SettingsWidget.
        - Использует indent=2 для читаемости.
        """
        try:
            self.config_path.parent.mkdir(exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            self.log("info", f"Конфигурация сохранена в {self.config_path}")
        except (OSError, IOError) as e:
            self.log("error", f"Не удалось сохранить конфигурацию: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Получает значение настройки из self.data.

        Args:
            key (str): Ключ (например, "full_log", "window_size")
            default (Any): Значение по умолчанию, если ключ не найден

        Returns:
            Any: Значение настройки или default

        Примеры:
            config.get("full_log", False) → True / False
            config.get("window_size") → [1000, 700]

        Примечание:
        - Используется в UI и процессах для получения пользовательских настроек.
        """
        return self.data.get(key, default)

    def set(self, key: str, value: Any):
        """
        Устанавливает значение настройки в self.data.

        Args:
            key (str): Ключ
            value (Any): Значение

        Returns:
            None

        Пример:
            config.set("full_log", True)
            config.set("last_used_file_path", "/home/user/data.xlsx")

        Примечание:
        - Не сохраняет автоматически — нужно вызвать config.save() отдельно.
        - Используется в SettingsWidget при изменении настроек.
        """
        self.data[key] = value

    def get_secret(self, key: str, default: str = None) -> Optional[str]:
        """
        Получает секретное значение (из .env).

        Args:
            key (str): Имя переменной (например, "OPENAI_API_KEY", "DMS_PASSWORD")
            default (str): Значение по умолчанию

        Returns:
            str or None: Значение переменной окружения

        Пример:
            password = config.get_secret("DMS_PASSWORD")
            api_key = config.get_secret("OPEN_ROUTER_API_KEY")

        Важно:
        - Не логгируется напрямую (для безопасности).
        - Используется в DMSOperation, AI-агенте и других сервисах.
        """
        return self.secrets.get(key, default)

    def ensure_directories(self):
        """
        Создаёт необходимые директории, если их нет.

        Шаги:
        1. Создать config/ — для settings.json
        2. Создать logs/ — для логов
        3. Создать temp/ или data/ — для временных файлов (опционально)

        Вызывается при инициализации.
        """
        Path("config").mkdir(exist_ok=True)
        Path("logs").mkdir(exist_ok=True)
        Path("temp").mkdir(exist_ok=True)
        Path("data").mkdir(exist_ok=True)

    def apply_settings(self):
        """
        Применяет изменения конфигурации в текущем сеансе немедленно, без перезапуска приложения.

        Этот метод вызывается после изменения настроек (например, в SettingsAppView),
        чтобы эффект вступил в силу сразу — не только в памяти, но и в интерфейсе.

        Он координирует обновление UI-компонентов через сигналы, отправляя события,
        которые слушаются другими частями приложения (например, Application, MainWindow).

        🔧 Что делает:
        1. Отправляет сигнал `config_changed` для ключей:
           - 'full_log' → чтобы показать/скрыть панель логов в GUI
           - 'window_size' → чтобы изменить размер окна
        2. Не меняет уровень логирования в файле (всегда DEBUG), но управляет только отображением в GUI.
        3. Не сохраняет настройки в файл — это делает отдельный вызов config.save().

        🔄 Жизненный цикл применения:
            SettingsAppView._on_save_clicked()
                → config.set("full_log", True)
                → config.apply_settings()  # ← Этот метод
                → config.config_changed.emit("full_log", True)
                → Application.on_config_changed("full_log", True)
                → MainWindow.show_logs_panel(True)

        📌 Почему не пересоздаём Logger?
        - Уровень логирования в файле всегда остаётся DEBUG — для полной аудитории.
        - В GUI мы просто показываем или скрываем панель, но не фильтруем логи.
        - Это позволяет:
            * Всегда сохранять детальные логи в файл.
            * Пользователю управлять только визуальной частью.

        🖥️ Применение размера окна:
        - При изменении 'window_size' в настройках:
            * config.apply_settings() отправляет сигнал 'window_size'
            * Application ловит сигнал и вызывает main_window.resize(width, height)
        - Окно мгновенно меняет размер — без перезапуска.

        💡 Пример использования:
            self.config.set("full_log", True)
            self.config.set("window_size", [1200, 800])
            self.config.apply_settings()  # ← Применяем всё сразу

        ⚠️ Важно:
        - Этот метод НЕ сохраняет настройки в файл. Для сохранения нужно вызвать config.save() отдельно.
        - Сигнал config_changed должен быть подключён в Application (см. Application.run()).

        🛠️ Расширяемость:
        В будущем можно добавить:
            - Применение темы (например, 'dark_mode')
            - Язык интерфейса ('language')
            - Шрифт, автосохранение и т.д.
        Просто добавь:
            self.config_changed.emit("new_setting", value)

        Returns:
            None
        """
        # 1. Управление панелью логов: показать/скрыть
        full_log = self.get("full_log", False)
        self.config_changed.emit("full_log", full_log)
        self.logger.info(
            f"✅ Режим полного лога {'включён' if full_log else 'отключён'} — панель логов {'показана' if full_log else 'скрыта'}")

        # 2. Применение размера окна
        window_size = self.get("window_size", [1920, 1080])
        width, height = window_size[0], window_size[1]
        maximized = self.get("maximized", False)
        self.config_changed.emit("window_mode", {"window_size": window_size, "maximized": maximized})
        self.logger.info(f"✅ Размер окна изменён: {width}x{height}")

        # 3. Другие настройки (заготовка на будущее)
        # Пример:
        # theme = self.get("theme", "light")
        # self.config_changed.emit("theme", theme)

    def create_default_config(self):
        """
        Создаёт файл settings.json с настройками по умолчанию.

        Пример содержимого:
        {
            "full_log": false,
            "window_size": [900, 700],
            "auto_save_logs": true,
            "tab_order": [...],
            "tabs": { ... }
        }

        Вызывается, если settings.json не существует.
        """
        default_data = {
            "log_file": "logs/app.log",
            "full_log": False,
            "icon_path": "assets/icon.png",
            "style_file": "styles/app.qss",
            "tab_order": [
                "check_invoices",
                "create_tt",
                "rebind_tt",
                "tasks",
                "ai_chat",
                "settings"
            ],
            "tabs": {
                "check_invoices": {
                    "title": "Проверка накладных",
                    "type": "business_process",
                    "module": "check_invoices",
                    "class": "CheckInvoicesView"
                },
                "create_tt": {
                    "title": "Создание ТТ",
                    "type": "business_process",
                    "module": "create_tt",
                    "class": "CreateTtView"
                },
                "rebind_tt": {
                    "title": "Перепривязка ТТ",
                    "type": "business_process",
                    "module": "rebind_tt",
                    "class": "RebindTtView"
                },
                "tasks": {
                    "title": "Задачи",
                    "type": "internal_app",
                    "module": "tasks",
                    "class": "TaskManagerView"
                },
                "ai_chat": {
                    "title": "Чат с AI-агентом",
                    "type": "internal_app",
                    "module": "ai_chat",
                    "class": "AIAgentChatView"
                },
                "settings": {
                    "title": "Настройки",
                    "type": "internal_app",
                    "module": "settings",
                    "class": "SettingsAppView"
                }
            }
        }
        self.data = default_data
        self.save()
        self.log("info", "Создан и сохранён дефолтный конфиг")

    def get_tab_config(self) -> dict:
        """
        Возвращает конфигурацию всех вкладок приложения.

        Returns:
            dict: {
                "tab_key": {
                    "title": "Отображаемое имя",
                    "type": "business_process|internal_app",
                    "module": "имя_модуля",
                    "class": "ИмяКлассаView"
                },
                ...
            }

        Пример:
            config.get_tab_config() → {
                "check_invoices": {
                    "title": "Проверка накладных",
                    "type": "business_process",
                    "module": "check_invoices",
                    "class": "CheckInvoicesView"
                }
            }

        Используется в Application для динамической регистрации вкладок.
        """
        return self.get("tabs", {})

    def get_tab_order(self) -> list:
        """
        Возвращает порядок вкладок.

        Returns:
            list: Список ключей вкладок в нужном порядке

        Пример:
            config.get_tab_order() → ["check_invoices", "settings", "ai_chat"]

        Если не задан — возвращает все ключи из tabs.
        """
        order = self.get("tab_order")
        if order:
            return order

        # Если порядок не задан — возвращаем все ключи
        return list(self.get_tab_config().keys())

    def _buffer_log(self, level: str, message: str):
        """Сохраняет лог в буфер, если logger ещё не готов"""
        self._log_buffer.append((level, message))
        # Всё равно выводим в консоль — чтобы видеть, даже если logger не инициализирован
        print(f"[{level.upper()}] {message}", file=sys.stderr)

    def _flush_buffer(self):
        """Сбрасывает буфер в настоящий логгер"""
        if self.logger:
            for level, msg in self._log_buffer:
                getattr(self.logger, level)(msg)
            self._log_buffer.clear()

    def log(self, level: str, message: str):
        """
        Логирует сообщение, используя Logger, если он доступен.
        Если нет — сохраняет в буфер и выводит в stderr.

        Args:
            level (str): 'debug', 'info', 'warning', 'error'
            message (str): Сообщение для логирования
        """
        level = level.lower()
        if level not in ("debug", "info", "warning", "error"):
            level = "info"

        if self.logger:
            getattr(self.logger, level)(message)
        else:
            from src.core.logger import Logger
            Logger.log_before_gui(level, message)

    def set_logger(self, logger):
        """
        Привязывает готовый экземпляр Logger к Config и сбрасывает буфер ранних логов.

        Args:
            logger (Logger): Инициализированный глобальный логгер.

        Шаги:
        1. Сохранить logger в self.logger.
        2. Перенаправить все накопленные сообщения из буфера в настоящий логгер.
        3. Залогировать успешную привязку: "Config: Logger attached. X buffered messages flushed."

        Примечание:
        - Вызывается из Application после инициализации Logger.
        - Гарантирует, что никакие ранние логи не потеряются.
        """
        self.logger = logger

        # Сбрасываем буфер
        flushed_count = 0
        for level, message in self._log_buffer:
            getattr(self.logger, level)(message)
            flushed_count += 1

        # Логируем факт привязки — уже через настоящий файл
        self.logger.info(f"Config: Logger attached. {flushed_count} buffered messages flushed.")
        self._log_buffer.clear()  # На всякий случай