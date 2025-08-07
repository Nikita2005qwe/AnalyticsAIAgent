# src/pages/dms/subsystem_selection_page.py

from .base_page import BasePage

class SubsystemSelectionPage(BasePage):
    # Локаторы
    DISTRIBUTOR_PANEL_BUTTON = (By.XPATH, "//button[contains(text(), 'Панель дистрибьютора')]")

    def __init__(self, driver):
        super().__init__(driver)

    def select_distributor_panel(self):
        """Выбирает панель дистрибьютора."""
        self.click_element(*self.DISTRIBUTOR_PANEL_BUTTON)