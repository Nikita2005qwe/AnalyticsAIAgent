import unittest
from src.services.invoice_factory import InvoiceFactory, INVOICE_PREFIX_REGIONS
from src.models.invoice import Invoice


class TestInvoiceFactory(unittest.TestCase):

    def test_create_invoice_siberia_numeric_prefix(self):
        """Тест создания накладной с числовым префиксом Сибири."""
        invoice = InvoiceFactory.create_invoice("01/12345")
        self.assertEqual(invoice.number, "01/12345")
        self.assertEqual(invoice.prefix, "01/")
        self.assertEqual(invoice.region, "siberia")
        self.assertFalse(invoice.found_in_dms)

        invoice = InvoiceFactory.create_invoice("02/67890")
        self.assertEqual(invoice.prefix, "02/")
        self.assertEqual(invoice.region, "siberia")

    def test_create_invoice_ural_numeric_prefix(self):
        """Тест создания накладной с числовым префиксом Урала."""
        invoice = InvoiceFactory.create_invoice("07/12345")
        self.assertEqual(invoice.number, "07/12345")
        self.assertEqual(invoice.prefix, "07/")
        self.assertEqual(invoice.region, "ural")

    def test_create_invoice_siberia_letter_prefix(self):
        """Тест создания накладной с буквенным префиксом Сибири."""
        invoice = InvoiceFactory.create_invoice("Е-12345")
        self.assertEqual(invoice.number, "Е-12345")
        self.assertEqual(invoice.prefix, "Е-")
        self.assertEqual(invoice.region, "siberia")

        invoice = InvoiceFactory.create_invoice("Б-67890")
        self.assertEqual(invoice.prefix, "Б-")
        self.assertEqual(invoice.region, "siberia")

    def test_create_invoice_ural_letter_prefix(self):
        """Тест создания накладной с буквенным префиксом Урала."""
        invoice = InvoiceFactory.create_invoice("Ч-12345")
        self.assertEqual(invoice.number, "Ч-12345")
        self.assertEqual(invoice.prefix, "Ч-")
        self.assertEqual(invoice.region, "ural")

    def test_create_invoice_unknown_prefix(self):
        """Тест создания накладной с неизвестным префиксом."""
        invoice = InvoiceFactory.create_invoice("XYZ12345")
        self.assertEqual(invoice.number, "XYZ12345")
        self.assertEqual(invoice.prefix, "")
        self.assertEqual(invoice.region, "unknown")

        # Тест без префикса
        invoice = InvoiceFactory.create_invoice("12345")
        self.assertEqual(invoice.prefix, "")
        self.assertEqual(invoice.region, "unknown")

    def test_create_invoice_empty_number(self):
        """Тест создания накладной с пустым номером."""
        invoice = InvoiceFactory.create_invoice("")
        self.assertEqual(invoice.number, "")
        self.assertEqual(invoice.prefix, "")
        self.assertEqual(invoice.region, "unknown")

    def test_create_invoices_from_numbers_list(self):
        """Тест создания списка накладных из списка номеров."""
        numbers = ["01/12345", "07/67890", "Е-11111", "XYZ99999", ""]
        invoices = InvoiceFactory.create_invoices_from_numbers(numbers)

        # Должно создать 4 накладные (пустая строка игнорируется)
        self.assertEqual(len(invoices), 4)

        # Проверяем порядок и данные
        self.assertEqual(invoices[0].number, "01/12345")
        self.assertEqual(invoices[0].region, "siberia")
        self.assertEqual(invoices[1].number, "07/67890")
        self.assertEqual(invoices[1].region, "ural")
        self.assertEqual(invoices[2].number, "Е-11111")
        self.assertEqual(invoices[2].region, "siberia")
        self.assertEqual(invoices[3].number, "XYZ99999")
        self.assertEqual(invoices[3].region, "unknown")

    def test_create_invoices_filter_invalid(self):
        """Тест фильтрации невалидных номеров."""
        numbers = ["01/12345", "nan", "", "07/67890", "nan"]
        invoices = InvoiceFactory.create_invoices_from_numbers(numbers)

        # Должно создать 2 накладные (без "nan" и пустых)
        self.assertEqual(len(invoices), 2)
        self.assertEqual(invoices[0].number, "01/12345")
        self.assertEqual(invoices[1].number, "07/67890")

    def test_extract_prefix_comprehensive(self):
        """Комплексный тест извлечения префиксов."""
        test_cases = [
            ("01/12345", "01/"),
            ("02/67890", "02/"),
            ("04/11111", "04/"),
            ("05/22222", "05/"),
            ("06/33333", "06/"),
            ("07/44444", "07/"),
            ("Е-12345", "Е-"),
            ("Б-67890", "Б-"),
            ("К-11111", "К-"),
            ("И-22222", "И-"),
            ("У-33333", "У-"),
            ("Ч-44444", "Ч-"),
            ("XYZ12345", ""),  # Неизвестный префикс
            ("12345", ""),  # Без префикса
            ("", ""),  # Пустая строка
        ]

        for invoice_number, expected_prefix in test_cases:
            with self.subTest(invoice_number=invoice_number):
                prefix = InvoiceFactory._extract_prefix(invoice_number)
                self.assertEqual(prefix, expected_prefix)

    def test_get_region_by_prefix_all_known(self):
        """Тест определения региона для всех известных префиксов."""
        # Тест Сибири
        siberia_prefixes = ["01/", "02/", "04/", "05/", "06/", "Е-", "Б-", "К-", "И-", "У-"]
        for prefix in siberia_prefixes:
            with self.subTest(prefix=prefix):
                region = InvoiceFactory._get_region_by_prefix(prefix)
                self.assertEqual(region, "siberia")

        # Тест Урала
        ural_prefixes = ["07/", "Ч-"]
        for prefix in ural_prefixes:
            with self.subTest(prefix=prefix):
                region = InvoiceFactory._get_region_by_prefix(prefix)
                self.assertEqual(region, "ural")

    def test_get_region_by_prefix_unknown(self):
        """Тест определения региона для неизвестных префиксов."""
        unknown_prefixes = ["XYZ", "ABC", "123", "", "08/"]
        for prefix in unknown_prefixes:
            with self.subTest(prefix=prefix):
                region = InvoiceFactory._get_region_by_prefix(prefix)
                self.assertEqual(region, "unknown")


if __name__ == '__main__':
    unittest.main()