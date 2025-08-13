from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class MainPage:
    def __init__(self, driver):
        self.driver = driver
        self.url = "https://goodfood.shop"

        # Модалка: "Да, верно"
        self.region_popup_button_locator = (
            By.XPATH,
            "//button[@buttontype='primary' and contains(@class, 'primary')]"
            "[.//div[contains(text(), 'Да, верно')]]"
        )

        # Кнопка "Войти" на главной
        self.login_button_locator = (
            By.CSS_SELECTOR,
            "button[buttontype='tertiary'].enter-btn"
        )

    def open(self):
        """Открывает главную страницу."""
        self.driver.get(self.url)
        return self

    def accept_region_popup(self):
        """Закрывает модальное окно с подтверждением региона (если появилось)."""
        try:
            button = WebDriverWait(self.driver, 20).until(
                EC.element_to_be_clickable(self.region_popup_button_locator)
            )
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
            button.click()
            print("✅ Модальное окно 'Да, верно' закрыто.")
        except Exception as e:
            print(f"ℹ️ Модальное окно не появилось или уже закрыто: {e}")
        return self

    def go_to_login_page(self):
        """Переходит на страницу входа через кнопку 'Войти'."""
        button = WebDriverWait(self.driver, 20).until(
            EC.element_to_be_clickable(self.login_button_locator)
        )
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
        button.click()
        return self