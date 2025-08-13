import pytest
from selenium.webdriver.support.wait import WebDriverWait
from src.pages.dms.subsystems_page import SubsystemsPage
from src.pages.dms.main_page import MainPage
from src.pages.dms.login_page import LoginPage
from dotenv import load_dotenv
from selenium import webdriver
import os


load_dotenv()

@pytest.fixture
def driver():
    driver = webdriver.Chrome()
    driver.maximize_window()
    yield driver
    driver.quit()


def test_login_and_open_distributor_panel(driver):
    """Тест: вход → /subsystems → переход в 'Панель дистрибьютора'"""
    username = os.getenv("DMS_USERNAME_SIB")
    password = os.getenv("DMS_PASSWORD_SIB")

    assert username, "DMS_USERNAME_SIB не задан в .env"
    assert password, "DMS_PASSWORD_SIB не задан в .env"

    # 1. Главная → модалка → "Войти"
    main_page = MainPage(driver)
    main_page.open()
    main_page.accept_region_popup()
    main_page.go_to_login_page()

    # 2. Вход в DMS
    login_page = LoginPage(driver)
    assert login_page.is_loaded(), "Страница входа не загрузилась"
    login_page.login(username, password)

    # 3. Ожидание перехода на /subsystems
    subsystems_page = SubsystemsPage(driver)
    WebDriverWait(driver, 25).until(
        lambda d: "/subsystems" in d.current_url
    )
    assert "/subsystems" in driver.current_url, "Не перешли на /subsystems"

    # 4. Проверка, что карточки загрузились
    assert subsystems_page.is_loaded(), "Страница подсистем не загрузилась"

    # 5. Переход в панель дистрибьютора
    subsystems_page.go_to_distributor_panel()

    # 6. Проверка перехода (URL должен измениться)
    try:
        WebDriverWait(driver, 20).until(
            lambda d: "dms.goodfood.shop" in d.current_url or "distributor" in d.current_url
        )
        print(f"✅ Успешно перешли на: {driver.current_url}")
    except:
        pytest.fail("Не удалось перейти на страницу панели дистрибьютора")