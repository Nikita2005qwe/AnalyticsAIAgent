"""
Модуль: invoice_regions.py
Описание: Статический справочник соответствия префикса → региону и городу.

Назначение:
- Централизованное хранение маппинга префиксов.
- Определение региона по префиксу.

Архитектурная роль:
- Справочник (catalog), часть домена.
- Не изменяется в рантайме.

Версия: v0.1
Автор: Боряков
Дата: 21.08.2025
Статус: Полностью готов
"""

from typing import Optional, Dict

# Полный маппинг префиксов → метаданные
INVOICE_PREFIX_REGIONS: Dict[str, Dict[str, str]] = {
    # Сибирь
    "01/": {"city": "Красноярск", "region": "siberia"},
    "02/": {"city": "Абакан", "region": "siberia"},
    "04/": {"city": "Новокузнецк", "region": "siberia", "alternative_city": "Новосибирск"},
    "05/": {"city": "Новосибирск", "region": "siberia"},
    "06/": {"city": "Омск", "region": "siberia"},
    "Е-": {"city": "Омск", "region": "siberia"},
    "Б-": {"city": "Абакан", "region": "siberia"},
    "К-": {"city": "Новосибирск", "region": "siberia"},
    "И-": {"city": "Новокузнецк", "region": "siberia"},
    "У-": {"city": "Красноярск", "region": "siberia"},
    # Урал
    "07/": {"city": "Челябинск", "region": "ural", "alternative_city": "Курган"},
    "Ч-": {"city": "Челябинск", "region": "ural"},
}


def get_region_by_prefix(prefix: str) -> Optional[str]:
    """
    Возвращает регион по префиксу накладной.

    Args:
        prefix (str): Префикс (например, "01/", "Ч-")

    Returns:
        str or None: "siberia", "ural" или None, если не найден.

    Используется в:
        InvoiceFactory.extract_prefix → get_region_by_prefix
    """
    info = INVOICE_PREFIX_REGIONS.get(prefix)
    return info["region"] if info else None


def get_city_by_prefix(prefix: str) -> Optional[str]:
    """
    Возвращает основной город по префиксу.

    Args:
        prefix (str): Префикс

    Returns:
        str or None: Город или None

    Используется в:
        UI (отображение города в таблице)
    """
    info = INVOICE_PREFIX_REGIONS.get(prefix)
    return info["city"] if info else None