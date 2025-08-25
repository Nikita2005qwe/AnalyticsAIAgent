# tests/test_invoice_factory.py
import pytest
from src.models.invoice.invoice_factory import InvoiceFactory
from src.models.invoice.invoice import Invoice

factory = InvoiceFactory()


def test_create_invoice_krasnoyarsk():
    """Тест: создание накладной из Красноярска с префиксом '01/'"""
    data = {
        "number": "01/179703",
        "isa_amount": 45439.77,
        "sfa_amount": None,
        "address": "Красноярский край, г Дивногорск, ул Бочкина, д 10А/3"
    }

    invoice = factory.from_dict(data)

    # Проверяем, что накладная создана
    assert invoice is not None
    assert isinstance(invoice, Invoice)

    # Проверяем поля
    assert invoice.number == "01/179703"
    assert invoice.prefix == "01/"
    assert invoice.region == "siberia"
    assert invoice.isa_amount == 45439.77
    assert invoice.sfa_amount is None
    assert invoice.found_in_dms is False
    assert invoice.status == "pending"


def test_extract_prefix_01():
    """Тест: извлечение префикса '01/'"""
    assert factory.extract_prefix("01/179703") == "01/"
    assert factory.extract_prefix("01/123") == "01/"


def test_create_invoice_unknown_prefix():
    """Тест: накладная с неизвестным префиксом — не создаётся"""
    data = {
        "number": "ВН-003448",
        "isa_amount": -666.63,
        "sfa_amount": None
    }

    invoice = factory.from_dict(data)
    assert invoice is None  # ← не создаём, потому что префикс не в списке


def test_filter_out_sfa_not_empty():
    """Тест: если SFA не пусто — всё равно создаём, фильтрация не здесь"""
    data = {
        "number": "01/123456",
        "isa_amount": 100.0,
        "sfa_amount": 100.0
    }
    invoice = factory.from_dict(data)
    assert invoice is not None
    assert invoice.sfa_amount == 100.0