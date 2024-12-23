import asyncio
import io
import json
import logging
import os

import backoff
import urllib3
from fake_useragent import UserAgent
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.edge.webdriver import WebDriver as Edge
from selenium.webdriver.firefox.options import Options as FirefoxOptions

# from undetected_geckodriver import Firefox
from selenium.webdriver.firefox.webdriver import WebDriver as Firefox
from selenium.webdriver.safari.options import Options as SafariOptions
from selenium.webdriver.safari.webdriver import WebDriver as Safari
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from telegram import Update
from undetected_chromedriver import Chrome, ChromeOptions

from citabot.constants import CYCLES, DELAY
from citabot.exceptions import RejectionURLException, TooManyRequestsException
from citabot.states import confirmed_cita
from citabot.steps import delete_message, office_selection, phone_mail
from citabot.tramites import (
    AsignacionNieStep2,
    AutorizacionDeRegresoStep2,
    BrexitStep2,
    CartaInvitacionStep2,
    CertificadosStep2,
    RecogidaDeTarjetaStep2,
    RenovacionAsiloStep2,
    SolicitudAsiloStep2,
    TomaHuellasStep2,
)
from citabot.types import Browsers, CustomerProfile, OperationType, Province
from citabot.utils import (
    Watcher,
    body_text,
    change_browser,
    change_driver,
    implicit_random_wait,
    kill_process_by_name,
    proxy_selector,
    wait_exact_time,
)

__all__ = [
    "CustomerProfile",
    "OperationType",
    "Province",
    "CitaBotBuilder",
]


class DriverBuilder:
    driver: Chrome | Firefox | Safari | Edge

    def __init__(
        self,
        context: CustomerProfile,
        browser: Browsers = Browsers.CHROME,
        headless: bool = False,
    ):
        if browser == Browsers.CHROME:
            options = ChromeOptions()
        elif browser == Browsers.FIREFOX:
            options = FirefoxOptions()
        elif browser == Browsers.SAFARI:
            options = SafariOptions()
        elif browser == Browsers.EDGE:
            options = EdgeOptions()

        user_agent = UserAgent()

        logging.info(
            f"\033[1;32mUser Agent. new user agent: {user_agent.random}\033[0m"
        )

        user_agent = UserAgent()

        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--ignore-ssl-errors")
        options.add_argument("--disable-gpu")

        settings = {
            "recentDestinations": [
                {"id": "Save as PDF", "origin": "local", "account": ""}
            ],
            "selectedDestinationId": "Save as PDF",
            "version": 2,
        }
        preferences = {
            "printing.print_preview_sticky_settings.appState": json.dumps(settings),
            "download.default_directory": os.getcwd(),
        }

        if context.proxy:
            iterator = proxy_selector()
            proxy = next(iterator)
            options.add_argument("--proxy-server=" + proxy)
            logging.info(f"\033[33m[Proxy: {proxy}]\033[0m")

        try:
            if browser == Browsers.CHROME:
                if context.chrome_profile_path:
                    options.add_argument(f"user-data-dir={context.chrome_profile_path}")
                if context.chrome_profile_name:
                    options.add_argument(
                        f"profile-directory={context.chrome_profile_name}"
                    )

                options.add_argument(f"--user-agent={user_agent.random}")
                options.add_experimental_option("prefs", preferences)
                options.add_argument("--kiosk-printing")
                driver = Chrome(
                    options=options,
                    headless=headless,
                    use_subprocess=False,
                )
            elif browser == Browsers.FIREFOX:
                options.set_preference(
                    "print.print_preview_sticky_settings.appState", json.dumps(settings)
                )

                # Set download directory
                options.set_preference("browser.download.dir", os.getcwd())
                options.set_preference("browser.download.folderList", 2)
                options.set_preference(
                    "browser.helperApps.neverAsk.saveToDisk", "application/pdf"
                )
                # set user agent

                options.set_preference("general.useragent.override", user_agent.random)

                if headless:
                    options.add_argument("--headless")

                driver = Firefox(
                    options=options,
                )
            elif browser == Browsers.SAFARI:
                driver = Safari(
                    options=options,
                )
            elif browser == Browsers.EDGE:
                driver = Edge(
                    options=options,
                )

            driver.execute_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )

            self.driver = driver
        except Exception as e:
            logging.error(e)
            return None

    @property
    def get_driver(self):
        return self.driver


