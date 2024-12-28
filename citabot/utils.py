import asyncio
import json
import logging
import math
import random
import time
from datetime import datetime as dt
from typing import Dict

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.edge.webdriver import WebDriver as Edge
from selenium.webdriver.safari.webdriver import WebDriver as Safari
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait
from undetected_chromedriver import Chrome
from undetected_geckodriver import Firefox

from citabot.constants import BROWSERS_LIST, DELAY, DRIVERS_LIST, LIVE_PROXIES
from citabot.exceptions import RejectionURLException, TooManyRequestsException
from citabot.types import CustomerProfile


def proxy_selector():
    while True:
        for proxy in LIVE_PROXIES:
            yield proxy


def change_browser():
    while True:
        for browser in BROWSERS_LIST:
            yield browser


def change_driver():
    while True:
        for driver in DRIVERS_LIST:
            yield driver


def generate_random_int(start: int, end: int):
    return math.floor(random.uniform(start, end))


def implicit_random_wait(
    driver: Chrome, seconds: int = 0, start: int = 2, end: int = 5
):
    """That's an implicit wait function

    Args:
        driver (Chrome): chromedriver instance
        seconds (int, optional): implicit wait in seconds. Defaults to 0.
        start (int, optional): floor value of random number. Defaults to 2.
        end (int, optional): ceil value of random number. Defaults to 5.
    """
    if seconds == 0:
        wait = generate_random_int(start, end)
    else:
        wait = seconds

    driver.implicitly_wait(wait)


async def random_wait_async(seconds: int = 0, start: int = 2, end: int = 5):
    """That's an async wait function in order to async task in a time gap will not block the main thread.

    Args:
        seconds (int, optional): implicit wait in seconds. Defaults to 0.
        start (int, optional): floor value of random number. Defaults to 2.
        end (int, optional): ceil value of random number. Defaults to 5.
    """
    if seconds == 0:
        random_seconds = generate_random_int(start, end)
        wait = asyncio.sleep(random_seconds)
        logging.info(f"Waiting for {random_seconds} seconds...")
    else:
        wait = asyncio.sleep(seconds)
        logging.info(f"Waiting for {seconds} seconds...")

    await wait


def wait_exact_time(driver: Chrome | Firefox, context: CustomerProfile):
    try:
        if context.wait_exact_time:
            WebDriverWait(driver, 1200).until(
                lambda _x: [dt.now().minute, dt.now().second] in context.wait_exact_time
            )
        return True
    except TimeoutException:
        logging.error("Timed out waiting for exact time")
        return None


def wait_for_element(driver: Chrome | Firefox, by: By, timeout: int = 10):
    try:
        by_selector = by
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located(by_selector)
        )
        return True
    except TimeoutException:
        logging.info("Timed out waiting for element to load")

        # check for title
        try:
            title = driver.title
            time.sleep(2)

            if "429 Too Many Requests" in title:
                raise TooManyRequestsException
            elif "Request Rejected" in title:
                raise RejectionURLException

            return None
        except TooManyRequestsException:
            raise
        except RejectionURLException:
            raise
        except Exception as e:
            logging.error(e)
            return None


def body_text(driver: Chrome | Firefox | Safari | Edge):
    try:
        WebDriverWait(driver, DELAY).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        return driver.find_element(By.TAG_NAME, "body").text
    except TimeoutException:
        logging.info("Timed out waiting for body to load")
        return ""


class Watcher:
    def __init__(self, driver: Chrome):
        self.driver = driver
        self.waiter = WebDriverWait(driver, 4)

        self.extranjeria = ".mf-simple-list--item.cat_extranjeria"
        self.citaPrevia = "[href='/pagina/index/directorio/icpplus']"
        self.acceder = "//*[@value='Acceder al Procedimiento']"
        self.selectAddressLevel1 = '//*[@id="form"]'
        self.acceptBtn = "#btnAceptar"
        self.selectTramites = '//*[@id="tramiteGrupo[1]"]'
        self.enterBtn = '//*[@id="btnEntrar"]'
        self.sendBtn = '//*[@id="btnEnviar"]'

        self.cookieAcceptBtn = "#cookie_action_close_header"

    async def open_extranjeria(self):
        self.driver.delete_all_cookies()
        self.driver.execute_script("window.localStorage.clear();")
        self.driver.execute_script("window.sessionStorage.clear();")

        self.driver.get(
            "https://icp.administracionelectronica.gob.es/icpplus/index.html/"
        )
        logging.info("Extranjeria page loaded")

    async def select_city(self, city, operation_category):
        __address_level1 = {"by": By.XPATH, "value": self.selectAddressLevel1}

        if not wait_for_element(self.driver, tuple(__address_level1.values())):
            return None

        address_level1 = self.driver.find_element(**__address_level1)

        select1 = Select(address_level1)
        select1.select_by_value(f"/{operation_category}/citar?p={city}&locale=es")

        __accept_button = {"by": By.ID, "value": "btnAceptar"}

        if not wait_for_element(self.driver, tuple(__accept_button.values())):
            return None

        accept_button = self.driver.find_element(**__accept_button)
        accept_button.send_keys(Keys.ENTER)

        logging.info("City accepted")

    async def accept_cookie(self):
        __cookie_accept_button = {"by": By.ID, "value": "cookie_action_close_header"}

        if not wait_for_element(self.driver, tuple(__cookie_accept_button.values())):
            return None

        cookie_accept_button = self.driver.find_element(**__cookie_accept_button)
        cookie_accept_button.send_keys(Keys.ENTER)

        logging.info("Cookie accepted")

    async def select_tramite(self, tramite):
        __tramites = {"by": By.XPATH, "value": self.selectTramites}

        if not wait_for_element(self.driver, tuple(__tramites.values())):
            return None

        tramites_select = self.driver.find_element(**__tramites)

        select2 = Select(tramites_select)
        select2.select_by_value(tramite)

        __accept_button2 = {"by": By.ID, "value": "btnAceptar"}

        if not wait_for_element(self.driver, tuple(__accept_button2.values())):
            return None

        accept_button2 = self.driver.find_element(**__accept_button2)
        accept_button2.send_keys(Keys.ENTER)

        return self.driver


def open_json_file(path) -> Dict[str, str]:
    try:
        with open(path, "r") as f:
            data = json.load(f)
            return data
    except FileNotFoundError:
        return {}
