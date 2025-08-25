"""
Модуль: invoices_rules.py
Описание: Бизнес-правила, применимые к объектам Invoice.

Назначение:
- Определить, должна ли накладная обрабатываться.
- Решить, как её подсвечивать.
- Проверить принадлежность к региону.

Архитектурная роль:
- Доменная логика (domain logic).
- Не зависит от UI или сервисов.

Зависимости:
- models.invoice.invoice
"""

from .invoice import Invoice


def should_process(invoice: Invoice) -> bool:
    """
    Проверяет, должна ли накладная участвовать в проверке.

    Условие:
    - Сумма в ISA ≠ 0
    - Сумма в SFA не пустая (не None)

    Args:
        invoice (Invoice): Объект накладной

    Returns:
        bool: True, если должна обрабатываться

    Используется в:
        FileService.load_and_filter_invoices()
    """
    pass


def is_from_region(invoice: Invoice, region: str) -> bool:
    """
    Проверяет, принадлежит ли накладная указанному региону.

    Args:
        invoice (Invoice): Накладная
        region (str): Регион ("siberia", "ural")

    Returns:
        bool: True, если invoice.region == region

    Используется в:
        CheckInvoicesProcess (группировка)
        ExcelStyleService (подсветка)
    """
    pass


def should_highlight_as_other_region(invoice: Invoice, current_region: str) -> bool:
    """
    Определяет, нужно ли подсвечивать накладную как "не свой регион".

    Args:
        invoice (Invoice): Накладная
        current_region (str): Регион, который сейчас проверяется

    Returns:
        bool: True, если регион накладной ≠ current_region и регион валидный

    Используется в:
        ExcelStyleService (цветовая заливка)
    """
    pass


def is_valid_for_dms_check(invoice: Invoice) -> bool:
    """
    Обобщённое правило: можно ли проверять накладную в DMS.

    Пока совпадает с should_process, но может расширяться.

    Args:
        invoice (Invoice)

    Returns:
        bool

    Используется в:
        CheckInvoicesProcess (финальная проверка перед поиском)
    """
    pass