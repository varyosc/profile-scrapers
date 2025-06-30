import json
import os
import re
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


def remove_duplicate_skills_paragraph(text):
    """Remove the duplicate skills paragraph
    made primarily for educations information

    Args:
        text {str} -- text to be cleaned
    Returns:
        str -- cleaned text
    """
    # Find all paragraphs that start with "Skills:"
    skill_paragraphs = re.findall(r'(Skills:.*?)(?=\n|$)', text, re.DOTALL)

    if len(skill_paragraphs) < 2:
        return text  # No duplicate to remove

    # Normalize both to compare (remove spaces after colon and strip whitespace)
    first_norm = re.sub(r'\s+', '', skill_paragraphs[0].replace("Skills:", "").strip())
    second_norm = re.sub(r'\s+', '', skill_paragraphs[1].replace("Skills:", "").strip())

    if first_norm == second_norm:
        # Remove second paragraph from original text
        second_para_escaped = re.escape(skill_paragraphs[1])
        return re.sub(second_para_escaped, '', text, count=1).strip()

    return text


def get_post_interactions(text):
    """Get the LinkedIn post interactions and return them
    seperated into reactions and comments+reposts of the post
    Args:
        text {str} -- text to be cleaned

    Returns:
        list -- [reactions, comments+reposts]
    """
    lines = text.strip().splitlines()
    return [lines[0], " . ".join(lines[1:])]


def get_contact_info(text):
    """Order the contact info text given to you in a dic variable
    Also remove the LinkedIn account link in contact info

    Args:
        text {str} -- text to be organized

    Returns:
        dict -- contact info
    """
    lines = text.strip().splitlines()
    info_dict = {}

    i = 0
    while i < len(lines) - 1:
        key = lines[i]
        value = lines[i + 1]

        # Skip the LinkedIn profile URL if explicitly named
        if value.lower().startswith("linkedin.com"):
            i += 2
            continue

        info_dict[key] = value
        i += 2

    return info_dict


