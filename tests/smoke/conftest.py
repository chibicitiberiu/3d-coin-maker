"""
Pytest configuration and fixtures for smoke tests.
"""
import pytest
import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService


def pytest_addoption(parser):
    """Add command line options for smoke tests."""
    parser.addoption(
        "--browser",
        action="store",
        default="chrome",
        help="Browser to use for testing: chrome, firefox"
    )
    parser.addoption(
        "--headless",
        action="store_true",
        default=True,
        help="Run browser in headless mode"
    )
    parser.addoption(
        "--base-url",
        action="store",
        default=None,
        help="Base URL for the application (if already running)"
    )
    parser.addoption(
        "--timeout",
        action="store",
        type=int,
        default=30,
        help="Default timeout for operations in seconds"
    )


@pytest.fixture(scope="session")
def browser_type(request):
    """Get browser type from command line."""
    return request.config.getoption("--browser")


@pytest.fixture(scope="session")
def headless(request):
    """Get headless mode from command line."""
    return request.config.getoption("--headless")


@pytest.fixture(scope="session")
def timeout(request):
    """Get timeout from command line."""
    return request.config.getoption("--timeout")


@pytest.fixture(scope="session")
def base_url(request):
    """Get base URL from command line."""
    return request.config.getoption("--base-url")


@pytest.fixture(scope="session")
def driver(browser_type, headless):
    """Create and configure WebDriver instance."""
    if browser_type.lower() == "firefox":
        options = FirefoxOptions()
        if headless:
            options.add_argument("--headless")
        options.add_argument("--width=1920")
        options.add_argument("--height=1080")
        
        # Try to create Firefox driver
        try:
            driver = webdriver.Firefox(options=options)
        except Exception:
            # Fallback to Chrome if Firefox fails
            driver = _create_chrome_driver(headless)
    else:
        driver = _create_chrome_driver(headless)
    
    driver.implicitly_wait(10)
    yield driver
    driver.quit()


def _create_chrome_driver(headless):
    """Create Chrome WebDriver with appropriate options."""
    options = ChromeOptions()
    if headless:
        options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-web-security")
    options.add_argument("--allow-running-insecure-content")
    
    return webdriver.Chrome(options=options)


@pytest.fixture
def test_image_path():
    """Path to test image file."""
    return os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "assets",
        "test-coin-image.png"
    )


def wait_for_url_ready(url, timeout=60, interval=2):
    """Wait for URL to be ready and responding."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                return True
        except requests.RequestException:
            pass
        time.sleep(interval)
    return False


def wait_for_health_check(health_url, timeout=60):
    """Wait for health check endpoint to be ready."""
    return wait_for_url_ready(health_url, timeout)