import logging
import requests
import time
import os
import pandas as pd
from datetime import datetime, timedelta
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from utills import get_html_content

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def generate_page_url(year: str, month: str):
    return f"https://www.sajr.co.za/{year}/{month}/"


def generate_monthly_page_urls(start_date, end_date):
    urls = []
    current_date = start_date
    while current_date >= end_date:
        year = current_date.year
        month = current_date.month
        url = f'https://www.sajr.co.za/{year}/{month}/'
        urls.append(url)
        if month == 1:
            current_date = datetime(year - 1, 12, 1)
        else:
            current_date = datetime(year, month - 1, 1)
    return urls

def fetch_monthly_urls(url, existing_urls=[]):
    """
    Fetches URLs from a given page and returns URLs that are not in the existing_urls list.

    Parameters:
        url (str): The URL of the page to scrape.
        existing_urls (list): List of URLs that are already known.

    Returns:
        list: List of new URLs found on the page that are not in existing_urls.
    """
    # Set up the web driver (make sure to specify the path to your driver if needed)
    driver = webdriver.Chrome()

    # Open the webpage
    driver.get(url)

    # Initialize the list of URLs
    urls = []

    while True:
        # Find all article elements using the correct CSS selector
        article_elements = driver.find_elements(By.CSS_SELECTOR, 'li.mvp-blog-story-wrap a[rel="bookmark"]')

        # Extract the href attributes from each element
        new_urls = [element.get_attribute('href') for element in article_elements]

        # Add new URLs to the list, avoiding duplicates
        unique_new_urls = [url for url in new_urls if url not in existing_urls and url not in urls]
        urls.extend(unique_new_urls)

        # Break the loop if no new unique URLs are found
        if not unique_new_urls:
            break

        try:
            # Wait for the "More Posts" button to be clickable
            more_posts_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '.mvp-inf-more-but'))
            )
            # Scroll into view before clicking
            driver.execute_script("arguments[0].scrollIntoView();", more_posts_button)
            # Click the "More Posts" button
            ActionChains(driver).move_to_element(more_posts_button).click().perform()
            time.sleep(3)  # Wait for new posts to load
        except (NoSuchElementException, ElementClickInterceptedException, Exception) as e:
            print(f"Exception occurred: {e}")
            break  # Break the loop if the "More Posts" button is not found or cannot be clicked

    # Close the web driver
    driver.quit()

    return urls
