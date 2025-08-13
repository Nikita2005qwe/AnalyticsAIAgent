from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class LoginPage:
    def __init__(self, driver):
        self.driver = driver
        self.login_field_locator = (By.ID, "login")
        self.password_field_locator = (By.ID, "password")
        self.submit_button_locator = (By.ID, "submitButton")

    def is_loaded(self):
        """Проверяет, загружена ли страница входа."""
        try:
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located(self.login_field_locator)
            )
            return True
        except:
            return False

    def login(self, username: str, password: str):
        """Выполняет ввод логина, пароля и нажатие кнопки 'Войти'."""
        login_field = WebDriverWait(self.driver, 15).until(
            EC.presence_of_element_located(self.login_field_locator)
        )
        login_field.clear()
        login_field.send_keys(username)

        password_field = self.driver.find_element(*self.password_field_locator)
        password_field.clear()
        password_field.send_keys(password)

        submit_button = self.driver.find_element(*self.submit_button_locator)
        submit_button.click()

        return self