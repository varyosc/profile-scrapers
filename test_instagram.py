import os
import time
from typing import List

from PIL import Image
from dotenv import load_dotenv
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.expected_conditions import element_to_be_clickable
from selenium.webdriver.support.ui import WebDriverWait

from utils import generate_file, use_driver


def get_profile(users: List[str], post_count, driver=None):
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

        bio = driver.find_element(By.XPATH, f"//section[@class='{bio_class}']").get_attribute("innerText")
        image_path = f"{user_id}.png"
        image_url = (driver.find_element(
            By.XPATH,
            f"""//img[@alt="{profile_photo_elm}"]""")
                     .get_attribute("src"))
        try:
            (WebDriverWait(driver, 3)
             .until(EC.presence_of_element_located(
                (By.XPATH,
                "//div[@class='_aagv']/img"))))
            print(f"Gettin {user_id}'s posts")
            posts = driver.find_elements(
                By.XPATH,
                "//div[@class='_aagv']/img")
            post_alts = []
        except NoSuchElementException:
            print(f"{user_id} has no posts or none found")
        else:
            # Reset the post to get the amount you want than, get them
            posts = posts[:post_count]
            for i, img in enumerate(posts):
                WebDriverWait(driver, 6).until(EC.element_to_be_clickable(img))
                img.screenshot(f"p{i}_{image_path}")
                post_alts.append(img.get_attribute("alt"))
        if "https" in image_url:
            try:
                driver.get(image_url)
                WebDriverWait(driver, 4).until(EC.presence_of_element_located((By.XPATH, "//body/img")))
                picture = driver.find_element(By.XPATH, "body/img")
                picture.screenshot(image_path)

                with Image.open(image_path) as img:
                    img = img.resize((400, 400))
                    img.save(image_path)

            except Exception as e:
                print(f"Failed to take or resize screenshot: {e}")

        generate_file(
            user_id,
            file_name,
            [image_path, bio, True])
    driver.quit()


def login(users: List[str], post_count: int):
    load_dotenv()

    username = os.getenv("INSTAGRAM_USERNAME")
    password = os.getenv("PASSWORD")

    driver = use_driver()
    url = "https://www.instagram.com/accounts/login/"

    print("Waiting for page to load...")

    try:
        # Open the webpage
        driver.get(url)

        if driver.current_url == url:
            # Login to instagram
            username_field = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.NAME, "username"))
            )
            username_field.send_keys(username)

            password_field = WebDriverWait(driver, 2).until(
                EC.presence_of_element_located((By.NAME, "password"))
            )
            password_field.send_keys(password)

            login_button = WebDriverWait(driver, 1).until(
                EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']"))
            )
            login_button.click()

            WebDriverWait(driver, 10).until(EC.url_changes(url))

            current_url = driver.current_url
            if "https://www.instagram.com/auth_platform/codeentry" in current_url:
                print("On the verification page, waiting longer...")
                WebDriverWait(driver, 120).until(EC.url_changes(current_url))

        print("Getting user's profile...")
        get_profile(users, post_count, driver)
    except Exception as e:
        print(f"Error waiting for the page to load: {e}")
        driver.quit()
        exit()

login(['tomcruise'], 3)