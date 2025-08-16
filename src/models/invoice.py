from dataclasses import dataclass
from typing import Optional


@dataclass
class Invoice:
    number: str  # Номер накладной с префиксом
    prefix: str  # Префикс направления деятельности
    region: str = "unknown"  # Регион (siberia, ural, unknown)

    # Системные поля
    found_in_dms: bool = False  # Найдена ли в системе DMS
    error_message: Optional[str] = None