import base64
import io
import logging
import os
import random
import re
import tempfile
import time
from base64 import b64decode
from datetime import datetime as dt
from json import JSONDecodeError
from typing import Dict

import requests
from anticaptchaofficial.imagecaptcha import imagecaptcha
from anticaptchaofficial.recaptchav3proxyless import recaptchaV3Proxyless
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.edge.webdriver import WebDriver as Edge
from selenium.webdriver.safari.webdriver import WebDriver as Safari
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait
from undetected_chromedriver import Chrome

# from undetected_geckodriver import Firefox
from selenium.webdriver.firefox.webdriver import WebDriver as Firefox

from citabot.constants import DELAY, REFRESH_PAGE_CYCLES
from citabot.states import confirmed_cita
from citabot.types import CustomerProfile, OperationType
from citabot.utils import body_text, implicit_random_wait

from .speaker import new_speaker

speaker = new_speaker()


# 5. Cita selection
def cita_selection(driver: Chrome | Firefox | Safari | Edge, context: CustomerProfile):
    resp_text = body_text(driver)

    if "DISPONE DE 5 MINUTOS" in resp_text:
        logging.info("[Step 4/6] Cita attempt -> selection hit!")
        if context.save_artifacts:
            driver.save_screenshot(f"citas-{dt.now()}.png".replace(":", "-"))

        position = find_best_date_slots(driver, context)
        if not position:
            return None

        implicit_random_wait(driver, seconds=2)
        success = process_captcha(driver, context)
        if not success:
            return None

        try:
            driver.find_elements(
                By.CSS_SELECTOR, "input[type='radio'][name='rdbCita']"
            )[position - 1].send_keys(Keys.SPACE)
        except Exception as e:
            logging.error(e)
            pass

        driver.execute_script("envia();")
        implicit_random_wait(driver, seconds=0.5)
        driver.switch_to.alert.accept()
    elif "Seleccione una de las siguientes citas disponibles" in resp_text:
        logging.info("[Step 4/6] Cita attempt -> selection hit!")
        if context.save_artifacts:
            driver.save_screenshot(f"citas-{dt.now()}.png".replace(":", "-"))

        try:
            date_els = driver.find_elements(
                By.CSS_SELECTOR, "#CitaMAP_HORAS thead [class^=colFecha]"
            )
            dates = sorted([*map(lambda x: x.text, date_els)])
            slots: Dict[str, list] = {}
            slot_table = driver.find_element(By.CSS_SELECTOR, "#CitaMAP_HORAS tbody")
            for row in slot_table.find_elements(By.CSS_SELECTOR, "tr"):
                appt_time = row.find_elements(By.TAG_NAME, "th")[0].text
                if context.min_time:
                    if appt_time < context.min_time:
                        continue
                if context.max_time:
                    if appt_time > context.max_time:
                        break

                for idx, cell in enumerate(row.find_elements(By.TAG_NAME, "td")):
                    try:
                        if slots.get(dates[idx]):
                            continue
                        slot = cell.find_element(
                            By.CSS_SELECTOR, "[id^=HUECO]"
                        ).get_attribute("id")
                        slots[dates[idx]] = [slot]
                    except Exception:
                        pass

            best_date = find_best_date(sorted(slots), context)
            if not best_date:
                return None
            slot = slots[best_date][0]

            implicit_random_wait(driver, seconds=2)
            success = process_captcha(driver, context)
            if not success:
                return None

            driver.execute_script(f"confirmarHueco({{id: '{slot}'}}, {slot[5:]});")
            driver.switch_to.alert.accept()
        except Exception as e:
            logging.error(e)
            return None
    else:
        logging.info("[Step 4/6] Cita attempt -> missed selection")
        return None

    # 6. Confirmation
    resp_text = body_text(driver)

    if "Debe confirmar los datos de la cita asignada" in resp_text:
        logging.info("[Step 5/6] Cita attempt -> confirmation hit!")
        if context.current_solver == recaptchaV3Proxyless:
            context.recaptcha_solver.report_correct_recaptcha()

        try:
            sms_verification = driver.find_element(By.ID, "txtCodigoVerificacion")
        except Exception as e:
            logging.error(e)
            sms_verification = None
            pass

        if context.sms_webhook_token:
            if sms_verification:
                code = get_code(context)
                if code:
                    logging.info(f"Received code: {code}")
                    sms_verification = driver.find_element(
                        By.ID, "txtCodigoVerificacion"
                    )
                    sms_verification.send_keys(code)

            confirm_appointment(driver, context)

            if context.save_artifacts:
                driver.save_screenshot(f"FINAL-SCREEN-{dt.now()}.png".replace(":", "-"))

            if context.bot_result:
                driver.quit()
                os._exit(0)
            return None
        else:
            if not sms_verification:
                confirm_appointment(driver, context)

            speaker.say("ENTER THE SHORT CODE FROM SMS")

            logging.info("Press Any button to CLOSE browser")
            input()
            driver.quit()
            os._exit(0)

    else:
        logging.info("[Step 5/6] Cita attempt -> missed confirmation")
        if context.current_solver == recaptchaV3Proxyless:
            context.recaptcha_solver.report_incorrect_recaptcha()
        elif context.current_solver == imagecaptcha:
            context.image_captcha_solver.report_incorrect_image_captcha()

        if context.save_artifacts:
            driver.save_screenshot(
                f"failed-confirmation-{dt.now()}.png".replace(":", "-")
            )
        return None


