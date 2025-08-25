# tests/services/test_file_handler.py
import os
import pytest
from unittest.mock import patch, mock_open, MagicMock
import pandas as pd

from src.services.file_handler import FileHandler


class TestFileHandler:
    """Тесты для FileHandler — чтение Excel-файла и извлечение данных о накладных."""

    @patch("src.services.file_handler.pd.read_excel")
    def test_read_invoices_success(self, mock_read_excel):
        """TC-FH-01: Успешное чтение данных с 12-й строки (skiprows=10)"""
        # Мокаем DataFrame как если бы прочитали из Excel
        mock_df = pd.DataFrame(
            {
                "Названия строк": ["05/050426", "Ч-054192"],
                "ID XCRM Parent": ["id1", "id2"],
                "Address Normalized": ["адрес1", "адрес2"],
                "ISA": ["100.00", "200.00"],
                "SFA": ["100.00", "200.00"],
            }
        )
        mock_read_excel.return_value = mock_df

        handler = FileHandler("data/sales.xlsx")
        data = handler.read_invoices()

        # Проверяем, что read_excel был вызван с правильными параметрами
        mock_read_excel.assert_called_once()
        args, kwargs = mock_read_excel.call_args
        assert "skiprows" in kwargs and kwargs["skiprows"] == 10
        assert "header" in kwargs and kwargs["header"] == 0

        # Проверяем результат
        assert len(data) == 2
        assert data[0]["number"] == "05/050426"
        assert data[1]["crm_id"] == "id2"
        assert data[0]["isa_amount"] == "100.00"
        assert data[1]["sfa_amount"] == "200.00"

    @patch("src.services.file_handler.pd.read_excel")
    def test_read_invoices_with_empty_cells_converted_to_none(self, mock_read_excel):
        """TC-FH-07: Пустые ячейки → None"""
        mock_df = pd.DataFrame(
            {
                "Названия строк": ["01/191906"],
                "ID XCRM Parent": ["{1C1975C2-B46D-F011-813A-005056011415}"],
                "Address Normalized": ["г Лесосибирск, ул Дружбы, д 2А"],
                "ISA": [""],  # пусто
                "SFA": ["140.13"],
            }
        )
        mock_read_excel.return_value = mock_df

        handler = FileHandler("data/sales.xlsx")
        data = handler.read_invoices()

        assert len(data) == 1
        row = data[0]
        assert row["number"] == "01/191906"
        assert row["isa_amount"] is None
        assert row["sfa_amount"] == "140.13"

    @patch("src.services.file_handler.pd.read_excel")
    def test_read_invoices_missing_required_columns_raises_error(self, mock_read_excel):
        """TC-FH-04: Ошибка при отсутствии обязательных столбцов"""
        mock_df = pd.DataFrame(
            {
                "Wrong Col 1": ["value1"],
                "Wrong Col 2": ["value2"],
            }
        )
        mock_read_excel.return_value = mock_df

        handler = FileHandler("data/sales.xlsx")

        with pytest.raises(ValueError, match="Отсутствуют обязательные столбцы"):
            handler.read_invoices()

    def test_read_invoices_file_not_found(self):
        """TC-FH-05: Файл не найден"""
        handler = FileHandler("nonexistent.xlsx")

        with pytest.raises(FileNotFoundError, match="Файл не найден"):
            handler.read_invoices()

    @patch("src.services.file_handler.pd.read_excel")
    def test_read_invoices_pandas_error_raises_runtime_error(self, mock_read_excel):
        """TC-FH-06: Обработка ошибки при чтении Excel (битый файл)"""
        mock_read_excel.side_effect = Exception("Invalid Excel format")

        # Важно: путь может быть любым, т.к. читаем моком
        handler = FileHandler("dummy.xlsx")  # не реальный путь

        with pytest.raises(FileNotFoundError, match="Файл не найден"):
            handler.read_invoices()

    @patch("src.services.file_handler.pd.read_excel")
    def test_read_invoices_renames_columns_correctly(self, mock_read_excel):
        """TC-FH-03: Столбцы корректно переименовываются"""
        mock_df = pd.DataFrame(
            {
                "Названия строк": ["05/050426"],
                "ID XCRM Parent": ["id"],
                "Address Normalized": ["addr"],
                "ISA": ["100"],
                "SFA": ["100"],
            }
        )
        mock_read_excel.return_value = mock_df

        handler = FileHandler("data/sales.xlsx")
        data = handler.read_invoices()

        row = data[0]
        expected_keys = {"number", "crm_id", "address", "isa_amount", "sfa_amount"}
        assert set(row.keys()) == expected_keys
        assert row["number"] == "05/050426"

    @patch("src.services.file_handler.pd.read_excel")
    def test_read_invoices_handles_comma_in_numbers(self, mock_read_excel):
        """TC-FH-08: Числа с запятой (например, '6,597.01') остаются строками для парсинга далее"""
        mock_df = pd.DataFrame(
            {
                "Названия строк": ["04/150535"],
                "ID XCRM Parent": ["{C2A83220-6035-ED11-812C-005056011415}"],
                "Address Normalized": ["г Кемерово, пр-кт Кузнецкий, д 256"],
                "ISA": ["6,597.01"],
                "SFA": ["6,597.01"],
            }
        )
        mock_read_excel.return_value = mock_df

        handler = FileHandler("data/sales.xlsx")
        data = handler.read_invoices()

        assert len(data) == 1
        row = data[0]
        assert row["isa_amount"] == "6,597.01"
        assert row["sfa_amount"] == "6,597.01"

    @patch("src.services.file_handler.pd.read_excel")
    def test_read_invoices_preserves_duplicate_rows(self, mock_read_excel):
        """TC-FH-10: Дублирующиеся строки не удаляются"""
        mock_df = pd.DataFrame(
            {
                "Названия строк": ["05/050426", "05/050426"],
                "ID XCRM Parent": ["id", "id"],
                "Address Normalized": ["addr", "addr"],
                "ISA": ["100", "100"],
                "SFA": ["100", "100"],
            }
        )
        mock_read_excel.return_value = mock_df

        handler = FileHandler("data/sales.xlsx")
        data = handler.read_invoices()

        assert len(data) == 2
        assert data[0]["number"] == "05/050426"
        assert data[1]["number"] == "05/050426"

    @patch("src.services.file_handler.pd.read_excel")
    def test_read_invoices_ignores_extra_columns(self, mock_read_excel):
        """TC-FH-09: Лишние столбцы игнорируются"""
        mock_df = pd.DataFrame(
            {
                "Названия строк": ["05/050426"],
                "ID XCRM Parent": ["id"],
                "Address Normalized": ["addr"],
                "ISA": ["100"],
                "SFA": ["100"],
                "Примечание": ["test"],  # лишний столбец
                "Дата": ["2025-08-01"],   # лишний
            }
        )
        mock_read_excel.return_value = mock_df

        handler = FileHandler("data/sales.xlsx")
        data = handler.read_invoices()

        assert len(data) == 1
        row = data[0]
        assert "Примечание" not in row
        assert "Дата" not in row

    @patch("src.services.file_handler.pd.read_excel")
    def test_read_invoices_strips_whitespace(self, mock_read_excel):
        """Доп. тест: значения очищаются от пробелов"""
        mock_df = pd.DataFrame(
            {
                "Названия строк": ["  05/050426  "],
                "ID XCRM Parent": ["  {id}  "],
                "Address Normalized": ["  г Новосибирск  "],
                "ISA": ["  100.00  "],
                "SFA": [""],
            }
        )
        mock_read_excel.return_value = mock_df

        handler = FileHandler("data/sales.xlsx")
        data = handler.read_invoices()

        row = data[0]
        assert row["number"] == "05/050426"
        assert row["crm_id"] == "{id}"
        assert row["address"] == "г Новосибирск"
        assert row["isa_amount"] == "100.00"
        assert row["sfa_amount"] is None

    @patch("src.services.file_handler.pd.read_excel")
    def test_read_invoices_handles_negative_and_zero_values(self, mock_read_excel):
        """Доп. тест: корректная обработка отрицательных и нулевых сумм"""
        mock_df = pd.DataFrame(
            {
                "Названия строк": ["ВВ-001274", "Е-001265"],
                "ID XCRM Parent": ["id1", "id2"],
                "Address Normalized": ["адрес1", "адрес2"],
                "ISA": ["-65.23", "0.00"],
                "SFA": ["", "0.00"],
            }
        )
        mock_read_excel.return_value = mock_df

        handler = FileHandler("data/sales.xlsx")
        data = handler.read_invoices()

        assert len(data) == 2
        assert data[0]["isa_amount"] == "-65.23"
        assert data[0]["sfa_amount"] is None
        assert data[1]["isa_amount"] == "0.00"
        assert data[1]["sfa_amount"] == "0.00"