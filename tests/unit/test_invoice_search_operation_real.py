# tests/test_invoice_search_operation_real.py

import pytest
from selenium.common.exceptions import TimeoutException, WebDriverException

from src.core.logger import Logger
from src.core.config import Config
from src.buisness_processes.check_invoices.operation import InvoiceSearchOperation


@pytest.fixture
def logger():
    """Простой логгер, который выводит в консоль."""
    return Logger()

@pytest.mark.real_browser
def test_invoice_search_operation_start_siberia(logger):
    """
    Интеграционный тест: запуск InvoiceSearchOperation для Сибири.
    Проверяет реальную сессию: вход, навигация, инициализация.
    """
    operation = None
    try:
        # Создаём операцию для Сибири
        config = Config(logger)
        config.load()
        operation = InvoiceSearchOperation(region="siberia", logger=logger, config=config)

        logger.info("🔄 Запуск метода start() для региона 'siberia'...")
        operation.start()

        # Проверяем, что сессия инициализирована
        assert operation._initialized is True, "Сессия не была инициализирована"
        logger.info("✅ Сессия инициализирована")

        # Проверяем, что мы на странице накладных
        assert operation.invoices_page is not None, "InvoicesPage не был инициализирован"
        assert operation.invoices_page.is_loaded() is True, "Страница накладных не загружена"

        logger.info("✅ Успешно вошли в DMS и попали на страницу накладных")

    except TimeoutException as e:
        pytest.fail(f"Таймаут при ожидании элемента: {e}")
    except WebDriverException as e:
        pytest.fail(f"Ошибка WebDriver: {e}")
    except Exception as e:
        pytest.fail(f"Неожиданная ошибка: {e}")
    finally:
        if operation:
            logger.info("🧹 Закрытие браузера...")
            operation.close()