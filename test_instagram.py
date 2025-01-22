import csv
import os
import time
from typing import List

from PIL import Image
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from utils import generate_file, use_driver


def get_profile(users: List[str], driver=webdriver.Chrome()):
    bio_class = "x7a106z x972fbf xcfux6l x1qhh985 xm0m39n x9f619 x78zum5 xdt5ytf x2lah0s xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x1n2onr6 x11njtxf xskmkbu x1pjya6o x14cbv0q x7wvtww x9v3v6d x17eookw x1q548z6"
    picture_class = "xpdipgo x972fbf xcfux6l x1qhh985 xm0m39n xk390pu x5yr21d xdj266r x11i5rnm xat24cr x1mh8g0r xl1xv1r xexx8yu x4uap5 x18d9i69 xkhd6sd x11njtxf xh8yej3"
    file_name = time.strftime("%Y%m%d%H%M%S", time.localtime()) + ".csv"

    for user_id in users:
        if not driver:
            driver = use_driver()

        bio_class = "xc3tme8 x18wylqe x1xdureb x1iom2gc x1vnunu7 x172qv1o xs5motx x69nqbv xywrmq2 x6ikm8r x10wlt62"

        for user_id in users:
            file_name = f"{user_id}.csv"
            profile_photo_elm = f"{user_id}'s profile picture"
            url = f'https://www.instagram.com/{user_id}/'

            # Navigate to the Instagram page
            driver.get(url)

            print("Waiting for page to load...")

            try:
                # Wait until the profile image is loaded
                WebDriverWait(driver, 60).until(
                    EC.presence_of_element_located((
                        By.XPATH, f"""//img[@alt="{profile_photo_elm}"]"""))
                )
                print("Page loaded successfully!")
            except TimeoutError as e:
                print(f"Error waiting for the page to load", e)
                driver.quit()
                exit()

            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')

            # Extract bio from section
            bio = soup.find("section", {"class": f"{bio_class}"}).text
            image_path = f"{user_id}.png"
            image_url = soup.find('img', alt=profile_photo_elm).get("src") if (
                soup.find('img', alt=profile_photo_elm)) else "Image not found"
            if "https" in image_url:
                try:
                    driver.get(image_url)
                    time.sleep(1)
                    driver.save_screenshot(image_path)

                    with Image.open(image_path) as img:
                        img = img.resize((400, 400))
                        img.save(image_path)

                except Exception as e:
                    print(f"Failed to take or resize screenshot: {e}")

            try:
                posts = driver.find_elements(
                    By.XPATH,
                    fr"//_aagv/img")
            except NoSuchElementException:
                print(f"{user_id} has no posts or none found")
            else:
                for img in posts:
                    img.screenshot(f"{image_path}_{img.alt}")
                    print("do stuffs with", img)
                    continue

            generate_file(user_id, file_name, [user_id, image_path, bio])
        driver.quit()


users = ["tomcruise"]
load_dotenv()

username = os.getenv("INSTAGRAM_USERNAME")
password = os.getenv("PASSWORD")

print(username)
driver = webdriver.Chrome()
url = "https://www.instagram.com/accounts/login/"

print("Waiting for page to load...")

try:
    # Open the webpage
    driver.get(url)

    if driver.current_url == url:
        # Login to instagram
        username_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "username"))  # Adjust selector as needed
        )
        username_field.send_keys(username)

        password_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "password"))  # Adjust selector as needed
        )
        password_field.send_keys(password)

        login_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']"))  # Adjust selector as needed
        )
        login_button.click()

        WebDriverWait(driver, 10).until(EC.url_changes(url))

        # Check if the URL contains the specific text
        current_url = driver.current_url
        if "https://www.instagram.com/auth_platform/codeentry" in current_url:
            print("On the verification page, waiting longer...")
            WebDriverWait(driver, 120).until(EC.url_changes(current_url))

    print("Getting user's profile...")
    get_profile(users, driver)
except Exception as e:
    print(f"Error waiting for the page to load: {e}")
    driver.quit()
    exit()
