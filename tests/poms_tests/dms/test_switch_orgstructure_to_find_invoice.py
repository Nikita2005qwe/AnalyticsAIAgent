import pytest
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from src.pages.dms.main_page import MainPage
from src.pages.dms.login_page import LoginPage
from src.pages.dms.subsystems_page import SubsystemsPage
from src.pages.dms.distributor_panel_page import DistributorPanelPage
from src.pages.dms.invoices_page import InvoicesPage
from dotenv import load_dotenv
import os


load_dotenv()


def test_switch_to_novosibirsk_and_find_invoice(driver):
    """Тест: смена площадки на Новосибирск → поиск накладной 05/048027"""
    username = os.getenv("DMS_USERNAME_SIB")
    password = os.getenv("DMS_PASSWORD_SIB")
    assert username, "DMS_USERNAME_SIB не задан в .env"
    assert password, "DMS_PASSWORD_SIB не задан в .env"

    # --- 1. Вход ---
    main_page = MainPage(driver)
    main_page.open().accept_region_popup().go_to_login_page()

    login_page = LoginPage(driver)
    assert login_page.is_loaded(), "Страница входа не загрузилась"
    login_page.login(username, password)

    # --- 2. Переход в подсистемы ---
    subsystems_page = SubsystemsPage(driver)
    WebDriverWait(driver, 25).until(lambda d: "/subsystems" in d.current_url)
    subsystems_page.go_to_distributor_panel()

    # --- 3. Ожидание загрузки DMS ---
    WebDriverWait(driver, 30).until(lambda d: "dms.goodfood.shop" in d.current_url)
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.CLASS_NAME, "side-menu__sections-list"))
    )

    # --- 4. Переход в "Накладные" ---
    distributor_panel = DistributorPanelPage(driver)
    distributor_panel.go_to_section("documents")

    # --- 5. Проверка: страница загружена и выбрана площадка по умолчанию ---
    invoices_page = InvoicesPage(driver)
    assert invoices_page.is_loaded(), "Страница накладных не загрузилась"

    # Ждём, пока в поле выбора появится "Абакан"
    try:
        invoices_page.wait_for_default_orgstructure_loaded("Абакан", timeout=30)
        current_org = invoices_page.get_current_orgstructure()
        print(f"✅ Текущая площадка: {current_org}")
    except Exception as e:
        pytest.fail(f"Не дождались выбора площадки по умолчанию (Абакан): {e}")

    # --- 6. Поиск накладной 05/048027 на Абакане → не должна находиться ---
    invoices_page.perform_search("05/048027")
    invoices_page.wait_for_search_result()

    assert invoices_page.is_empty(), "Накладная 05/048027 не должна находиться на площадке Абакан"
    print("✅ Накладная 05/048027 не найдена на Абакане — корректно")

    # --- 7. Смена площадки на Новосибирск ---
    invoices_page.select_orgstructure_by_city("Новосибирск")

    # --- 8. Проверка, что площадка изменилась ---
    new_org = invoices_page.get_current_orgstructure()
    assert "Новосибирск" in new_org, f"Площадка не изменилась: {new_org}"
    print(f"✅ Площадка изменена на: {new_org}")

    # --- 9. Поиск накладной 05/048027 ---
    invoices_page.perform_search("05/048027")
    invoices_page.wait_for_search_result()

    found_invoices = invoices_page.get_all_invoices()
    assert not invoices_page.is_empty(), "Накладная 05/048027 должна быть найдена на Новосибирске"
    assert len(found_invoices) >= 1, "Не найдено ни одной накладной после смены площадки"

    invoice = found_invoices[0]
    assert "05/048027" in invoice["number"], f"Найдена не та накладная: {invoice['number']}"
    print(f"✅ Найдена накладная: {invoice['number']} | Сумма: {invoice['total']} | Статус: {invoice['status']}")

    print("🎉 Успешно: смена площадки и поиск накладной работают корректно.")