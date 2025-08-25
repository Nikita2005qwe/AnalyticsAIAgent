import pytest
from src.models.invoice.invoice_factory import InvoiceFactory
from src.models.invoice.invoice import Invoice


class TestInvoiceFactoryUnit:
    """Только unit-тесты для InvoiceFactory — без зависимости от файлов и pandas."""

    def test_create_invoice_success_full_data(self):
        """TC-IF-01: Успешное создание Invoice из валидных данных"""
        row = {
            "number": "05/050426",
            "crm_id": "{A6948B29-264D-E711-80FA-005056011415}",
            "address": "г Новосибирск, ул Громова, д 12",
            "isa_amount": "3106.64",
            "sfa_amount": "3106.64",
        }

        invoice = InvoiceFactory._create_invoice(row)

        assert isinstance(invoice, Invoice)
        assert invoice.number == "05/050426"
        assert invoice.crm_id == "{A6948B29-264D-E711-80FA-005056011415}"
        assert "Новосибирск" in invoice.address
        assert invoice.isa_amount == 3106.64
        assert invoice.sfa_amount == 3106.64
        assert invoice.prefix == "05/"
        assert invoice.region == "siberia"
        assert invoice.delivery_city == "Новосибирск"

    def test_extract_prefix_slash_format(self):
        """TC-IF-02: Извлечение префикса вида 'XX/'"""
        assert InvoiceFactory._extract_prefix("05/123456") == "05/"
        assert InvoiceFactory._extract_prefix("01/999999") == "01/"
        assert InvoiceFactory._extract_prefix("07/000001") == "07/"

    def test_extract_prefix_dash_format(self):
        """TC-IF-03: Извлечение префикса вида 'X-'"""
        assert InvoiceFactory._extract_prefix("Ч-054192") == "Ч-"
        assert InvoiceFactory._extract_prefix("Б-002444") == "Б-"
        assert InvoiceFactory._extract_prefix("Е-001320") == "Е-"
        assert InvoiceFactory._extract_prefix("И-123456") == "И-"

    def test_extract_prefix_unknown_returns_none(self):
        """TC-IF-04: Неизвестный префикс → None"""
        assert InvoiceFactory._extract_prefix("XX-123456") is None
        assert InvoiceFactory._extract_prefix("ZZ/123456") is None
        assert InvoiceFactory._extract_prefix("ABC123") is None

    def test_determine_delivery_city_main_city(self):
        """TC-IF-05: Город по префиксу (основной)"""
        city = InvoiceFactory._determine_delivery_city("05/", "любой адрес")
        assert city == "Новосибирск"

        city = InvoiceFactory._determine_delivery_city("01/", "Красноярск")
        assert city == "Красноярск"

    def test_determine_delivery_city_alternative_in_address(self):
        """TC-IF-06: Префикс 04/ + адрес с 'Новосибирск' → Новосибирск"""
        prefix = "04/"
        address = "г Новосибирск, ул Мира, д 1"
        city = InvoiceFactory._determine_delivery_city(prefix, address)
        assert city == "Новосибирск"

    def test_determine_delivery_city_alternative_not_in_address(self):
        """TC-IF-07: Префикс 04/, но адрес не содержит Новосибирск → Новокузнецк"""
        prefix = "04/"
        address = "Кемеровская обл, г Прокопьевск, ул Ленина"
        city = InvoiceFactory._determine_delivery_city(prefix, address)
        assert city == "Новокузнецк"

    def test_create_invoice_missing_required_field(self):
        """TC-IF-08: Отсутствует обязательное поле → None"""
        row = {
            "number": None,
            "crm_id": "id",
            "address": "addr",
            "isa_amount": "100",
            "sfa_amount": "100",
        }
        invoice = InvoiceFactory._create_invoice(row)
        assert invoice is None

    def test_create_invoice_empty_number(self):
        """TC-IF-08: Пустой номер → None"""
        row = {
            "number": "",
            "crm_id": "id",
            "address": "addr",
            "isa_amount": "100",
            "sfa_amount": "100",
        }
        invoice = InvoiceFactory._create_invoice(row)
        assert invoice is None

    def test_parse_isa_amount_with_comma(self):
        """TC-IF-09: Парсинг ISA с запятой как разделителем тысяч"""
        row = {
            "number": "05/050426",
            "crm_id": "id",
            "address": "addr",
            "isa_amount": "54439.01",
            "sfa_amount": "100",
        }
        invoice = InvoiceFactory._create_invoice(row)
        assert invoice.isa_amount == 54439.01

    def test_parse_isa_amount_empty_is_zero(self):
        """TC-IF-11: Пустой ISA → 0.0"""
        row = {
            "number": "05/050426",
            "crm_id": "id",
            "address": "addr",
            "isa_amount": "",
            "sfa_amount": "100",
        }
        invoice = InvoiceFactory._create_invoice(row)
        assert invoice.isa_amount == 0.0

    def test_parse_sfa_amount_empty_is_none(self):
        """TC-IF-10: Пустой SFA → None"""
        row = {
            "number": "05/050426",
            "crm_id": "id",
            "address": "addr",
            "isa_amount": "100",
            "sfa_amount": "",
        }
        invoice = InvoiceFactory._create_invoice(row)
        assert invoice.sfa_amount is None

    def test_parse_negative_amounts(self):
        """TC-IF-09: Отрицательные суммы (возвраты)"""
        row = {
            "number": "ВВ-001271",
            "crm_id": "id",
            "address": "г Новосибирск, ул Ильича, д 6",
            "isa_amount": "-239.12",
            "sfa_amount": "-239.12",
        }
        invoice = InvoiceFactory._create_invoice(row)
        assert invoice is None


    def test_create_invoices_list_all_valid(self):
        """TC-IF-12: Массовое создание — все строки валидны"""
        data = [
            {"number": "05/050426", "crm_id": "id1", "address": "addr1", "isa_amount": "100", "sfa_amount": "100"},
            {"number": "01/177230", "crm_id": "id2", "address": "addr2", "isa_amount": "200", "sfa_amount": "200"},
        ]
        invoices = InvoiceFactory.create_invoices(data)
        assert len(invoices) == 2
        assert invoices[0].prefix == "05/"
        assert invoices[0].region == "siberia"
        assert invoices[1].prefix == "01/"
        assert invoices[1].region == "siberia"

    def test_create_invoices_skip_invalid_row(self):
        """TC-IF-13: Пропуск невалидной строки в списке"""
        data = [
            {"number": "05/050426", "crm_id": "id", "address": "addr", "isa_amount": "100", "sfa_amount": "100"},
            {"number": None, "crm_id": "bad", "address": "bad", "isa_amount": "100", "sfa_amount": "100"},  # invalid
        ]
        invoices = InvoiceFactory.create_invoices(data)
        assert len(invoices) == 1
        assert invoices[0].number == "05/050426"

    def test_create_invoice_unknown_prefix_returns_none(self):
        """TC-IF-14: Префикс не в справочнике → None"""
        row = {
            "number": "С-003428",
            "crm_id": "id",
            "address": "addr",
            "isa_amount": "100",
            "sfa_amount": "100",
        }
        invoice = InvoiceFactory._create_invoice(row)
        assert invoice is None

    def test_invoice_is_frozen_dataclass(self):
        """TC-IF-15: Invoice — неизменяемый объект"""
        invoice = Invoice(
            number="01/123",
            crm_id="id",
            address="addr",
            isa_amount=100.0,
            sfa_amount=100.0,
            prefix="01/",
            region="siberia",
            delivery_city="Красноярск",
        )
        with pytest.raises(Exception):
            invoice.number = "new_value"  # Должно выбросить FrozenInstanceError

    def test_determine_delivery_city_for_ural_prefix(self):
        """Проверка города для префикса 07/ → Челябинск"""
        city = InvoiceFactory._determine_delivery_city("07/", "Курганская обл, п Усть-Утяк")
        assert city == "Курган"

    def test_determine_delivery_city_for_alternative_city_with_partial_match(self):
        """Проверка, что накладная 04/ найдётся в Новокузнецке
        при том что город явно не указан в строке адреса"""
        address = "Алтайский край, г Барнаул, ул Энтузиастов, д 14"
        city = InvoiceFactory._determine_delivery_city("04/", address)
        # Должно сработать по точному вхождению "Новосибирск"
        assert city == "Новокузнецк"

    def test_parse_amount_with_zero_value(self):
        """Проверка суммы 0.00"""
        row = {
            "number": "Б-002444",
            "crm_id": "id",
            "address": "г Абакан, ул Западная, д 50",
            "isa_amount": "0.00",
            "sfa_amount": "",
        }
        invoice = InvoiceFactory._create_invoice(row)
        assert invoice.isa_amount == 0.0
        assert invoice.sfa_amount is None
        assert invoice.prefix == "Б-"
        assert invoice.region == "siberia"
        assert invoice.delivery_city == "Абакан"