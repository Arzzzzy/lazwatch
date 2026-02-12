import os
import json
import random
import sys
import time
from datetime import datetime
from colorama import Fore, Style, init

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

init()  # Initialize colorama

# Define paths relative to the project root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
PERSIST_SEEN_FILE = os.path.join(DATA_DIR, "seen_items.json")

# Ensure data directory exists
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

def now_iso():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def normalize_title(t: str):
    return ' '.join((t or "").strip().split()).lower()

def load_seen():
    if os.path.exists(PERSIST_SEEN_FILE):
        try:
            with open(PERSIST_SEEN_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_seen(data, log_callback=None):
    try:
        with open(PERSIST_SEEN_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        if log_callback:
            log_callback(f"Failed saving seen file: {e}", "red")

def setup_driver(headless=False, log_callback=None):
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    options.add_argument("--start-maximized")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.implicitly_wait(5)
        return driver
    except Exception as e:
        if log_callback:
            log_callback(f"Failed to initialize WebDriver: {e}", "red")
        return None

def play_alarm(log_callback=None):
    if sys.platform == "win32":
        try:
            import winsound
            winsound.Beep(1000, 1000)
        except Exception:
            if log_callback: log_callback('\a', "yellow")
    else:
        if log_callback: log_callback('\a', "yellow")

def human_like_wait(min_sec=8, max_sec=15, log_callback=None):
    wait_time = random.uniform(min_sec, max_sec)
    if log_callback:
        log_callback(f"Waiting ~{wait_time:.1f} seconds before next check...")
    time.sleep(wait_time)

def human_like_scroll(driver):
    try:
        for _ in range(random.randint(1, 3)):
            scroll_y = random.randint(100, 400)
            driver.execute_script(f"window.scrollBy(0, {scroll_y});")
            time.sleep(random.uniform(0.5, 1.5))
        if random.random() < 0.3:
            driver.execute_script(f"window.scrollBy(0, -{random.randint(50, 150)});")
    except Exception:
        pass