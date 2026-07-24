import time
import re

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException

from urllib.parse import urlparse, parse_qs

from config import (
    MAX_PAGES,
    PAGE_LOAD_WAIT,
    SCROLL_PAUSE,
    RETRY_COUNT
)

from utils.browser import create_driver
from utils.filters import is_data_role
from utils.cleaner import clean_text
from utils.exporter import Exporter
from utils.logger import Logger

from utils.master_db import (
    remove_existing_urls,
    append_to_master
)

import os

def wait_page(driver):

    WebDriverWait(driver,30).until(

        lambda d:
        d.execute_script(
            "return document.readyState"
        )=="complete"

    )
    
def scroll_page(driver):

    last=0

    while True:

        driver.execute_script(

            "window.scrollTo(0,document.body.scrollHeight)"

        )

        time.sleep(SCROLL_PAUSE)

        new=driver.execute_script(

            "return document.body.scrollHeight"

        )

        if new==last:

            break

        last=new
        
def search_keyword(url):

    query=parse_qs(

        urlparse(url).query

    )

    return query.get(

        "q",

        ["dice"]

    )[0]
    
def page_url(base,page):

    if "page=" in base:

        return re.sub(

            r"page=\d+",

            f"page={page}",

            base

        )

    sep="&" if "?" in base else "?"

    return base+f"{sep}page={page}"
    
def collect_links(driver):

    urls=set()

    cards=driver.find_elements(

        By.CSS_SELECTOR,

        "a[href*='/job-detail/']"

    )

    for card in cards:

        href=card.get_attribute("href")

        if not href:

            continue

        href=href.split("?")[0]

        urls.add(href)

    return urls

def get_title(driver):

    try:

        return driver.find_element(

            By.TAG_NAME,

            "h1"

        ).text.strip()

    except:

        return ""

def get_company(driver):

    try:

        x=driver.find_element(

            By.CSS_SELECTOR,

            "[data-cy='companyName']"

        )

        return x.text.strip()

    except:

        return ""
        
def get_location(driver):

    try:

        x=driver.find_element(

            By.CSS_SELECTOR,

            "[data-cy='location']"

        )

        return x.text.strip()

    except:

        return ""
        
def get_description(driver):

    try:

        body=driver.execute_script(

            "return document.body.innerText"

        )

        return clean_text(body)

    except:

        return ""
        
def scrape_job(driver,url):

    driver.get(url)

    wait_page(driver)

    time.sleep(2)

    title=get_title(driver)

    if not is_data_role(title):

        return None

    company=get_company(driver)

    location=get_location(driver)

    description=get_description(driver)

    return {

        "url":url,

        "title":title,

        "company":company,

        "location":location,

        "description":description

    }

def crawl_links(driver, base_url, logger):

    all_links = set()

    previous_count = 0

    for page in range(1, MAX_PAGES + 1):

        url = page_url(base_url, page)

        logger.write(f"\nPage {page}")

        try:

            driver.get(url)

            wait_page(driver)

            time.sleep(PAGE_LOAD_WAIT)

            scroll_page(driver)

            links = collect_links(driver)

            logger.write(f"Found {len(links)} links")

            all_links.update(links)

            logger.write(f"Total unique links : {len(all_links)}")

            # no new links found
            if len(all_links) == previous_count:

                logger.write("No new jobs. Stopping.")

                break

            previous_count = len(all_links)

        except Exception as e:

            logger.write(str(e))

            continue

    return sorted(all_links)

def scrape_with_retry(driver, url):

    for attempt in range(RETRY_COUNT):

        try:

            job = scrape_job(driver, url)

            if job:

                return job

        except Exception:

            pass

        time.sleep(2)

    return None
    
def export_job(exporter, job):
    """
    Add one successfully scraped Dice job to the exporter.
    """

    url = job.get("url", "")
    title = job.get("title", "")
    company = job.get("company", "")
    location = job.get("location", "")
    description = job.get("description", "")

    if url and url not in exporter.links:
        exporter.links.append(url)

    formatted_description = (
        f"Company: {company or 'Not available'}\n"
        f"Location: {location or 'Not available'}\n\n"
        f"{description}"
    )

    exporter.jobs.append(
        (
            url,
            title,
            formatted_description
        )
    )
    
