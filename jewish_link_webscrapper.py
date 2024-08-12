import logging
import requests
import time
import os
import pandas as pd
from requests.adapters import HTTPAdapter
from bs4 import BeautifulSoup
from requests.packages.urllib3.util.retry import Retry

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
from utills import get_html_content, read_existing_data


def generate_page_urls(base_url: str, n: int) -> list:
    urls = []
    for i in range(1, n):
        url = f"{base_url}{i}/"
        urls.append(url)
    return urls
