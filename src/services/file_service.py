import pandas as pd
from pathlib import Path
from typing import List
import os
from src.models.invoice import Invoice


class FileService:
    """Сервис для работы с файлами Excel и данными приложения."""

    def __init__(self):
        self.supported_extensions = ['.xlsx', '.xls']

    def load_invoice_numbers_from_excel(self, file_path: str, sheet_name: str) -> List[str]:
        """
        Загружает номера накладных из Excel файла.

        Args:
            file_path: Путь к Excel файлу
            sheet_name: Имя листа

        Returns:
            List[str]: Список номеров накладных

        Raises:
            FileNotFoundError: Если файл не найден
            ValueError: Если файл имеет неподдерживаемый формат
        """
        if not self.validate_file_path(file_path):
            raise FileNotFoundError(f"Файл не найден: {file_path}")

        file_extension = Path(file_path).suffix.lower()
        if file_extension not in self.supported_extensions:
            raise ValueError(f"Неподдерживаемый формат файла: {file_extension}")

        try:
            # Читаем Excel файл
            df = pd.read_excel(file_path, sheet_name=sheet_name)

            invoice_numbers = []
            # Определяем, какой столбец содержит номера накладных
            target_column = None

            # Способ 1: Ищем столбец с названием "Номера" (как в реальном файле)
            if 'Номера' in df.columns:
                target_column = 'Номера'
            # Способ 2: Ищем столбец 'A' (стандартный случай)
            elif 'A' in df.columns:
                target_column = 'A'
            # Способ 3: Берем первый столбец по индексу
            elif len(df.columns) > 0:
                target_column = df.columns[0]

            if target_column is not None:
                column_data = df[target_column]

                for value in column_data:
                    # Проверяем, что значение не NaN
                    if pd.notna(value):
                        invoice_number = str(value).strip()
                        # Фильтруем пустые значения и 'nan'
                        if invoice_number and invoice_number.lower() != 'nan':
                            invoice_numbers.append(invoice_number)

            return invoice_numbers

        except Exception as e:
            raise ValueError(f"Ошибка при чтении файла: {str(e)}")

    def save_trade_points_to_excel(self, trade_points: List, output_path: str) -> bool:
        """
        Сохраняет торговые точки в Excel файл.

        Args:
            trade_points: Список объектов TradePoint
            output_path: Путь для сохранения файла

        Returns:
            bool: Успешность операции
        """
        try:
            # Создаем DataFrame из торговых точек
            data = []
            for tp in trade_points:
                row = {
                    'Название в 1С': tp.name_1c,
                    'Владелец': tp.owner,
                    'Вид ТТ из 1С': tp.point_type_1c,
                    'Полный адрес': tp.full_address,
                    'Код ESR': tp.esr_code,
                    'Название в CRM': tp.crm_name,
                    'Тип ТТ в CRM': tp.crm_point_type,
                    'Вид ассортимента': tp.assortment_type,
                    'Местонахождение': tp.location_type,
                    'Площадь': tp.area,
                    'Сеть': tp.chain_name,
                    'Направление деятельности': tp.business_direction,
                    'Статус': tp.status.value,
                    'Ошибка': tp.error_message or ''
                }
                data.append(row)

            df = pd.DataFrame(data)
            df.to_excel(output_path, index=False)
            return True

        except Exception as e:
            print(f"Ошибка при сохранении файла: {str(e)}")
            return False

    def validate_file_path(self, file_path: str) -> bool:
        """
        Проверяет корректность пути к файлу.

        Args:
            file_path: Путь к файлу

        Returns:
            bool: Валидность пути
        """
        if not file_path:
            return False

        path = Path(file_path)
        return path.exists() and path.is_file()