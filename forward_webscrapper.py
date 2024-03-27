import logging
import os
import time
import pandas as pd
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from utills import get_html_content, read_existing_data

def get_title_forward(article_page):
    title_element = article_page.find('h1' ,class_="heading-2")
    if title_element:
        return title_element.text.strip()
    else:
        return "No Title"

def get_category_forward(article_page):
    title_element = article_page.find('a' ,class_="eyebrow small black")
    if title_element:
        return title_element.text.strip()
    else:
        return "No Category"

def get_tags_forward(article_page )- >list:
    tags_element = article_page.find("ul" ,class_="tags-list")
    if tags_element:
        tags = tags_element.find_all("li")
        return [tag.text.strip() for tag in tags]
    else:
        return "No Tags"

def get__author_forward(article_page):
    # Check first for 'no-avatar' class
    author_element = article_page.find("div", class_="post-author no-avatar")
    if author_element:
        author_link = author_element.find('a')
        if author_link:  # Ensure there's an <a> tag to avoid AttributeError
            return author_link.text.strip()

    # If not found, check for 'single' class
    author_element = article_page.find("div", class_="post-author single")
    if author_element:
        author_link = author_element.find('a')
        if author_link:  # Ensure there's an <a> tag to avoid AttributeError
            return author_link.text.strip()

    return "Could not get author name"

def get_date_forward(article_page):
    # Check first for 'no-avatar' classs
    author_element = article_page.find("div", class_="post-author no-avatar")
    if author_element:
        date_span = author_element.find('span')  # Corrected variable name
        if date_span:  # Corrected condition to check the right variable
            return date_span.text.strip()  # Corrected variable name

    # If not found, check for 'single' class
    author_element = article_page.find("div", class_="post-author single")
    if author_element:
        date_span = author_element.find('span')  # Use the same corrected variable name for consistency
        if date_span:  # Ensure there's a span tag to avoid AttributeError
            return date_span.text.strip()  # Corrected variable name

    return "Could not get article date"

def get_full_article_forward(article_page):
    paragraphs = article_page.find("article").find_all("p")
    full_text = ' '.join([paragraph.text.strip() for paragraph in paragraphs])
    return full_text.replace('\n', '').replace('\t', ' ')

def process_article(df, article_url):
    """Process an article URL and add data to the DataFrame."""
    logging.info(f"Scraping data from article URL: {article_url}")
    article_page = get_html_content(article_url)
    soup = BeautifulSoup(article_page, "html.parser")
    if article_page is not None:
        title = get_title_forward(soup)
        category = get_category_forward(soup)
        content = get_full_article_forward(soup)
        date = get_date_forward(soup)
        tags = get_tags_forward(soup)
        authors = get_author_forward(soup)
        new_row = pd.DataFrame([{
            "date": date,
            "title": title,
            "category" :category,
            "content": content,
            "urls": article_url,
            "tags": tags,
            "authors" :authors

        }])
        df = pd.concat([df, new_row], ignore_index=True)
        print(f"Data for {article_url} added to DataFrame")
        logging.info(f"Data for {article_url} added to DataFrame")
        time.sleep(2)
    else:
        logging.warning(f"Failed to fetch content from article URL: {article_url}")

    return df