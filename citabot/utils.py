import logging

from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait
from undetected_chromedriver import Chrome
from selenium.webdriver.common.keys import Keys


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
        return self.driver