@app.command('get')
def get_profile(filter_loc = "",
        do_filter_loc = False,
        filter_industry = "",
        do_filter_industry = False,
        filter_edu = "",
        do_filter_edu = False,
        filter_followers = 0,
        filter_others = "",
        do_filter_others = False,
        people_count = 10,
        post_count = 3):
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
    current_batch = {
        "batch_loc": filter_loc,
        "batch_industry": filter_industry,
        "batch_edu": filter_edu,
        "batch_followers": filter_followers,
        "batch_others": filter_others,
        "batch_content": {}
    }
    print("Starting search...")
    if filter_loc:
        address = address + f"+%22{filter_loc}%22+"
        filter_loc = filter_loc.strip().lower()
    if filter_industry:
        address = address + f"+%22{filter_industry}%22+"
        filter_industry = filter_industry.strip().lower()
    if filter_edu:
        filter_edu = filter_edu.strip().lower()
    if filter_others:
        filter_others = filter_others.strip().lower()
        address = address + f"+%22{filter_others}%22+"

    driver.get("https://www.linkedin.com/login")
    print("Checking if logged in...")
    WebDriverWait(driver, 120).until(
        EC.url_changes("https://www.linkedin.com/login"))
    if "checkpoint" in driver.current_url:
        print("On the verification page, waiting longer...")
        WebDriverWait(driver, 120).until(EC.url_changes(driver.current_url))

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
            if filter_loc and do_filter_loc:
                if sub_text_res and filter_loc not in sub_text_res.lower():
                    continue
            if (do_filter_industry
                    and filter_industry
                    and filter_industry not in description_res.lower()):
                profile_object["check_industry"] = True

            profile_address_list.append(profile_object)
        search_index += 10

    for profile_object in profile_address_list:
        profile_id = link_to_id(profile_object["address"])
        print("adding profile of", profile_id)
        driver.get(profile_object["address"])
        profile_address = f"https://www.linkedin.com/in/{profile_id}/"

        WebDriverWait(driver, 25).until(
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

        current_batch['batch_content'][profile_id]['follower_count'] = follower_count
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, "//h1")
            )
        )
        current_batch['batch_content'][profile_id]['title'] = driver.find_element(By.XPATH, "//h1").text

        WebDriverWait(driver, 5).until(EC.presence_of_element_located(
            (By.XPATH,
             "//div/span[@class='text-body-small inline t-black--light break-words']")
        ))
        current_batch['batch_content'][profile_id]['location'] = (driver.find_element(
            By.XPATH,
            "//div/span[@class='text-body-small inline t-black--light break-words']")
                                    .text)
        if (do_filter_loc and not check_filter(filter_loc,
                                               current_batch['batch_content'][profile_id]['location'].lower(),
                                               "location",
                                               profile_id)):
            del current_batch['batch_content'][profile_id]
            continue

        about_sections = driver.find_elements(
            By.XPATH,
            "//div[@data-generated-suggestion-target]")
        try:
            WebDriverWait(driver, 5).until(EC.presence_of_element_located(
                (By.XPATH,
                 "//section[./div[@id='experience']]//ul/li")
            ))
            last_occupation = driver.find_elements(
                By.XPATH,
                "//section[./div[@id='experience']]//ul/li")[0].text
        except TimeoutException:
            last_occupation = ""

        if profile_object["check_industry"]:
            if len(about_sections) > 1:
                if (not check_filter(filter_industry,
                                     about_sections[1].text.lower()
                                     + about_sections[0].text.lower()
                                     + last_occupation.lower(),
                                     "industry",
                                     profile_id)):
                    del current_batch['batch_content'][profile_id]
                    continue
            if not check_filter(filter_industry,
                                about_sections[0].text.lower()
                                + last_occupation.lower(),
                                "industry",
                                profile_id):
                del current_batch['batch_content'][profile_id]
                continue

        current_batch['batch_content'][profile_id]['last_occupation']\
            = remove_redundant_lines(last_occupation)
        current_batch['batch_content'][profile_id]['description'] = (about_sections[1].text
                                       if (
                                              len(about_sections)) > 1 else (
            about_sections[0].text))

        # Get the profile image address here to process later
        try:
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located(
                    (By.XPATH,
                     f"//button/img[@alt='{current_batch['batch_content'][profile_id]['title']}']")))
            img_element = f"//button/img[@alt='{current_batch['batch_content'][profile_id]['title']}']"
        except TimeoutException:
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located(
                    (By.XPATH,
                     f"//button/img[@alt='"
                     f"{current_batch['batch_content'][profile_id]['title']}"
                     f", #OPEN_TO_WORK']")))
            img_element = (f"//button/img[@alt='"
                           f"{current_batch['batch_content'][profile_id]['title']}"
                           f", #OPEN_TO_WORK']")
        img_address = (driver.find_element(By.XPATH, img_element)
                       .get_attribute("src"))

        # Redirect ot get their contact info now
        driver.get(f"{profile_address}overlay/contact-info/")
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located(
                (By.XPATH,
                 "//section[h2]/div")
            ))
        contact_info = driver.find_element(
            By.XPATH,
            "//section[h2]/div"
        ).text
        current_batch['batch_content'][profile_id]['contact_info'] = get_contact_info(contact_info)

        # Redirect to get the Education of this person now
        driver.get(f"{profile_address}details/education/")
        try:
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located(
                    (By.XPATH,
                     "//main/section//ul/li[.//ul//ul]")
                ))
            educations = driver.find_elements(By.XPATH,
                                              "//main/section//ul/li[.//ul//ul]")
        except TimeoutException:
            educations = driver.find_elements(By.XPATH,
                                              "//main/section//ul/li[.//ul]")
        except NoSuchElementException:
            educations = ""

        for e in range(len(educations)):
            educations[e] = remove_redundant_lines(educations[e].text)
            educations[e] = remove_duplicate_skills_paragraph(educations[e])
        if do_filter_edu and not check_filter(
                filter_edu,
                "".join(educations).lower(),
                "education",
                profile_id):
            del current_batch['batch_content'][profile_id]
            continue
        current_batch['batch_content'][profile_id]['education'] = educations

        # Check filter others if user has decided for it
        if do_filter_others:
            if (not check_filter(filter_others,
                                 current_batch['batch_content'][profile_id]['title'].lower()
                                 + current_batch['batch_content'][profile_id]['description'].lower()
                                 + current_batch['batch_content'][profile_id]['last_occupation'].lower()
                                 + current_batch['batch_content'][profile_id]['location'].lower()
                                 + "".join(educations).lower(),
                                 "others",
                                 profile_id)):
                del current_batch['batch_content'][profile_id]
                continue

        # Process the previously caught profile image
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
                                    f"{profile_id}.png")
            img = driver.find_element(By.XPATH,
                                      "//body/img")
            img.screenshot(img_path)
            current_batch['batch_content'][profile_id]['image'] = img_path
        except Exception as e:
            print("No profile image found ", e)
            current_batch['batch_content'][profile_id]['image'] = os.path.join(os.getcwd(),
                                                 "linkedin",
                                                 "img",
                                                 "default.png")

        if post_count:
            print(f"Getting {current_batch['batch_content'][profile_id]['title']}'s post(s)")
            post_object_xpath = "//main//ul[.//ul]//div[./h2]"
            post_text_xpath = "./div/div//div[@dir]/span"
            post_origin_xpath = "./div/div[1]"
            post_interactions_xpath = "./div//ul[.//button]"
            post_image_xpath = ".//button//img[@loading]"
            post_article_xpath = ".//article//a"
            post_rotation = 3
            p = 0
            driver.get(f"{profile_address}recent-activity/all/")
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located(
                        (
                            By.XPATH, post_object_xpath)
                    ))
                posts_object = driver.find_elements(By.XPATH, post_object_xpath)
            except TimeoutException:
                print(current_batch['batch_content'][profile_id]['title'],
                      "has no post")
                posts_object = []
            while p < post_count:
                if p > post_rotation and post_rotation < post_count:
                    posts_object = driver.find_elements(By.XPATH, post_object_xpath)
                    post_rotation += 3
                post = posts_object[p]
                print("Getting post ", p)
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'})", post)
                try:
                    WebDriverWait(post, 4).until(
                        EC.presence_of_element_located((
                            By.XPATH, post_text_xpath)))
                    post_text = post.find_element(By.XPATH, post_text_xpath).text
                except TimeoutException:
                    post_text = None
                post_origin = post.find_element(By.XPATH, post_origin_xpath).text
                post_origin = remove_redundant_lines(post_origin)
                post_origin = post_origin.replace(" Follow", "")
                post_origin = post_origin.replace(" 1st", "")
                post_origin = post_origin.replace(" 2nd", "")
                post_origin = post_origin.replace(" 3rd+", "")
                # The try for post's interactions if there is any
                try:
                    post_interactions = post.find_element(
                        By.XPATH, post_interactions_xpath).text
                    post_reactions, post_comment_reposts = get_post_interactions(post_interactions)
                except NoSuchElementException:
                    post_reactions, post_comment_reposts = 0, None
                # The try for post's linked article if there is one
                try:
                    WebDriverWait(post, 3).until(
                        EC.element_to_be_clickable((
                            By.XPATH, post_article_xpath)))
                    post_article = post.find_element(
                        By.XPATH, post_article_xpath).get_attribute("href")
                except NoSuchElementException:
                    post_article = None
                except TimeoutException:
                    post_article = None
                # The try for post image if there is one
                try:
                    WebDriverWait(post, 3).until(
                        EC.element_to_be_clickable((
                            By.XPATH, post_image_xpath)))
                    post_image = post.find_element(
                        By.XPATH, post_image_xpath)
                    post_image_path = os.path.join(os.getcwd(),
                                                   "linkedin",
                                                   "posts",
                                                   f"{profile_id}_{p}.png")
                    post_image.screenshot(post_image_path)
                except NoSuchElementException:
                    post_image_path = None
                except TimeoutException:
                    post_image_path = None
                if not post_image_path:
                    try:
                        post_image = post.find_element(By.XPATH, ".//iframe")
                        post_image_path = os.path.join(os.getcwd(),
                                                       "linkedin",
                                                       "posts",
                                                       f"{profile_id}_{p}.png")
                        post_image.screenshot(post_image_path)
                    except NoSuchElementException:
                        post_image_path = None
                    except TimeoutException:
                        post_image_path = None
                if not post_image_path:
                    try:
                        post_image = post.find_element(
                            By.XPATH, ".//video")
                        post_image_path = os.path.join(os.getcwd(),
                                                       "linkedin",
                                                       "posts",
                                                       f"{profile_id}_{p}.png")
                        post_image.screenshot(post_image_path)
                    except NoSuchElementException:
                        post_image_path = None
                    except TimeoutException:
                        post_image_path = None
                current_batch['batch_content'][profile_id]['post'] = {
                    "original_poster":post_origin,
                    "text":post_text,
                    "related_article":post_article,
                    "reactions":int(post_reactions),
                    "comment_reposts":post_comment_reposts,
                    "image":post_image_path
                }
                p += 1

    driver.quit()
    filename = (filter_loc + " " + filter_industry + " "
                + str(filter_followers) + " " + filter_others + ".json")
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(current_batch, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    app()