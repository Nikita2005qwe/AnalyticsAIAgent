import pandas as pd


def debug_excel_file():
    """Отладочная функция для понимания структуры файла."""
    file_path = "data/Книга1.xlsx"

    # Получаем список листов
    xl = pd.ExcelFile(file_path)
    print(f"Доступные листы: {xl.sheet_names}")

    # Читаем первый лист
    sheet_name = xl.sheet_names[0]
    print(f"Чтение листа: {sheet_name}")

    # Читаем с разными параметрами
    df1 = pd.read_excel(file_path, sheet_name=sheet_name)
    print(f"Структура DataFrame:")
    print(f"  Колонки: {list(df1.columns)}")
    print(f"  Размер: {df1.shape}")
    print(f"  Первые 5 строк:")
    print(df1.head())

    # Проверяем содержимое первого столбца
    if len(df1.columns) > 0:
        first_column = df1.iloc[:, 0]
        print(f"\nПервый столбец:")
        print(first_column.head(10))
        print(f"Типы данных: {first_column.dtype}")

        # Фильтруем накладные
        valid_invoices = []
        for value in first_column:
            if pd.notna(value):
                invoice_str = str(value).strip()
                if invoice_str and invoice_str.lower() != 'nan':
                    valid_invoices.append(invoice_str)

        print(f"\nВалидные накладные ({len(valid_invoices)}):")
        for i, inv in enumerate(valid_invoices[:10]):
            print(f"  {i + 1}. {inv}")


if __name__ == "__main__":
    debug_excel_file()