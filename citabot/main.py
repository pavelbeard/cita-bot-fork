import asyncio
import io
import logging
import os
from typing import Any, Dict

from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.webdriver import WebDriver as Chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.webdriver import WebDriver as Firefox
from telegram import Update

from citabot.constants import CYCLES
from citabot.driver_utils import DriverBuilder, WebDriverErrorHandler
from citabot.exceptions import (
    FastForwardInaccessibleException,
    RejectionURLException,
    TooManyRequestsException,
)
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
from citabot.types import (
    CustomerProfile,
    InitPageTool,
    OperationConfig,
    OperationType,
    Province,
)
from citabot.utils import (
    Watcher,
    body_text,
    implicit_random_wait,
    wait_exact_time,
    wait_for_element,
)

__all__ = [
    "CustomerProfile",
    "OperationType",
    "Province",
    "CitaBot",
]


class CitaBot:
    # special cases for some provinces
    SPECIAL_PROVINCES = {
        Province.BARCELONA: OperationConfig(
            category="icpplustieb", param="tramiteGrupo[0]"
        ),
        Province.ALICANTE: OperationConfig(category="icpco", param="tramiteGrupo[1]"),
        Province.ILLES_BALEARS: OperationConfig(
            category="icpco", param="tramiteGrupo[1]"
        ),
        Province.LAS_PALMAS: OperationConfig(category="icpco", param="tramiteGrupo[1]"),
        Province.S_CRUZ_TENERIFE: OperationConfig(
            category="icpco", param="tramiteGrupo[1]"
        ),
        Province.MADRID: OperationConfig(
            category="icpplustiem", param="tramiteGrupo[1]"
        ),
        Province.MÁLAGA: OperationConfig(category="icpco", param="tramiteGrupo[0]"),
        Province.MELILLA: OperationConfig(category="icpplus", param="tramiteGrupo[1]"),
        Province.SEVILLA: OperationConfig(category="icpplus", param="tramiteGrupo[1]"),
    }

    def __init__(self, context: CustomerProfile, update: Update = None):
        self.update = update
        self.context = context
        self.driver = None

        confirmed_cita.update(
            {
                "doc_value": context.doc_value,
            }
        )

    def _get_operation_config(self) -> OperationConfig:
        """Get operation config based on the province"""
        if self.context.province in self.SPECIAL_PROVINCES:
            return self.SPECIAL_PROVINCES[self.context.province]
        else:
            return OperationConfig(category="icpplus", param="tramiteGrupo[1]")

    async def _handle_success(self, data: Dict[str, Any]) -> None:
        await self.update.effective_message.reply_text("🎉 CITA CONFIRMADA !!!!")

        # if there is a screenshot, send it
        if data.get("screenshot"):
            image_file = io.BytesIO(data.get("screenshot"))
            image_file.name = "cita-confirmada.png"
            image_file.seek(0)
            await self.update.effective_message.reply_photo(photo=image_file)

        # send confirmation message
        if code := data.get("code"):
            await self.update.effective_message.reply_text(
                f"Codigo de confirmacion: {code}"
            )

    async def start(self, cycles: int = CYCLES) -> bool | None:
        update = self.update
        context = self.context

        logging.basicConfig(
            format="%(asctime)s - %(message)s",
            level=logging.INFO,
            **context.log_settings,
        )

        # clear any sms message if exists in the hook
        if context.sms_webhook_token:
            delete_message(context.sms_webhook_token)

        # get operation config and urls
        config = self._get_operation_config()
        fast_forward_url, fast_forward_url2 = config.get_urls(
            context.province.value, context.operation_code.value
        )

        with DriverBuilder(context) as driver:
            self.driver = driver
            error_handler = WebDriverErrorHandler(driver=self.driver)

            for i in range(cycles):
                try:
                    logging.info(f"\033[33m[Attempt: {i + 1}/{CYCLES}]\033[0m")
                    logging.info(
                        f"🔄 Trying to catch cita en {context.province}. Attempt {i + 1}/{CYCLES}"
                    )

                    result = await self.cycle_cita(
                        driver,
                        context,
                        fast_forward_url,
                        fast_forward_url2,
                        config.category,
                        error_handler,
                    )

                    if result:
                        logging.info("🎉 Application confirmed !!!!")
                        await update.effective_message.reply_text(
                            "🎉 CITA CONFIRMADA !!!!"
                        )

                        data = {**confirmed_cita}
                        if data.get("screenshot"):
                            image_file = io.BytesIO(data.get("screenshot"))
                            image_file.name = "cita-confirmada.png"
                            image_file.seek(0)
                            await update.effective_message.reply_photo(photo=image_file)
                        await update.effective_message.reply_text(
                            f"Codigo de confirmacion: {data.get('code')}"
                        )

                        return True

                except KeyboardInterrupt:
                    logging.error("Keyboard interrupt")
                    await update.effective_message.reply_text("Terminando...")
                    error_handler.cleanup_orphaned_processes()
                    logging.info("Driver closed")
                    await update.effective_message.reply_text("Terminado.")
                    raise
                except asyncio.CancelledError:
                    logging.info("Cancelling...")
                    await update.effective_message.reply_text("Cancelando...")
                    error_handler.cleanup_orphaned_processes()
                    logging.info("Driver closed")
                    await update.effective_message.reply_text("Cancelado.")
                    raise
                except Exception as e:
                    logging.error(
                        f"Something went wrong... Comprueba el bot... 😔. {str(e)}",
                        exc_info=True,
                    )
                    await update.effective_message.reply_text(
                        "Something went wrong... Comprueba el bot... 😔"
                    )
                    raise

    async def _get_page(
        self,
        driver: Chrome | Firefox,
        context: CustomerProfile,
        fast_forward_url: str,
        fast_forward_url2: str,
        operation_category: str,
        init_page_tool: InitPageTool = InitPageTool.FAST_FORWARD,
    ):
        try:
            if init_page_tool == InitPageTool.WATCHER:
                watcher = Watcher(driver)
                await watcher.open_extranjeria()
                await asyncio.sleep(2)
                await watcher.select_city(context.province.value, operation_category)
                await asyncio.sleep(2)
                await watcher.accept_cookie()
                await asyncio.sleep(2)
                implicit_random_wait(driver, seconds=2)
                await watcher.select_tramite(context.operation_code.value)

                logging.info("[Watcher] Loaded initial page.")

                return True

            elif init_page_tool == InitPageTool.FAST_FORWARD:
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
                        raise FastForwardInaccessibleException

                    context.first_load = False

                    logging.info("[Fast forward] Loaded initial page.")
                    return True

        except FastForwardInaccessibleException:
            return False
        except TimeoutException:
            raise WebDriverException
        except TooManyRequestsException:
            raise
        except RejectionURLException:
            raise

    async def get_page(
        self,
        driver: Chrome | Firefox,
        context: CustomerProfile,
        fast_forward_url: str,
        fast_forward_url2: str,
        operation_category: str,
    ):
        """Handles the initial page loading with different tools."""
        if fast_forward_result := await self._get_page(
            driver,
            context,
            fast_forward_url,
            fast_forward_url2,
            operation_category,
            InitPageTool.FAST_FORWARD,
        ):
            return fast_forward_result

        if watcher_result := await self._get_page(
            driver,
            context,
            fast_forward_url,
            fast_forward_url2,
            operation_category,
            InitPageTool.WATCHER,
        ):
            return watcher_result

    async def cycle_cita(
        self,
        driver: Chrome | Firefox,
        context: CustomerProfile,
        fast_forward_url: str,
        fast_forward_url2: str,
        operation_category: str,
        error_handler: WebDriverErrorHandler,
    ):
        """Executes the cycle of the bot."""

        @error_handler.handle_error
        async def execute(
            driver=driver,
            context=context,
            fast_forward_url=fast_forward_url,
            fast_forward_url2=fast_forward_url2,
            operation_category=operation_category,
        ):
            await self.get_page(
                driver=driver,
                context=context,
                fast_forward_url=fast_forward_url,
                fast_forward_url2=fast_forward_url2,
                operation_category=operation_category,
            )

            # 1. Instructions page:
            logging.info("[Step 1/6] Instructions page")
            if not wait_for_element(driver, (By.ID, "btnEntrar"), 10):
                logging.error("Timed out waiting for Instructions page to load")
                return None

            if (
                os.environ.get("CITA_TEST")
                and context.operation_code == OperationType.TOMA_HUELLAS
            ):
                logging.info("Instructions page loaded")
                return True

            driver.find_element(By.ID, "btnEntrar").send_keys(Keys.ENTER)
            # 2. Personal info
            logging.info("[Step 2/6] Personal info")
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

            if not wait_for_element(driver, (By.ID, "btnConsultar"), 5):
                logging.error("Timed out waiting for Solicitar page to load")
                return None

            if not wait_exact_time(driver, context):
                logging.error("Timed out waiting for exact time")
                return None

            # 3. Solicitar cita:
            selection_result = office_selection(driver, context)
            if selection_result is None:
                return None

            # 4. Contact info:
            return phone_mail(driver, context)

        result = await execute(
            driver=driver,
            context=context,
            fast_forward_url=fast_forward_url,
            fast_forward_url2=fast_forward_url2,
            operation_category=operation_category,
        )
        return result