class CitaBotBuilder:
    update: Update
    context: CustomerProfile
    driver: Chrome

    def __init__(self, context: CustomerProfile, update: Update = None):
        self.update = update
        self.context = context

        confirmed_cita.update(
            {
                "doc_value": context.doc_value,
            }
        )

    async def start(
        self, update: Update, cycles: int = CYCLES
    ) -> dict | KeyboardInterrupt | None:
        context = self.context

        logging.basicConfig(
            format="%(asctime)s - %(message)s",
            level=logging.INFO,
            **context.log_settings,  # type: ignore
        )
        if context.sms_webhook_token:
            delete_message(context.sms_webhook_token)

        operation_category = "icpplus"
        operation_param = "tramiteGrupo[1]"

        if context.province == Province.BARCELONA:
            operation_category = "icpplustieb"
            operation_param = "tramiteGrupo[0]"
        elif context.province in [
            Province.ALICANTE,
            Province.ILLES_BALEARS,
            Province.LAS_PALMAS,
            Province.S_CRUZ_TENERIFE,
        ]:
            operation_category = "icpco"
        elif context.province == Province.MADRID:
            operation_category = "icpplustiem"
        elif context.province == Province.MÁLAGA:
            operation_category = "icpco"
            operation_param = "tramiteGrupo[0]"
        elif context.province in [
            Province.MELILLA,
            Province.SEVILLA,
        ]:
            operation_param = "tramiteGrupo[0]"

        fast_forward_url = f"https://icp.administracionelectronica.gob.es/{operation_category}/citar?p={context.province.value}"
        fast_forward_url2 = f"https://icp.administracionelectronica.gob.es/{operation_category}/acInfo?{operation_param}={context.operation_code.value}"

        success = False
        result = False
        cancelled = False
        driver_connection_lost = False
        browser_iterator = change_browser()
        driver_iterator = change_driver()

        while True:
            browser_name = next(browser_iterator)
            driver_name = next(driver_iterator)
            driver = DriverBuilder(context, browser=browser_name).get_driver

            for i in range(cycles):
                try:
                    logging.info(f"\033[33m[Attempt: {i + 1}/{cycles}]\033[0m")
                    logging.info(
                        f"🔄 Intentando citar en {context.province}. Attempt {i + 1}/{cycles}"
                    )

                    result = await cycle_cita(
                        driver,
                        context,
                        fast_forward_url,
                        fast_forward_url2,
                        operation_category,
                    )
                except KeyboardInterrupt:
                    logging.error("Keyboard interrupt")
                    raise
                except TimeoutException:
                    logging.error("Timeout exception")
                    continue
                except asyncio.CancelledError:
                    cancelled = True
                    break
                except urllib3.exceptions.HTTPError:
                    driver_connection_lost = True
                    logging.error("Connection with the driver was lost")
                    break
                except Exception as e:
                    logging.error(f"SMTH BROKEN: {e}")
                    await update.effective_message.reply_text(
                        "Something went wrong... Comprueba el bot... 😔"
                    )
                    break

                if result:
                    success = True
                    logging.info("WIN")

                    await update.effective_message.reply_text("🎉 CITA CONFIRMADA !!!!")
                    data = {**confirmed_cita}
                    if data.get("screenshot"):
                        image_file = io.BytesIO(data.get("screenshot"))
                        image_file.name = "cita-confirmada.png"
                        image_file.seek(0)
                        await update.effective_message.reply_photo(photo=image_file)
                    await update.effective_message.reply_text(
                        f"Codigo de confirmacion: {data.get('code')}"
                    )

                    return success

            if cancelled:
                await update.effective_message.reply_text("Cancelando...")
                driver.quit()
                return None

            if not success:
                if driver_connection_lost:
                    kill_process_by_name(name=browser_name.value)  # browser
                    kill_process_by_name(name=driver_name.value)  # driver
                    
                    driver_connection_lost = False

                else:
                    logging.error("FAIL")
                    driver.close()
                    driver.quit()

                await asyncio.sleep(5)


def log_backoff(details):
    logging.error(
        f"Unable to load the initial page, backing off {details['wait']:0.1f} seconds"
    )


