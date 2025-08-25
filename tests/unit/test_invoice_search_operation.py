# tests/test_invoice_search_operation.py

import pytest
from selenium.common.exceptions import WebDriverException

from src.core.logger import Logger
from src.core.config import Config
from src.models.invoice.invoice import Invoice, CheckStatus, CheckedInvoice
from src.buisness_processes.check_invoices.operation import InvoiceSearchOperation


@pytest.fixture
def logger():
    return Logger()


@pytest.fixture
def operation_siberia(logger):
    """Фикстура: операция для Сибири."""
    config = Config(logger)
    config.load()
    op = InvoiceSearchOperation(region="siberia", logger=logger, config=config)
    yield op
    if op._initialized:
        op.close()


@pytest.fixture
def sample_invoice():
    """Пример накладной из Сибири."""
    return Invoice(
        number="01/195472",
        crm_id="{E3BDA348-F996-E811-811C-005056011415}",
        address="Красноярский край, г Дивногорск, ул Бочкина, д 10А/3",
        isa_amount=1000.0,
        sfa_amount=500.0,
        prefix="01",
        region="siberia",
        delivery_city="Красноярск"
    )


# --- ТЕСТЫ ---


def test_operation_start_siberia(operation_siberia):
    """Проверяет, что сессия DMS успешно запускается для Сибири."""
    operation_siberia.start()

    assert operation_siberia._initialized is True
    assert operation_siberia.invoices_page is not None


def test_check_invoice_found(operation_siberia, sample_invoice, logger):
    """Проверяет, что найденная накладная возвращает статус FOUND."""
    # Запускаем сессию
    operation_siberia.start()

    # Проверяем накладную
    result = operation_siberia.check_invoice(sample_invoice)

    # Проверяем результат
    assert isinstance(result, CheckedInvoice), "Результат должен быть экземпляром CheckedInvoice"
    assert result.status == CheckStatus.FOUND
    assert result.invoice.number == sample_invoice.number
    assert result.invoice.region == "siberia"

    # Проверяем лог
    # (в реальности можно мокать logger, но здесь мы просто смотрим вывод)
    logger.info(f"✅ Тест: накладная {sample_invoice.number} — статус: {result.status}")


def test_check_invoice_not_found(operation_siberia, logger):
    """Проверяет, что ненайденная накладная возвращает NOT_FOUND."""
    operation_siberia.start()

    fake_invoice = Invoice(
        number="99/999999",  # заведомо несуществующий номер
        crm_id="",
        address="",
        isa_amount=100.0,
        sfa_amount=50.0,
        prefix="99",
        region="siberia",
        delivery_city="Красноярск"
    )

    result = operation_siberia.check_invoice(fake_invoice)

    assert result.status == CheckStatus.NOT_FOUND
    assert result.invoice.number == fake_invoice.number
    logger.info(f"✅ Тест: накладная {fake_invoice.number} — не найдена (ожидаемо)")


def test_switch_to_city_success(operation_siberia):
    """Проверяет, что переключение на город работает."""
    operation_siberia.start()

    # Пробуем переключиться на Красноярск
    try:
        operation_siberia._switch_to_city("Красноярск")
        current = operation_siberia.invoices_page.get_current_orgstructure()
        assert "Красноярск" in current
    except Exception as e:
        pytest.fail(f"Не удалось переключиться на город: {e}")


def test_check_invoice_returns_checked_invoice(operation_siberia, sample_invoice):
    """Проверяет, что check_invoice возвращает CheckedInvoice с оригиналом."""
    operation_siberia.start()
    result = operation_siberia.check_invoice(sample_invoice)

    assert hasattr(result, "invoice")
    assert hasattr(result, "status")
    assert isinstance(result.invoice, Invoice)
    assert result.invoice.number == sample_invoice.number


# --- СКИПАЕМЫЕ ТЕСТЫ (для ручного запуска) ---


@pytest.mark.manual
def test_check_invoice_real_data_from_excel(operation_siberia, logger):
    """
    Ручной тест: проверка нескольких накладных из Excel.
    Запускать только с реальным файлом.
    """
    # Пример: загрузи файл и передай накладные
    test_cases = [

    ]

    operation_siberia.start()

    for inv in test_cases:
        logger.info(f"🔍 Проверка: {inv.number}")
        result = operation_siberia.check_invoice(inv)
        status = "✅ Найдена" if result.status == CheckStatus.FOUND else "❌ Не найдена"
        logger.info(f"{status} — {inv.number}")