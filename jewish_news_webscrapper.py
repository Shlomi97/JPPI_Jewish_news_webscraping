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
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    import time
    import logging

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
