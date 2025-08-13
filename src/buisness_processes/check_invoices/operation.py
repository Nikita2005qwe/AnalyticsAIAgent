from dotenv import load_dotenv
import os
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from src.pages.dms.main_page import MainPage
from src.pages.dms.login_page import LoginPage
from src.pages.dms.subsystems_page import SubsystemsPage
from src.pages.dms.distributor_panel_page import DistributorPanelPage
from src.pages.dms.invoices_page import InvoicesPage
from src.buisness_processes.data.settings_for_invoices_check import INVOICE_PREFIX_REGIONS

load_dotenv()


class DMSOperation:
    """
    Операция поиска накладной в DMS.
    Поддерживает работу с разными регионами (сибирь, урал).
    Каждый экземпляр — одна сессия (один аккаунт).
    """

    # Сопоставление региона → переменные окружения
    CREDENTIALS = {
        "siberia": ("DMS_USERNAME_SIB", "DMS_PASSWORD_SIB"),
        "ural": ("DMS_USERNAME_URAL", "DMS_PASSWORD_URAL"),
    }

    def __init__(self, region: str):
        """
        :param region: "siberia" или "ural"
        """
        self.region = region.lower()
        if self.region not in self.CREDENTIALS:
            raise ValueError(f"Неизвестный регион: {region}")

        self.driver = None
        self.invoices_page = None
        self._initialized = False

    def _start_dms(self):
        """Запускает DMS с учётом региона."""
        if self._initialized:
            return

        username_key, password_key = self.CREDENTIALS[self.region]
        username = os.getenv(username_key)
        password = os.getenv(password_key)

        if not username:
            raise ValueError(f"{username_key} не задан в .env")
        if not password:
            raise ValueError(f"{password_key} не задан в .env")

        try:
            self.driver = webdriver.Chrome()
            self.driver.maximize_window()

            main_page = MainPage(self.driver)
            main_page.open().accept_region_popup().go_to_login_page()

            login_page = LoginPage(self.driver)
            assert login_page.is_loaded(), "Страница входа не загрузилась"
            login_page.login(username, password)

            subsystems_page = SubsystemsPage(self.driver)
            WebDriverWait(self.driver, 25).until(lambda d: "/subsystems" in d.current_url)
            subsystems_page.go_to_distributor_panel()

            WebDriverWait(self.driver, 30).until(lambda d: "dms.goodfood.shop" in d.current_url)
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.CLASS_NAME, "side-menu__sections-list"))
            )

            distributor_panel = DistributorPanelPage(self.driver)
            distributor_panel.go_to_section("documents")

            self.invoices_page = InvoicesPage(self.driver)
            assert self.invoices_page.is_loaded(), "Страница накладных не загрузилась"

            self.invoices_page.wait_for_default_orgstructure_loaded(self.region, timeout=30)
            self._initialized = True

        except Exception as e:
            self._safe_quit()
            raise RuntimeError(f"Ошибка при запуске DMS ({self.region}): {e}")

    def _get_city_and_region(self, invoice_number: str) -> tuple[str, str]:
        """
        Возвращает город и регион по префиксу.
        :raises ValueError: Если префикс не найден.
        """
        for prefix, data in INVOICE_PREFIX_REGIONS.items():
            if invoice_number.startswith(prefix):
                return data["city"], data["region"]
        raise ValueError(f"Неизвестный префикс: {invoice_number}")

    def _switch_to_city(self, city: str):
        """Переключается на площадку по названию города."""
        expected = f"ООО «Континент» ({city})"
        current = self.invoices_page.get_current_orgstructure()
        if current != expected:
            self.invoices_page.select_orgstructure_by_city(city)

    def check_invoice(self, invoice_number: str) -> bool:
        """
        Проверяет накладную.
        Предусловие: операция создана под нужный регион.
         1. Сначала — на основной площадке.
        2. Если не найдена и есть alternative_city — пробует на альтернативной.
        """
        if not self._initialized:
            self._start_dms()

        # Определяем префикс и данные
        prefix_data = None
        for prefix, data in INVOICE_PREFIX_REGIONS.items():
            if invoice_number.startswith(prefix):
                prefix_data = data
                break

        if not prefix_data:
            raise ValueError(f"Неизвестный префикс: {invoice_number}")

        if prefix_data["region"] != self.region:
            raise ValueError(f"Накладная относится к региону '{prefix_data['region']}', а сессия — '{self.region}'")

        # Основной город
        main_city = prefix_data["city"]
        self._switch_to_city(main_city)
        self.invoices_page.perform_search(invoice_number)
        self.invoices_page.wait_for_search_result()

        if not self.invoices_page.is_empty():
            return True

        # Если не найдена, и есть альтернативная площадка — пробуем
        alt_city = prefix_data.get("alternative_city")
        if alt_city:
            self._switch_to_city(alt_city)
            self.invoices_page.perform_search(invoice_number)
            self.invoices_page.wait_for_search_result()
            return not self.invoices_page.is_empty()  # True, если найдена на альтернативной

        return False

    def close(self):
        self._safe_quit()

    def _safe_quit(self):
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                print(f"[DMSOperation] Ошибка при закрытии: {e}")
            self.driver = None
            self.invoices_page = None
            self._initialized = False