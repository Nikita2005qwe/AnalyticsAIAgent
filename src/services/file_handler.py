"""
Версия: v0.1
Автор: Боряков
Дата: 21.08.2025
Статус: полностью готово
Помогает, пока что прочитать накладные из файла excel.
В будущем будет полноценным оркестратором для функций обработки и чтения файлов разных форматов.
"""
import os
from typing import List, Dict
import pandas as pd


class FileHandler:
    """
    Обработчик Excel-файла.
    Читает файл, начиная с 12-й строки (индекс 10), считая 11-ю строку заголовками.
    """

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.full_path = os.path.join(os.getcwd(), file_path)

    def read_invoices(self, sheet_name: str) -> List[Dict]:
        """
        Читает Excel-файл и возвращает список словарей с данными о накладных.

        Строки:
            - Строка 1–10: фильтры, сводки — пропускаются.
            - Строка 11: заголовки (столбцы).
            - Строка 12 и далее: данные.

        Returns:
            List[Dict]: Список строк в виде словарей.
        """
        if not os.path.exists(self.full_path):
            raise FileNotFoundError(f"Файл не найден: {self.full_path}")

        try:
            # Пропускаем первые 10 строк (0-индексация: строки 0–9), 10-я — заголовки (индекс 10)
            df = pd.read_excel(self.full_path, sheet_name=sheet_name, skiprows=10, header=0, dtype=str)

            # Убедимся, что у нас есть нужные столбцы
            expected_columns = {"Названия строк", "ID XCRM Parent", "Address Normalized", "ISA", "SFA"}
            missing = expected_columns - set(df.columns)
            if missing:
                raise ValueError(f"Отсутствуют обязательные столбцы: {missing}")

            # Переименовываем только нужные столбцы
            data = df.rename(columns={
                "Названия строк": "number",
                "ID XCRM Parent": "crm_id",
                "Address Normalized": "address",
                "ISA": "isa_amount",
                "SFA": "sfa_amount",
            })

            # Оставляем только нужные колонки
            data = data[["number", "crm_id", "address", "isa_amount", "sfa_amount"]]

            # Конвертируем в список словарей
            records = data.to_dict(orient="records")

            # Приводим пустые строки к None
            cleaned_records = []
            for record in records:
                cleaned = {
                    k: (v.strip() if isinstance(v, str) and v.strip() != "" else None)
                    for k, v in record.items()
                }
                cleaned_records.append(cleaned)

            return cleaned_records

        except ValueError as e:
            if "does not exist" in str(e):
                raise ValueError(f"Лист '{sheet_name}' не найден в файле '{self.full_path}'. Проверьте название листа.")
            else:
                raise e  # другие ValueError (например, проблемы с парсингом)
        except FileNotFoundError:
            # Это уже обработано выше, но на всякий случай
            raise
        except Exception as e:
            # Все остальные ошибки (включая ошибки pandas) — оборачиваем в RuntimeError
            raise RuntimeError(f"Ошибка при чтении Excel-файла: {e}")