import logging
import requests
import os
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# Configure the logging settings
logging.basicConfig(filename='scraping_log.txt', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


def get_html_content(url: str):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"}
    session = requests.Session()
    retry = Retry(connect=3, backoff_factor=0.5)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)

    try:
        logging.info(f"Fetching content from {url}")
        response = session.get(url, headers=headers)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx and 5xx)
        html_content = response.content
        logging.info("Webpage content fetched successfully")
        return html_content
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to fetch webpage content. Error: {e}")
        return None


def read_existing_data(file_path: str, columns=("date", "title", "content", "urls", "tags", "authors")):
    """Read existing data from CSV file."""
    if os.path.exists(file_path):
        return pd.read_csv(file_path)
    else:
        return pd.DataFrame(columns=columns)
