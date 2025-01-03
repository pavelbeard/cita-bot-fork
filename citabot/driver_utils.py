import json
import logging
import random
from contextlib import contextmanager
from typing import Any, Dict, Optional

from fake_useragent import UserAgent
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.webdriver import WebDriver as Chrome
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.webdriver import WebDriver as Firefox
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

from citabot.constants import LIVE_PROXIES
from citabot.types import BrowserConfig, Browsers, CustomerProfile


class DriverBuilder:
    DEFAULT_PDF_SETTINGS = {
        "recentDestinations": [{"id": "Save as PDF", "origin": "local", "account": ""}],
        "selectedDestinationId": "Save as PDF",
        "version": 2,
    }
    
    # headers
    CHROME_HEADERS = {
        "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
    }

    counter = 0
    driver = None

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

        # disable detection
        options.add_argument("--incognito")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option(
            "excludeSwitches", ["enable-automation", "enable-logging"]
        )
        options.add_experimental_option("useAutomationExtension", False)

        # configure security and performance
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--ignore-ssl-errors")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        # caps
        caps = DesiredCapabilities.CHROME
        caps["goog:loggingPrefs"] = {"performance": "ALL"}
        

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

        # disable detection
        options.set_preference("dom.webdriver.enabled", False)
        options.set_preference("useAutomationExtension", False)
        options.set_preference("devtools.jsonview.enabled", False)
        options.set_preference("browser.privatebrowsing.autostart", True)

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
                DriverBuilder.driver = Chrome(
                    options=options,
                    service=service if self.config.driver_path else None,
                )

                # Additional code to modify navigator.webdriver property
                DriverBuilder.driver.execute_cdp_cmd(
                    "Page.addScriptToEvaluateOnNewDocument",
                    {
                        "source": """
                        Object.defineProperty(navigator, 'webdriver', {
                            get: () => undefined
                        })
                    """
                    },
                )

                # set user agent
                DriverBuilder.driver.execute_cdp_cmd(
                    "Network.setUserAgentOverride",
                    {"userAgent": DriverBuilder.user_agent()},
                )

            elif self.browser_type == Browsers.FIREFOX:
                options = self.configure_firefox_options()
                service = FirefoxService(
                    executable_path=self.config.driver_path
                    if self.config.driver_path
                    else None
                )
                DriverBuilder.driver = Firefox(
                    options=options,
                    service=service if self.config.driver_path else None,
                )

                # Additional code to modify navigator.webdriver property
                DriverBuilder.driver.execute_script(
                    "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
                )

            DriverBuilder.driver.maximize_window()

            return DriverBuilder.driver
        except Exception as e:
            logging.error("Failed to build driver: %s", str(e))
            return None

    @contextmanager
    def create_driver(self):
        """Create a new driver instance."""
        try:
            driver = self.build()
            self.driver = DriverBuilder.driver
            yield driver
        finally:
            if self.driver:
                try:
                    self.driver.quit()
                except Exception as e:
                    logging.error("Error while closing driver: %s", str(e))

    def __enter__(self):
        if not DriverBuilder.driver:
            DriverBuilder.driver = self.build()
            return DriverBuilder.driver
        else:
            return DriverBuilder.driver

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is not None:
            DriverBuilder.driver.quit()
        
        return True
                
