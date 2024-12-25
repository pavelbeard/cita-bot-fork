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


def check_form_exists(driver: Chrome):
    try:
        WebDriverWait(driver, DELAY).until(
            EC.presence_of_element_located((By.ID, "txtIdCitado"))
        )
        return True
    except TimeoutException:
        logging.error("Timed out waiting for form to load")
        return False


def input_data(driver: Chrome, context: CustomerProfile):
    driver.find_element(By.ID, "txtIdCitado").send_keys(context.doc_value)
    driver.find_element(By.ID, "txtDesCitado").send_keys(context.name)
    driver.find_element(By.ID, "txtAnnoCitado").send_keys(context.year_of_birth)


class TomaHuellasStep2(ICitaAction):
    def __init__(self, driver: Chrome, context: CustomerProfile):
        self.driver = driver
        self.context = context

    def do(self):
        driver = self.driver
        context = self.context

        if not check_form_exists(driver):
            return None

        # Select country
        select = Select(driver.find_element(By.ID, "txtPaisNac"))
        select.select_by_visible_text(context.country)

        # Select doc type
        if context.doc_type == DocType.PASSPORT:
            driver.find_element(By.ID, "rdbTipoDocPas").send_keys(Keys.SPACE)
        elif context.doc_type == DocType.NIE:
            driver.find_element(By.ID, "rdbTipoDocNie").send_keys(Keys.SPACE)

        # enter doc number, name and year of birth
        input_data(driver, context)

        return True


class RecogidaDeTarjetaStep2(ICitaAction):
    def __init__(self, driver: Chrome, context: CustomerProfile):
        self.driver = driver
        self.context = context

    def do(self):
        driver = self.driver
        context = self.context

        if not check_form_exists(driver):
            return None

        # Select doc type
        if context.doc_type == DocType.PASSPORT:
            driver.find_element(By.ID, "rdbTipoDocPas").send_keys(Keys.SPACE)
        elif context.doc_type == DocType.NIE:
            driver.find_element(By.ID, "rdbTipoDocNie").send_keys(Keys.SPACE)

        # enter doc number, name and year of birth
        input_data(driver, context)

        return True


class SolicitudAsiloStep2(ICitaAction):
    def __init__(self, driver: Chrome, context: CustomerProfile):
        self.driver = driver
        self.context = context

    def do(self):
        driver = self.driver
        context = self.context

        if not check_form_exists(driver):
            return None

        # Select doc type
        if context.doc_type == DocType.PASSPORT:
            driver.find_element(By.ID, "rdbTipoDocPas").send_keys(Keys.SPACE)
        elif context.doc_type == DocType.NIE:
            driver.find_element(By.ID, "rdbTipoDocNie").send_keys(Keys.SPACE)

        # enter doc number, name and year of birth
        input_data(driver, context)

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

        if not check_form_exists(driver):
            return None

        # Select doc type
        if context.doc_type == DocType.NIE:
            driver.find_element(By.ID, "rdbTipoDocNie").send_keys(Keys.SPACE)

        # enter doc number, name and year of birth
        input_data(driver, context)

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

        if not check_form_exists(driver):
            return None

        # Select doc type
        if context.doc_type == DocType.PASSPORT:
            driver.find_element(By.ID, "rdbTipoDocPas").send_keys(Keys.SPACE)
        elif context.doc_type == DocType.NIE:
            driver.find_element(By.ID, "rdbTipoDocNie").send_keys(Keys.SPACE)

        # enter doc number, name and year of birth
        input_data(driver, context)

        return True


class CartaInvitacionStep2(ICitaAction):
    def __init__(self, driver: Chrome, context: CustomerProfile):
        self.driver = driver
        self.context = context

    def do(self):
        driver = self.driver
        context = self.context

        if not check_form_exists(driver):
            return None

        # Select doc type
        if context.doc_type == DocType.PASSPORT:
            driver.find_element(By.ID, "rdbTipoDocPas").send_keys(Keys.SPACE)
        elif context.doc_type == DocType.DNI:
            driver.find_element(By.ID, "rdbTipoDocDni").send_keys(Keys.SPACE)
        elif context.doc_type == DocType.NIE:
            driver.find_element(By.ID, "rdbTipoDocNie").send_keys(Keys.SPACE)

        # enter doc number, name and year of birth
        input_data(driver, context)

        return True


class CertificadosStep2(ICitaAction):
    def __init__(self, driver: Chrome, context: CustomerProfile):
        self.driver = driver
        self.context = context

    def do(self):
        driver = self.driver
        context = self.context

        if not check_form_exists(driver):
            return None

        # Select doc type
        if context.doc_type == DocType.PASSPORT:
            driver.find_element(By.ID, "rdbTipoDocPas").send_keys(Keys.SPACE)
        elif context.doc_type == DocType.NIE:
            driver.find_element(By.ID, "rdbTipoDocNie").send_keys(Keys.SPACE)
        elif context.doc_type == DocType.DNI:
            driver.find_element(By.ID, "rdbTipoDocDni").send_keys(Keys.SPACE)

        # enter doc number, name and year of birth
        input_data(driver, context)

        return True


class AutorizacionDeRegresoStep2(ICitaAction):
    def __init__(self, driver: Chrome, context: CustomerProfile):
        self.driver = driver
        self.context = context

    def do(self):
        driver = self.driver
        context = self.context

        if not check_form_exists(driver):
            return None

        # Select doc type
        if context.doc_type == DocType.PASSPORT:
            driver.find_element(By.ID, "rdbTipoDocPas").send_keys(Keys.SPACE)
        elif context.doc_type == DocType.NIE:
            driver.find_element(By.ID, "rdbTipoDocNie").send_keys(Keys.SPACE)

        # enter doc number, name and year of birth
        input_data(driver, context)

        return True


class AsignacionNieStep2(ICitaAction):
    def __init__(self, driver: Chrome, context: CustomerProfile):
        self.driver = driver
        self.context = context

    def do(self):
        driver = self.driver
        context = self.context

        if not check_form_exists(driver):
            return None

        # Select doc type
        if context.doc_type == DocType.PASSPORT:
            option = driver.find_element(By.ID, "rdbTipoDocPas")
            if option:
                option.send_keys(Keys.SPACE)

        # enter doc number, name and year of birth
        input_data(driver, context)

        # Select country
        select = Select(driver.find_element(By.ID, "txtPaisNac"))
        select.select_by_visible_text(context.country)

        return True
