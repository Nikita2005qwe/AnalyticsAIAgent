import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv
import os

load_dotenv()

@pytest.fixture
def driver():
    driver = webdriver.Chrome()
    driver.maximize_window()
    yield driver
    driver.quit()

def test_login_siberia(driver):
    """Тест: вход под Сибирью и проверка редиректа на /subsystems."""
    url = os.getenv("DMS_BASE_URL")
    username = os.getenv("DMS_USERNAME_SIB")
    password = os.getenv("DMS_PASSWORD_SIB")

    assert url, "Не задан DMS_BASE_URL в .env"
    assert username, "Не задан DMS_USERNAME_SIB в .env"
    assert password, "Не задан DMS_PASSWORD_SIB в .env"

    # 1. Открываем страницу входа
    driver.get(url)

    # 2. Вводим логин
    login_field = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.ID, "login"))
    )
    login_field.clear()
    login_field.send_keys(username)

    # 3. Вводим пароль
    password_field = driver.find_element(By.ID, "password")
    password_field.clear()
    password_field.send_keys(password)

    # 4. Нажимаем "Войти"
    submit_button = driver.find_element(By.ID, "submitButton")
    submit_button.click()

    # 5. Проверяем редирект на /subsystems
    try:
        WebDriverWait(driver, 20).until(
            lambda d: "/subsystems" in d.current_url
        )
        assert "/subsystems" in driver.current_url, "Не произошёл редирект на /subsystems"
    except:
        pytest.fail("Не удалось перейти на страницу подсистем после входа")