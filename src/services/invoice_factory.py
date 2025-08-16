import re
from typing import List
from src.models.invoice import Invoice

# Константы для регионов
INVOICE_PREFIX_REGIONS: dict[str, dict] = {
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


class InvoiceFactory:
    """Фабрика для создания и обогащения накладных."""

    @staticmethod
    def create_invoice(invoice_number: str) -> Invoice:
        """
        Создает накладную с автоматическим определением префикса и региона.

        Args:
            invoice_number: Номер накладной

        Returns:
            Invoice: Созданная накладная
        """
        prefix = InvoiceFactory._extract_prefix(invoice_number)
        region = InvoiceFactory._get_region_by_prefix(prefix)

        return Invoice(
            number=invoice_number,
            prefix=prefix,
            region=region
        )

    @staticmethod
    def create_invoices_from_numbers(invoice_numbers: List[str]) -> List[Invoice]:
        """
        Создает список накладных из списка номеров.

        Args:
            invoice_numbers: Список номеров накладных

        Returns:
            List[Invoice]: Список созданных накладных
        """
        return [InvoiceFactory.create_invoice(num) for num in invoice_numbers if num and num != 'nan']

    @staticmethod
    def _extract_prefix(invoice_number: str) -> str:
        """
        Извлекает префикс из номера накладной.

        Префиксы бывают:
        - С числовым форматом: "01/12345", "07/67890"
        - С буквенным форматом: "Е-12345", "Ч-67890"

        Args:
            invoice_number: Номер накладной

        Returns:
            str: Префикс накладной
        """
        # Проверяем числовые префиксы (01/, 07/, etc)
        for prefix in ["01/", "02/", "04/", "05/", "06/", "07/"]:
            if invoice_number.startswith(prefix):
                return prefix

        # Проверяем буквенные префиксы (Е-, Ч-, etc)
        match = re.match(r'^([А-Я])-', invoice_number)
        if match:
            return f"{match.group(1)}-"

        # Если префикс не найден, возвращаем пустую строку
        return ""

    @staticmethod
    def _get_region_by_prefix(prefix: str) -> str:
        """
        Определяет регион по префиксу накладной.

        Args:
            prefix: Префикс накладной

        Returns:
            str: Регион ("siberia", "ural", "unknown")
        """
        prefix_data = INVOICE_PREFIX_REGIONS.get(prefix, {})
        return prefix_data.get("region", "unknown")