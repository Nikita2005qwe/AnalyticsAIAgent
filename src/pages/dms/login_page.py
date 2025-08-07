# src/pages/dms/login_page.py

from .base_page import BasePage

class LoginPage(BasePage):
    # 🔹 Правильные локаторы (на основе твоего HTML)
    LOGIN_INPUT = (By.ID, "login")
    PASSWORD_INPUT = (By.ID, "password")
    SUBMIT_BUTTON = (By.ID, "submitButton")

    def login(self, username: str, password: str):
        """
        Выполняет вход в DMS.
        Args:
            username: логин (email или телефон)
            password: пароль
        """
        # Ввод логина
        self.input_text(*self.LOGIN_INPUT, username)

        # Ввод пароля
        self.input_text(*self.PASSWORD_INPUT, password)

        # Нажатие кнопки "Войти"
        self.click_element(*self.SUBMIT_BUTTON)