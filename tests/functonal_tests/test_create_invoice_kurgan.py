# tests/functonal_tests/test_create_invoice_kurgan.py
import pytest
from src.models.invoice.invoice_factory import InvoiceFactory
from src.models.invoice.invoice import Invoice


factory = InvoiceFactory()


def test_create_invoice_kurgan():
    """Тест: создание накладной из Кургана с префиксом '07/'"""
    data = {
        "number": "07/046227",
        "isa_amount": 13808.31,
        "sfa_amount": 13808.31,
        "address": "г Курган, ул Карбышева, д 13"
    }

    invoice = factory.from_dict(data)

    # Проверяем, что накладная создана
    assert invoice is not None
    assert isinstance(invoice, Invoice)

    # Проверяем поля
    assert invoice.number == "07/046227"
    assert invoice.prefix == "07/"
    assert invoice.region == "ural"
    assert invoice.isa_amount == 13808.31
    assert invoice.sfa_amount == 13808.31
    assert invoice.found_in_dms is False
    assert invoice.status == "pending"


def test_extract_prefix_07():
    """Тест: извлечение префикса '07/'"""
    assert factory.extract_prefix("07/046227") == "07/"
    assert factory.extract_prefix("07/123") == "07/"


def test_get_city_by_prefix_07():
    """Тест: префикс '07/' → город 'Челябинск'"""
    from src.models.invoice.invoice_regions import get_city_by_prefix
    city = get_city_by_prefix("07/")
    assert city == "Челябинск"


def test_get_alternative_city_for_07():
    """Тест: у префикса '07/' есть альтернативный город — 'Курган'"""
    from src.models.invoice.invoice_regions import INVOICE_PREFIX_REGIONS
    alt_city = INVOICE_PREFIX_REGIONS["07/"].get("alternative_city")
    assert alt_city == "Курган"