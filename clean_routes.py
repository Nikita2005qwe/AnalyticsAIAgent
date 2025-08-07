import pandas as pd
import sys

# Путь к входному файлу
input_file = 'Н354.xlsx'
output_file_name = None

try:
    # 1. Читаем файл
    df = pd.read_excel(input_file)

    # 2. Удаляем столбец "УИД", если он есть
    if 'УИД' in df.columns:
        df = df.drop(columns=['УИД'])

    # 3. Удаляем строки, где 'Идентификатор торговой точки' пустой
    df = df.dropna(subset=['Идентификатор торговой точки'])

    # 4. Переименовываем столбец и заполняем "Визит ESR"
    df = df.rename(columns={'Наименование владельца': 'Тип визита'})
    df['Тип визита'] = 'Визит ESR'

    # 5. Определяем, какие Идентификаторы встречаются один раз (уникальные)
    id_counts = df['Идентификатор торговой точки'].value_counts()
    unique_ids = id_counts[id_counts == 1].index

    # Устанавливаем Цикличность визита = 2 для уникальных точек
    df.loc[df['Идентификатор торговой точки'].isin(unique_ids), 'Цикличность визита'] = 2

    # 6. Устанавливаем "Повторить до" = 31.12.2025 для всех строк
    df['Повторить до'] = '31.12.2025'

    # 7. Получаем имя сотрудника (берем первое значение — оно везде одинаковое)
    employee_name = df['Наименование сотрудника'].iloc[0]
    output_file_name = f"{employee_name}.xlsx"

    # 8. Сохраняем результат
    df.to_excel(output_file_name, index=False)
    print(f"✅ Обработка завершена. Результат сохранён в файл: {output_file_name}")

except Exception as e:
    print(f"❌ Ошибка при обработке файла: {e}")
    sys.exit(1)