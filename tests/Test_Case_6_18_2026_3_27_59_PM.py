import os
import time
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException


SCREENSHOT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screenshots")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)


@pytest.fixture
def driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--lang=en-US")
    drv = webdriver.Chrome(options=options)
    drv.set_page_load_timeout(45)
    yield drv
    drv.quit()


def _save_screenshot(drv, name):
    try:
        path = os.path.join(SCREENSHOT_DIR, f"{name}_{int(time.time())}.png")
        drv.save_screenshot(path)
        print(f"Screenshot saved: {path}")
    except WebDriverException as e:
        print(f"Could not save screenshot: {e}")


def test_youtube_search_for_keyword(driver):
    wait = WebDriverWait(driver, 20)
    search_term = "Vayuyantra"
    try:
        # Step 1: Navigate to YouTube
        driver.get("https://www.youtube.com/")
        wait.until(EC.title_contains("YouTube"))

        # Step 2: Locate and fill the search input (selector: name=search_query)
        search_input = wait.until(
            EC.element_to_be_clickable((By.NAME, "search_query"))
        )
        search_input.clear()
        search_input.send_keys(search_term)

        # Verify typed value
        assert search_input.get_attribute("value") == search_term, \
            f"Expected search box to contain {search_term!r}, got {search_input.get_attribute('value')!r}"

        # Step 3: Click the Search button (aria-label=Search)
        search_button = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label='Search']"))
        )
        try:
            search_button.click()
        except WebDriverException:
            # Fallback: submit via ENTER key
            search_input.send_keys(Keys.ENTER)

        # Step 4: Wait for results page
        wait.until(EC.url_contains("/results?search_query="))
        wait.until(EC.title_contains(search_term))

        current_url = driver.current_url
        assert "/results" in current_url, f"Expected results page, got {current_url}"
        assert "search_query=" in current_url, f"Expected search_query param in URL, got {current_url}"
        assert search_term.lower() in current_url.lower(), \
            f"Expected {search_term!r} in URL, got {current_url}"
        assert search_term.lower() in driver.title.lower(), \
            f"Expected {search_term!r} in title, got {driver.title!r}"

        # Verify that some result content rendered
        wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "ytd-search, #contents"))
        )

    except TimeoutException as te:
        _save_screenshot(driver, "youtube_search_timeout")
        pytest.fail(f"Timeout during YouTube search flow: {te}")
    except AssertionError:
        _save_screenshot(driver, "youtube_search_assertion_failure")
        raise
    except Exception as e:
        _save_screenshot(driver, "youtube_search_unexpected_error")
        pytest.fail(f"Unexpected error during YouTube search flow: {e}")