def scrape_all_jobs(driver, urls, exporter, logger):

    total = len(urls)

    logger.write(f"\nScraping {total} jobs")

    for i, url in enumerate(urls, start=1):

        logger.write(f"[{i}/{total}]")

        job = scrape_with_retry(driver, url)

        if job is None:

            exporter.failed.append(url)

            logger.write("Failed")

            continue

        export_job(exporter, job)

        logger.write(job["title"])
        
def print_summary(exporter, logger):
    logger.write("\n" + "=" * 70)
    logger.write("DICE SCRAPING SUMMARY")
    logger.write("=" * 70)

    logger.write(
        f"Links collected: {len(exporter.links)}"
    )

    logger.write(
        f"Jobs successfully saved: {len(exporter.jobs)}"
    )

    logger.write(
        f"Failed URLs: {len(exporter.failed)}"
    )

    logger.write("=" * 70)
    
def scrape(base_url, output_folder):
    """
    Main entry point for the Dice scraper.

    Parameters
    ----------
    base_url : str
        Dice search-results URL entered by the user.

    output_folder : str or Path
        Folder created by main.py for this scraping run.
    """

    logger = Logger("Dice")
    exporter = Exporter(output_folder)
    driver = None

    logger.write("=" * 70)
    logger.write("DICE SCRAPER STARTED")
    logger.write("=" * 70)
    logger.write(f"Search URL: {base_url}")
    logger.write(f"Output Folder: {output_folder}")

    try:
        # --------------------------------------------------
        # START BROWSER
        # --------------------------------------------------

        logger.write("\nLaunching browser...")

        driver = create_driver()

        # --------------------------------------------------
        # READ SEARCH KEYWORD
        # --------------------------------------------------

        keyword = search_keyword(base_url)

        logger.write(f"Search Keyword: {keyword}")

        # --------------------------------------------------
        # COLLECT UNIQUE JOB LINKS
        # --------------------------------------------------

        logger.write("\nCollecting Dice job links...")

        job_urls = crawl_links(
            driver=driver,
            base_url=base_url,
            logger=logger
        )

        logger.write(
            f"Total unique job links collected: {len(job_urls)}"
        )

        # --------------------------------------------------
        # REMOVE ALREADY SCRAPED JOBS
        # --------------------------------------------------

        master_dir = os.path.join("outputs", "Dice")
        os.makedirs(master_dir, exist_ok=True)

        master_file = os.path.join(
            master_dir,
            "Master_Dice.xlsx"
        )

        job_urls = remove_existing_urls(
            job_urls,
            master_file
        )

        logger.write(
            f"New jobs to scrape: {len(job_urls)}"
        )

        if not job_urls:
            logger.write("No new jobs found.")
            return

        if not job_urls:
            logger.write(
                "No Dice job links were found. Scraper stopped."
            )
            return

        # Save collected links before JD extraction.
        # This preserves the links even if the browser later fails.
        for url in job_urls:
            if url not in exporter.links:
                exporter.links.append(url)

        # --------------------------------------------------
        # SCRAPE JOB DETAILS
        # --------------------------------------------------

        logger.write("\nStarting job-description extraction...")

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

        # --------------------------------------------------
        # EXPORT OUTPUT FILES
        # --------------------------------------------------

        logger.write("\nSaving output files...")

        exporter.save()

        # --------------------------------------------------
        # FINAL SUMMARY
        # --------------------------------------------------

        print_summary(
            exporter=exporter,
            logger=logger
        )

        logger.write(f"Files saved in: {output_folder}")

    except KeyboardInterrupt:
        logger.write(
            "\nScraping was stopped manually by the user."
        )

        # Preserve everything collected before interruption.
        try:
            exporter.save()
            logger.write("Partial results were saved.")
        except Exception as save_error:
            logger.write(
                f"Could not save partial results: {save_error}"
            )

    except Exception as error:
        logger.write(
            f"\nFatal Dice scraper error: "
            f"{type(error).__name__}: {error}"
        )

        # Attempt to preserve partial results.
        try:
            exporter.save()
            logger.write("Partial results were saved.")
        except Exception as save_error:
            logger.write(
                f"Could not save partial results: {save_error}"
            )

        raise

    finally:
        # --------------------------------------------------
        # CLOSE BROWSER
        # --------------------------------------------------

        if driver is not None:
            try:
                driver.quit()
                logger.write("Browser closed successfully.")
            except Exception as close_error:
                logger.write(
                    f"Browser cleanup warning: {close_error}"
                )

        logger.write("=" * 70)
        logger.write("DICE SCRAPER FINISHED")
        logger.write("=" * 70)