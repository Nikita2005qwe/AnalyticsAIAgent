from dataclasses import dataclass
from typing import Optional
from enum import Enum


class PointStatus(Enum):
    PENDING = "pending"  # Ожидает обработки
    PROCESSING = "processing"  # В процессе создания
    CREATED = "created"  # Успешно создана
    ERROR = "error"  # Ошибка при создании


@dataclass
class TradePoint:
    # Базовые поля от пользователя
    name_1c: str  # Название в 1С (полное)
    owner: str  # Владелец (контрагент)
    point_type_1c: str  # Вид ТТ из 1С
    full_address: str  # Полный адрес с индексом
    esr_code: str  # Код ESR

    # Поля, заполняемые системой
    crm_name: str = ""  # Название в CRM (без индекса, без кода владельца)
    crm_point_type: str = ""  # Тип ТТ в CRM (на основе point_type_1c)
    assortment_type: str = ""  # Вид ассортимента (на основе crm_point_type)
    location_type: str = ""  # Местонахождение (на основе name_1c)
    area: str = "1-50"  # Площадь (всегда 1-50)
    chain_name: str = ""  # Название сети (на основе owner) или "NO CHAIN"
    business_direction: str = ""  # Направление деятельности (по ESR коду)
    xcrm_guid: Optional[str] = None  # GUID после создания в CRM

    # Системные поля
    status: PointStatus = PointStatus.PENDING
    error_message: Optional[str] = None

    @property
    def short_owner(self) -> str:
        """Владелец без кода вначале"""
        parts = self.owner.split(' ', 1)
        return parts[1] if len(parts) > 1 else self.owner

    @property
    def clean_address(self) -> str:
        """Адрес без индекса"""
        import re
        return re.sub(r'^\d{6}\s*', '', self.full_address).strip()