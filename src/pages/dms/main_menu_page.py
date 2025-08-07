# src/pages/dms/main_menu_page.py

from .base_page import BasePage

class MainMenuPage(BasePage):
    # Локаторы
    SUBSYSTEM_SELECTION_BUTTON = (By.XPATH, "//a[contains(text(), 'Выбор подсистемы')]")

    def __init__(self, driver):
        super().__init__(driver)

    def go_to_subsystem_selection(self):
        """Переходит на страницу выбора подсистемы."""
        self.click_element(*self.SUBSYSTEM_SELECTION_BUTTON)