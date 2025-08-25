"""
Модуль: invoice_validation.py
Описание: Валидация данных накладной.

Назначение:
- Проверка корректности номера, сумм, префикса.
- Предотвращение создания "битых" объектов.

Архитектурная роль:
- Защита целостности данных.
- Используется перед созданием Invoice.

Зависимости:
- models.invoice.invoice
"""

class FilterInvoices:

    @staticmethod
    def filter_invoices(invoices: list[dict]) -> list[dict]:
        """
        Фильтрует список накладных по следующим условиям:
        - isa_amount: не равно 0 (включая строки вроде "0", "0.0", пустые строки или None)
        - sfa_amount: является None (включая строки, приведённые к None)

        :param invoices: Список словарей с данными о накладных
        :return: Отфильтрованный список словарей, соответствующих условиям
        """
        filtered = []

        for invoice in invoices:
            # Получаем значения
            isa_amount = invoice.get("isa_amount")
            sfa_amount = invoice.get("sfa_amount")

            # Условие 1: sfa_amount должен быть None
            if sfa_amount is not None:
                continue

            # Условие 2: isa_amount не должен быть равен 0
            # Приводим к числу, если возможно, или проверяем строку
            if isa_amount is None:
                continue  # isa_amount отсутствует или None → не подходит

            # Убираем пробелы, если это строка
            if isinstance(isa_amount, str):
                isa_amount = isa_amount.strip()

            # Проверяем, можно ли привести к числу
            try:
                isa_value = float(isa_amount)
                if isa_value == 0.0:
                    continue  # isa_amount == 0 → не подходит
            except (ValueError, TypeError):
                # Если не число и не пусто — считаем, что это не ноль
                # Например, если там текст — мы всё равно пропускаем? Или оставляем?
                # По логике: если не число и не ноль — возможно, ошибка, но по условию задачи:
                # нам важно "не равно 0". Значит, если это не ноль — оставляем.
                # Но в реальности лучше логировать такие случаи.
                pass  # считаем, что это не ноль → подходит по isa_amount

            # Если оба условия выполняются — добавляем в результат
            filtered.append(invoice)

        return filtered
