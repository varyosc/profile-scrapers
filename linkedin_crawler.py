import json
import os
import time

import typer
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from utils import use_driver

app = typer.Typer()


def link_to_id(link: str) -> str:
    link = link.split("?")[0]
    link = link.split("in/")[1]
    link = link.strip()
    return link


def check_filter(text_filter: str, desired_text: str,
                 filter_type: str, user_id: str) -> bool:
    """Get the text and filter and check if the filter applies to the text

    Args:
        text_filter {str} -- The filter's content
        desired_text {str} -- Text to check
        user_id {str} -- The user id to be displayed in message if needed
        filter_type {str} -- "industry", "location" or "others"

    Returns:
        True if filter exists and applies, False and give appropriate
        message otherwise.

    """
    if not text_filter:
        return True
    if text_filter in desired_text:
        return True
    else:
        print(f"Mismatch of filter: {filter_type}, for user: ", user_id)
        return False


def remove_redundant_lines(text: str) -> str:
    """Take any given text and remove duplicates of the same lines in it

    Args:
        text {str} -- text to be cleaned
    Returns:
        str -- cleaned text
    """
    lines = text.strip().splitlines()
    result = []

    for line in lines:
        if result and line.strip() == result[-1]:
            continue
        result.append(line.strip())

    return "\n".join(result)