def get_messages(sms_webhook_token):
    try:
        url = f"https://webhook.site/token/{sms_webhook_token}/requests?page=1&sorting=newest"
        return requests.get(url).json()["data"]
    except JSONDecodeError:
        raise Exception("sms_webhook_token is incorrect")


def delete_message(sms_webhook_token, message_id=""):
    url = f"https://webhook.site/token/{sms_webhook_token}/request/{message_id}"
    requests.delete(url)


def get_code(context: CustomerProfile):
    for i in range(60):
        messages = get_messages(context.sms_webhook_token)
        if not messages:
            time.sleep(5)
            continue

        content = messages[0].get("text_content")
        match = re.search("CODIGO (.*), DE", content)
        if match:
            delete_message(context.sms_webhook_token, messages[0].get("uuid"))
            return match.group(1)

    return None


def add_reason(driver: Chrome, context: CustomerProfile):
    try:
        if context.operation_code == OperationType.SOLICITUD_ASILO:
            element = driver.find_element(By.ID, "txtObservaciones")
            element.send_keys(context.reason_or_type)
    except Exception as e:
        logging.error(e)


def process_captcha(driver: Chrome | Firefox | Safari | Edge, context: CustomerProfile):
    if context.auto_captcha:
        if not context.anticaptcha_api_key:
            logging.error("Anticaptcha API key is empty")
            return None

        if len(driver.find_elements(By.ID, "reCAPTCHA_site_key")) > 0:
            captcha_result = solve_recaptcha(driver, context)
        elif len(driver.find_elements(By.CSS_SELECTOR, "img.img-thumbnail")) > 0:
            captcha_result = solve_image_captcha(driver, context)
        else:
            captcha_result = True

        if not captcha_result:
            return None

    else:
        logging.info(
            "HEY, DO SOMETHING HUMANE TO TRICK THE CAPTCHA (select text, move cursor etc.) and press ENTER"
        )
        for i in range(10):
            speaker.say("ALARM")
        input()

    return True


