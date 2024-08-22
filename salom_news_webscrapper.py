import logging
import requests
import time
import os
import pandas as pd
from requests.adapters import HTTPAdapter
from bs4 import BeautifulSoup
from requests.packages.urllib3.util.retry import Retry
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
from utills import get_html_content


def get_next_url(current_url: str) -> str:
    html = get_html_content(current_url)
    # Parse the HTML content with BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')

    # Find the <a> tag with the class "article-nav-previous"
    next_article_link = soup.find('a', class_='article-main-next-prev')
    # Get the href attribute, which contains the URL
    if next_article_link:
        next_url = next_article_link.get('href')
        print(next_url)
        return next_url
    else:
        return None
