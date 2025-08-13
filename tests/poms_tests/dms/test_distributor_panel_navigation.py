import pytest
from selenium.webdriver.support.wait import WebDriverWait
from src.pages.dms.subsystems_page import SubsystemsPage
from src.pages.dms.main_page import MainPage
from src.pages.dms.login_page import LoginPage
from src.pages.dms.distributor_panel_page import DistributorPanelPage
from dotenv import load_dotenv
import os

load_dotenv()

def test_login_and_navigate_to_documents(driver):
    """Тест: вход → Панель дистрибьютора → переход в раздел 'Документы'"""
    username = os.getenv("DMS_USERNAME_SIB")
    password = os.getenv("DMS_PASSWORD_SIB")

    assert username, "DMS_USERNAME_SIB не задан в .env"
    assert password, "DMS_PASSWORD_SIB не задан в .env"

    # 1. Главная → модалка → "Войти"
    main_page = MainPage(driver)
    main_page.open()
    main_page.accept_region_popup()
    main_page.go_to_login_page()

    # 2. Вход
    login_page = LoginPage(driver)
    assert login_page.is_loaded(), "Страница входа не загрузилась"
    login_page.login(username, password)

    # 3. Переход на /subsystems
    subsystems_page = SubsystemsPage(driver)
    WebDriverWait(driver, 25).until(lambda d: "/subsystems" in d.current_url)
    assert "/subsystems" in driver.current_url, "Не перешли на /subsystems"

    # 4. Переход в панель дистрибьютора
    subsystems_page.go_to_distributor_panel()

    # 5. Ожидание загрузки панели
    distributor_panel = DistributorPanelPage(driver)
    # 5. Ожидание редиректа на dms.goodfood.shop
    WebDriverWait(driver, 20).until(
        lambda d: "dms.goodfood.shop" in d.current_url
    )
    print(f"✅ Перешли на: {driver.current_url}")

    # 6. Переход в раздел "Документы"
    distributor_panel.go_to_section("documents")

    # 7. Проверка: URL изменился или загрузилась страница
    try:
        WebDriverWait(driver, 20).until(
            lambda d: "document" in d.current_url.lower()
        )
        print(f"✅ Успешно перешли в раздел 'Документы': {driver.current_url}")
    except:
        pytest.fail("Не удалось перейти в раздел 'Документы'")