def solve_recaptcha(driver: Chrome | Firefox | Safari | Edge, context: CustomerProfile):
    if not context.recaptcha_solver:
        site_key = driver.find_element(By.ID, "reCAPTCHA_site_key").get_attribute(
            "value"
        )
        page_action = driver.find_element(By.ID, "action").get_attribute("value")
        logging.info("Anticaptcha: site key: " + site_key)
        logging.info("Anticaptcha: action: " + page_action)

        context.recaptcha_solver = recaptchaV3Proxyless()
        context.recaptcha_solver.set_verbose(1)
        context.recaptcha_solver.set_key(context.anticaptcha_api_key)
        context.recaptcha_solver.set_website_url(
            "https://icp.administracionelectronica.gob.es"
        )
        context.recaptcha_solver.set_website_key(site_key)
        context.recaptcha_solver.set_page_action(page_action)
        context.recaptcha_solver.set_min_score(0.9)

    context.current_solver = type(context.recaptcha_solver)

    g_response = context.recaptcha_solver.solve_and_return_solution()
    if g_response != 0:
        logging.info("Anticaptcha: g-response: " + g_response)
        driver.execute_script(
            f"document.getElementById('g-recaptcha-response').value = '{g_response}'"
        )
        return True
    else:
        logging.error("Anticaptcha: " + context.recaptcha_solver.err_string)
        return None


def solve_image_captcha(
    driver: Chrome | Firefox | Safari | Edge, context: CustomerProfile
):
    if not context.image_captcha_solver:
        context.image_captcha_solver = imagecaptcha()
        context.image_captcha_solver.set_verbose(1)
        context.image_captcha_solver.set_key(context.anticaptcha_api_key)

    context.current_solver = type(context.image_captcha_solver)

    try:
        img = driver.find_elements(By.CSS_SELECTOR, "img.img-thumbnail")[0]
        tmp = tempfile.NamedTemporaryFile(delete=False)
        tmp.write(b64decode(img.get_attribute("src").split(",")[1].strip()))
        tmp.close()

        captcha_result = context.image_captcha_solver.solve_and_return_solution(
            tmp.name
        )
        if captcha_result != 0:
            logging.info("Anticaptcha: captcha text: " + captcha_result)
            element = driver.find_element(By.ID, "captcha")
            element.send_keys(captcha_result)
            return True
        else:
            logging.error("Anticaptcha: " + context.image_captcha_solver.err_string)
            return None
    finally:
        os.unlink(tmp.name)


def find_best_date_slots(
    driver: Chrome | Firefox | Safari | Edge, context: CustomerProfile
):
    try:
        els = driver.find_elements(By.CSS_SELECTOR, "[id^=lCita_]")
        dates = sorted([*map(lambda x: x.text, els)])
        best_date = find_best_date(dates, context)
        if best_date:
            return dates.index(best_date) + 1
    except Exception as e:
        logging.error(e)

    return None


def find_best_date(dates, context: CustomerProfile):
    if not context.min_date and not context.max_date:
        return dates[0]

    pattern = re.compile(r"\d{2}/\d{2}/\d{4}")
    date_format = "%d/%m/%Y"

    for date in dates:
        try:
            found = pattern.findall(date)[0]
            if found:
                appt_date = dt.strptime(found, date_format)
                if context.min_date:
                    if appt_date < dt.strptime(context.min_date, date_format):
                        continue
                if context.max_date:
                    if appt_date > dt.strptime(context.max_date, date_format):
                        continue

                return date
        except Exception as e:
            logging.error(e)
            continue

    logging.info(
        f"Nothing found for dates {context.min_date} - {context.max_date}, {context.min_time} - {context.max_time}, skipping"
    )
    return None


def select_office(driver: Chrome | Firefox | Safari | Edge, context: CustomerProfile):
    if not context.auto_office:
        speaker.say("MAKE A CHOICE")
        logging.info("Select office and press ENTER")
        input()
        return True
    else:
        el = driver.find_element(By.ID, "idSede")
        select = Select(el)
        if context.save_artifacts:
            offices_path = os.path.join(
                os.getcwd(), f"offices-{dt.now()}.html".replace(":", "-")
            )
            with io.open(offices_path, "w", encoding="utf-8") as f:
                f.write(el.get_attribute("innerHTML"))

        if context.offices:
            for office in context.offices:
                try:
                    select.select_by_value(office.value)
                    return True
                except Exception as e:
                    logging.error(e)
                    if context.operation_code == OperationType.RECOGIDA_DE_TARJETA:
                        return None

        for i in range(5):
            options = list(
                filter(lambda o: o.get_attribute("value") != "", select.options)
            )
            default_count = len(select.options)
            first_element = 0 if len(options) == default_count else 1
            select.select_by_index(random.randint(first_element, default_count - 1))
            if el.get_attribute("value") not in context.except_offices:  # type: ignore
                return True
            continue

        return None