@app.command('get')
def get_profile(filter_loc="", filter_industry="",
                filter_followers="", filter_others=""):
    """Search and find the requested people on LinkedIn
     and store them.

     Params:
         filter_loc (Character) : len40, null=True

         filter_industry (Character) : len40, null=True

         filter_followers (Character) : len40, null=True

         filter_others (Character) : len40, null=True

         driver (Webdriver) : selenium webdriver

     Returns: None, writes two files, a profile image png file with the
     associated user's id as name and a json file containing all the data
     """
    driver = use_driver()
    address = "https://www.google.com/search?q=site%3Alinkedin.com%2Fin%2F"
    people_count = 10
    current_batch = {
        "batch_loc": filter_loc,
        "batch_industry": filter_industry,
        "batch_followers": filter_followers,
        "batch_others": filter_others,
        "batch_content": []
    }
    print("Starting search...")
    if filter_loc:
        address = address + f"+%22{filter_loc}%22+"
    if filter_industry:
        address = address + f"+%22{filter_industry}%22+"
    if filter_followers:
        filter_followers = int(filter_followers)
    if filter_others:
        address = address + f"+%22{filter_others}%22+"
    filter_loc = filter_loc.lower().strip()
    filter_industry = filter_industry.lower().strip()
    filter_others = filter_others.lower().strip()

    driver.get("https://www.linkedin.com/login")
    print("Checking if logged in...")
    WebDriverWait(driver, 120).until(
        EC.url_changes("https://www.linkedin.com/login"))
    current_url = driver.current_url
    if "checkpoint" in current_url:
        print("On the verification page, waiting longer...")
        WebDriverWait(driver, 120).until(EC.url_changes(current_url))

    search_index = 0
    profile_address_list = []

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
                WebDriverWait(driver, 60).until(EC.url_contains("search?q="))
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located(
                        (By.XPATH,
                         "//div[@data-sncf]"))
                )
            else:
                driver.quit()
                raise TimeoutException()
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located(
                (By.XPATH,
                 "//a//cite"))
        )
        print("Results found!")
        profiles = driver.find_elements(By.XPATH, "//div[@data-snc]")
        profiles = profiles[:int(people_count)]
        print("Checking filter(s)...")
        for profile in profiles:
            profile_object = {
                "check_industry": False,
                "address": (profile.find_element(By.XPATH, ".//div/span/a[h3]")
                            .get_attribute("href"))}
            # Lookin through the search data to find early filter mismatches

            try:
                description_res = profile.find_element(
                    By.XPATH, ".//div[@data-sncf]/div[2]").text.replace("...", "")
                sub_text_res = profile.find_element(
                    By.XPATH, ".//div[@data-sncf]/div[1]").text.replace("...", "")
            except NoSuchElementException:
                description_res = profile.find_element(
                    By.XPATH, ".//div[@data-sncf]/div[1]").text.replace("...", "")
                sub_text_res = None
            if filter_loc:
                if sub_text_res and filter_loc not in sub_text_res.lower():
                    continue
            if filter_industry and filter_industry not in description_res.lower():
                profile_object["check_industry"] = True

            profile_address_list.append(profile_object)
        search_index += 10

    for profile_object in profile_address_list:
        profile_id = link_to_id(profile_object["address"])
        print("adding profile of", profile_id)
        driver.get(profile_object["address"])

        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located(
                (By.XPATH, "//div/p/span")
            )
        )
        follower_count = driver.find_elements(By.XPATH, "//div/p/span")[0].text
        if "follower" not in follower_count:
            time.sleep(1)
            follower_count = driver.find_elements(By.XPATH, "//div/p/span")[0].text
        follower_count = follower_count.replace(",", "")
        follower_count = follower_count.split(" ")[0]
        follower_count = follower_count.strip()
        try:
            follower_count = int(follower_count)
        except ValueError:
            follower_count = 0
        if filter_followers and follower_count < filter_followers:
            print("Mismatch of filter: followers, for user: ", profile_id)
            continue

        linkedin_object = {
            "userID": profile_id,
            "followers": follower_count,
            "title": "",
            "location": "",
            "description": "",
            "last_occupation": "",
        }
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, "//h1")
            )
        )
        linkedin_object["title"] = driver.find_element(By.XPATH, "//h1").text
        about_sections = driver.find_elements(
            By.XPATH,
            "//div[@data-generated-suggestion-target]")
        try:
            WebDriverWait(driver, 5).until(EC.presence_of_element_located(
                (By.XPATH,
                 "//section[./div[@id='experience']]//ul/li")
            ))
            last_occupation = driver.find_elements(By.XPATH,
                                                   "//section[./div[@id='experience']]//ul/li")[0].text
        except TimeoutException:
            last_occupation = ""
        linkedin_object["last_occupation"] = remove_redundant_lines(last_occupation)
        linkedin_object["description"] = about_sections[1].text if (
                                                                       len(about_sections)) > 1 else (
            about_sections[0].text)
        if profile_object["check_industry"]:
            if len(about_sections) > 1:
                if (not check_filter(filter_industry,
                                     about_sections[1].text.lower()
                                     + about_sections[0].text.lower()
                                     + last_occupation.lower(),
                                     "industry",
                                     profile_id)):
                    continue
            if not check_filter(filter_industry,
                                about_sections[0].text.lower()
                                + last_occupation.lower(),
                                "industry",
                                profile_id):
                continue

        linkedin_object["location"] = (driver.find_element(
            By.XPATH,
            "//div/span[@class='text-body-small inline t-black--light break-words']")
                                    .text)
        if (not check_filter(filter_loc,
                             linkedin_object["location"].lower(),
                             "location",
                             profile_id)):
            continue
        try:
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located(
                    (By.XPATH,
                     f"//button/img[@alt='{linkedin_object["title"]}']")))
            img_element = f"//button/img[@alt='{linkedin_object["title"]}']"
        except TimeoutException:
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located(
                    (By.XPATH,
                     f"//button/img[@alt='{linkedin_object["title"]}, #OPEN_TO_WORK']")))
            img_element = f"//button/img[@alt='{linkedin_object["title"]}, #OPEN_TO_WORK']"
        img_address = driver.find_element(By.XPATH, img_element).get_attribute("src")
        try:
            if "https" not in img_address:
                raise Exception
            driver.get(img_address)
            WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable(
                    (By.XPATH,
                     "//body/img"))
            )
            img_path = os.path.join(os.getcwd(),
                                    "linkedin",
                                    "img",
                                    f"{linkedin_object["userID"]}.png")
            img = driver.find_element(By.XPATH,
                                      "//body/img")
            img.screenshot(img_path)
            linkedin_object["image"] = img_path
        except Exception as e:
            print("No profile image found ", e)
            linkedin_object["image"] = os.path.join(os.getcwd(),
                                                 "linkedin",
                                                 "img",
                                                 "default.png")
        current_batch["batch_content"].append(linkedin_object)

    driver.quit()
    filename = (filter_loc + " " + filter_industry + " "
                + str(filter_followers) + " " + filter_others + ".json")
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(current_batch, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    app()