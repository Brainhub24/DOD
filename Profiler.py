#!/usr/bin/env python3

"""
Python Web Scraper for Extracting Biographical Profiles
--------------------------------------------------------
Description:
    This script scrapes biographical profiles from all pages of a specified FQDN.
    It extracts details like profile name, job title, profile URL, and background image URL.
    The script automatically follows pagination to retrieve profiles from all pages.

Version     : v1.6.0
"""

import os
import requests
from bs4 import BeautifulSoup
from tabulate import tabulate
from datetime import datetime
import time
import json

# Configurable FQDN
BASE_URL = "https://www.defense.gov"
BIOGRAPHIES_URL_TEMPLATE = f"{BASE_URL}/About/Biographies/?Page={{}}"
MAX_TITLE_LENGTH = 80  # Max length of job titles for display


def validate_yes_no(prompt):
    """
    Prompt the user for a yes/no response.
    Args:
        prompt (str): The question to ask the user.
    Returns:
        bool: True if the user agrees, False otherwise.
    """
    while True:
        response = input(f"{prompt} (Yes/No or 1/0): ").strip().lower()
        if response in {"yes", "y", "1"}:
            return True
        elif response in {"no", "n", "0"}:
            return False
        else:
            print("Invalid input. Please enter 'Yes', 'No', 'Y', 'N', '1', or '0'.")


def fetch_page_content(url):
    """
    Fetches HTML content from a given URL.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching the page: {e}")
        exit()


def parse_biographies(html_content, current_count=0):
    """
    Parses the HTML content to extract biography information.
    """
    soup = BeautifulSoup(html_content, "html.parser")
    biography_items = soup.find_all("div", class_="item dgov-card-1")
    profiles = []

    for index, item in enumerate(biography_items, start=current_count + 1):
        try:
            onclick_script = item.get("onclick", "")
            profile_url = ""
            if onclick_script:
                start_index = onclick_script.find("('") + 2
                end_index = onclick_script.find("')", start_index)
                profile_url = onclick_script[start_index:end_index]

            poster_div = item.find("div", class_="poster")
            background_image_url = (
                poster_div["style"].split("url(")[-1].strip(");").strip("'\"")
                if poster_div and "background-image" in poster_div.get("style", "")
                else ""
            )

            name_span = item.find("span", class_="adetail-bio-name")
            full_name = name_span.text.strip() if name_span else "N/A"

            job_title_span = item.find("span", class_="bio-job-title")
            job_title = job_title_span.text.strip() if job_title_span else "N/A"

            profiles.append({
                "No": index,
                "Name": full_name,
                "Job Title": job_title,
                "Profile URL": profile_url if profile_url.startswith("http") else f"{BASE_URL}/{profile_url.lstrip('/')}",
                "Background Image URL": background_image_url,
            })
        except Exception as e:
            print(f"Error processing item: {e}")
            continue

    return profiles


def fetch_all_profiles():
    """
    Iterates through all available pages to fetch all profiles.
    """
    profiles = []
    page_number = 1

    print("Fetching biographies page content...")
    while True:
        print(f"  → Processing page {page_number}...")
        url = BIOGRAPHIES_URL_TEMPLATE.format(page_number)
        html_content = fetch_page_content(url)

        page_profiles = parse_biographies(html_content, current_count=len(profiles))
        if not page_profiles:
            print("  → No more profiles found. Stopping pagination.")
            break

        profiles.extend(page_profiles)
        page_number += 1

    print("\nParsing biographies completed.")
    return profiles


def display_profiles(profiles):
    """
    Displays the profiles in a structured table in the console.
    """
    table_data = [
        [
            profile["No"],
            profile["Name"],
            (profile["Job Title"][:MAX_TITLE_LENGTH] + "...") if len(profile["Job Title"]) > MAX_TITLE_LENGTH else profile["Job Title"],
            profile["Profile URL"]
        ]
        for profile in profiles
    ]
    headers = ["No", "Name", "Job Title", "Profile URL"]

    print("\nExtracted Profiles:")
    print(tabulate(sorted(table_data, key=lambda x: x[0]), headers=headers, tablefmt="grid"))


def save_profiles_to_file(profiles):
    """
    Saves the extracted profiles to a JSON file with a date and time in the filename.
    """
    timestamp = time.time()
    date_time = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"profiles_{date_time}.json"

    with open(filename, "w") as file:
        json.dump(profiles, file, indent=4)
    print(f"\nProfiles saved to '{filename}'.")


def main():
    """
    Main function to orchestrate the scraping process.
    """
    os.system("clear")  # Clear the terminal screen
    print("Welcome to the DoD Profile Scraper!")

    if validate_yes_no("Do you want to get all DoD Profiles?"):
        print("\nStarting the profile scraper...\n")
        profiles = fetch_all_profiles()
        display_profiles(profiles)
        save_profiles_to_file(profiles)
        print("\nScraping process completed successfully.")
    else:
        print("\nExiting... No profiles were retrieved.")


if __name__ == "__main__":
    main()
