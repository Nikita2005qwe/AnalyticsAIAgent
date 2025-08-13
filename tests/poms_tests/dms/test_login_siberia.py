import pytest
from src.pages.dms.main_page import MainPage
from src.pages.dms.login_page import LoginPage
from dotenv import load_dotenv
import os
from selenium.webdriver.support.wait import WebDriverWait
from selenium import webdriver


load_dotenv()

@pytest.fixture
def driver():
    driver = webdriver.Chrome()
    driver.maximize_window()
    yield driver
    driver.quit()

def test_navigate_to_login_page(driver):
    """Тест: открыть goodfood.shop → закрыть модалку → перейти на страницу входа"""
    main_page = MainPage(driver)
    main_page.open()
    main_page.accept_region_popup()  # Закрываем "Да, верно"
    main_page.go_to_login_page()    # Кликаем "Войти"

    # Проверяем, что URL изменился (предполагаем, что ведёт на DMS)
    WebDriverWait(driver, 20).until(
        lambda d: "login" in d.current_url.lower() or "dms" in d.current_url
    )
    assert "login" in driver.current_url.lower(), "Не перешли на страницу входа"

def test_login_to_dms_with_siberia(driver):
    """Тест: полный сценарий — от главной до входа в DMS /subsystems"""
    # Данные из .env
    username = os.getenv("DMS_USERNAME_SIB")
    password = os.getenv("DMS_PASSWORD_SIB")

    assert username, "DMS_USERNAME_SIB не задан в .env"
    assert password, "DMS_PASSWORD_SIB не задан в .env"

    # Шаг 1: Главная → модалка → "Войти"
    main_page = MainPage(driver)
    main_page.open()
    main_page.accept_region_popup()
    main_page.go_to_login_page()

    # Шаг 2: Проверка загрузки страницы входа
    login_page = LoginPage(driver)
    assert login_page.is_loaded(), "Страница входа не загрузилась"

    # Шаг 3: Вход
    login_page.login(username, password)

    # Шаг 4: Проверка успешного входа
    try:
        WebDriverWait(driver, 25).until(
            lambda d: "/subsystems" in d.current_url
        )
        assert "/subsystems" in driver.current_url, "Не перешли на /subsystems после входа"
    except Exception as e:
        pytest.fail(f"Не удалось перейти на /subsystems: {e}")