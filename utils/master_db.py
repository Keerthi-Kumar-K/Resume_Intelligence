import os
import pandas as pd
from datetime import datetime


COLUMNS = [
    "URL",
    "Title",
    "Company",
    "Location",
    "Date Added"
]


def load_master(master_file):

    if not os.path.exists(master_file):

        df = pd.DataFrame(columns=COLUMNS)
        df.to_excel(master_file, index=False)
        return set()

    df = pd.read_excel(master_file)

    if "URL" not in df.columns:
        return set()

    return set(df["URL"].dropna().astype(str))


def remove_existing_urls(urls, master_file):

    existing = load_master(master_file)

    return [u for u in urls if u not in existing]


def append_to_master(jobs, master_file):

    if os.path.exists(master_file):
        master = pd.read_excel(master_file)
    else:
        master = pd.DataFrame(columns=COLUMNS)

    rows = []

    for url, title, body in jobs:

        company = ""
        location = ""

        for line in body.splitlines():

            if line.startswith("Company:"):
                company = line.replace("Company:", "").strip()

            elif line.startswith("Location:"):
                location = line.replace("Location:", "").strip()

        rows.append([
            url,
            title,
            company,
            location,
            datetime.now().strftime("%Y-%m-%d")
        ])

    new_df = pd.DataFrame(rows, columns=COLUMNS)

    master = pd.concat([master, new_df], ignore_index=True)

    master.drop_duplicates(
        subset=["URL"],
        inplace=True
    )

    master.to_excel(master_file, index=False)