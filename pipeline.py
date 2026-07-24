JOBS = {
    "scrape": {
        "name": "Job Scraper",
        "script": "main.py",
        "depends": []
    },

    "filter": {
        "name": "JD Filter",
        "script": "JD_filter/jd_filter.py",
        "depends": ["scrape"]
    }
}