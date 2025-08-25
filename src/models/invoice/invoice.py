"""
Модуль: invoice.py
Описание: Модель накладной — основная сущность домена.

Назначение:
- Хранить **исходные данные о накладной** из Excel-файла.
- Быть неизменяемой после создания (dataclass).
- Содержать все поля, приходящие из файла: номер, ID, адрес, суммы.
- Включать **delivery_city** — город доставки, извлечённый из адреса.

Архитектурная роль:
- Доменный объект (Entity), представляющий строку из файла.
- Не содержит логики процесса — только данные.
- Передаётся между слоями: services → processes → reporting.

Зависимости:
- Нет (чистая модель, только данные).

Версия: v0.1
Автор: Боряков
Дата: 21.08.2025
Статус: Полностью готово
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


@dataclass(frozen=True)
class Invoice:
    """
    Сущность "Накладная" — полная копия строки из Excel.

    Атрибуты:
    - number (str): Номер накладной (например, "01/179703")
    - crm_id (str): Уникальный ID из CRM (например, "{E3BDA348-F996-E811-811C-005056011415}")
    - address (str): Полный адрес доставки (например, "Красноярский край, г Дивногорск, ул Бочкина, д 10А/3")
    - isa_amount (float): Сумма ISA (может быть 0, отрицательной)
    - sfa_amount (float or None): Сумма SFA (None, если пусто)
    - prefix (str): Префикс накладной ("01/", "Ч-", "И-", "Е-" и т.д.)
    - region (str): Регион по префиксу: "siberia", "ural", "unknown"
    - delivery_city (str): Город доставки, извлечённый из адреса (например, "Красноярск")

    Примечание:
    - Это **исходные данные**, не результат проверки.
    - Поля found_in_dms, error_message, status — добавляются позже в процессе.
    """

    # === Данные из Excel ===
    number: str
    crm_id: str
    address: str
    isa_amount: float
    sfa_amount: Optional[float]

    # === Производные поля (вычисляются при создании) ===
    prefix: str
    region: str
    delivery_city: str

class CheckStatus(Enum):
    FOUND = "found"
    NOT_FOUND = "not_found"
    ERROR = "error"
    UNKNOWN = "unknown"

@dataclass(frozen=True)
class CheckedInvoice:
    """Накладная со статусом"""
    invoice: Invoice
    status: CheckStatus
