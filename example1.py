import json
import os
import sys

from citabot import CustomerProfile, DocType, Office, OperationType, Province, try_cita

if __name__ == "__main__":
    # USE DATA.JSON TO FILL YOUR PERSONAL DATA
    data = json.load(open("data.json"))
    
    if 'doc_value' not in data:
        print("Please add your doc_value in data.json")
        exit(1)
    if 'country' not in data:
        print("Please add your country in data.json")
        exit(1)
    if 'name' not in data:
        print("Please add your name in data.json")
        exit(1)
    if 'phone' not in data:
        print("Please add your phone in data.json")
        exit(1)
    if 'email' not in data:
        print("Please add your email in data.json")
        exit(1)
    if 'year_of_birth' not in data:
        print("Please add your year_of_birth in data.json")
        exit(1)
    
    customer = CustomerProfile(
        anticaptcha_api_key=os.environ.get("ANTICAPTCHA_KEY"),  # Anti-captcha API Key (auto_captcha=False to disable it)
        auto_captcha=True,  # Enable anti-captcha plugin (if False, you have to solve reCaptcha manually and press ENTER in the Terminal)
        auto_office=True,
        chrome_driver_path="/Users/pavelbeard/Documents/Projects/cita_catcher/src/drivers/chromedriver",
        save_artifacts=True,  # Record available offices / take available slots screenshot
        province=Province.ALICANTE, # put your province here
        operation_code=OperationType.RENOVACION_ASILO,
        doc_type=DocType.NIE,  # DocType.NIE or DocType.PASSPORT
        doc_value=data["doc_value"],  # NIE or Passport number, no spaces.
        country=data["country"],
        name=data["name"],  # Your Name
        phone=data["phone"],  # Phone number (use this format, please)
        email=data["email"],  # Email
        year_of_birth=data["year_of_birth"],
        # Offices in order of preference
        # This selects specified offices one by one or a random one if not found.
        # For recogida only the first specified office will be attempted or none
        offices=[Office.BENIDORM, Office.ALICANTE_COMISARIA], # put your offices here
    )
    if "--autofill" not in sys.argv:
        try_cita(context=customer, cycles=200)  # Try 200 times
    else:
        from mako.template import Template

        tpl = Template(
            filename=os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "citabot/template/autofill.mako"
            )
        )
        print(tpl.render(ctx=customer))  # Autofill for Chrome


# In Terminal run:
#   python3 example1.py
# or:
#   python3 example1.py --autofill
