import csv
import os

from dotenv import load_dotenv
from selenium import webdriver


def use_driver():
    """Create an instance of webdriver with our desired settings

    Returns: selenium webdriver
    """
    load_dotenv()
    options = webdriver.EdgeOptions()
    options.unhandled_prompt_behavior = 'dismiss'
    user_data_path = os.getenv('BROWSER_PROFILE')
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


def generate_file(user_id, file_name: str, content: list):
    with open(file_name, 'a', encoding="utf-8-sig") as file:
        writer = csv.writer(file)
        content.append(user_id)
        writer.writerow(content)
        print("Added profile!")

