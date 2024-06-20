import time
import logging
import os
from os.path import exists
import pandas as pd
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from utills import get_html_content

# Configure the logging settings
logging.basicConfig(filename='scraping_log.txt', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


def generate_article_url(base_url: str, article_num: int) -> str:
    return f"{base_url}{article_num}/"


def extract_article_number(url: str) -> int:
    parts = url.split('/')
    article_number = parts[-2]  # -2 because the last part is '', so we take the second last
    return int(article_number)


def get_next_article_url(current_url: str, base_url: str) -> str:
    current_article_number = extract_article_number(current_url)
    next_article_number = current_article_number + 1
    next_article_url = generate_article_url(base_url, next_article_number)
    return next_article_url


def get_next_article_url(current_url: str, base_url: str) -> str:
    current_article_number = extract_article_number(current_url)
    next_article_number = current_article_number + 1
    next_article_url = generate_article_url(base_url, next_article_number)
    return next_article_url


def get_article_date(article_page) -> str:
    date_element = article_page.find('p', class_='date')
    if date_element:
        return date_element.text.strip().split(maxsplit=1)[0]
    else:
        return "No date available"


def get_article_title(article_page) -> str:
    title_element = article_page.find('h1', class_='title')
    if title_element:
        return title_element.text.strip()
    else:
        return "No title available"


def get_article_category(article_page) -> str:
    category_element = article_page.find('div', class_='breadcrumbs')
    if category_element:
        return category_element.find('a').text.strip()
    else:
        return "No category available"


def get_article_tags(article_page) -> list:
    tags = []
    tags_element = article_page.find('div', class_='tags')
    if tags_element:
        tag_links = tags_element.find_all('a')
        for tag_link in tag_links:
            tag_span = tag_link.find('span')
            if tag_span:
                tags.append(tag_span.text.strip())
    return tags


def get_article_full_text(article_page) -> str:
    text_element = article_page.find(class_="markdown-body checkpoint__loader")
    paragraphs = text_element.find_all('p') if text_element else []
    full_text = ' '.join([paragraph.text.strip() for paragraph in paragraphs])
    return full_text


def process_article(df, article_url):
    """Process an article URL and add data to the DataFrame."""
    logging.info(f"Scraping data from article URL: {article_url}")
    article_page_content = get_html_content(article_url)
    article_page = BeautifulSoup(article_page_content, 'html.parser') if article_page_content else None

    if article_page and article_page.find(class_="page-404"):
        raise ValueError("404 Page Not Found")

    if article_page:
        title = get_article_title(article_page)
        print(title)
        content = get_article_full_text(article_page)
        date = get_article_date(article_page)
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