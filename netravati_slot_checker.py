import os
import re
import time
import smtplib
from datetime import datetime
from email.mime.text import MIMEText

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

# === Credentials from GitHub Actions Secrets ===
SENDER_EMAIL   = os.environ["GMAIL_EMAIL"]
APP_PASSWORD   = os.environ["GMAIL_APP_PASSWORD"]
RECEIVER_EMAIL = SENDER_EMAIL

# === Chrome paths from GitHub Actions environment ===
CHROME_BINARY = os.environ.get("CHROME_BINARY", "/usr/bin/chromium-browser")
CHROME_DRIVER = os.environ.get("CHROME_DRIVER", "/usr/bin/chromedriver")

def send_email(subject: str, body: str):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From']    = SENDER_EMAIL
    msg['To']      = RECEIVER_EMAIL
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(SENDER_EMAIL, APP_PASSWORD)
        server.send_message(msg)

def check_availability():
    # Configure headless Chromium
    chrome_options = Options()
    chrome_options.binary_location = CHROME_BINARY
    # Use the new headless mode and disable shared memory to avoid CI issues
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--remote-allow-origins=*")

    # Increase startup timeout in CI
    service = Service(CHROME_DRIVER, start_timeout=120)
    driver  = webdriver.Chrome(service=service, options=chrome_options)
    wait    = WebDriverWait(driver, 15)

    try:
        driver.get("https://aranyavihaara.karnataka.gov.in")
        print("🌐 Opened homepage")

        # 1) Select District (ಚಿಕ್ಕಮಗಳೂರು)
        dd = wait.until(EC.presence_of_element_located((By.ID, "district")))
        Select(dd).select_by_visible_text("ಚಿಕ್ಕಮಗಳೂರು")
        print("✅ District selected")

        # 2) Select Trek by value (113 = ನೇತ್ರಾವತಿ ಚಾರಣ)
        td = wait.until(EC.element_to_be_clickable((By.ID, "trek")))
        Select(td).select_by_value("113")
        print("✅ Trek selected")

        # 3) Open calendar and pick date “28”
        date_input = wait.until(EC.element_to_be_clickable((By.ID, "check_in")))
        date_input.click()
        print("📅 Calendar opened")

        day_cell = wait.until(EC.element_to_be_clickable((
            By.XPATH,
            "//td[not(contains(@class,'disabled')) and normalize-space()='28']"
        )))
        day_cell.click()
        print("✅ Date picked")

        # 4) Click “Check Availability”
        check_btn = wait.until(EC.element_to_be_clickable((By.ID, "check_avail")))
        check_btn.click()
        print("🔍 Check Availability clicked")

        # 5) Parse slot counts
        time.sleep(3)
        slots = driver.find_elements(By.CLASS_NAME, "available_text")
        total_available = total_capacity = 0
        for slot in slots:
            m = re.search(r'(\d+)\s*/\s*(\d+)', slot.text.strip())
            if m:
                total_available += int(m.group(1))
                total_capacity  += int(m.group(2))

        # 6) Build and send email
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        if total_available > 0:
            subject = f"🎉 Slots Available: {total_available}/{total_capacity}"
            body    = (
                f"Hey Chandu,\n\n"
                f"{total_available} of {total_capacity} slots are open for the Netravati trek on 28 June.\n"
                f"Book here: https://aranyavihaara.karnataka.gov.in\n\n"
                f"Checked at: {now}"
            )
        else:
            subject = "ℹ️ No Slots Available for Netravati"
            body    = (
                f"Hey Chandu,\n\n"
                f"No slots are available for the Netravati trek on 28 June (0/{total_capacity}).\n"
                f"Next check at: {now}\n"
                f"Link: https://aranyavihaara.karnataka.gov.in"
            )

        send_email(subject, body)
        print(f"✉️ Email sent: {subject}")

    except Exception as e:
        print(f"❌ Error: {type(e).__name__} – {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    check_availability()
