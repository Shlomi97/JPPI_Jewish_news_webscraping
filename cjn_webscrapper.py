import logging
import os
import time

import pandas as pd
from os.path import exists
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from selenium import webdriver
from selenium.common.exceptions import ElementClickInterceptedException, TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from utills import get_html_content

# Set up logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def fetch_new_article_urls_until_known(base_url, existing_urls):
    driver = webdriver.Chrome()
    driver.get(base_url)

    articles_urls = []
    click_attempts = 0
    max_attempts = 5

    try:
        while click_attempts < max_attempts:
            try:
                load_more_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable(
                        (By.CSS_SELECTOR, ".js--load-more-button.feed-pagination__load-more-button"))
                )
                driver.execute_script("arguments[0].scrollIntoView(true);", load_more_button)
                driver.execute_script("window.scrollBy(0, -150);")
                load_more_button.click()
                click_attempts += 1
                print(f"Clicked 'Load More' button {click_attempts} times.")

                WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "article.tease-archive > a"))
                )

            except ElementClickInterceptedException:
                time.sleep(2)
                driver.execute_script("arguments[0].click();", load_more_button)

            urls_elements = driver.find_elements(By.CSS_SELECTOR, "article.tease-archive > a")
            for url_element in urls_elements:
                url = url_element.get_attribute('href')
                if url in existing_urls:
                    print(f"Encountered known URL, stopping: {url}")
                    return articles_urls
                if url not in articles_urls:  # Avoid duplicates in the current session
                    articles_urls.append(url)
                    print(len(articles_urls))

    except TimeoutException:
        print("Reached the end of the page or encountered a timeout.")

    finally:
        driver.quit()
        print(f"Total unique articles collected: {len(articles_urls)}")
        return articles_urls


def get_title_cjn(article_page):
    title_element = article_page.find('h1', attrs={"itemprop": "headline"})

    if title_element:
        return title_element.get_text(strip=True)
    else:
        return "No Title"


def get_author_cjn(article_page):
    author_element = article_page.find('span', attrs={"itemprop": "name"})

    if author_element:
        return author_element.get_text(strip=True)
    else:
        return "No Author"


def get_date_cjn(article_page):
    date_element = article_page.find('time', attrs={"itemprop": "datePublished"})

    if date_element:
        return date_element.get_text(strip=True)
    else:
        return "No date"


def get_full_article_cjn(article_page):
    paragraphs = article_page.find(class_="single-main-content single-main-content--post").find_all("p")
    full_text = ' '.join([paragraph.text.strip() for paragraph in paragraphs])
    return full_text.replace('\n', '').replace('\t', ' ')


def process_article(df, article_url):
    """Process an article URL and add data to the DataFrame."""
    logging.info(f"Scraping data from article URL: {article_url}")
    article_page = get_html_content(article_url)
    soup = BeautifulSoup(article_page, "html.parser")
    if article_page is not None:
        title = get_title_cjn(soup)
        content = get_full_article_cjn(soup)
        date = get_date_cjn(soup)
        authors = get_authors_cjn(soup)
        new_row = pd.DataFrame([{
            "date": date,
            "title": title,
            "content": content,
            "urls": article_url,
            "authors": authors
        }])
        df = pd.concat([df, new_row], ignore_index=True)
        print(f"Data for {article_url} added to DataFrame")
        logging.info(f"Data for {article_url} added to DataFrame")
        time.sleep(2)
    else:
        logging.warning(f"Failed to fetch content from article URL: {article_url}")

    return df

def fetch_all_data_cjn(base_url, file_path='cjn.csv'):
    # Check if the file exists to load existing data
    if exists(file_path):
        df_existing = pd.read_csv(file_path)
        existing_urls = df_existing['urls'].tolist()
    else:
        df_existing = pd.DataFrame(columns=["date", "title", "category", "content", "urls", "tags", "authors"])
        existing_urls = []
    new_urls = fetch_new_article_urls_until_known(base_url, existing_urls)
    df_new = pd.DataFrame(columns=["date", "title", "category", "content", "urls", "tags", "authors"])
    for url in new_urls:
        df_new = process_article(df_new, url)
    df_combined = pd.concat([df_new,df_existing],ignore_index=True).drop_duplicates(subset=['urls']).reset_index(drop=True)

    df_combined.to_csv(file_path, index=False)
    print(f"Updated data saved to {file_path}. Total records: {len(df_combined)}")
    logging.info(f"Script execution completed forward ")

