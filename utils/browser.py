from selenium import webdriver

from selenium.webdriver.chrome.service import Service

from webdriver_manager.chrome import ChromeDriverManager

from config import HEADLESS


def create_driver():

    options = webdriver.ChromeOptions()

    if HEADLESS:

        options.add_argument("--headless=new")

    options.add_argument("--start-maximized")

    options.add_argument("--disable-notifications")

    options.add_argument("--disable-popup-blocking")

    options.add_argument("--disable-gpu")

    options.add_argument("--no-sandbox")

    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(

        service=Service(

            ChromeDriverManager().install()

        ),

        options=options

    )

    return driver