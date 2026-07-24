# ==========================================================
# workday.py
# PART 1/4
# ==========================================================

import os
import re
import time

from urllib.parse import (
    urlparse,
    parse_qs,
    urlencode,
    urlunparse
)

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from config import (
    MAX_PAGES,
    PAGE_LOAD_WAIT,
    SCROLL_PAUSE,
    RETRY_COUNT
)

from utils.browser import create_driver
from utils.cleaner import clean_text
from utils.filters import is_data_role
from utils.exporter import Exporter
from utils.logger import Logger

from utils.master_db import (
    remove_existing_urls,
    append_to_master
)


# ==========================================================
# HELPERS
# ==========================================================

def wait_page(driver):

    WebDriverWait(driver, 30).until(

        lambda d:

        d.execute_script(

            "return document.readyState"

        ) == "complete"

    )


def scroll_page(driver):

    last_height = 0

    while True:

        driver.execute_script(

            "window.scrollTo(0, document.body.scrollHeight);"

        )

        time.sleep(SCROLL_PAUSE)

        new_height = driver.execute_script(

            "return document.body.scrollHeight"

        )

        if new_height == last_height:

            break

        last_height = new_height


def search_keyword(url):

    query = parse_qs(

        urlparse(url).query

    )

    for key in [

        "q",

        "query",

        "keywords",

        "search"

    ]:

        if key in query:

            return query[key][0]

    return "workday"


def page_url(base_url, page):

    parsed = urlparse(base_url)

    params = parse_qs(parsed.query)

    params["page"] = [str(page)]

    new_query = urlencode(

        params,

        doseq=True

    )

    return urlunparse(

        (

            parsed.scheme,

            parsed.netloc,

            parsed.path,

            parsed.params,

            new_query,

            parsed.fragment

        )

    )


# ==========================================================
# LINK COLLECTION
# ==========================================================

def collect_links(driver):

    urls = set()

    anchors = driver.find_elements(

        By.TAG_NAME,

        "a"

    )

    for a in anchors:

        href = a.get_attribute("href")

        if not href:

            continue

        href = href.split("?")[0]

        lower = href.lower()

        if "/job/" in lower:

            urls.add(href)

            continue

        if "/jobs/" in lower:

            urls.add(href)

            continue

        if "/career" in lower:

            urls.add(href)

            continue

        if "/details/" in lower:

            urls.add(href)

            continue

    return urls
 
 # ==========================================================
# workday.py
# PART 2/4
# ==========================================================

# ==========================================================
# JOB DETAILS
# ==========================================================

def get_title(driver):

    selectors = [

        "h1",

        "[data-automation-id='jobPostingHeader']",

        "[data-automation-id='jobPostingHeaderText']",

        "[data-automation-id='jobTitle']"

    ]

    for selector in selectors:

        try:

            title = driver.find_element(

                By.CSS_SELECTOR,

                selector

            ).text.strip()

            if title:

                return title

        except:

            pass

    return ""


def get_company(driver):

    selectors = [

        "[data-automation-id='company']",

        "[data-automation-id='companyName']",

        ".company",

        ".company-name"

    ]

    for selector in selectors:

        try:

            value = driver.find_element(

                By.CSS_SELECTOR,

                selector

            ).text.strip()

            if value:

                return value

        except:

            pass

    return ""


def get_location(driver):

    selectors = [

        "[data-automation-id='locations']",

        "[data-automation-id='location']",

        ".location",

        ".job-location"

    ]

    for selector in selectors:

        try:

            value = driver.find_element(

                By.CSS_SELECTOR,

                selector

            ).text.strip()

            if value:

                return value

        except:

            pass

    return ""


def get_description(driver):

    selectors = [

        "[data-automation-id='jobPostingDescription']",

        "[data-automation-id='jobDescription']",

        ".job-description",

        "main"

    ]

    for selector in selectors:

        try:

            text = driver.find_element(

                By.CSS_SELECTOR,

                selector

            ).text

            if len(text) > 500:

                return clean_text(text)

        except:

            pass

    return clean_text(

        driver.execute_script(

            "return document.body.innerText"

        )

    )


def scrape_job(driver, url):

    driver.get(url)

    wait_page(driver)

    time.sleep(2)

    title = get_title(driver)

    if not is_data_role(title):

        return None

    return {

        "url": url,

        "title": title,

        "company": get_company(driver),

        "location": get_location(driver),

        "description": get_description(driver)

    }


# ==========================================================
# CRAWL SEARCH RESULTS
# ==========================================================

