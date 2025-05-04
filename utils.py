import csv
import json
import os
import subprocess

from dotenv import load_dotenv
from selenium import webdriver


def kill_process(process_name):
    """Kill all processes matching process_name."""
    try:
        if os.name == 'nt':  # Windows
            subprocess.call(f'taskkill /f /im {process_name}', stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:  # Unix/Linux/Mac
            subprocess.call(f'pkill -f {process_name}', shell=True)
    except Exception as e:
        print(f"Error killing {process_name}: {e}")


def use_driver():
    """Create an instance of webdriver with our desired settings

    Returns: selenium webdriver
    """
    load_dotenv()
    kill_process("msedge.exe")
    kill_process("msedgedriver.exe")
    options = webdriver.EdgeOptions()
    options.unhandled_prompt_behavior = 'dismiss'
    user_data_path = os.getenv('BROWSER_PROFILE')
    print("driver initialized...")
    options.add_argument(rf"user-data-dir={user_data_path}")
    options.add_argument("--disable-notifications")
    options.add_experimental_option("prefs", {
        "profile.default_content_setting_values.notifications": 2,
        "profile.default_content_setting_values.popups": 0,
    })
    # options.add_argument("--headless")
    # options.add_argument("--disable-gpu")
    # options.add_argument("--no-sandbox")
    driver = webdriver.Edge(options=options)
    return driver


def generate_file(filename: str, content: dict):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(content, f, indent=4, ensure_ascii=False)

