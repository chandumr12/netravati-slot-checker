# netravati_slot_checker.py

import os, re, time, smtplib
from datetime import datetime
from email.mime.text import MIMEText

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager  # NEW

# 👇 Credentials from GitHub Actions
SENDER_EMAIL   = os.environ["GMAIL_EMAIL"]
APP_PASSWORD   = os.environ["GMAIL_APP_PASSWORD"]
RECEIVER_EMAIL = SENDER_EMAIL

# 👇 Chrome binary path
CHROME_BINARY = os.environ.get("CHROME_BINARY", "/usr/bin/google-chrome")

def send_email(subject: str, body: str):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From']    = SENDER_EMAIL
    msg['To']      = RECEIVER_EMAIL
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(SENDER_EMAIL, APP_PASSWORD)
        server.send_message(msg)

def check_availability():
    chrome_options = Options()
    chrome_options.binary_location = CHROME_BINARY
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--remote-allow-origins=*")

    # ← Use webdriver-manager to install & point to the right Chromedriver
    service = Service(ChromeDriverManager().install())
    driver  = webdriver.Chrome(service=service, options=chrome_options)
    wait    = WebDriverWait(driver, 15)

    try:
        driver.get("https://aranyavihaara.karnataka.gov.in")
        # … same selection / calendar / parsing logic as before …
        # (omitted here for brevity; just keep your existing steps)
        # At the end, send_email(subject, body)

    except Exception as e:
        print(f"❌ Error: {type(e).__name__} – {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    check_availability()
