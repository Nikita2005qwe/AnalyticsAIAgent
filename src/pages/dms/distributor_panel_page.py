# src/pages/dms/distributor_panel_page.py

from .base_page import BasePage

class DistributorPanelPage(BasePage):
    # Локаторы
    DOCUMENTS_NAVIGATION_LINK = (By.XPATH, "//a[contains(text(), 'Документы')]")

    def __init__(self, driver):
        super().__init__(driver)

    def open_documents_section(self):
        """Переходит в раздел 'Документы'."""
        self.click_element(*self.DOCUMENTS_NAVIGATION_LINK)