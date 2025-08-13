from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class SubsystemsPage:
    def __init__(self, driver):
        self.driver = driver
        # 🔹 Локатор по тексту внутри карточки
        self.distributor_panel_card_locator = (
            By.XPATH,
            "//nes-subsystem-card[.//div[contains(text(), 'Панель дистрибьютора')]]//a"
        )

    def is_loaded(self):
        """Проверяет, загрузилась ли страница подсистем (хотя бы одна карточка есть)."""
        try:
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "nes-subsystem-card"))
            )
            return True
        except:
            return False

    def go_to_distributor_panel(self):
        """Кликает по карточке 'Панель дистрибьютора'."""
        card_link = WebDriverWait(self.driver, 20).until(
            EC.element_to_be_clickable(self.distributor_panel_card_locator)
        )
        # Прокрутка к элементу (карточки могут быть ниже)
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", card_link)
        card_link.click()
        return self