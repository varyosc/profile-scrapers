import re
import time
from traceback import print_tb
from typing import List

import typer
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from utils import generate_file, use_driver

app = typer.Typer()


@app.command("get")
def get_profile(users: List[str], driver=None):
    """Get a list of user profiles and return their bio and profile
    image if any telegram account exists for them

    Arguments:
        users {List[str]} -- List of user names or phone numbers
        driver {seleniumWebdriver} -- Optional. pass the driver session
    Returns: None, writes two files, a profile image png file with the
    associated user's id as name and a csv file containing
    """
    if not driver:
        driver = use_driver()

    picture_class = "profile-avatars-avatar"
    bio_class = "row-title pre-wrap"
    file_name = ("telegram"
                 + time.strftime("%Y%m%d", time.localtime())
                 + ".csv")

    for user_id in users:
        try:
            if re.search(r"^\d{10}$", str(int(user_id))):
                WebDriverWait(driver, 5).until(EC.element_to_be_clickable(
                    (By.ID,
                    "new-menu"))
                )
                contact_menu = driver.find_element(
                    By.ID,
                    "new-menu"
                )
                contact_menu.click()
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located(
                        (By.CLASS_NAME,
                         "btn-menu-overlay"))
                )
                new_chat = driver.find_element(
                    By.XPATH,
                    "//div[@class='btn-menu top-left active was-open']/div[3]"
                )
                new_chat.click()
                WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable(
                        (By.XPATH,
                         "//button[@class='btn-circle btn-corner z-depth-1 is-visible rp']"))
                )
                time.sleep(1)
                add_contact = driver.find_element(
                    By.XPATH,
                    "//button[@class='btn-circle btn-corner z-depth-1 is-visible rp']/div[1]"
                )
                add_contact.click()
                WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable(
                        (By.XPATH,
                         "//div[@class='input-field input-field-name']"))
                )
                name_input = driver.find_element(
                    By.XPATH,
                    "//div[@class='input-field input-field-name']/div[1]"
                )
                name_input.send_keys(user_id)
                WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable(
                        (By.XPATH,
                         "//div[@class='input-field input-field-phone']"))
                )
                phone_input = driver.find_element(
                    By.XPATH,
                    "//div[@class='input-field input-field-phone']/div[1]"
                )
                phone_input.send_keys(user_id)
                WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable(
                        (By.XPATH,
                         "//button[@class='btn-primary btn-color-primary']"))
                )
                create_contact_button = driver.find_element(
                    By.XPATH,
                    "//button[@class='btn-primary btn-color-primary']"
                )
                create_contact_button.click()
                WebDriverWait(driver, 60).until(
                    EC.invisibility_of_element_located(
                        (By.XPATH,
                         "//button[@class='btn-primary btn-color-primary']"))
                )
                WebDriverWait(driver, 15).until(
                    EC.element_to_be_clickable(
                        (By.XPATH,
                         "//div[@class='input-search']"))
                )
                try:
                    search_bar_input = driver.find_element(
                        By.XPATH,
                        "//div[@class='input-search']/input[1]"
                    )
                    search_bar_input.click()
                    search_bar_input.send_keys(user_id)
                    time.sleep(1)
                    WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable(
                            (By.XPATH,
                             "//ul[@id='contacts']/a[1]"))
                    )
                    requested_user = driver.find_element(
                        By.XPATH,
                        "//ul[@id='contacts']/a[1]"
                    )
                    requested_user.click()
                except Exception as e:
                    generate_file("NO telegram account",
                                  file_name,
                                  ["no account for user:", user_id])
                    print(e)
                    continue


        except Exception as e:
            print("getting uesr by id ", e)
            url = f'https://web.telegram.org/k/#?tgaddr=tg%3A%2F%2Fresolve%3Fdomain%3D{user_id}'
            driver.get(url)

        print("Waiting for page to load...")
        try:
            # Wait until the profile image is loaded
            WebDriverWait(driver, 60).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "person"))
            )
            print("Page loaded successfully!")
        except Exception as e:
            print(f"Error waiting for the page to load: {e}")
            driver.quit()
            exit()

        # Get the page source after everything is loaded
        chat = driver.find_element(
            By.CSS_SELECTOR,
            ".person"
        )
        chat.click()
        WebDriverWait(driver, 60).until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//div/div[@class='row-title pre-wrap']"
        )))
        bio = driver.find_element(By.XPATH,
                "//div/div[@class='row-title pre-wrap']").text
        WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH,
                                        f"//div[@class='avatar avatar-like avatar-full"
                                        + " avatar-gradient profile-avatars-avatar-first']"
                                        + "/img[@class='avatar-photo']")))
        img = driver.find_element(
            By.XPATH,
            f"//div[@class='avatar avatar-like avatar-full"
            + " avatar-gradient profile-avatars-avatar-first']"
        )
        try:
            img.click()
        except Exception as e:
            print("selenium error, image will be lower quality! ", e)
        finally:
            print("")
        time.sleep(.7)
        img.screenshot(f'{user_id}.png')
        # Save all the user's info
        generate_file(user_id, file_name, [bio, f'{user_id}.png'])
        driver.quit()


@app.command("login")
def login(users: List[str]):
    driver = use_driver()
    url = "https://web.telegram.org/k"

    print("On the verification page, waiting longer...")

    # Open the webpage
    driver.get(url)

    WebDriverWait(driver, 60).until(EC.url_changes(url))

    print("Getting user's profile...")
    get_profile(users, driver)


if __name__ == "__main__":
    app()
