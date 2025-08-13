from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class DistributorPanelPage:
    def __init__(self, driver):
        self.driver = driver

        # Локаторы для пунктов меню (по тексту)
        self.menu_item_locator_template = (
            By.XPATH,
            "//div[@class='sections-list__item-name text' and normalize-space()='{text}']/ancestor::li"
        )

        # Словарь для быстрого доступа
        self.menu_items = {
            "orders": "Заказы",
            "sites": "Площадки",
            "warehouses": "Склады и остатки",
            "sku": "SKU и ассортимент",
            "clients": "Клиенты и торговые точки",
            "documents": "Документы",
            "journal": "Журнал",
            "loyalty": "Программа лояльности",
            "notifications": "Уведомления",
        }

    def is_loaded(self):
        """Проверяет, загрузилась ли панель дистрибьютора (есть хотя бы одно меню)."""
        try:
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CLASS_NAME, "side-menu__sections-list"))
            )
            return True
        except:
            return False

    def go_to_section(self, section_key: str):
        """
        Переходит в указанный раздел.
        :param section_key: ключ из menu_items, например 'documents', 'orders', 'warehouses'
        """
        if section_key not in self.menu_items:
            raise ValueError(f"Неизвестный раздел: {section_key}. Доступные: {list(self.menu_items.keys())}")

        section_text = self.menu_items[section_key]

        # Формируем локатор по тексту
        locator = (
            By.XPATH,
            f"//div[@class='sections-list__item-name text' and normalize-space()='{section_text}']/ancestor::li"
        )

        # Ждём и кликаем
        try:
            item = WebDriverWait(self.driver, 20).until(
                EC.element_to_be_clickable(locator)
            )
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", item)
            item.click()
            return self
        except Exception as e:
            raise RuntimeError(f"Не удалось перейти в раздел '{section_text}': {e}")