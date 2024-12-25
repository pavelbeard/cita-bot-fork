from selenium.webdriver.firefox.webdriver import WebDriver as Firefox
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options as FirefoxOptions


def test_gecko():
    options = FirefoxOptions()
    options.set_preference(
        "profile",
        "/home/heavycream/snap/firefox/common/.mozilla/firefox/od698swz.selenium/",
    )
    
    service = FirefoxService(
        executable_path="/home/heavycream/Documents/drivers/geckodriver"
    )
    driver = Firefox(
        service=service,
        options=options,
    )
    driver.get("https://www.google.com")
    print(driver.title)


if __name__ == "__main__":
    test_gecko()
