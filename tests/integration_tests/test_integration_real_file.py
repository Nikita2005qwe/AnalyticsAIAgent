import unittest
import os
import pandas as pd
from src.services.file_handler import FileService
from src.services.invoice_factory import InvoiceFactory


class TestIntegrationRealFile(unittest.TestCase):
    """Интеграционные тесты с реальным файлом."""

    def setUp(self):
        """Настройка для тестов с реальным файлом."""
        self.file_service = FileService()
        self.real_file_path = "data/Книга1.xlsx"

    def test_file_exists(self):
        """Проверяем, что файл существует."""
        self.assertTrue(
            os.path.exists(self.real_file_path),
            f"Файл {self.real_file_path} не найден"
        )

    def test_load_invoice_numbers_from_real_file(self):
        """Тест загрузки номеров накладных из реального файла."""
        # Проверяем существование файла
        self.assertTrue(os.path.exists(self.real_file_path))

        # Получаем имя листа из файла
        xl = pd.ExcelFile(self.real_file_path)
        sheet_name = xl.sheet_names[0]  # 'выгрузка_PU'

        # Загружаем номера накладных
        invoice_numbers = self.file_service.load_invoice_numbers_from_excel(
            self.real_file_path, sheet_name
        )

        # Проверяем, что найдено 14 накладных
        self.assertEqual(len(invoice_numbers), 14)

        # Проверяем наличие конкретных накладных
        expected_numbers = ['07/048574', '02/048574', '04/048574']
        for num in expected_numbers:
            self.assertIn(num, invoice_numbers)

    def test_process_invoices_from_real_file(self):
        """Тест обработки накладных из реального файла."""
        # Проверяем существование файла
        self.assertTrue(os.path.exists(self.real_file_path))

        # Получаем имя листа из файла
        xl = pd.ExcelFile(self.real_file_path)
        sheet_name = xl.sheet_names[0]  # 'выгрузка_PU'

        # Загружаем номера накладных
        invoice_numbers = self.file_service.load_invoice_numbers_from_excel(
            self.real_file_path, sheet_name
        )

        # Создаем накладные через фабрику
        invoices = InvoiceFactory.create_invoices_from_numbers(invoice_numbers)

        # Проверяем общее количество
        self.assertEqual(len(invoices), 14)


if __name__ == '__main__':
    unittest.main()