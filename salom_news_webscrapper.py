import logging
import requests
import time
from os.path import exists
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
    # Function to convert Turkish date to standard date format


def convert_turkish_date(date_str):
    month_map = {
        'Ocak': '01',
        'Şubat': '02',
        'Mart': '03',
        'Nisan': '04',
        'Mayıs': '05',
        'Haziran': '06',
        'Temmuz': '07',
        'Ağustos': '08',
        'Eylül': '09',
        'Ekim': '10',
        'Kasım': '11',
        'Aralık': '12'
    }
    parts = date_str.split()
    day = parts[0]
    month = month_map[parts[1]]
    year = parts[2]
    return f'{year}-{month}-{day}'


def get_title(article_page) -> str:
    title_element = article_page.find('h1', class_="hbr-dty-bslk mtop15 mbot15")
    if title_element:
        title = title_element.text.strip()
        return title
    else:
        return "No Title"


def get_date(article_page):
    date_element = article_page.find_all('span', class_='hbr-dty-meta-item')[-1]
    if date_element:
        return convert_turkish_date(date_element.get_text(strip=True))
    return None


def get_full_article(article_page) -> str:
    content_block = article_page.find('div', class_="col-md-12 mbot15 hicerikdty")
    if content_block:
        paragraphs = content_block.find_all('p')
        full_text = ' '.join([paragraph.text.strip() for paragraph in paragraphs[:-1]])
        return full_text.replace('\n', '').replace('\t', ' ')
    else:
        return "No article content available"


def get_tags(article_page) -> list:
    tags = []
    tags_div = article_page.find('div', class_="htaglist")
    if tags_div:
        tags_links = tags_div.find_all('a')
        for tag_link in tags_links:
            tags.append(tag_link.text.strip())
    return tags


def get_category(article_page):
    category_element = article_page.find_all('span', class_='hbr-dty-meta-item')[0]
    if category_element:
        return category_element.get_text(strip=True)
    return None


def process_article(df, article_url):
    """Process an article URL and add data to the DataFrame."""
    logging.info(f"Scraping data from article URL: {article_url}")
    article_page = get_html_content(article_url)
    if article_page is not None:
        soup = BeautifulSoup(article_page, "html.parser")
        title = get_title(soup)
        content = get_full_article(soup)
        date = get_date(soup)
        tags = get_tags(soup)
        category = get_category(soup)
        new_row = pd.DataFrame([{
            "date": date,
            "title": title,
            "content": content,
            "urls": article_url,
            "tags": tags,
            "category": category
        }])
        df = pd.concat([df, new_row], ignore_index=True)
        print(f"Data for {article_url} added to DataFrame")
        logging.info(f"Data for {article_url} added to DataFrame")
        time.sleep(2)
    else:
        logging.warning(f"Failed to fetch content from article URL: {article_url}")

    return df


def fetch_all_data_salom_news(base_url, file_path='salom_news.csv'):
    if exists(file_path):
        df_existing = pd.read_csv(file_path)
    else:
        df_existing = pd.DataFrame(columns=["date", "title", "content", "url", "category", "tags"])
    df_new = pd.DataFrame(columns=["date", "title", "content", "urls", "category", "tags"])
    last_url = df_existing['url'].iloc[0] if len(df_existing) > 0 else base_url
    while last_url:
        last_url = get_next_url(last_url)
        time.sleep(7)
        df_new = process_article(df_new, last_url)
    df_existing['date'] = pd.to_datetime(df_existing['date'], errors='coerce')
    df_new['date'] = pd.to_datetime(df_new['date'], errors='coerce')
    df = pd.concat([df_new, df_existing], ignore_index=True)
    print(f"Updated data saved to {file_path}. Total records: {len(df)}")
    logging.info(f"Script execution complete salom news")
    return df
