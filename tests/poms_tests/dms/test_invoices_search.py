from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from src.pages.dms.main_page import MainPage
from src.pages.dms.login_page import LoginPage
from src.pages.dms.subsystems_page import SubsystemsPage
from src.pages.dms.distributor_panel_page import DistributorPanelPage
from src.pages.dms.invoices_page import InvoicesPage
from dotenv import load_dotenv
import os


load_dotenv()


def test_invoices_search_and_validation(driver):
    """Тест: поиск накладных по префиксу 02 → проверка данных → проверка отсутствия чужих накладных"""
    username = os.getenv("DMS_USERNAME_SIB")
    password = os.getenv("DMS_PASSWORD_SIB")
    assert username, "DMS_USERNAME_SIB не задан в .env"
    assert password, "DMS_PASSWORD_SIB не задан в .env"

    # --- 1. Вход на сайт ---
    main_page = MainPage(driver)
    main_page.open().accept_region_popup().go_to_login_page()

    # --- 2. Авторизация ---
    login_page = LoginPage(driver)
    assert login_page.is_loaded(), "Страница входа не загрузилась"
    login_page.login(username, password)

    # --- 3. Переход в подсистемы ---
    subsystems_page = SubsystemsPage(driver)
    WebDriverWait(driver, 25).until(lambda d: "/subsystems" in d.current_url)
    subsystems_page.go_to_distributor_panel()

    # --- 4. Ожидание загрузки DMS ---
    WebDriverWait(driver, 30).until(lambda d: "dms.goodfood.shop" in d.current_url)
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.CLASS_NAME, "side-menu__sections-list"))
    )

    # --- 5. Переход в "Накладные" ---
    distributor_panel = DistributorPanelPage(driver)
    distributor_panel.go_to_section("documents")

    # --- 6. Проверка загрузки страницы ---
    invoices_page = InvoicesPage(driver)
    assert invoices_page.is_loaded(), "Страница накладных не загрузилась"
    invoices_page.wait_for_search_result()

    # --- 7. Проверка: есть ли данные при пустом поиске ---
    all_invoices = invoices_page.get_all_invoices()
    print(f"📦 Загружено накладных: {len(all_invoices)}")

    assert len(all_invoices) > 0, "Нет ни одной накладной при пустом поиске"
    assert all(inv.get("number") for inv in all_invoices), "Найдены накладные без номера"
    assert all(invoices_page.is_valid_invoice_number(inv["number"]) for inv in all_invoices), \
        "Обнаружены накладные с некорректным форматом номера"

    # Проверим, что все номера начинаются с "02/" (Абакан)
    abakan_invoices = [inv for inv in all_invoices if inv["number"].startswith("02/")]
    assert len(abakan_invoices) == len(all_invoices), \
        f"Ожидались только накладные из Абакана (02/...), но найдены другие: {[inv['number'] for inv in all_invoices if not inv['number'].startswith('02/')]}"

    # --- 8. Поиск по префиксу 02/ ---
    search_examples = ["02/056718", "056718", "02"]
    for query in search_examples:
        invoices_page.perform_search(query)
        invoices_page.wait_for_search_result()

        results = invoices_page.get_all_invoices()
        assert len(results) > 0, f"Не найдено накладных по запросу '{query}'"

        search_part = query.replace("02/", "").strip()
        found = False
        for inv in results:
            clean_number = inv["number"].strip().replace("\u00A0", "").replace(" ", "")
            if search_part in clean_number:
                found = True
                break

        assert found, f"Ни одна из найденных накладных не содержит '{search_part}' в номере: {[inv['number'] for inv in results]}"

    # --- 9. Проверка: чужие накладные НЕ находятся ---
    not_found_numbers = ["04/523872", "06/235292", "07/283902", "Ч-898544"]

    for number in not_found_numbers:
        invoices_page.perform_search(number)
        invoices_page.wait_for_search_result()

        assert invoices_page.is_empty(), f"Накладная {number} не должна находиться, но результат не пустой"
        print(f"✅ Корректно: накладная {number} не найдена (принадлежит другой площадке)")

    print("🎉 Все проверки пройдены: поиск, валидация, фильтрация по площадке работают корректно.")