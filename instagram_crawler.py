import os
from typing import List

import typer
from PIL import Image
from dotenv import load_dotenv
from selenium.webdriver import ActionChains
from selenium.webdriver.common.actions.wheel_input import ScrollOrigin
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from utils import generate_file, use_driver

app = typer.Typer()


@app.command("get")
def get_profile(users: List[str], post_count, driver=None):
    if not driver:
        driver = use_driver()
    try:
        post_count = int(post_count)
    except:
        post_count = 3

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
                    "//div[@class='_aagv']/img")
            except:
                print(f"{user_id} has no posts or none found")
            else:
                # Reset the post to get the amount you want than, get them
                posts = posts[:post_count]
                for i, img in enumerate(posts):
                    scroll_origin = ScrollOrigin.from_element(img)
                    (ActionChains(driver)
                     .scroll_from_origin(scroll_origin, 0, 100)
                     .perform())
                    WebDriverWait(driver, 18).until(
                        EC.element_to_be_clickable(img))
                    post_path = os.path.join(
                        os.getcwd(),
                        f"instagram",
                        "posts",
                        f"{user_id}_p{i}.png")
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

                user_profile["image"] = image_path if "https" in image_url else image_url
                user_profile["bio"] = bio
                generate_file(user_id+".json", user_profile)
        except Exception as e:
            driver.quit()
            print(f"error: {e}")


    driver.quit()


@app.command()
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
        return get_profile(users, post_count, driver)
    except Exception as e:
        driver.quit()
        print("error: ", e)


if __name__ == "__main__":
    app()
