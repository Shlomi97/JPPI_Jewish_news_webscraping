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


def fetch_all_data_jewish_ru(base_url, file_path='jewish_ru.csv'):
    """Fetch data from pages and articles."""
    if exists(file_path):
        df_existing = pd.read_csv(file_path)
    else:
        df_existing = pd.DataFrame(columns=["date", "title", "content", "url", "category", "tags"])

    last_article_num = extract_article_number(df_existing['urls'].iloc[0]) if len(df_existing) > 0 else 199000
    print(last_article_num)
    article_url = generate_article_url(base_url, last_article_num + 1)
    df_new = pd.DataFrame(columns=["date", "title", "content", "urls", "category", "tags"])

    consecutive_404_count = 0  # Track consecutive 404 errors

    try:
        while consecutive_404_count < 7:
            print(article_url)
            try:
                df_new = process_article(df_new, article_url)
                # Save the final DataFrame to the specified file path
                consecutive_404_count = 0  # Reset counter upon successful fetch
            except ValueError as ve:
                if str(ve) == "404 Page Not Found":
                    logging.info("404 Page encountered.")
                    consecutive_404_count += 1
                    if consecutive_404_count == 7:
                        df_new['date'] = pd.to_datetime(df_new['date'], format='%d.%m.%Y')
                        df = pd.concat([df_new, df_existing], ignore_index=True)
                        break  # Exit loop if three consecutive 404 errors occur
            except KeyboardInterrupt:
                logging.info("Execution interrupted by the user.")
                break
            except Exception as e:
                logging.error(f"An error occurred: {e}")

            article_url = get_next_article_url(article_url, base_url)

    except KeyboardInterrupt:
        logging.info("Execution interrupted by the user.")
    except Exception as e:
        logging.error(f"An error occurred: {e}")
    df.to_csv(file_path, index=False)
    print(f"Updated data saved to {file_path}. Total records: {len(df)}")
    logging.info(f"Script execution complete jewish_ru")


    return df
