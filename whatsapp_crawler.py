import os
import re
import time
from typing import List

import typer
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from utils import generate_file, use_driver


app = typer.Typer()

@app.command("get")
def get_profile(users: List[str], driver):
    if not driver:
        driver = use_driver()

    for user_id in users:
        try:
            user_id = str(user_id)
            try:
                if re.search(r"^\d{10}", str(int(user_id))):
                    print("Correct phone format...")
                else:
                    raise ValueError()
            except ValueError:
                print("please inter a valid phone number...")
            bio_xpath = "//section//span[@title]"
            image_object_xpath = "//section//img"
            profile_image_xpath = "//div[@class='_ajuf _ajuh']//img"
            url = (f'https://web.whatsapp.com/'
                   f'send/?phone={user_id}&text&type=phone_number&app_absent=0')
            driver.get(url)
            print("getting profile...")
            WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//div[@title]/div")))
            profile_object = driver.find_element(By.XPATH, "//div[@title]/div")
            profile_object.click()
            try:
                WebDriverWait(driver, 4).until(
                    EC.presence_of_element_located((By.XPATH, bio_xpath)))
                bio = driver.find_element(By.XPATH, bio_xpath).text
            except:
                bio = f"{user_id} has no bio"
            user_profile = {"userID": user_id,
                            "bio": bio,
                            "image": ""}
            try:
                WebDriverWait(driver, 4).until(
                    EC.element_to_be_clickable((
                        By.XPATH, image_object_xpath)))
                image_object = driver.find_element(
                    By.XPATH, image_object_xpath)
                image_object.click()
                WebDriverWait(driver, 4).until(
                    EC.presence_of_element_located((
                        By.XPATH, profile_image_xpath)))
                time.sleep(.1)
                print("getting image...")
                img_path = os.path.join(
                    os.getcwd(),
                    "whatsapp",
                    "img",
                    f"{user_id}.png")
                profile_image = driver.find_element(
                    By.XPATH, profile_image_xpath)
                profile_image.screenshot(img_path)
            except:
                print("user has no image...")
                img_path = os.path.join(os.getcwd(),
                                        "whatsapp",
                                        "img",
                                        f"default.png")
            user_profile["bio"] = bio
            user_profile["image"] = img_path
            generate_file(user_id+".json", user_profile)
        except Exception as e:
            print("error: ", e)
    driver.quit()


@app.command("login")
def login(users: List[str]):
    driver = use_driver()
    url = "https://web.whatsapp.com/"

    try:
        print("On the verification page, waiting longer...")
        driver.get(url)

        WebDriverWait(driver, 60).until(
            EC.element_to_be_clickable((By.XPATH, "//div/div/img")))

        print("Getting user's profile...")
        return get_profile(users, driver)
    except Exception as e:
        print(f"Error waiting for the page to load: {e}")
        driver.quit()


if __name__ == "__main__":
    app()