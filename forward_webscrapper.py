import logging
import time
import pandas as pd
from os.path import exists
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementClickInterceptedException, TimeoutException
from utills import get_html_content


def fetch_new_article_urls_until_known(base_url, existing_urls):
    driver = webdriver.Chrome()  # Adjust the path if necessary
    driver.get(base_url)
    articles_urls = []  # Initialize as a list for preserving order
    click_attempts = 0
    max_attempts = 5  # Adjust based on how many times you want to click "Load More"

    try:
        while click_attempts < max_attempts:
            try:
                # Wait for the "Load More" button to be clickable and click it
                load_more_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, ".alm-load-more-btn.more"))
                )
                driver.execute_script("arguments[0].scrollIntoView(true);", load_more_button)
                driver.execute_script("window.scrollBy(0, -150);")  # Scroll up a bit if needed
                load_more_button.click()
                click_attempts += 1

                # Wait for a short period to ensure new content has loaded
                WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a.post.heading-image*"))
                )

            except ElementClickInterceptedException:
                # If still not clickable after the scroll, wait a bit and try clicking again
                time.sleep(2)  # Optional sleep, can adjust based on behavior
                driver.execute_script("arguments[0].click();", load_more_button)

            # Fetch new URLs
            urls_elements = driver.find_elements(By.CSS_SELECTOR, "a.post.heading-image*")
            for url_element in urls_elements:
                url = url_element.get_attribute('href')
                if url in existing_urls:
                    logging.warning(f"{url} already extracted, stopping the loop")
                    break
                else:
                    articles_urls.append(url_element.get_attribute('href'))
            else:
                continue  # Only executed if the inner loop did NOT break
            break  # Break the outer loop if the inner loop was broken

    except TimeoutException:
        logging.warning(f"Reached the end of the page or encountered a timeout.")

    finally:
        # Remove duplicates while preserving order
        articles_urls = list(dict.fromkeys(articles_urls))
        driver.quit()  # Make sure to quit the driver to close the browser window
    return articles_urls


def get_title_forward(article_page):
    title_element = article_page.find('h1', class_="heading-2")
    return title_element.text.strip() if title_element else "No Title"


def get_category_forward(article_page):
    category_element = article_page.find('a', class_="eyebrow small black")
    return category_element.text.strip() if category_element else "No Category"


def get_tags_forward(article_page) -> list:
    tags_element = article_page.find("ul", class_="tags-list")
    return [tag.text.strip() for tag in tags_element.find_all("li")] if tags_element else ["No Tags"]


def get_authors_forward(article_page) -> list:
    # Use CSS selector to find all divs where class starts with "post-author"
    author_elements = article_page.select('div[class^="post-author"]')
    authors = []
    for author_element in author_elements:
        authors_links = author_element.find_all('a')
        for author_link in authors_links:
            authors.append(author_link.text.strip())
    return authors


def get_date_forward(article_page):
    # Use CSS selector to find the first div where class starts with "post-author"
    author_element = article_page.select_one('div[class^="post-author"]')
    if author_element:
        date_element = author_element.find_all('span')[-1]
        if date_element:  # Ensure there's an <a> tag
            return date_element.text.strip()

    return "Could not get article date"


def get_full_article_forward(article_page):
    paragraphs = article_page.find("article").find_all("p")
    full_text = ' '.join(paragraph.text.strip() for paragraph in paragraphs)
    return full_text.replace('\n', '').replace('\t', ' ')


def process_article(df, article_url):
    logging.info(f"Scraping data from article URL: {article_url}")
    article_page = get_html_content(article_url)
    if article_page:
        soup = BeautifulSoup(article_page, "html.parser")
        title = get_title_forward(soup)
        category = get_category_forward(soup)
        content = get_full_article_forward(soup)
        date = get_date_forward(soup)
        tags = get_tags_forward(soup)
        authors = get_authors_forward(soup)

        new_row = {
            "date": date,
            "title": title,
            "category": category,
            "content": content,
            "urls": article_url,
            "tags": tags,
            "authors": authors
        }

        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        logging.info(f"Data for {article_url} added to DataFrame")
    else:
        logging.warning(f"Failed to fetch content from article URL: {article_url}")
    time.sleep(2)
    return df


def fetch_all_data_forward(base_url, file_path='forward.csv'):
    # Check if the file exists to load existing data
    if exists(file_path):
        df_existing = pd.read_csv(file_path)
        existing_urls = df_existing['urls'].tolist()
    else:
        df_existing = pd.DataFrame(columns=["date", "title", "category", "content", "urls", "tags", "authors"])
        existing_urls = []
    new_urls = fetch_new_article_urls_until_known(base_url, existing_urls)
    df_new = pd.DataFrame(columns=["date", "title", "category", "content", "urls", "tags", "authors"])
    for url in new_urls:
        df_new = process_article(df_new, url)
    df_combined = pd.concat([df_existing, df_new]).drop_duplicates(subset=['urls']).reset_index(drop=True)
    df_combined.to_csv(file_path, index=False)
    print(f"Updated data saved to {file_path}. Total records: {len(df_combined)}")
    logging.info(f"Script execution completed forward ")
