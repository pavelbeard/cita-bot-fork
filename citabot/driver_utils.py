import asyncio
import json
import logging
import random
from contextlib import contextmanager, suppress
from functools import wraps
from typing import Any, Dict, Optional

import psutil
import urllib3
from fake_useragent import UserAgent
from selenium.common.exceptions import (
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.webdriver import WebDriver as Chrome
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.webdriver import WebDriver as Firefox

from citabot.constants import LIVE_PROXIES
from citabot.exceptions import RejectionURLException, TooManyRequestsException
from citabot.types import BrowserConfig, Browsers, CustomerProfile
from citabot.utils import handle_blocking_situations


class DriverBuilder:
    DEFAULT_PDF_SETTINGS = {
        "recentDestinations": [{"id": "Save as PDF", "origin": "local", "account": ""}],
        "selectedDestinationId": "Save as PDF",
        "version": 2,
    }

    def __init__(
        self,
        context: CustomerProfile,
        config: Optional[BrowserConfig] = None,
        browser_type: Browsers = Browsers.FIREFOX,
        additional_options: Optional[Dict[str, Any]] = None,
    ):
        self.context = context
        self.config = config or BrowserConfig(
            driver_path=context.driver_path,
            proxy=context.proxy,
        )
        self.browser_type = browser_type
        self.driver = None
        self._user_agent = None
        self.additional_options = additional_options

    @staticmethod
    def user_agent() -> UserAgent:
        ua = UserAgent().random
        _user_agent = ua
        logging.warning(
            f"\033[1;32m[User Agent] Applying new user agent: {_user_agent}\033[0m"
        )

        return _user_agent

    def configure_chrome_options(self) -> ChromeOptions:
        """Configure Chrome specific options."""
        options = ChromeOptions()

        # configure security and performance
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--ignore-ssl-errors")
        options.add_argument("--disable-gpu")

        # set user agent
        options.add_argument("--user-agent=" + DriverBuilder.user_agent())

        if self.config.headless:
            options.add_argument("--headless")

        if self.config.proxy:
            proxy = random.choice(LIVE_PROXIES)
            options.add_argument("--proxy-server=" + proxy)
            logging.info(f"\033[33m[Proxy: {proxy}]\033[0m")

        if self.additional_options:
            for key, value in self.additional_options.items():
                options.add_argument(f"--{key}={value}")

        return options

    def configure_firefox_options(self) -> FirefoxOptions:
        """Configure Firefox specific options."""
        options = FirefoxOptions()

        # configure pdf settings
        options.set_preference(
            "print.print_preview_sticky_settings.appState",
            json.dumps(self.DEFAULT_PDF_SETTINGS),
        )

        # configure download directory
        options.set_preference("browser.download.dir", self.config.download_dir)
        options.set_preference("browser.download.folderList", 2)
        options.set_preference(
            "browser.helperApps.neverAsk.saveToDisk", "application/pdf"
        )

        # configure security and performance
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--ignore-ssl-errors")
        options.add_argument("--disable-gpu")

        # set user agent
        options.set_preference("general.useragent.override", DriverBuilder.user_agent())

        if self.config.headless:
            options.add_argument("--headless")

        # set additional options
        if self.additional_options:
            for key, value in self.additional_options.items():
                options.add_argument(key, value)

        return options

    def build(self) -> Chrome | Firefox:
        try:
            if self.browser_type == Browsers.CHROME:
                options = self.configure_chrome_options()
                service = ChromeService(
                    executable_path=self.config.driver_path
                    if self.config.driver_path
                    else None
                )
                self.driver = Chrome(
                    options=options,
                    service=service if self.config.driver_path else None,
                )
            elif self.browser_type == Browsers.FIREFOX:
                options = self.configure_firefox_options()
                service = FirefoxService(
                    executable_path=self.config.driver_path
                    if self.config.driver_path
                    else None
                )
                self.driver = Firefox(
                    options=options,
                    service=service if self.config.driver_path else None,
                )

            self.driver.execute_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )

            return self.driver
        except Exception as e:
            logging.error("Failed to build driver: %s", str(e))
            return None

    @contextmanager
    def create_driver(self):
        """Create a new driver instance."""
        try:
            driver = self.build()
            yield driver
        finally:
            if self.driver:
                try:
                    self.driver.quit()
                except Exception as e:
                    logging.error("Error while closing driver: %s", str(e))

    def __enter__(self):
        return self.build()

    def __exit__(self, exc_type, exc_value, traceback):
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                logging.error("Error while closing driver: %s", str(e))


