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

    for user_id in users:
        try:
            if re.search(r"^\d{11}", str(int(user_id))):
                print("Correct phone format...")
            else:
                raise ValueError()
        except ValueError:
            print("please inter a valid phone number...")
        file_name = "whatsapp" + user_id + ".csv"
        bio_xpath = "//span/span[@class='x13faqbe _ao3e selectable-text copyable-text']"
        image_object_xpath = "//div[@role='button']/img"
        profile_image_xpath = "//div/img[@class='xhtitgo xh8yej3 x5yr21d _ao3e']"
        url = (f'https://web.whatsapp.com/'
               f'send/?phone={user_id}&text&type=phone_number&app_absent=0')
        driver.get(url)
        print("getting profile...")
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//div[@title]/div/img")))
        profile_object = driver.find_element(By.XPATH, "//div[@title]/div/img")
        profile_object.click()
        WebDriverWait(driver, 4).until(
            EC.presence_of_element_located((By.XPATH, bio_xpath)))
        bio = driver.find_element(By.XPATH, bio_xpath).text
        WebDriverWait(driver, 4).until(
            EC.element_to_be_clickable((By.XPATH, image_object_xpath)))
        image_object = driver.find_element(By.XPATH, image_object_xpath)
        image_object.click()
        WebDriverWait(driver, 4).until(
            EC.presence_of_element_located((By.XPATH, profile_image_xpath)))
        time.sleep(.1)
        print("getting image...")
        profile_image = driver.find_element(By.XPATH, profile_image_xpath)
        profile_image.screenshot(f'{user_id}.png')
        generate_file(user_id, file_name, [bio, f'{user_id}.png'])
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