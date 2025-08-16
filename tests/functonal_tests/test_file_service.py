import unittest
import tempfile
import os
from pathlib import Path
import pandas as pd
from src.services.file_service import FileService


class TestFileService(unittest.TestCase):

    def setUp(self):
        """Создаем временные файлы для тестов."""
        self.file_service = FileService()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Удаляем временные файлы."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_load_invoice_numbers_from_excel_success(self):
        """Тест успешной загрузки номеров накладных из Excel."""
        # Создаем тестовый Excel файл с накладными
        test_data = pd.DataFrame({
            'A': ['01/12345', '07/67890', 'Е-11111', 'XYZ99999', ''],
            'B': ['Данные1', 'Данные2', 'Данные3', 'Данные4', 'Данные5']
        })

        excel_path = Path(self.temp_dir) / "invoices.xlsx"
        test_data.to_excel(excel_path, index=False, sheet_name="Сверка продаж")

        # Загружаем номера накладных
        invoice_numbers = self.file_service.load_invoice_numbers_from_excel(
            str(excel_path), "Сверка продаж"
        )

        # Проверяем результаты (пустая строка должна быть отфильтрована)
        self.assertEqual(len(invoice_numbers), 4)
        self.assertIn('01/12345', invoice_numbers)
        self.assertIn('07/67890', invoice_numbers)
        self.assertIn('Е-11111', invoice_numbers)
        self.assertIn('XYZ99999', invoice_numbers)

    def test_load_invoice_numbers_from_excel_empty_cells(self):
        """Тест загрузки с пустыми ячейками."""
        # Создаем тестовый Excel файл с пустыми ячейками
        test_data = pd.DataFrame({
            'A': ['01/12345', '', '07/67890', 'nan', None]
        })

        excel_path = Path(self.temp_dir) / "invoices_with_empty.xlsx"
        test_data.to_excel(excel_path, index=False, sheet_name="Сверка продаж")

        invoice_numbers = self.file_service.load_invoice_numbers_from_excel(
            str(excel_path), "Сверка продаж"
        )

        # Должно загрузить только 2 накладные (без пустых, 'nan' и None)
        self.assertEqual(len(invoice_numbers), 2)
        self.assertIn('01/12345', invoice_numbers)
        self.assertIn('07/67890', invoice_numbers)

    def test_load_invoice_numbers_from_excel_file_not_found(self):
        """Тест обработки несуществующего файла."""
        with self.assertRaises(FileNotFoundError):
            self.file_service.load_invoice_numbers_from_excel(
                "/nonexistent/file.xlsx", "Сверка продаж"
            )

    def test_load_invoice_numbers_from_excel_unsupported_format(self):
        """Тест обработки неподдерживаемого формата файла."""
        # Создаем файл с неподдерживаемым расширением
        txt_file = Path(self.temp_dir) / "test.txt"
        txt_file.touch()

        with self.assertRaises(ValueError) as context:
            self.file_service.load_invoice_numbers_from_excel(str(txt_file), "Сверка продаж")

        self.assertIn("Неподдерживаемый формат файла", str(context.exception))

    def test_validate_file_path_valid(self):
        """Тест валидации корректного пути."""
        # Создаем временный файл
        temp_file = Path(self.temp_dir) / "test.xlsx"
        temp_file.touch()

        self.assertTrue(self.file_service.validate_file_path(str(temp_file)))

    def test_validate_file_path_invalid(self):
        """Тест валидации некорректного пути."""
        # Несуществующий файл
        self.assertFalse(self.file_service.validate_file_path("/nonexistent/file.xlsx"))
        # Пустая строка
        self.assertFalse(self.file_service.validate_file_path(""))
        # Директория вместо файла
        self.assertFalse(self.file_service.validate_file_path(self.temp_dir))

    def test_save_trade_points_to_excel_success(self):
        """Тест успешного сохранения торговых точек."""
        from src.models.trade_point import TradePoint, PointStatus

        # Создаем тестовые торговые точки
        trade_points = [
            TradePoint(
                name_1c="АЗС №123",
                owner="12345 ООО Нефть",
                point_type_1c="АЗС",
                full_address="656000 г. Барнаул, ул. Ленина, 1",
                esr_code="ESR001"
            )
        ]

        output_path = Path(self.temp_dir) / "trade_points.xlsx"
        result = self.file_service.save_trade_points_to_excel(trade_points, str(output_path))

        self.assertTrue(result)
        self.assertTrue(output_path.exists())


if __name__ == '__main__':
    unittest.main()