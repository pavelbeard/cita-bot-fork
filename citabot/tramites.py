from undetected_chromedriver import Chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.select import Select
from selenium.common.exceptions import TimeoutException

import logging

from citabot.types import ICitaAction, CustomerProfile, DocType
from citabot.constants import DELAY


class TomaHuellasStep2(ICitaAction):
    def __init__(self, driver: Chrome, context: CustomerProfile):
        self.driver = driver
        self.context = context

    def do(self):
        driver = self.driver
        context = self.context

        try:
            WebDriverWait(driver, DELAY).until(
                EC.presence_of_element_located((By.ID, "txtPaisNac"))
            )
        except TimeoutException:
            logging.error("Timed out waiting for form to load")
            return None

        # Select country
        select = Select(driver.find_element(By.ID, "txtPaisNac"))
        select.select_by_visible_text(context.country)

        # Select doc type
        if context.doc_type == DocType.PASSPORT:
            driver.find_element(By.ID, "rdbTipoDocPas").send_keys(Keys.SPACE)
        elif context.doc_type == DocType.NIE:
            driver.find_element(By.ID, "rdbTipoDocNie").send_keys(Keys.SPACE)

        # Enter doc number and name
        element = driver.find_element(By.ID, "txtIdCitado")
        element.send_keys(context.doc_value, Keys.TAB, context.name)

        return True


class RecogidaDeTarjetaStep2(ICitaAction):
    def __init__(self, driver: Chrome, context: CustomerProfile):
        self.driver = driver
        self.context = context

    def do(self):
        driver = self.driver
        context = self.context

        try:
            WebDriverWait(driver, DELAY).until(
                EC.presence_of_element_located((By.ID, "txtIdCitado"))
            )
        except TimeoutException:
            logging.error("Timed out waiting for form to load")
            return None

        # Select doc type
        if context.doc_type == DocType.PASSPORT:
            driver.find_element(By.ID, "rdbTipoDocPas").send_keys(Keys.SPACE)
        elif context.doc_type == DocType.NIE:
            driver.find_element(By.ID, "rdbTipoDocNie").send_keys(Keys.SPACE)

        # Enter doc number and name
        element = driver.find_element(By.ID, "txtIdCitado")
        element.send_keys(context.doc_value, Keys.TAB, context.name)

        return True


class SolicitudAsiloStep2(ICitaAction):
    def __init__(self, driver: Chrome, context: CustomerProfile):
        self.driver = driver
        self.context = context

    def do(self):
        driver = self.driver
        context = self.context

        try:
            WebDriverWait(driver, DELAY).until(
                EC.presence_of_element_located((By.ID, "txtIdCitado"))
            )
        except TimeoutException:
            logging.error("Timed out waiting for form to load")
            return None

        # Select doc type
        if context.doc_type == DocType.PASSPORT:
            driver.find_element(By.ID, "rdbTipoDocPas").send_keys(Keys.SPACE)
        elif context.doc_type == DocType.NIE:
            driver.find_element(By.ID, "rdbTipoDocNie").send_keys(Keys.SPACE)

        # Enter doc number and name
        element = driver.find_element(By.ID, "txtIdCitado")
        element.send_keys(
            context.doc_value, Keys.TAB, context.name, Keys.TAB, context.year_of_birth
        )

        # Select country
        select = Select(driver.find_element(By.ID, "txtPaisNac"))
        select.select_by_visible_text(context.country)

        return True


class RenovacionAsiloStep2(ICitaAction):
    def __init__(self, driver: Chrome, context: CustomerProfile):
        self.driver = driver
        self.context = context

    def do(self):
        driver = self.driver
        context = self.context

        try:
            WebDriverWait(driver, DELAY).until(
                EC.presence_of_element_located((By.ID, "txtIdCitado"))
            )
        except TimeoutException:
            logging.error("Timed out waiting for form to load")
        
        try:
            WebDriverWait(driver, DELAY).until(
                EC.presence_of_element_located((By.ID, "txtDesCitado"))
            )
        except TimeoutException:
            logging.error("Timed out waiting for form to load")
            return None

        # Select doc type
        if context.doc_type == DocType.NIE:
            driver.find_element(By.ID, "rdbTipoDocNie").send_keys(Keys.SPACE)

        # Enter doc number and name
        element = driver.find_element(By.ID, "txtIdCitado")
        if element:
            element.send_keys(
                context.doc_value, Keys.TAB, context.name, Keys.TAB, context.year_of_birth
            )
        else:
            element = driver.find_element(By.ID, "txtAnnoCitado")
            element.send_keys(
                context.doc_value, Keys.TAB, context.name, Keys.TAB, context.year_of_birth
            )

        # Select country
        select = Select(driver.find_element(By.ID, "txtPaisNac"))
        select.select_by_visible_text(context.country)

        return True


