"""
Версия: v0.1
Автор: Боряков
Дата: 21.08.2025
Статус: Полностью готово
Модуль содержит класс, который производит нужные накладные.
Обеспечивает полный контроль, что накладная соответствует формату входных данных
"""

from typing import List, Dict, Optional
from dataclasses import asdict
from .invoice import Invoice
from .invoice_regions import INVOICE_PREFIX_REGIONS, get_region_by_prefix, get_city_by_prefix


class InvoiceFactory:
    """
    Фабрика для создания объектов Invoice из словарей (сырых данных).
    """

    @staticmethod
    def create_invoices(data: List[Dict]) -> List[Invoice]:
        """
        Создаёт список Invoice из списка словарей.

        Args:
            data (List[Dict]): Список словарей с ключами:
                - 'number'
                - 'crm_id'
                - 'address'
                - 'isa_amount'
                - 'sfa_amount'

        Returns:
            List[Invoice]
        """
        invoices = []
        for row in data:
            invoice = InvoiceFactory._create_invoice(row)
            if invoice:
                invoices.append(invoice)
        return invoices

    @staticmethod
    def _create_invoice(row: Dict) -> Optional[Invoice]:
        """
        Создаёт один объект Invoice.

        Args:
            row (Dict): Строка данных.

        Returns:
            Invoice или None, если обязательные поля отсутствуют.
        """
        try:
            number = str(row["number"]).strip()
            crm_id = str(row["crm_id"]).strip()
            address = str(row["address"]).strip()

            # Парсим суммы
            isa_amount = float(row["isa_amount"]) if row["isa_amount"] not in (None, "") else 0.0
            sfa_amount = float(row["sfa_amount"]) if row["sfa_amount"] not in (None, "") else None

            # Извлечение префикса
            prefix = InvoiceFactory._extract_prefix(number)
            if not prefix:
                return None

            # Определение региона
            region = get_region_by_prefix(prefix)
            if not region:
                return None

            # Определение города доставки
            delivery_city = InvoiceFactory._determine_delivery_city(prefix, address)

            return Invoice(
                number=number,
                crm_id=crm_id,
                address=address,
                isa_amount=isa_amount,
                sfa_amount=sfa_amount,
                prefix=prefix,
                region=region,
                delivery_city=delivery_city,
            )
        except (KeyError, ValueError, TypeError):
            return None

    @staticmethod
    def _extract_prefix(number: str) -> Optional[str]:
        """
        Извлекает префикс из номера накладной.

        Поддерживаемые форматы: "01/123456", "И-008743", "Ч-001234" и т.д.

        Args:
            number (str): Номер накладной.

        Returns:
            str or None: Префикс, например "01/", "И-", "Ч-"
        """
        if number.startswith(("01/", "02/", "04/", "05/", "06/", "07/")):
            return number[:3]
        elif number.startswith(("Е-", "Б-", "К-", "И-", "У-", "Ч-")):
            return number[:2]
        return None

    @staticmethod
    def _determine_delivery_city(prefix: str, address: str) -> str:
        """
        Определяет город доставки по префиксу и адресу.

        Если у префикса есть alternative_city (например, у "04/" — "Новосибирск"),
        и этот город встречается в адресе, то используется он.
        Иначе — основной город из маппинга.

        Args:
            prefix (str): Префикс накладной.
            address (str): Полный адрес.

        Returns:
            str: Город доставки.
        """
        info = INVOICE_PREFIX_REGIONS.get(prefix, {})
        main_city = info.get("city")
        alt_city = info.get("alternative_city")

        # Если нет альтернативного города — возвращаем основной
        if not alt_city:
            return main_city

        # Если есть альтернативный — проверяем, есть ли он в адресе
        if (alt_city in address) or ("Томск" in address):
            return alt_city
        return main_city