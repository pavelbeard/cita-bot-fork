from contextlib import suppress
import time
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
            if (
                process.name() == "Google Chrome"
                and "--test-type=webdriver" in process.cmdline()
            ):
                with suppress(psutil.NoSuchProcess):
                    print(process.cmdline())
                    process.kill()
                    return


def test_proxies():
    from selenium.webdriver.chrome.webdriver import WebDriver as Chrome
    from selenium.webdriver.chrome.options import Options as ChromeOptions

    options = ChromeOptions()

    proxies = [
        "51.79.170.92:80",
        "87.248.129.32:80",
        "109.236.83.153:8888",
        "103.152.112.120:80",
        "23.247.136.252:80",
        "178.48.68.61:18080",
        "159.65.230.46:8888",
        "143.110.232.177:80",
        "82.102.10.253:80",
        "102.50.248.123:9172",
        "157.254.53.50:80",
        "159.65.221.25:80",
        "149.202.91.219:80",
        "147.135.128.218:80",
        "168.119.53.93:80",
        "158.255.77.166:80",
        "51.158.169.52:29976",
        "85.115.112.178:8197",
        "108.7.232.77:3128",
        "152.26.229.52:9443",
        "143.42.191.48:80",
        "209.97.150.167:3128",
        "147.182.180.242:80",
        "89.179.112.252:5678",
        "72.10.164.178:11341",
        "130.255.76.106:80",
        "185.105.102.179:80",
        "89.145.162.81:3128",
        "176.31.110.126:45517",
        "162.223.90.130:80",
        "154.90.48.76:80",
        "188.40.59.208:3128",
        "103.152.112.157:80",
        "178.128.113.118:23128",
        "217.182.210.152:80",
        "45.128.135.249:1080",
        "185.105.102.189:80",
        "38.242.199.124:8089",
        "47.89.184.18:3128",
        "78.28.152.111:80",
        "194.182.178.90:3128",
        "135.181.154.225:80",
        "116.203.139.209:8081",
        "245.166.239.171:8080",
        "198.49.68.80:80",
        "51.89.255.67:80",
        "213.14.32.74:4153",
        "213.14.32.67:4153",
        "213.74.223.69:4153",
        "185.170.233.103:47574",
        "213.6.68.94:5678",
        "213.74.223.77:4153",
        "213.16.81.182:35559",
        "162.241.46.6:64353",
        "217.27.149.190:4153",
        "5.8.240.93:4153",
        "213.149.156.87:5678",
        "165.140.185.179:39593",
        "195.140.226.32:5678",
        "234.35.16.231:8080",
        "154.73.28.49:8080",
        "39.101.65.228:3132",
        "194.28.224.123:8080",
        "158.255.77.168:80",
        "45.117.31.217:58080",
        "37.110.130.223:8081",
        "38.156.73.148:8080",
    ]

    for proxy in proxies:
        try:
            options.add_argument("--proxy-server=" + proxy)
            driver = Chrome(
                options=options,
            )

            driver.get(
                "https://icp.administracionelectronica.gob.es/icpplus/index.html"
            )

            time.sleep(1)
            if driver.title == "Proceso automático para la solicitud de cita previa":
                with open("live_proxies.txt", "a") as f:
                    f.write(proxy + "\n")

                print(f"Proxy {proxy} is live")
            else:
                raise
        except Exception:
            print(f"Error with proxy {proxy}. Skipping...")
        finally:
            driver.quit()


def test_webdriver_detection():
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options

    chrome_options = Options()
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)

    # service = Service("/Users/pavelbeard/Documents/drivers/chromedriver")
    driver = webdriver.Chrome(options=chrome_options)

    # Additional code to modify navigator.webdriver property
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {
            "source": """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            })
        """
        },
    )

    # Your automation code here
    driver.get("https://intoli.com/blog/not-possible-to-block-chrome-headless/chrome-headless-test.html")
    time.sleep(10)
    driver.quit()
    
    


if __name__ == "__main__":
    test_webdriver_detection()
