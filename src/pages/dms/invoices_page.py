from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re


class InvoicesPage:
    def __init__(self, driver):
        self.driver = driver

        # 🔹 Поле поиска
        self.search_input_locator = (
            By.XPATH,
            "//input[@placeholder='Поиск' and contains(@class, 'gui-input-field-element')]"
        )

        # 🔹 Выбор площадки (оргструктура)
        self.orgstructure_input_locator = (
            By.XPATH,
            "//input[contains(@class, 'gui-select__input') and @title]"
        )

        # 🔹 Список опций (выпадающий список)
        self.orgstructure_dropdown_locator = (
            By.CLASS_NAME, "gui-select__options"
        )
        self.orgstructure_option_locator = (
            By.XPATH,
            "//div[contains(@class, 'gui-select__option') and contains(text(), '{city}')]"
        )
        # 🔹 Таблица с состоянием загрузки
        self.loading_table_locator = (
            By.CSS_SELECTOR,
            "gui-table.invoice-list.invoice-list--loading"
        )

        # 🔹 Таблица
        self.table_body_locator = (By.CLASS_NAME, "gui-table-body")
        self.table_row_locator = (By.TAG_NAME, "tr")
        self.table_cell_locator = (By.TAG_NAME, "td")

        # 🔹 Сообщение "Нет данных"
        self.empty_message_locator = (
            By.XPATH,
            "//div[contains(@class, 'empty-message') or contains(text(), 'Нет данных') or contains(text(), 'ничего не найдено')]"
        )

        # 🔹 Словарь колонок
        self.columns = {
            "number": "invoiceNumber",
            "date": "invoiceDate",
            "order": "orderNumber",
            "org": "organization",
            "outlet": "outlet",
            "orgstructure": "orgstructure",
            "store": "store",
            "delivery_date": "deliveryDate",
            "total": "total",
            "status": "status",
        }

    def is_loaded(self):
        """Ждёт появления таблицы и завершения загрузки."""
        wait = WebDriverWait(self.driver, 30)

        try:
            # Сначала ждём появления самой таблицы
            wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "invoice-list"))
            )
            # Затем ждём, пока уйдёт состояние загрузки
            wait.until_not(
                EC.presence_of_element_located(self.loading_table_locator)
            )
            return True
        except:
            return False

    def wait_for_search_result(self):
        wait = WebDriverWait(self.driver, 3)

        # Запоминаем старый tbody (если есть)
        try:
            old_tbody = self.driver.find_element(*self.table_body_locator)
        except:
            old_tbody = None

        # Ждём исчезновения загрузки
        try:
            wait.until_not(
                EC.presence_of_element_located(self.loading_table_locator)
            )
        except:
            pass

        # Если был старый tbody — ждём, что он исчез
        if old_tbody:
            try:
                wait.until(EC.staleness_of(old_tbody))
            except:
                pass

        # Финальная проверка результата
        wait.until(
            lambda d: self.is_empty() or len(self.get_rows()) > 0,
            message="Не дождались результата поиска"
        )
        return self
    
    def is_invoice_found(self, expected_number: str) -> bool:
        """
        Проверяет, что в таблице есть накладная с точным номером.
        """
        rows = self.get_rows()
        for row in rows:
            data = self.get_invoice_data(row)
            invoice_number = data.get("number", "").strip()
            if invoice_number == expected_number:
                return True
        return False

    def element_exists(self, element):
        """Проверяет, всё ли ещё существует элемент."""
        try:
            element.is_displayed()
            return True
        except:
            return False

    def perform_search(self, query: str):
        """Очищает и вводит текст в поле поиска."""
        search_input = WebDriverWait(self.driver, 20).until(
            EC.visibility_of_element_located(self.search_input_locator)
        )
        search_input.click()
        search_input.clear()
        search_input.send_keys(query)
        # Можно добавить sleep(0.3), если ввод "рвётся"
        return self

    def get_current_orgstructure(self):
        """Возвращает текущую выбранную площадку (из title)."""
        try:
            input_field = self.driver.find_element(*self.orgstructure_input_locator)
            return input_field.get_attribute("title").strip()
        except:
            return ""

    def wait_for_default_orgstructure_loaded(self, region: str, timeout=30):
        """
        Ждёт, пока в поле выбора площадки появится значение с указанным городом.
        """
        dict_of_region = {
            "siberia": "Абакан",
            "ural": "Курган"
        }
        WebDriverWait(self.driver, timeout).until(
            lambda d: dict_of_region[region] in self.get_current_orgstructure()
        )
        return self

    def select_orgstructure_by_city(self, city: str):
        """
        Меняет площадку, вводя название в поле и нажимая Enter.
        Пример: select_orgstructure_by_city("Новосибирск")
        """
        expected_text = f"ООО «Континент» ({city})"

        # 1. Находим поле ввода
        input_field = WebDriverWait(self.driver, 15).until(
            EC.element_to_be_clickable(self.orgstructure_input_locator)
        )

        # 2. Очищаем поле (на всякий случай)
        input_field.click()  # Кликаем, чтобы активировать
        input_field.send_keys(Keys.CONTROL + "a")  # Выделяем всё
        input_field.send_keys(Keys.DELETE)  # Удаляем

        # 3. Вводим название площадки
        input_field.send_keys(expected_text)
        print(f"⌨️ Введено в поле выбора: {expected_text}")

        # 4. Нажимаем Enter
        input_field.send_keys(Keys.ENTER)
        print("✅ Нажато Enter — выбор подтверждён")

        # 5. Ждём, что значение установилось
        WebDriverWait(self.driver, 15).until(
            lambda d: city in self.get_current_orgstructure()
        )
        print(f"✅ Текущая площадка: {self.get_current_orgstructure()}")

        return self

    def get_rows(self):
        """
        Всегда ищет свежие строки таблицы.
        """
        try:
            # Явно перезапрашиваем tbody и строки
            tbody = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(self.table_body_locator)
            )
            rows = tbody.find_elements(*self.table_row_locator)
            return [
                row for row in rows
                if len(row.find_elements(By.TAG_NAME, "td")) > 0
            ]
        except:
            return []

    def get_invoice_data(self, row):
        """
        Извлекает данные из строки по именам колонок.
        Возвращает словарь: {number: ..., date: ..., total: ...}
        """
        cells = row.find_elements(*self.table_cell_locator)
        if len(cells) < len(self.columns):
            return {}

        data = {}
        for col_key, col_name in self.columns.items():
            # Находим ячейку по атрибуту gui-col-name
            cell = row.find_element(By.CSS_SELECTOR, f"[gui-col-name='{col_name}']")
            text = cell.text.strip().replace("\u00A0", " ")  # Замена неразрывного пробела
            data[col_key] = text
        return data

    def get_all_invoices(self):
        """Возвращает список всех накладных (в виде словарей)."""
        rows = self.get_rows()
        invoices = []
        for row in rows:
            data = self.get_invoice_data(row)
            if data.get("number"):  # если номер есть
                invoices.append(data)
        return invoices

    def is_empty(self):
        """Проверяет, отображается ли сообщение 'Нет данных'."""
        try:
            message = self.driver.find_element(*self.empty_message_locator)
            return message.is_displayed()
        except:
            return False

    def is_valid_invoice_number(self, number: str) -> bool:
        """Проверяет формат номера: XX/XXXXXX или Ч-XXXXXX."""
        number = number.strip()
        pattern = r"^(\d{2}/\d{6}|Ч-\d{6})$"
        return bool(re.match(pattern, number))