class BrexitStep2(ICitaAction):
    def __init__(self, driver: Chrome, context: CustomerProfile):
        self.driver = driver
        self.context = context

    def do(self):
        driver = self.driver
        context = self.context

        try:
            WebDriverWait(driver, DELAY).until(
                EC.presence_of_element_located((By.ID, "txtIdCitado"))
            )
        except TimeoutException:
            logging.error("Timed out waiting for form to load")

        try:
            WebDriverWait(driver, DELAY).until(
                EC.presence_of_element_located((By.ID, "txtDesCitado"))
            )
        except TimeoutException:
            logging.error("Timed out waiting for form to load")
            return None

        # Select doc type
        if context.doc_type == DocType.PASSPORT:
            driver.find_element(By.ID, "rdbTipoDocPas").send_keys(Keys.SPACE)
        elif context.doc_type == DocType.NIE:
            driver.find_element(By.ID, "rdbTipoDocNie").send_keys(Keys.SPACE)

        # Enter doc number and name
        element = driver.find_element(By.ID, "txtIdCitado")

        if element:
            element.send_keys(context.doc_value, Keys.TAB, context.name)
        else:
            element = driver.find_element(By.ID, "txtDesCitado")
            element.send_keys(context.doc_value, Keys.TAB, context.name)

        return True


class CartaInvitacionStep2(ICitaAction):
    def __init__(self, driver: Chrome, context: CustomerProfile):
        self.driver = driver
        self.context = context

    def do(self):
        driver = self.driver
        context = self.context

        # Select doc type
        if context.doc_type == DocType.PASSPORT:
            driver.find_element(By.ID, "rdbTipoDocPas").send_keys(Keys.SPACE)
        elif context.doc_type == DocType.DNI:
            driver.find_element(By.ID, "rdbTipoDocDni").send_keys(Keys.SPACE)
        elif context.doc_type == DocType.NIE:
            driver.find_element(By.ID, "rdbTipoDocNie").send_keys(Keys.SPACE)

        # Enter doc number and name
        element = driver.find_element(By.ID, "txtIdCitado")
        element.send_keys(context.doc_value, Keys.TAB, context.name)

        return True


class CertificadosStep2(ICitaAction):
    def __init__(self, driver: Chrome, context: CustomerProfile):
        self.driver = driver
        self.context = context

    def do(self):
        driver = self.driver
        context = self.context

        try:
            WebDriverWait(driver, DELAY).until(
                EC.presence_of_element_located((By.ID, "txtIdCitado"))
            )
        except TimeoutException:
            logging.error("Timed out waiting for form to load")
            return None

        # Select doc type
        if context.doc_type == DocType.PASSPORT:
            driver.find_element(By.ID, "rdbTipoDocPas").send_keys(Keys.SPACE)
        elif context.doc_type == DocType.NIE:
            driver.find_element(By.ID, "rdbTipoDocNie").send_keys(Keys.SPACE)
        elif context.doc_type == DocType.DNI:
            driver.find_element(By.ID, "rdbTipoDocDni").send_keys(Keys.SPACE)

        # Enter doc number and name
        element = driver.find_element(By.ID, "txtIdCitado")
        element.send_keys(context.doc_value, Keys.TAB, context.name)

        return True


class AutorizacionDeRegresoStep2(ICitaAction):
    def __init__(self, driver: Chrome, context: CustomerProfile):
        self.driver = driver
        self.context = context

    def do(self):
        driver = self.driver
        context = self.context

        try:
            WebDriverWait(driver, DELAY).until(
                EC.presence_of_element_located((By.ID, "txtIdCitado"))
            )
        except TimeoutException:
            logging.error("Timed out waiting for form to load")
            return None

        # Select doc type
        if context.doc_type == DocType.PASSPORT:
            driver.find_element(By.ID, "rdbTipoDocPas").send_keys(Keys.SPACE)
        elif context.doc_type == DocType.NIE:
            driver.find_element(By.ID, "rdbTipoDocNie").send_keys(Keys.SPACE)

        # Enter doc number and name
        element = driver.find_element(By.ID, "txtIdCitado")
        element.send_keys(context.doc_value, Keys.TAB, context.name)

        return True


class AsignacionNieStep2(ICitaAction):
    def __init__(self, driver: Chrome, context: CustomerProfile):
        self.driver = driver
        self.context = context

    def do(self):
        driver = self.driver
        context = self.context

        try:
            WebDriverWait(driver, DELAY).until(
                EC.presence_of_element_located((By.ID, "txtIdCitado"))
            )
        except TimeoutException:
            logging.error("Timed out waiting for form to load")
            return None

        # Select doc type
        if context.doc_type == DocType.PASSPORT:
            option = driver.find_element(By.ID, "rdbTipoDocPas")
            if option:
                option.send_keys(Keys.SPACE)

        # Enter doc number, name and year of birth
        element = driver.find_element(By.ID, "txtIdCitado")
        element.send_keys(
            context.doc_value, Keys.TAB, context.name, Keys.TAB, context.year_of_birth
        )

        # Select country
        select = Select(driver.find_element(By.ID, "txtPaisNac"))
        select.select_by_visible_text(context.country)

        return True
