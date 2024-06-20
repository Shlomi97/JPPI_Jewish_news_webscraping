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
