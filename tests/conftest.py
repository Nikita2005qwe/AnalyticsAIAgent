import sys
from pathlib import Path
import pytest
from selenium import webdriver
import shutil
import tempfile

# Добавляем корневую директорию проекта в PYTHONPATH
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

@pytest.fixture
def driver():
    driver = webdriver.Chrome()
    driver.maximize_window()
    yield driver
    driver.quit()

@pytest.fixture(scope="session")
def temp_dir():
    """Фикстура для создания временной директории."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)

@pytest.fixture
def sample_invoice_data():
    """Фикстура с тестовыми данными накладных."""
    return [
        ("01/12345", "01/", "siberia"),
        ("07/67890", "07/", "ural"),
        ("Е-11111", "Е-", "siberia"),
        ("Ч-22222", "Ч-", "ural"),
        ("XYZ99999", "", "unknown"),
        ("12345", "", "unknown")
    ]

@pytest.fixture
def real_file_path():
    """Фикстура с путем к реальному файлу."""
    return "data/Книга1.xlsx"