class DriverConnectionHandler:
    def __init__(self):
        self.active_driver_pids = set()
        self.active_browser_pids = set()

    def register_driver(self, driver: Chrome | Firefox):
        try:
            if isinstance(driver, Chrome):
                self.active_driver_pids.add(driver.service.process.pid)
            elif isinstance(driver, Firefox):
                self.active_driver_pids.add(driver.service.process.pid)
                self.active_browser_pids.add(driver.caps.get("moz:processID"))

        except Exception as e:
            logging.error(e)

    def cleanup_orphaned_processes(self):
        """Clean up orphaned driver and spawned by him browser processes."""
        # Phase 1: Kill driver processes
        for pid in self.active_driver_pids.copy():
            try:
                process = psutil.Process(pid)
                if process.name() in [
                    "chromedriver",
                    "geckodriver",
                    "undetected_chromedriver",
                ]:
                    logging.info(
                        f"Killing driver process: [{process.pid}]={process.name()}"
                    )
                    process.kill()
                    self.active_driver_pids.remove(pid)
            except psutil.NoSuchProcess:
                pass
            except Exception as e:
                logging.error(e)

        # Phase 2: Kill browser processes
        with suppress(psutil.ZombieProcess):
            for pid in self.active_browser_pids.copy():
                try:
                    process = psutil.Process(pid)
                    if process.name() in [
                        "Google Chrome",
                        "Chromium",
                        "Firefox",
                    ]:
                        logging.info(
                            f"Killing browser process: [{process.pid}]={process.name()}"
                        )
                        process.kill()
                        self.active_browser_pids.remove(pid)
                except psutil.NoSuchProcess:
                    pass
                except Exception as e:
                    logging.error(e)

            # Kill remaining orphaned processes with cmdline --test-type=webdriver
            for process in psutil.process_iter(attrs=["pid", "name", "cmdline"]):
                try:
                    name = process.info["name"]
                    # cmdline = process.info["cmdline"]
                    pid = process.info["pid"]
                    if (
                        name in ["geckodriver", "chromedriver", "firefox"]
                        # and ("--test-type=webdriver" or "--marionette") in cmdline
                    ):
                        logging.info(f"Killing orphaned process: [{pid}]={name}")
                        process.kill()
                except psutil.NoSuchProcess:
                    pass
                except psutil.AccessDenied:
                    pass
                except Exception as e:
                    logging.error(e)


