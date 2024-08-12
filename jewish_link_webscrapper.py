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


def get_articles_urls_from_page(page_url) -> list:
    page_content = get_html_content(page_url)
    soup = BeautifulSoup(page_content, "html.parser")

    urls = []

    if soup:
        # Find all h3 elements with the specified classes
        h3_tags = soup.find_all('h3', class_=['ctitle ctitle--white', 'cheadlinetitle'])
        print(h3_tags)
        for h3 in h3_tags:
            # Find the <a> tag inside each h3 and get the href attribute
            a_tag = h3.find('a')
            if a_tag and a_tag.has_attr('href'):
                urls.append(a_tag['href'])
    else:
        return []

    return urls


def get_title(article_page) -> str:
    title_element = article_page.find('h1', class_="ej-section-single__title")
    if title_element:
        title = title_element.text.strip()
        return title
    else:
        return "No Title"


def get_date(article_page) -> str:
    date_element = article_page.find('div', class_="ej-single-content__date")
    if date_element:
        date = date_element.text.strip()
        return date
    else:
        return None


def get_full_article(article_page) -> str:
    content_block = article_page.find('div', class_="editor-style")
    if content_block:
        paragraphs = content_block.find_all('p')
        full_text = ' '.join([paragraph.text.strip() for paragraph in paragraphs[:-3]])
        return full_text.replace('\n', '').replace('\t', ' ')
    # Replace newline characters
    else:
        return "No article content available"


def get_tags(article_page) -> list:
    tags = []
    tags_div = article_page.find('div', class_="ej-single-content__tags")
    if tags_div:
        tags_links = tags_div.find_all('a')
        for tag_link in tags_links:
            tags.append(tag_link.text.strip())
    return tags


def get_categories(article_page) -> list:
    # Find the categories div
    categories = []
    categories_div = article_page.find('div', class_="ej-section-single__categories")
    if categories_div:
        category_links = categories_div.find_all('a')
        for category_link in category_links:
            categories.append(category_link.text.strip())
    return categories


def process_article(df, article_url):
    """Process an article URL and add data to the DataFrame."""
    logging.info(f"Scraping data from article URL: {article_url}")
    article_page = get_html_content(article_url)
    soup = BeautifulSoup(article_page, "html.parser")
    if article_page is not None:
        title = get_title(soup)
        content = get_full_article(soup)
        date = get_date(soup)
        tags = get_tags(soup)
        category = get_categories(soup)
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

def fetch_all_data_jewish_link(base_url, n, file_path='jewish_link.csv'):
    """Fetch data from pages and articles."""
    df = read_existing_data(file_path)
    generated_urls = generate_page_urls(base_url, n)
    temp_df = pd.DataFrame(
        columns=["date", "title", "content", "urls", "tags", "category"])  # Initialize a temporary DataFrame

    for url in generated_urls:
        print(f'main url:{url}')
        logging.info(f"Processing page URL: {url}")
        print(f"Processing page URL: {url}")
        page = get_html_content(url)
        if page is None:
            continue
        articles_urls = get_articles_urls_from_page(url)
        print(articles_urls)
        break_outer_loop = False  # Flag to control the outer loop
        for article_url in articles_urls:
            print(article_url)
            if article_url in df['urls'].values:
                logging.info(f"Article {article_url} already processed. Stopping loop.")
                break_outer_loop = True
                break
            try:
                temp_df = process_article(temp_df, article_url)
                print('the df is filling itself',len(temp_df))
            except Exception as e:
                logging.error(f"Error processing article {article_url}: {e}")
        if break_outer_loop:
            break  # Break out of outer loop
    temp_df = temp_df.reset_index(drop=True)
    # Concatenate temp_df with df to maintain the correct order
    df_combined = pd.concat([temp_df,df], ignore_index=True).reset_index(drop=True)

    # Save the final DataFrame to the specified file path
    df_combined.to_csv(file_path, index=False,encoding='utf-8')

    logging.info("Script execution completed Jewish Link ")

    return df_combined