@backoff.on_exception(
    backoff.constant,
    TimeoutException,
    interval=350,
    max_tries=(10 if os.environ.get("CITA_TEST") else None),
    on_backoff=log_backoff,
    logger=None,
)
@backoff.on_exception(
    backoff.constant,
    TooManyRequestsException,
    interval=600,
    max_tries=(10 if os.environ.get("CITA_TEST") else None),
    on_backoff=log_backoff,
    logger=None,
)
async def get_page(
    driver: Chrome | Firefox | Safari | Edge,
    context: CustomerProfile,
    fast_forward_url: str,
    fast_forward_url2: str,
    operation_category: str,
):
    fast_forward_trigger_failure = False
    watcher_trigger_failure = False
    browser_change_trigger_failure = False

    browser_iterator = change_browser()

    while True:
        if not fast_forward_trigger_failure:
            if context.first_load:
                driver.delete_all_cookies()

                driver.set_page_load_timeout(300 if context.first_load else 50)
                # Fix chromedriver 103 bug
                implicit_random_wait(driver, seconds=1)
                driver.get(fast_forward_url)
                implicit_random_wait(driver, seconds=5)
                if context.first_load:
                    try:
                        driver.execute_script("window.localStorage.clear();")
                        driver.execute_script("window.sessionStorage.clear();")
                    except Exception as e:
                        logging.error(e)
                        pass
                driver.get(fast_forward_url2)
                implicit_random_wait(driver, seconds=5)

                resp_text = body_text(driver)
                if "CITA PREVIA EXTRANJERÍA" not in resp_text:
                    context.first_load = True
                    logging.info("fast forward not loaded, starting from main page")
                    fast_forward_trigger_failure = True
                    continue

                context.first_load = False
                break

        elif not watcher_trigger_failure:
            try:
                watcher = Watcher(driver)
                await watcher.open_extranjeria()
                await watcher.select_city(context.province.value, operation_category)
                await watcher.accept_cookie()
                await watcher.select_tramite(context.operation_code.value)

                logging.info("Loaded initial page")
                break
            except TooManyRequestsException:
                raise TooManyRequestsException
            except RejectionURLException:
                raise RejectionURLException
            except Exception as e:
                logging.exception(e)

                watcher_trigger_failure = True
                driver.quit()
                continue

        elif not browser_change_trigger_failure:
            try:
                browser = next(browser_iterator)
                logging.info(f"\033[33m[Browser]: change to {browser}\033[0m")
                driver = DriverBuilder(context, browser).get_driver

                fast_forward_trigger_failure = False
                watcher_trigger_failure = False

            except Exception:
                raise TimeoutException


async def cycle_cita(
    driver: Chrome | Firefox | Safari | Edge,
    context: CustomerProfile,
    fast_forward_url,
    fast_forward_url2,
    operation_category,
):
    await get_page(
        driver, context, fast_forward_url, fast_forward_url2, operation_category
    )

    # 1. Instructions page:
    try:
        WebDriverWait(driver, DELAY).until(
            EC.presence_of_element_located((By.ID, "btnEntrar"))
        )
    except TimeoutException:
        logging.error("Timed out waiting for Instructions page to load")
        return None

    if (
        os.environ.get("CITA_TEST")
        and context.operation_code == OperationType.TOMA_HUELLAS
    ):
        logging.info("Instructions page loaded")
        return True

    driver.find_element(By.ID, "btnEntrar").send_keys(Keys.ENTER)

    # 2. Personal info:
    logging.info("[Step 1/6] Personal info")
    success = False
    if context.operation_code == OperationType.TOMA_HUELLAS:
        success = TomaHuellasStep2(driver, context).do()
    elif context.operation_code == OperationType.RECOGIDA_DE_TARJETA:
        success = RecogidaDeTarjetaStep2(driver, context).do()
    elif context.operation_code == OperationType.SOLICITUD_ASILO:
        success = SolicitudAsiloStep2(driver, context).do()
    elif context.operation_code == OperationType.RENOVACION_ASILO:
        success = RenovacionAsiloStep2(driver, context).do()
    elif context.operation_code == OperationType.BREXIT:
        success = BrexitStep2(driver, context).do()
    elif context.operation_code == OperationType.CARTA_INVITACION:
        success = CartaInvitacionStep2(driver, context).do()
    elif context.operation_code in [
        OperationType.CERTIFICADOS_NIE,
        OperationType.CERTIFICADOS_NIE_NO_COMUN,
        OperationType.CERTIFICADOS_RESIDENCIA,
        OperationType.CERTIFICADOS_UE,
    ]:
        success = CertificadosStep2(driver, context).do()
    elif context.operation_code == OperationType.AUTORIZACION_DE_REGRESO:
        success = AutorizacionDeRegresoStep2(driver, context).do()
    elif context.operation_code == OperationType.ASIGNACION_NIE:
        success = AsignacionNieStep2(driver, context).do()

    if not success:
        return None

    implicit_random_wait(driver, seconds=2)
    driver.find_element(By.ID, "btnEnviar").send_keys(Keys.ENTER)

    try:
        WebDriverWait(driver, 7).until(
            EC.presence_of_element_located((By.ID, "btnConsultar"))
        )
    except TimeoutException:
        logging.error("Timed out waiting for Solicitar page to load")
        return None

    try:
        wait_exact_time(driver, context)
    except TimeoutException:
        logging.error("Timed out waiting for exact time")
        return None

    # 3. Solicitar cita:
    selection_result = office_selection(driver, context)
    if selection_result is None:
        return None

    # 4. Contact info:
    return phone_mail(driver, context)