def crawl_links(driver, base_url, logger):

    all_links = set()

    previous_count = 0

    for page in range(1, MAX_PAGES + 1):

        logger.write(f"\nScanning Page {page}")

        try:

            driver.get(

                page_url(base_url, page)

            )

            wait_page(driver)

            time.sleep(PAGE_LOAD_WAIT)

            scroll_page(driver)

            links = collect_links(driver)

            logger.write(

                f"Found {len(links)} links"

            )

            all_links.update(links)

            logger.write(

                f"Unique links : {len(all_links)}"

            )

            if len(all_links) == previous_count:

                logger.write(

                    "No new links detected."

                )

                break

            previous_count = len(all_links)

        except Exception as e:

            logger.write(str(e))

            continue

    return sorted(all_links)
    
# ==========================================================
# workday.py
# PART 3/4
# ==========================================================

def scrape_with_retry(driver, url):

    for attempt in range(RETRY_COUNT):

        try:

            job = scrape_job(
                driver,
                url
            )

            if job:
                return job

        except Exception:
            pass

        time.sleep(2)

    return None


def export_job(exporter, job):

    if job["url"] not in exporter.links:

        exporter.links.append(
            job["url"]
        )

    exporter.jobs.append(

        (

            job["url"],

            job["title"],

            f"""Company: {job['company']}

Location: {job['location']}

{job['description']}"""

        )

    )


def scrape_all_jobs(

    driver,

    urls,

    exporter,

    logger

):

    total = len(urls)

    logger.write(

        f"\nExtracting {total} jobs..."

    )

    for index, url in enumerate(

        urls,

        start=1

    ):

        logger.write(

            f"[{index}/{total}]"

        )

        job = scrape_with_retry(

            driver,

            url

        )

        if job is None:

            exporter.failed.append(url)

            logger.write("Failed")

            continue

        export_job(

            exporter,

            job

        )

        logger.write(

            job["title"]

        )


def print_summary(exporter, logger):

    logger.write("\n" + "=" * 70)

    logger.write("WORKDAY SUMMARY")

    logger.write("=" * 70)

    logger.write(

        f"Links : {len(exporter.links)}"

    )

    logger.write(

        f"Jobs  : {len(exporter.jobs)}"

    )

    logger.write(

        f"Failed: {len(exporter.failed)}"

    )

    logger.write("=" * 70)

# ==========================================================
# workday.py
# PART 4/4
# ==========================================================

def scrape(base_url, output_folder):
    """
    Main entry point for the Workday scraper.
    """

    logger = Logger("Workday")

    exporter = Exporter(output_folder)

    driver = None

    master_dir = os.path.join(
        "outputs",
        "Workday"
    )

    os.makedirs(
        master_dir,
        exist_ok=True
    )

    master_file = os.path.join(
        master_dir,
        "Master_Workday.xlsx"
    )

    logger.write("=" * 70)
    logger.write("WORKDAY SCRAPER STARTED")
    logger.write("=" * 70)

    logger.write(f"Search URL : {base_url}")
    logger.write(f"Output Folder : {output_folder}")

    try:

        logger.write("\nLaunching browser...")

        driver = create_driver()

        keyword = search_keyword(base_url)

        logger.write(
            f"Search Keyword : {keyword}"
        )

        logger.write(
            "\nCollecting job links..."
        )

        job_urls = crawl_links(

            driver=driver,

            base_url=base_url,

            logger=logger

        )

        logger.write(

            f"Collected {len(job_urls)} unique links."

        )

        job_urls = remove_existing_urls(

            job_urls,

            master_file

        )

        logger.write(

            f"New jobs to scrape : {len(job_urls)}"

        )

        if len(job_urls) == 0:

            logger.write(

                "No new jobs found."

            )

            return

        logger.write(

            "\nExtracting job descriptions..."

        )

        scrape_all_jobs(

            driver=driver,

            urls=job_urls,

            exporter=exporter,

            logger=logger

        )

        append_to_master(

            exporter.jobs,

            master_file

        )

        logger.write(

            "\nSaving output files..."

        )

        exporter.save()

        print_summary(

            exporter,

            logger

        )

        logger.write(

            "\nWorkday scraping completed successfully."

        )

    except KeyboardInterrupt:

        logger.write(

            "\nScraper stopped by user."

        )

        try:

            exporter.save()

        except:

            pass

    except Exception as e:

        logger.write(

            f"\nFatal Error: {e}"

        )

        try:

            exporter.save()

        except:

            pass

        raise

    finally:

        if driver:

            try:

                driver.quit()

            except:

                pass

        logger.write("=" * 70)
        logger.write("WORKDAY SCRAPER FINISHED")
        logger.write("=" * 70)