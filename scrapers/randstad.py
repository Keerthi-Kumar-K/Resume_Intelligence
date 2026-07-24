import time
import re

from urllib.parse import urlparse, parse_qs

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

import os

def wait_page(driver):

    WebDriverWait(driver, 30).until(
        lambda d: d.execute_script(
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

    if "query" in query:
        return query["query"][0]

    if "keywords" in query:
        return query["keywords"][0]

    return "randstad"
    
def page_url(base_url, page):

    if "page=" in base_url:

        return re.sub(
            r"page=\d+",
            f"page={page}",
            base_url
        )

    separator = "&" if "?" in base_url else "?"

    return f"{base_url}{separator}page={page}"
    
def collect_links(driver):

    links = set()

    anchors = driver.find_elements(
        By.TAG_NAME,
        "a"
    )

    for a in anchors:

        href = a.get_attribute("href")

        if not href:
            continue

        href_lower = href.lower()

        if "/jobs/" in href_lower:

            href = href.split("?")[0]

            links.add(href)

    return links
    
def get_title(driver):

    selectors = [

        "h1",

        "[data-testid='job-title']",

        ".job-title",

        ".job-header h1"

    ]

    for selector in selectors:

        try:

            return driver.find_element(
                By.CSS_SELECTOR,
                selector
            ).text.strip()

        except:
            pass

    return ""
    
def get_company(driver):

    selectors = [

        "[data-testid='company-name']",

        ".company-name",

        ".job-company"

    ]

    for selector in selectors:

        try:

            return driver.find_element(
                By.CSS_SELECTOR,
                selector
            ).text.strip()

        except:
            pass

    return ""
    
def get_location(driver):

    selectors = [

        "[data-testid='job-location']",

        ".job-location",

        ".location"

    ]

    for selector in selectors:

        try:

            return driver.find_element(
                By.CSS_SELECTOR,
                selector
            ).text.strip()

        except:
            pass

    return ""
    
def get_description(driver):

    selectors = [

        "[data-testid='job-description']",

        ".job-description",

        ".description",

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

            page_links = collect_links(driver)

            logger.write(
                f"Found {len(page_links)} links"
            )

            all_links.update(page_links)

            logger.write(
                f"Unique links: {len(all_links)}"
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

            f"""Company:
{job['company']}

Location:
{job['location']}

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

    for index, url in enumerate(urls, start=1):

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

    logger.write("\n" + "=" * 60)

    logger.write("RANDSTAD SUMMARY")

    logger.write("=" * 60)

    logger.write(
        f"Links : {len(exporter.links)}"
    )

    logger.write(
        f"Jobs  : {len(exporter.jobs)}"
    )

    logger.write(
        f"Failed: {len(exporter.failed)}"
    )

    logger.write("=" * 60)
    
def scrape(base_url, output_folder):
    """
    Main entry point for the Randstad scraper.
    """

    logger = Logger("Randstad")

    exporter = Exporter(output_folder)

    driver = None

    logger.write("=" * 70)
    logger.write("RANDSTAD SCRAPER STARTED")
    logger.write("=" * 70)

    logger.write(f"Search URL : {base_url}")
    logger.write(f"Output Folder : {output_folder}")

    try:

        logger.write("\nLaunching browser...")

        driver = create_driver()

        keyword = search_keyword(base_url)

        logger.write(f"Search Keyword : {keyword}")

        logger.write("\nCollecting job links...")

        job_urls = crawl_links(
            driver=driver,
            base_url=base_url,
            logger=logger
        )

        logger.write(
            f"Collected {len(job_urls)} unique links."
        )

        master_dir = os.path.join("outputs","Randstad")
        os.makedirs(master_dir, exist_ok=True)

        master_file = os.path.join(
            master_dir,
            "Master_Randstad.xlsx"
        )

        job_urls = remove_existing_urls(
            job_urls,
            master_file
        )

        logger.write(
            f"New jobs to scrape: {len(job_urls)}"
        )

        if len(job_urls) == 0:

            logger.write(
                "No jobs found."
            )

            return

        logger.write("\nExtracting job descriptions...")

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

        logger.write("\nSaving output files...")

        exporter.save()

        print_summary(
            exporter,
            logger
        )

        logger.write(
            "\nRandstad scraping completed successfully."
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
        logger.write("RANDSTAD SCRAPER FINISHED")
        logger.write("=" * 70)