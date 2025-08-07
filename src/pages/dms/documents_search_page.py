# src/pages/dms/documents_search_page.py

from .base_page import BasePage

class DocumentsSearchPage(BasePage):
    # Локаторы
    SEARCH_INPUT = (By.ID, "invoiceSearchInput")
    SEARCH_RESULT_TABLE = (By.CSS_SELECTOR, "table.data-table")
    NO_DATA_MESSAGE = (By.XPATH, "//div[contains(text(), 'Данные не найдены')]")
    SEARCH_BUTTON = (By.ID, "searchButton")

    def __init__(self, driver):
        super().__init__(driver)

    def search_invoice(self, invoice_number):
        """Вводит номер накладной и выполняет поиск."""
        self.input_text(*self.SEARCH_INPUT, invoice_number)
        self.click_element(*self.SEARCH_BUTTON)

    def is_result_found(self):
        """Проверяет, есть ли данные по накладной."""
        try:
            self.wait.until(EC.presence_of_element_located(self.SEARCH_RESULT_TABLE))
            return True
        except:
            pass

        try:
            self.wait.until(EC.presence_of_element_located(self.NO_DATA_MESSAGE))
            return False
        except:
            return False  # Если ничего не нашли — считаем ошибкой