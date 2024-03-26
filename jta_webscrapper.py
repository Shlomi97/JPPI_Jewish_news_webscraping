import logging
import os
import time
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

def process_article(df, article_url):
    """Process an article URL and add data to the DataFrame."""
    logging.info(f"Scraping data from article URL: {article_url}")
    article_page = get_html_content(article_url)
    soup = BeautifulSoup(article_page, "html.parser")
    if article_page is not None:
        title = get_article_title_jta(soup)
        content = get_full_article_jta(soup)
        date = get_date_from_article_jta(soup)
        tags = get_tags_jta(soup)
        authors = get_author_jta(soup)
        new_row = pd.DataFrame([{
            "date": date,
            "title": title,
            "content": content,
            "urls": article_url,
            "tags": tags,
            "authors":authors

        }])
        df = pd.concat([df, new_row], ignore_index=True)
        print(f"Data for {article_url} added to DataFrame")
        logging.info(f"Data for {article_url} added to DataFrame")
        time.sleep(2)
    else:
        logging.warning(f"Failed to fetch content from article URL: {article_url}")

    return df

def fetch_all_data_jta(base_url, n, file_path='jta.csv'):
    """Fetch data from pages and articles."""
    df = read_existing_data(file_path)
    generated_urls = generate_page_urls(base_url, n)

    temp_df = pd.DataFrame(
        columns=["date", "title", "content", "urls", "tags", "authors"])  # Initialize a temporary DataFrame

    for url in generated_urls:
        logging.info(f"Processing page URL: {url}")
        print(f"Processing page URL: {url}")
        page = get_html_content(url)
        if page is None:
            continue
        articles_urls = get_articles_urls_from_page_jta(url)
        break_outer_loop = False  # Flag to control the outer loop
        for article_url in articles_urls:
            print(article_url)
            if article_url in df['urls'].values:
                logging.info(f"Article {article_url} already processed. Stopping loop.")
                break_outer_loop = True
                break
            try:
                df = process_article(df, article_url)
            except Exception as e:
                logging.error(f"Error processing article {article_url}: {e}")
        if break_outer_loop:
            break  # Break out of outer loop
    temp_df['date'] = pd.to_datetime(temp_df['date']).dt.strftime('%d-%b-%y')
    # Concatenate temp_df with df to maintain the correct order
    df = pd.concat([temp_df, df], ignore_index=True)

    # Save the final DataFrame to the specified file path
    df.to_csv(file_path, index=False, encoding='utf-8')

    logging.info("Script execution completed jta ")

    return df