class WebDriverErrorHandler:
    """
    This class is used to handle errors that occur during the execution of a web driver.
    It provides a mechanism to retry the execution of a web driver in case of errors.
    """

    def __init__(
        self,
        driver: Chrome | Firefox,
        max_retries: int = 3,
        base_delay: int = 300,
        max_delay: int = 600,
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.connection_handler = DriverConnectionHandler()
        self.connection_handler.register_driver(driver=driver)

    def _listen_for_blocking_situations(self, driver: Chrome | Firefox):
        for task in asyncio.all_tasks():
            if task.get_name() == "blocking_listener":
                task.cancel()

        asyncio.create_task(
            handle_blocking_situations(driver=driver),
            name="blocking_listener",
        )

    @property
    def cleanup_orphaned_processes(self):
        return self.connection_handler.cleanup_orphaned_processes

    def exponential_backoff(self, attempt: int) -> float:
        """Calculate exponential backoff delay and jitter."""
        delay = min(self.base_delay * (2**attempt), self.max_delay)
        jitter = random.uniform(0, 0.1 * delay)
        return delay + jitter

    def handle_error(self, func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            attempt = 0
            last_exception = None
            driver: Chrome | Firefox = kwargs.get("driver")
            context = kwargs.get("context")

            while attempt < self.max_retries:
                try:
                    function_result = await func(*args, **kwargs)
                    return function_result

                # region: TooManyRequestsException
                except TooManyRequestsException as e:
                    logging.warning(f"Requests limit exceeded on attempt {attempt}")
                    delay = self.exponential_backoff(attempt)
                    logging.info(
                        f"[429 Too Many Requests] Waiting for {delay:.2f} seconds before retry."
                    )
                    await asyncio.sleep(delay)
                    last_exception = e

                except RejectionURLException as e:
                    logging.warning("Rejected URL on attempt {attempt}")

                    if driver and context:
                        new_driver = await self.recover_driver(
                            driver=driver, context=context
                        )
                        kwargs["driver"] = new_driver

                    logging.info("[Rejection URL] Waiting for 3 seconds before retry.")
                    await asyncio.sleep(3)
                    last_exception = e
                # endregion

                except WebDriverException as e:
                    logging.warning(
                        f"WebDriverException occurred on attempt {attempt}: {str(e)}"
                    )
                    logging.error(f"WebDriverException: {e}", exc_info=True)

                    title = driver.title
                    delay = self.exponential_backoff(attempt)
                    await asyncio.sleep(10)

                    if title == "429 Too Many Requests":
                        logging.info(
                            f"[429 Too Many Requests] Waiting for {delay:.2f} seconds before retry."
                        )
                        await asyncio.sleep(delay)

                    if driver and context and title == "Request Rejected":
                        new_driver = await self.recover_driver(
                            driver=driver, context=context
                        )
                        await asyncio.sleep(3)

                    last_exception = e

                except urllib3.exceptions.HTTPError as e:
                    logging.warning(
                        f"Connection with the driver is lost on attempt {attempt}: {str(e)}"
                    )

                    if driver and context:
                        new_driver = await self.recover_driver(
                            driver=kwargs["driver"], context=kwargs["context"]
                        )
                        kwargs["driver"] = new_driver

                    last_exception = e

                except TimeoutException as e:
                    logging.warning(
                        f"TimeoutException occurred on attempt {attempt}: {str(e)}"
                    )
                    logging.error(f"TimeoutException: {e}")
                    last_exception = e

                    attempt += 1

                except Exception as e:
                    logging.error(f"Exception occurred on attempt {attempt}: {str(e)}")
                    logging.error(f"Exception: {e}")
                    last_exception = e

                    attempt += 1

            logging.error(f"Maximum retries exceeded: {last_exception}")
            raise last_exception

        return wrapper

    async def refresh_session(self, driver: Chrome | Firefox):
        try:
            driver.delete_all_cookies()
            driver.execute_script("window.localStorage.clear();")
            driver.execute_script("window.sessionStorage.clear();")

            # new user agent

            ua = DriverBuilder.user_agent()

            if isinstance(driver, Chrome):
                pass
                # driver("--user-agent=" + ua)
            elif isinstance(driver, Firefox):
                pass
                # driver.add("general.useragent.override", ua)

            return driver

        except Exception as e:
            logging.error(e)

    async def recover_driver(
        self,
        driver: Chrome | Firefox,
        context: CustomerProfile,
        config: Optional[BrowserConfig] = None,
        additional_options: Optional[Dict[str, Any]] = None,
    ):
        logging.info("Recovering driver...")

        self.connection_handler.cleanup_orphaned_processes()

        driver = DriverBuilder(
            context=context,
            config=config,
            additional_options=additional_options,
        ).build()

        return driver
