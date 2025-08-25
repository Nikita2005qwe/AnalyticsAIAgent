import unittest
import os
import sys
import logging
from unittest.mock import Mock
from src.core.logger import Logger


class TestLogger(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Создаём временную директорию для всех тестов"""
        cls.temp_dirs = []

    @classmethod
    def tearDownClass(cls):
        """Очищаем все временные директории после всех тестов"""
        for temp_dir in cls.temp_dirs:
            try:
                if os.path.exists(temp_dir):
                    import shutil
                    shutil.rmtree(temp_dir, ignore_errors=True)
            except:
                pass

    def setUp(self):
        """Сброс синглтона перед каждым тестом"""
        if Logger._instance is not None:
            # Закрываем все обработчики
            for handler in Logger._instance._logger.handlers[:]:
                handler.close()
                Logger._instance._logger.removeHandler(handler)
            Logger._instance = None
        Logger._logger = None

    def create_temp_log_file(self, suffix="test"):
        """Создаёт уникальный путь для лога и запоминает директорию"""
        log_dir = f"temp_logs_{suffix}"
        log_file = f"{log_dir}/app.log"
        self.temp_dirs.append(log_dir)  # Для очистки в конце
        return log_file

    def test_singleton_enforced(self):
        """Проверяет, что нельзя создать экземпляр напрямую"""
        Logger.get_instance()
        with self.assertRaises(RuntimeError):
            Logger()

    def test_get_instance_returns_same_object(self):
        """Проверяет, что get_instance возвращает один и тот же объект"""
        logger1 = Logger.get_instance()
        logger2 = Logger.get_instance()
        self.assertIs(logger1, logger2)

    def test_log_file_is_created_and_written(self):
        """Проверяет, что файл лога создаётся и в него можно писать"""
        log_file = self.create_temp_log_file("file_created")

        logger = Logger.get_instance(log_file=log_file)
        logger.info("Тестовое сообщение")

        # Сбрасываем буфер
        for handler in logger._logger.handlers:
            if isinstance(handler, logging.FileHandler):
                handler.flush()

        self.assertTrue(os.path.exists(log_file), "Файл лога не был создан")
        with open(log_file, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn("INFO", content)
            self.assertIn("Тестовое сообщение", content)

    def test_all_log_levels_are_recorded(self):
        """Проверяет, что все уровни логирования работают (с уровнем DEBUG)"""
        log_file = self.create_temp_log_file("levels")

        logger = Logger.get_instance(log_file=log_file, level="DEBUG")

        logger.debug("Отладка")
        logger.info("Информация")
        logger.warning("Предупреждение")
        logger.error("Ошибка")

        for handler in logger._logger.handlers:
            if isinstance(handler, logging.FileHandler):
                handler.flush()

        self.assertTrue(os.path.exists(log_file))
        with open(log_file, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn("DEBUG", content)
            self.assertIn("Отладка", content)
            self.assertIn("INFO", content)
            self.assertIn("Информация", content)
            self.assertIn("WARNING", content)
            self.assertIn("Предупреждение", content)
            self.assertIn("ERROR", content)
            self.assertIn("Ошибка", content)

    def test_directory_is_created_automatically(self):
        """Проверяет, что директория для логов создаётся автоматически"""
        log_file = self.create_temp_log_file("dir_created")

        # Убедимся, что папки нет
        log_dir = os.path.dirname(log_file)
        if os.path.exists(log_dir):
            import shutil
            shutil.rmtree(log_dir, ignore_errors=True)

        self.assertFalse(os.path.exists(log_dir), "Директория уже существует до создания")

        logger = Logger.get_instance(log_file=log_file)
        logger.info("Test")

        for handler in logger._logger.handlers:
            if isinstance(handler, logging.FileHandler):
                handler.flush()

        self.assertTrue(os.path.exists(log_dir), "Директория не была создана")
        self.assertTrue(os.path.exists(log_file), "Файл лога не был создан")

    def test_gui_handler_emits_signal(self):
        """Проверяет, что GUI-обработчик отправляет сигнал с правильными аргументами"""
        mock_signal = Mock()
        log_file = self.create_temp_log_file("gui")

        logger = Logger.get_instance(log_file=log_file)
        logger.setup_gui_handler(target_signal=mock_signal)

        logger.warning("GUI: сообщение")

        # Проверяем, что сигнал был вызван
        mock_signal.log.emit.assert_called_once_with("WARNING", "GUI: сообщение")

    def test_gui_handler_does_not_duplicate(self):
        """Проверяет, что GUI-обработчик добавляется только один раз"""
        log_file = self.create_temp_log_file("gui_once")
        mock_signal = Mock()

        logger = Logger.get_instance(log_file=log_file)
        logger.setup_gui_handler(mock_signal)
        logger.setup_gui_handler(mock_signal)  # Повторный вызов

        # Фильтруем по наличию атрибута signal (уникально для GUIHandler)
        gui_handlers = [h for h in logger._logger.handlers if hasattr(h, 'signal')]
        self.assertEqual(len(gui_handlers), 1, "GUI-обработчик добавлен более одного раза")

    def test_logger_respects_log_level(self):
        """Проверяет, что при уровне INFO сообщения DEBUG не попадают в файл"""
        log_file = self.create_temp_log_file("level_info")

        logger = Logger.get_instance(log_file=log_file, level="INFO")
        logger.debug("Это debug-сообщение")
        logger.info("Это info-сообщение")

        for handler in logger._logger.handlers:
            if isinstance(handler, logging.FileHandler):
                handler.flush()

        self.assertTrue(os.path.exists(log_file))
        with open(log_file, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertNotIn("DEBUG", content, "DEBUG сообщение попало в лог при уровне INFO")
            self.assertIn("INFO", content)
            self.assertIn("info-сообщение", content)


if __name__ == '__main__':
    unittest.main(verbosity=2)