"""
tests/test_invoice_checker_process_real.py

Интеграционный тест: запуск полного процесса проверки накладных.

Цель:
- Проверить, что InvoiceCheckerProcess.run() корректно:
  1. Читает Excel-файл
  2. Фильтрует накладные
  3. Создаёт Invoice-объекты
  4. Проверяет накладные через InvoiceSearchOperation (с реальным браузером)
  5. Генерирует отчёт
  6. Логирует время выполнения

Особенности:
- Запускается с реальным браузером (требует DMS-доступ)
- Использует реальный Excel-файл
- Полностью повторяет продакшн-сценарий
- Проверяет инициализацию, выполнение, завершение
- Не использует моки

Предусловие:
- Файл "data/test_invoices.xlsx" существует
- Содержит листы: "мой куб GC", "мой куб BF", "мой куб PU"
- Столбцы: "Названия строк", "ID XCRM Parent", "Address Normalized", "ISA", "SFA"
- Номера накладных начинаются с "01/" (Сибирь) или "02/" (Урал)
- Пользователь авторизован в DMS (или логин/пароль в config.json)
"""

import pytest
from selenium.common.exceptions import WebDriverException, TimeoutException
from src.core.logger import Logger
from src.core.config import Config
from src.buisness_processes.check_invoices.process import InvoiceCheckerProcess


@pytest.fixture
def logger():
    """Возвращает реальный Logger, как в других тестах."""
    return Logger()


@pytest.mark.real_browser
def test_invoice_checker_process_run_real(logger):
    """
    Интеграционный тест: запуск полного процесса проверки накладных.

    Проверяет:
    - Успешное чтение файла
    - Фильтрация по isa_amount ≠ 0 и sfa_amount = None
    - Создание Invoice-объектов
    - Проверка накладных в DMS (через реальный браузер)
    - Генерация отчёта
    - Логирование времени выполнения
    """
    process = None
    try:
        # Загружаем конфиг
        config = Config(logger=logger)
        config.load()

        # Создаём процесс
        process = InvoiceCheckerProcess(logger=logger, config=config)

        # Путь к тестовому файлу
        file_path = "data/SO продажи_сверка ISA_SFA 08.2025 001.xlsx"

        logger.info("📁 Проверка: существует ли файл...")
        assert (
            __import__("os").path.exists(file_path)
        ), f"Файл не найден: {file_path}"

        logger.info(f"🚀 Запуск полного процесса проверки накладных из {file_path}...")
        process.run(file_path)

        # Если дошли сюда — процесс завершился без исключений
        logger.info("✅ Процесс завершён успешно")

        # Проверяем, что отчёт создан
        report_path = "data/report_of_checking_invoices.xlsx"
        assert __import__("os").path.exists(report_path), f"Отчёт не создан: {report_path}"
        logger.info(f"📄 Отчёт найден: {report_path}")

    except AssertionError as e:
        pytest.fail(f"Ошибка утверждения: {e}")
    except TimeoutException as e:
        pytest.fail(f"Таймаут при ожидании элемента в браузере: {e}")
    except WebDriverException as e:
        pytest.fail(f"Ошибка WebDriver (браузер упал): {e}")
    except Exception as e:
        pytest.fail(f"Неожиданная ошибка в процессе: {e}")
    finally:
        if process and hasattr(process, "operator") and process.operator:
            logger.info("🧹 Закрытие браузера через operator.close()...")
            try:
                process.operator.close()  # Закрываем браузер, если был запущен
            except Exception as e:
                logger.error(f"Ошибка при закрытии operator: {e}")

        logger.info("🔚 Тест завершён")