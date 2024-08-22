import logging
import time
import pandas as pd
from os.path import exists
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utills import get_html_content


def fetch_new_article_urls_until_known(base_url, existing_urls):
    driver = webdriver.Chrome()  # Adjust the path if necessary
    driver.get(base_url)
    articles_urls = []  # Initialize as a list for preserving order
    click_attempts = 0
    max_attempts = 30  # Adjust based on how many times you want to click "Load More"

    try:
        while click_attempts < max_attempts:
            time.sleep(2)
            try:
                load_more_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "div.item.load-more > a"))
                )
                driver.execute_script("arguments[0].scrollIntoView(true);", load_more_button)
                driver.execute_script("window.scrollBy(0, -150);")
                load_more_button.click()
                click_attempts += 1
                logging.info(f"Clicked 'Load More' button {click_attempts} times.")
                time.sleep(2)
            except Exception as e:
                logging.error(f"Failed to click 'Load More': {e}")
                print(e)
                break  # Break out of loop if unable to click "Load More"

            urls_elements = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.headline > a"))
            )
            for url_element in urls_elements:
                article_url = url_element.get_attribute('href')
                if article_url in existing_urls:
                    logging.info("URL already extracted, stopping the process.")
                    break  # Break the loop if URL is already extracted
                if article_url not in articles_urls:
                    articles_urls.append(article_url)
            else:
                continue  # Only executed if the inner loop did NOT break
            break  # Break the outer loop if the inner loop DID break
            time.sleep(2)

    except Exception as general_exception:
        logging.error(f"An error occurred: {general_exception}")

    finally:
        # Remove duplicates and filter out existing URLs
        new_articles_urls = [url for url in list(dict.fromkeys(articles_urls)) if url not in existing_urls]
        logging.info(f"Total new unique articles collected: {len(new_articles_urls)}")
        driver.quit()
        return new_articles_urls


def get_title_jewish_news(article_page):
    title_element = article_page.find(class_="headline")
    return title_element.text.strip() if title_element else "No Title"


def get_tags_jewish_news(article_page):
    tags = []
    topics_div = article_page.find("div", class_="article-topics")
    if topics_div:
        tag_links = topics_div.find_all("a")
        for link in tag_links:
            tags.append(link.text.strip())
    return tags


def get_authors_jewish_news(article_page):
    authors = []
    byline_div = article_page.find("div", class_="wrap-byline")
    if byline_div:
        author_links = byline_div.find_all("a", class_="byline-link")
        for link in author_links:
            authors.append(link.text.strip())
    return authors


def get_date_jewish_news(article_page):
    date = "No Date"
    byline_div = article_page.find("div", class_="wrap-byline")
    if byline_div:
        date_span = byline_div.find("span", class_="date")
        if date_span:
            date = date_span.text.strip()
    return date


def get_full_article_jewish_news(article_page):
    content_div = article_page.find("div", class_="the-content")
    if content_div:
        # Extract all paragraphs, ignoring non-text elements and join them into a single string
        paragraphs = content_div.find_all("p")
        full_text = ' '.join(paragraph.text for paragraph in paragraphs if paragraph.text)
        return full_text.replace('\n', ' ').replace('\t', ' ').strip()
    else:
        return "Article content not found."


def process_article(df, article_url):
    """Process a Jewish News article URL and add data to the DataFrame."""
    logging.info(f"Scraping data from article URL: {article_url}")
    article_page = get_html_content(article_url)
    if article_page is not None:
        soup = BeautifulSoup(article_page, "html.parser")
        title = get_title_jewish_news(soup)
        content = get_full_article_jewish_news(soup)
        date = get_date_jewish_news(soup)
        tags = get_tags_jewish_news(soup)
        authors = get_authors_jewish_news(soup)
        new_row = pd.DataFrame([{
            "date": date,
            "title": title,
            "content": content,
            "urls": article_url,
            "tags": tags,
            "authors": authors
        }])
        df = pd.concat([df, new_row], ignore_index=True)
        print(f"Data for {article_url} added to DataFrame")
        logging.info(f"Data for {article_url} added to DataFrame")
        time.sleep(2)
    else:
        logging.warning(f"Failed to fetch content from article URL: {article_url}")

    return df


def fetch_all_data_jewish_news(base_url, file_path='Jewish_news.csv'):
    # Check if the file exists to load existing data
    if exists(file_path):
        df_existing = pd.read_csv(file_path)
        existing_urls = df_existing['urls'].tolist()
    else:
        df_existing = pd.DataFrame(columns=["date", "title", "content", "urls", "tags", "authors"])
        existing_urls = []
    new_urls = fetch_new_article_urls_until_known(base_url, existing_urls)
    df_new = pd.DataFrame(columns=["date", "title", "content", "urls", "tags", "authors"])
    for url in new_urls:
        df_new = process_article(df_new, url)
    df_existing['date'] = pd.to_datetime(df_existing['date'], errors='coerce',format='mixed')
    df_new['date'] = pd.to_datetime(df_new['date'], errors='coerce',format='mixed')
    df_combined = pd.concat([df_new, df_existing], ignore_index=True).drop_duplicates(subset=['urls']).reset_index(
        drop=True)

    df_combined.to_csv(file_path, index=False)
    print(f"Updated data saved to {file_path}. Total records: {len(df_combined)}")
    logging.info(f"Script execution completed {file_path} ")
