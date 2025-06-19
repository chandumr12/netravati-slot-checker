import re
import time
import smtplib
from datetime import datetime
from email.mime.text import MIMEText

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

# === Email Configuration ===
SENDER_EMAIL   = "chandumr999@gmail.com"
APP_PASSWORD   = "rbynkxvvegaucffy"
RECEIVER_EMAIL = "chandumr999@gmail.com"

def send_email(subject: str, body: str):
    """Generic helper to send an email."""
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From']    = SENDER_EMAIL
    msg['To']      = RECEIVER_EMAIL

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(SENDER_EMAIL, APP_PASSWORD)
        server.send_message(msg)

def check_availability():
    # 1) Setup ChromeDriver
    chrome_options = Options()
    # chrome_options.add_argument("--headless")    # uncomment for headless
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")

    driver = webdriver.Chrome(options=chrome_options)
    wait   = WebDriverWait(driver, 15)

    try:
        driver.get("https://aranyavihaara.karnataka.gov.in")
        print("🌐 Opened homepage")

        # 2) Select District
        dd = wait.until(EC.presence_of_element_located((By.ID, "district")))
        Select(dd).select_by_visible_text("ಚಿಕ್ಕಮಗಳೂರು")
        print("✅ District selected")

        # 3) Select Trek (value=113 → ನೇತ್ರಾವತಿ ಚಾರಣ)
        td = wait.until(EC.element_to_be_clickable((By.ID, "trek")))
        Select(td).select_by_value("113")
        print("✅ Trek selected")

        # 4) Pick Date
        date_input = wait.until(EC.element_to_be_clickable((By.ID, "check_in")))
        date_input.click()
        print("📅 Calendar opened")

        day_cell = wait.until(EC.element_to_be_clickable((
            By.XPATH,
            "//td[not(contains(@class,'disabled')) and normalize-space()='28']"
        )))
        day_cell.click()
        print("✅ Date picked")

        # 5) Click “Check Availability”
        check_btn = wait.until(EC.element_to_be_clickable((By.ID, "check_avail")))
        check_btn.click()
        print("🔍 Check Availability clicked")

        # 6) Parse slot counts
        time.sleep(3)  # wait for results
        slots = driver.find_elements(By.CLASS_NAME, "available_text")

        total_available = 0
        total_capacity  = 0
        for slot in slots:
            text = slot.text.strip()                # e.g. "0/300 ಲಭ್ಯವಿದೆ"
            m = re.search(r'(\d+)\s*/\s*(\d+)', text)
            if m:
                available = int(m.group(1))
                capacity  = int(m.group(2))
                total_available += available
                total_capacity  += capacity

        # 7) Build and send the email
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
