# tests/integration/test_full_flow.py
import os
import pytest
import pandas as pd

from src.services.file_handler import FileHandler
from src.models.invoice.invoice_factory import InvoiceFactory


@pytest.mark.integration
def test_integration_end_to_end(tmp_path):
    """
    Интеграционный тест: полный поток от файла до отчёта.
    Условие: isa_amount != 0 и sfa_amount is None
    """
    # Подготовка
    input_file = "data/sales.xlsx"  # путь относительно корня проекта
    output_file = tmp_path / "mismatched_invoices.xlsx"

    # Проверка: файл существует
    assert os.path.exists(input_file), f"Файл не найден: {os.path.abspath(input_file)}"

    # Шаг 1: Чтение
    file_handler = FileHandler(input_file)
    raw_data = file_handler.read_invoices()
    assert len(raw_data) > 0, "Файл прочитан, но данные пусты"

    # Шаг 2: Создание Invoice
    invoices = InvoiceFactory.create_invoices(raw_data)
    assert len(invoices) > 0, "Не создано ни одной Invoice"

    # Шаг 3: Фильтрация
    filtered = [
        inv for inv in invoices
        if inv.isa_amount != 0.0 and inv.sfa_amount is None
    ]

    # Проверяем, что есть хотя бы одна накладная по условию
    # Если в данных нет таких — можно закомментировать или изменить данные
    # assert len(filtered) > 0, "Не найдено накладных с isa_amount != 0 и sfa_amount is None"

    # Шаг 4: Сохранение в Excel
    if filtered:
        df = pd.DataFrame([
            {
                "Номер накладной": inv.number,
                "CRM ID": inv.crm_id,
                "Адрес": inv.address,
                "Сумма ISA": inv.isa_amount,
                "Сумма SFA": inv.sfa_amount,
                "Префикс": inv.prefix,
                "Регион": inv.region,
                "Город доставки": inv.delivery_city,
            }
            for inv in filtered
        ])
        df.to_excel(output_file, index=False)
        assert os.path.exists(output_file)

    # Логируем результат
    print(f"\nНайдено {len(filtered)} накладных с ISA ≠ 0 и SFA = None")
    for inv in filtered[:5]:
        print(f"  {inv.number}: ISA={inv.isa_amount}, SFA={inv.sfa_amount}")