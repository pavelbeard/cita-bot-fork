from contextlib import suppress
import re
import subprocess
import psutil
from selenium.webdriver.firefox.webdriver import WebDriver as Firefox
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options as FirefoxOptions


def test_gecko():
    options = FirefoxOptions()
    options.set_preference(
        "profile",
        "/Users/pavelbeard/Documents/drivers/geckodriver",
    )

    service = FirefoxService(
        executable_path="/Users/pavelbeard/Documents/drivers/geckodriver",
    )
    driver = Firefox(
        service=service,
        options=options,
    )
    driver.get("https://www.google.com")

    from psutil import Process

    driver_process = Process(driver.service.process.pid)
    browser_process = Process(driver.caps.get("moz:processID"))

    print(driver_process.name())
    print(driver_process.pid)
    print(driver_process.cmdline())

    print(browser_process.name())
    print(browser_process.pid)
    print(browser_process.cmdline())

    driver_process.kill()


def test_chrome():
    from selenium.webdriver.chrome.webdriver import WebDriver as Chrome
    from selenium.webdriver.chrome.service import Service as ChromeService
    from selenium.webdriver.chrome.options import Options as ChromeOptions

    options = ChromeOptions()

    service = ChromeService(
        executable_path="/Users/pavelbeard/Documents/drivers/chromedriver",
    )

    driver = Chrome(
        # service=service,
        options=options,
    )
    driver.get("https://www.google.com")

    from psutil import Process

    driver_process = Process(driver.service.process.pid)

    print(driver_process.name())
    print(driver_process.pid)
    print(driver_process.cmdline())

    

    driver_process.kill()
    
    with suppress(psutil.ZombieProcess):
        for process in psutil.process_iter():
            if process.name() == "Google Chrome" and "--test-type=webdriver" in process.cmdline():
                with suppress(psutil.NoSuchProcess):
                    print(process.cmdline())
                    process.kill()
                    return


if __name__ == "__main__":
    test_chrome()
