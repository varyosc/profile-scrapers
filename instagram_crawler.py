import os
import re
from typing import List

import typer
from PIL import Image
from dotenv import load_dotenv
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from utils import generate_file, use_driver

app = typer.Typer()


@app.command("get")
def get_profile(users: List[str], post_count, driver=None):
    if not driver:
        try:
            driver = use_driver()
        except Exception as e:
            print("Another instance of Your browser is already open \n" + str(e))

    if not post_count:
        try:
            post_count = int(post_count)
        except:
            post_count = 0

    for user_id in users:
        try:
            user_id = str(user_id)
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
                raise TimeoutError(f"Error waiting for the page to load: ", e)

            if driver.find_elements(
                    By.XPATH,
                    "//section[div[div[span]]]"):
                driver.find_element(By.XPATH, "//section[div[div[span]]]//div[@role='button']").click()

            bio = driver.find_element(
                By.XPATH,
                f"//section[div[div[span]]]").text
            user_profile = {
                "userID": user_id,
                "bio": "",
                "image": ""}
            image_path = os.path.join(
                os.getcwd(),
                f"instagram",
                "img",
                f"{user_id}.png")
            image_url = (driver.find_element(
                By.XPATH,
                f"""//img[@alt="{profile_photo_elm}"]""")
                         .get_attribute("src"))
            try:
                WebDriverWait(driver, 4).until(
                    EC.presence_of_element_located(
                        (By.XPATH,
                         "//div[@class='_aagv']/img")))
                print(f"Gettin {user_id}'s posts")
                posts = driver.find_elements(
                    By.XPATH,
                    "//div[@class='_aagv']")
            except Exception as e:
                print(f"{user_id} has no posts or none found\n", e)
            else:
                # Reset the post to get the amount you want than, get them
                posts = posts[:post_count]
                for i, img in enumerate(posts):
                    driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'})", img)
                    post_image = img.find_element(By.XPATH, "./img")
                    WebDriverWait(driver, 18).until(
                        EC.element_to_be_clickable(post_image))
                    post_path = os.path.join(
                        os.getcwd(),
                        f"instagram\\posts\\{user_id}_p{i}.png")
                    img.screenshot(post_path)
            if "https" in image_url:
                try:
                    driver.get(image_url)
                    WebDriverWait(driver, 4).until(
                        EC.presence_of_element_located((By.XPATH, "//body/img")))
                    picture = driver.find_element(By.XPATH, "//body/img")
                    picture.screenshot(image_path)

                    with Image.open(image_path) as img:
                        img = img.resize((400, 400))
                        img.save(image_path)

                except Exception as e:
                    print(f"Failed to take or resize screenshot: {e}")

                user_profile.image = image_path

            else:
                user_profile.image = os.path.join(os.getcwd(), "instagram", "img", "default.png")

                user_profile["image"] = image_path if "https" in image_url else image_url
                user_profile["bio"] = bio
                generate_file(user_id+".json", user_profile)
        except Exception as e:
            driver.quit()
            print(f"error: {e}")


    driver.quit()


@app.command()
def login(users: List[str], post_count: int, should_get = True):
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

        if should_get:
            print("Getting user's profile...")
            return get_profile(users, post_count, driver)
        else:
            return driver
    except Exception as e:
        driver.quit()
        print("error: ", e)


def filter_users(people_count=10,
                 post_count=0,
                 required_attributes=None,
                 normal_attributes=None,
                 optional_attributes=None,
                 banned_attributes=None):
    if post_count:
        try:
            post_count = int(post_count)
        except Exception as e:
            print(f"Failed to parse post count: {e}")
            post_count = 0

    search_index = 0
    user_ids = []
    address = "https://www.google.com/search?q=site:instagram.com%2F"

    if required_attributes:
        required_attributes = [a.strip() for a in required_attributes.split("$")]
        for attribute in required_attributes:
            attribute = attribute.replace(" ", "+")
            address = address + f'+"{attribute}"'

    if normal_attributes:
        normal_attributes = [a.strip() for a in normal_attributes.split("$")]
        for attribute in normal_attributes:
            attribute = attribute.replace(" ", "+")
            address = address + f'+{attribute}'

    if optional_attributes:
        optional_attributes = [a.strip() for a in optional_attributes.split("$")]
        for attribute in optional_attributes:
            attribute = attribute.replace(" ", "+")
            address = address + f'+OR+{attribute}'

    if banned_attributes:
        banned_attributes = [a.strip() for a in banned_attributes.split("$")]
        for attribute in banned_attributes:
            attribute = attribute.replace(" ", "+")
            address = address + f'+-"{attribute}"'

    driver = login([], post_count, should_get=False)

    while people_count > search_index:
        search_address = address + f"&start={search_index}"
        driver.get(search_address)
        try:
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located(
                    (By.XPATH,
                     "//div[@data-snc]"))
            )
        except TimeoutException:
            current_url = driver.current_url
            if "https://www.google.com/sorry/index?continue" in current_url:
                print("On Google robot check page, waiting longer...")
                iframe = driver.find_element(By.XPATH, '//form/div')
                iframe.click()
                WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((
                        By.XPATH,
                        "//body/div/div[./iframe]"))
                )
                iframe = driver.find_element(By.XPATH, "//body/div/div/iframe")
                iframe.click()
                driver.switch_to.frame(iframe)
                WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((
                        By.XPATH,
                        "//div[@class='button-holder help-button-holder']"))
                )
                solver = driver.find_element(
                    By.XPATH,
                    "//div[@class='button-holder help-button-holder']")
                solver.click()
                WebDriverWait(driver, 30).until(EC.url_changes(driver.current_url))
            else:
                driver.quit()
                print("Could not resolve google captcha automatically")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH,
                 "//a//cite"))
        )
        print("Results found!")
        profiles = [p.get_attribute('href') for p in driver.find_elements(By.XPATH, "//div/span/a[h3]")]
        profiles = profiles[:int(people_count)]
        print("Checking filter(s)...")
        len_profiles = len(profiles)
        p = 0
        while p < len_profiles:
            if (not re.match(r"^https://www.instagram.com/.+/$", profiles[p])
                    or "/reel/" in profiles[p]
                    or "/p/" in profiles[p]):
                del profiles[p]
                len_profiles -= 1
                p -= 1

            if '/channel' in profiles[p]:
                profiles[p] = profiles[p].replace("/channel", "")

            if '/reels' in profiles[p]:
                profiles[p] = profiles[p].replace("/reels", "")
            p += 1

        # This line is to remove any duplicate addresses
        profiles = list(set(profiles))
        user_ids += [u.replace("https://www.instagram.com/", "").replace("/", "") for u in profiles]
        search_index += 10

    return get_profile(user_ids, post_count, driver)


if __name__ == "__main__":
    app()