def office_selection(
    driver: Chrome | Firefox | Safari | Edge, context: CustomerProfile
):
    driver.execute_script("enviar('solicitud');")

    for i in range(REFRESH_PAGE_CYCLES):
        resp_text = body_text(driver)

        if "Seleccione la oficina donde solicitar la cita" in resp_text:
            logging.info("[Step 2/6] Office selection")

            # Office selection:
            implicit_random_wait(driver, seconds=0.3)
            try:
                WebDriverWait(driver, DELAY).until(
                    EC.presence_of_element_located((By.ID, "btnSiguiente"))
                )
            except TimeoutException:
                logging.error("Timed out waiting for offices to load")
                return None

            res = select_office(driver, context)
            if res is None:
                implicit_random_wait(driver, seconds=5)
                driver.refresh()
                continue

            btn = driver.find_element(By.ID, "btnSiguiente")
            btn.send_keys(Keys.ENTER)
            return True
        elif "En este momento no hay citas disponibles" in resp_text:
            implicit_random_wait(driver, seconds=5)
            driver.refresh()
            continue
        else:
            logging.info("[Step 2/6] Office selection -> No offices")
            return None


def phone_mail(driver: Chrome | Firefox | Safari | Edge, context: CustomerProfile):
    try:
        WebDriverWait(driver, DELAY).until(
            EC.presence_of_element_located((By.ID, "txtTelefonoCitado"))
        )
        logging.info("[Step 3/6] Contact info")
    except TimeoutException:
        logging.error("Timed out waiting for contact info page to load")
        return None

    element = driver.find_element(By.ID, "txtTelefonoCitado")
    element.send_keys(context.phone)

    try:
        element = driver.find_element(By.ID, "emailUNO")
        element.send_keys(context.email)

        element = driver.find_element(By.ID, "emailDOS")
        element.send_keys(context.email)
    except Exception:
        pass

    add_reason(driver, context)

    driver.execute_script("enviar();")

    return cita_selection(driver, context)


def confirm_appointment(
    driver: Chrome | Firefox | Safari | Edge, context: CustomerProfile
):
    driver.find_element(By.ID, "chkTotal").send_keys(Keys.SPACE)
    driver.find_element(By.ID, "enviarCorreo").send_keys(Keys.SPACE)

    btn = driver.find_element(By.ID, "btnConfirmar")
    btn.send_keys(Keys.ENTER)

    resp_text = body_text(driver)
    ctime = dt.now()

    if "CITA CONFIRMADA" in resp_text:
        context.bot_result = True
        code = driver.find_element(By.ID, "justificanteFinal").text
        logging.info(f"[Step 6/6] Justificante cita: {code}")
        if context.save_artifacts:
            image_name = f"CONFIRMED-CITA-{ctime}.png".replace(":", "-")
            screenshot = driver.get_screenshot_as_base64(image_name)
            screenshot_b64 = base64.b64decode(screenshot)

            confirmed_cita.update(
                {
                    **confirmed_cita,
                    "code": code,
                    "screenshot": screenshot_b64,
                }
            )
            # TODO: fix saving to PDF
            # btn = driver.find_element(By.ID, "btnImprimir")
            # btn.send_keys(Keys.ENTER)
            # # Give some time to save appointment pdf
            # time.sleep(5)

        return True
    elif "Lo sentimos, el código introducido no es correcto" in resp_text:
        logging.error("Incorrect code entered")
    else:
        error_name = f"error-{ctime}.png".replace(":", "-")
        driver.save_screenshot(error_name)

    return None
