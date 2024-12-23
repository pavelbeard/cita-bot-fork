import asyncio
import logging
import math
import random
from datetime import datetime as dt
import re

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

from citabot.constants import BROWSERS_LIST, DELAY, LIVE_PROXIES
from citabot.types import CustomerProfile
from citabot.exceptions import TooManyRequestsException


def proxy_selector():
    while True:
        for proxy in LIVE_PROXIES:
            yield proxy


def change_driver():
    while True:
        for browser in BROWSERS_LIST:
            yield browser


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
        wait = asyncio.sleep(generate_random_int(start, end))
    else:
        wait = asyncio.sleep(seconds)

    await wait


def wait_exact_time(driver: Chrome | Firefox | Safari | Edge, context: CustomerProfile):
    if context.wait_exact_time:
        WebDriverWait(driver, 1200).until(
            lambda _x: [dt.now().minute, dt.now().second] in context.wait_exact_time
        )


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

        self.extranjeria = ".mf-simple-list--item.cat_extranjeria"
        self.citaPrevia = "[href='/pagina/index/directorio/icpplus']"
        self.acceder = "//*[@value='Acceder al Procedimiento']"
        self.selectAddressLevel1 = '//*[@id="form"]'
        self.acceptBtn = "#btnAceptar"
        self.selectTramites = '//*[@id="tramiteGrupo[1]"]'
        self.enterBtn = '//*[@id="btnEntrar"]'
        self.sendBtn = '//*[@id="btnEnviar"]'

        self.cookieAcceptBtn = "#cookie_action_close_header"

    def open_extranjeria(self):
        driver: Chrome = self.driver
        waiter = WebDriverWait(driver, 10)

        driver.get("https://icp.administracionelectronica.gob.es/icpplus/index.html/")

        logging.info("Extranjeria page loaded")
        
        if re.search("The user has sent too many requests", self.driver.page_source):
            raise TooManyRequestsException()

        self.driver = driver
        self.waiter = waiter

    def select_city(self, city, operation_category):
        __address_level1 = {"by": By.XPATH, "value": self.selectAddressLevel1}
        address_level1 = self.driver.find_element(**__address_level1)

        select1 = Select(address_level1)
        select1.select_by_value(f"/{operation_category}/citar?p={city}&locale=es")

        accept_button = self.driver.find_element(By.ID, "btnAceptar")
        self.waiter.until(lambda x: accept_button.is_displayed())
        accept_button.send_keys(Keys.ENTER)

        logging.info("City accepted")

    def accept_cookie(self):
        cookie_accept_button = self.driver.find_element(
            By.ID, "cookie_action_close_header"
        )
        self.waiter.until(lambda x: cookie_accept_button.is_displayed())
        cookie_accept_button.send_keys(Keys.ENTER)

        logging.info("Cookie accepted")

    def select_tramite(self, tramite):
        __tramites = {"by": By.XPATH, "value": self.selectTramites}
        tramites_select = self.driver.find_element(**__tramites)
        self.waiter.until(lambda x: tramites_select.is_displayed())

        select2 = Select(tramites_select)
        select2.select_by_value(tramite)

        accept_button2 = self.driver.find_element(By.ID, "btnAceptar")
        self.waiter.until(lambda x: accept_button2.is_displayed())
        accept_button2.send_keys(Keys.ENTER)
        
        if "Requested URL was rejected" in body_text(self.driver):
            raise Exception("Requested URL was rejected")
        
        return self.driver
