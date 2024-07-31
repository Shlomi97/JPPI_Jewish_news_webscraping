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


def get_title(article_page):
    # Find the <h1> element with the class and itemprop attributes
    title_element = article_page.find('h1', class_='mvp-post-title', attrs={"itemprop": "headline"})

    if title_element:
        return title_element.get_text(strip=True)
    else:
        return "No Title"


def get_date(article_page):
    # Find the <time> element with the itemprop attribute and class name containing 'post-date'
    date_element = article_page.find('time', attrs={"itemprop": "datePublished"})

    if date_element and 'post-date' in date_element.get('class', []):
        return date_element.get_text(strip=True)
    else:
        return "No date"


def get_article_category(article_page) -> str:
    # Find the <h3> element with the class "mvp-post-cat"
    category_element = article_page.find('h3', class_='mvp-post-cat')

    if category_element:
        # Find the <span> within the <a> tag inside the <h3>
        category_span = category_element.find('span', class_='mvp-post-cat')
        if category_span:
            return category_span.text.strip()

    return "No category available"


def get_article_tags(article_page) -> list:
    tags = []
    # Find the <span> element with itemprop="keywords"
    tags_element = article_page.find('span', itemprop='keywords')

    if tags_element:
        # Find all <a> tags within the found <span>
        tag_links = tags_element.find_all('a')
        for tag_link in tag_links:
            # Append the text of each <a> tag, stripping any extra whitespace
            tags.append(tag_link.text.strip())

    return tags


def get_article_full_text(article_page):
    content_div = article_page.find('div', id='mvp-content-main')
    if content_div:
        paragraphs = content_div.find_all('p')
        full_text = ' '.join([paragraph.text.strip() for paragraph in paragraphs])
        return full_text.replace('\n', '').replace('\t', ' ')
    else:
        return "No article content available"


def process_article(df, article_url):
    """Process an article URL and add data to the DataFrame."""
    logging.info(f"Scraping data from article URL: {article_url}")
    article_page_content = get_html_content(article_url)
    article_page = BeautifulSoup(article_page_content, 'html.parser')
    if article_page:
        title = get_title(article_page)
        print(title)
        content = get_article_full_text(article_page)
        date = get_date(article_page)
        category = get_article_category(article_page)
        tags = get_article_tags(article_page)

        new_row = pd.DataFrame([{
            "date": date,
            "title": title,
            "content": content,
            "url": article_url,
            "category": category,
            "tags": tags
        }])

        df = pd.concat([df, new_row], ignore_index=True)
        logging.info(f"Data for {article_url} added to DataFrame")
        time.sleep(6)
    else:
        logging.warning(f"Failed to fetch content from article URL: {article_url}")

    return df

