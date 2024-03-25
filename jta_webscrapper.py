import logging
import os
import pandas as pd
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from utills import get_html_content


def generate_page_urls(base_url: str, n: int,
                       url_ending="?s=&amp;from_date=01%2F01%2F2021&amp;to_date=&amp;sort_by=newest&amp;") -> list:
    urls = []
    base_url = base_url + "/page/"
    for i in range(1, n):
        url = f"{base_url}{i}{url_ending}"
        urls.append(url)
    return urls


def get_articles_urls_from_page(page_url) -> list:
    page_content = get_html_content(page_url)
    soup = BeautifulSoup(page_content, "html.parser")
    urls = soup.find_all('h2', class_='entry-title content-meta__title')
    urls = [url.find('a').get('href') for url in urls if url.find('a')]
    return urls


def get_article_title_jta(article_page) -> str:
    title = article_page.find('h1', class_="entry-title").text.strip()
    return title


def get_date_from_article_jta(article_page) -> str:
    date = article_page.find('span', class_="post-meta-info__date").text.strip()
    return date


def get_full_article_jta(article_page) -> str:
    paragraphs = article_page.find(class_="entry-content").find_all("p")
    full_text = ' '.join([paragraph.text.strip() for paragraph in paragraphs])
    # Replace newline characters
    return full_text.replace('\n', '').replace('\t', ' ')


def get_author_jta(article_page) -> str:
    author = article_page.find(class_="post-info__oped-name").text.strip()
    return author


def get_tags_jta(article_page) -> str:
    tag = article_page.find('div', class_="post-categories").text.strip().replace('\t', '').replace('\n', '')
    return tag
