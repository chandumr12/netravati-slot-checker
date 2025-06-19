import os
import platform
import re
import time
import logging
import smtplib
from datetime import datetime
from email.mime.text import MIMEText

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType

# ─── CONFIGURE LOGGING ──────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s %(message)s",
    datefmt="%H:%M:%S",
    level=logging.INFO
)

# ─── DETECT CHROME BINARY ───────────────────────────────────────────────────────
if "GITHUB_ACTIONS" in os.environ:
    # path where setup-chrome@v1 installs Chromium
    DEFAULT_CHROME = "/opt/hostedtoolcache/setup-chrome/chromium/stable/x64/chrome"
elif platform.system() == "Darwin":
    # default macOS Chrome path
    DEFAULT_CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
else:
    # fallback for Linux
    DEFAULT_CHROME = "/usr/bin/chromium-browser"

CHROME_BINARY = os.environ.get("CHROME_BINARY", DEFAULT_CHROME)

# ─── CREDENTIALS ────────────────────────────────────────────────────────────────
SENDER_EMAIL   = os.environ.get("GMAIL_EMAIL", "")
APP_PASSWORD   = os.environ.get("GMAIL_APP_PASSWORD", "")
RECEIVER_EMAIL = SENDER_EMAIL

def send_email(subject: str, body: str):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From']    = SENDER_EMAIL
    msg['To']      = RECEIVER_EMAIL
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(SENDER_EMAIL, APP_PASSWORD)
        server.send_message(msg)

def check_availability():
    # 1) Setup headless Chrome
    options = Options()
    options.binary_location = CHROME_BINARY
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--remote-allow-origins=*")

    # 2) Install matching ChromeDriver for Google Chrome
    service = Service(
        ChromeDriverManager(chrome_type=ChromeType.GOOGLE).install(),
        start_timeout=180
    )
    driver = webdriver.Chrome(service=service, options=options)
    wait   = WebDriverWait(driver, 15)

    try:
        t0 = time.perf_counter()
        driver.get("https://aranyavihaara.karnataka.gov.in")
        logging.info(f"Loaded homepage in {time.perf_counter()-t0:.1f}s")

        # 3) Select District
        t0 = time.perf_counter()
        dd = wait.until(EC.presence_of_element_located((By.ID, "district")))
        Select(dd).select_by_visible_text("ಚಿಕ್ಕಮಗಳೂರು")
        logging.info(f"Selected district in {time.perf_counter()-t0:.1f}s")

        # 4) Select Trek by value
        t0 = time.perf_counter()
        td = wait.until(EC.element_to_be_clickable((By.ID, "trek")))
        Select(td).select_by_value("113")
        logging.info(f"Selected trek in {time.perf_counter()-t0:.1f}s")

        # 5) Pick Date 28
        t0 = time.perf_counter()
        date_input = wait.until(EC.element_to_be_clickable((By.ID, "check_in")))
        date_input.click()
        day_cell = wait.until(EC.element_to_be_clickable((
            By.XPATH, "//td[not(contains(@class,'disabled')) and normalize-space()='28']"
        )))
        day_cell.click()
        logging.info(f"Picked date in {time.perf_counter()-t0:.1f}s")

        # 6) Click “Check Availability”
        t0 = time.perf_counter()
        check_btn = wait.until(EC.element_to_be_clickable((By.ID, "check_avail")))
        check_btn.click()
        logging.info(f"Clicked check button in {time.perf_counter()-t0:.1f}s")

        # 7) Wait for slot elements
        t0 = time.perf_counter()
        slots = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "available_text")))
        logging.info(f"Slots appeared in {time.perf_counter()-t0:.1f}s")

        # 8) Parse slot counts
        t0 = time.perf_counter()
        total_avail = total_cap = 0
        for slot in slots:
            m = re.search(r'(\d+)\s*/\s*(\d+)', slot.text.strip())
            if m:
                total_avail += int(m.group(1))
                total_cap   += int(m.group(2))
        logging.info(f"Parsed {len(slots)} slots in {time.perf_counter()-t0:.1f}s")

        # 9) Build & send email
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        if total_avail > 0:
            subject = f"🎉 Slots Available: {total_avail}/{total_cap}"
            body    = (
                f"Hey Chandu,\n\n"
                f"{total_avail}/{total_cap} slots open for Netravati on 28 June.\n"
                f"Book: https://aranyavihaara.karnataka.gov.in\n\n"
                f"Checked at: {now}"
            )
        else:
            subject = "ℹ️ No Slots Available for Netravati"
            body    = (
                f"Hey Chandu,\n\n"
                f"No slots (0/{total_cap}) available for Netravati on 28 June.\n"
                f"Next check at: {now}\n"
                f"https://aranyavihaara.karnataka.gov.in"
            )
        send_email(subject, body)
        logging.info(f"Sent email → {subject}")

    except Exception as e:
        logging.error(f"Error: {type(e).__name__} – {e}")

    finally:
        driver.quit()

if __name__ == "__main__":
    check_availability()
