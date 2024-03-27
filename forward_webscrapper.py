import logging
import time
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementClickInterceptedException, TimeoutException
# Assuming get_html_content and read_existing_data are defined in 'utills.py' correctly
from utills import get_html_content


def fetch_new_article_urls_until_known(existing_urls):
    driver = webdriver.Chrome()  # Adjust the path if necessary
    driver.get("https://forward.com/news/")
    known_urls = set(existing_urls)  # Set of known URLs for fast lookup
    new_urls = set()  # Set to collect new URLs
    max_attempts = 5  # Adjust based on how many times you want to click "Load More"

    try:
        while True:
            try:
                # Wait for the "Load More" button to be clickable and click it
                load_more_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, ".alm-load-more-btn.more"))
                )
                driver.execute_script("arguments[0].scrollIntoView(true);", load_more_button)
                driver.execute_script("window.scrollBy(0, -150);")  # Adjust scrolling as necessary
                load_more_button.click()

                # Wait for a short period to ensure new content has loaded
                WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a.post.heading-image.news"))
                )

            except ElementClickInterceptedException:
                # If still not clickable, use JavaScript to click
                driver.execute_script("arguments[0].click();", load_more_button)
            except TimeoutException:
                print("Timed out waiting for more articles to load or no more 'Load More' button.")
                break

            # Fetch new URLs and check each one
            urls_elements = driver.find_elements(By.CSS_SELECTOR, "a.post.heading-image.news")
            for url_element in urls_elements:
                url = url_element.get_attribute('href')
                if url in known_urls:
                    print("Encountered an already known URL. Stopping.")
                    break  # Stop if the URL is known
                else:
                    new_urls.add(url)
            else:
                continue  # Only executed if the inner loop did NOT break
            break  # Break the outer loop if the inner loop was broken

    finally:
        driver.quit()  # Make sure to quit the driver to close the browser window

    return list(new_urls)  # Convert the set of new URLs to a list before returning


def get_title_forward(article_page):
    title_element = article_page.find('h1', class_="heading-2")
    return title_element.text.strip() if title_element else "No Title"


def get_category_forward(article_page):
    category_element = article_page.find('a', class_="eyebrow small black")
    return category_element.text.strip() if category_element else "No Category"


def get_tags_forward(article_page) -> list:
    tags_element = article_page.find("ul", class_="tags-list")
    return [tag.text.strip() for tag in tags_element.find_all("li")] if tags_element else ["No Tags"]


def get_author_forward(article_page):
    author_element = article_page.find("div", class_="post-author no-avatar") or article_page.find("div",
                                                                                                   class_="post-author single")
    author_link = author_element.find('a') if author_element else None
    return author_link.text.strip() if author_link else "Could not get author name"


def get_date_forward(article_page):
    date_element = article_page.find("div", class_="post-author no-avatar") or article_page.find("div",
                                                                                                 class_="post-author single")
    date_span = date_element.find('span') if date_element else None
    return date_span.text.strip() if date_span else "Could not get article date"


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
        authors = get_author_forward(soup)

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
