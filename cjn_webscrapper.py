from os.path import exists
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementClickInterceptedException, TimeoutException
from utills import get_html_content


def fetch_new_article_urls_until_known(base_url, existing_urls):
    driver = webdriver.Chrome()
    driver.get(base_url)

    articles_urls = []
    click_attempts = 0
    max_attempts = 5

    try:
        while click_attempts < max_attempts:
            try:
                load_more_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable(
                        (By.CSS_SELECTOR, ".js--load-more-button.feed-pagination__load-more-button"))
                )
                driver.execute_script("arguments[0].scrollIntoView(true);", load_more_button)
                driver.execute_script("window.scrollBy(0, -150);")
                load_more_button.click()
                click_attempts += 1
                print(f"Clicked 'Load More' button {click_attempts} times.")

                WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "article.tease-archive > a"))
                )

            except ElementClickInterceptedException:
                time.sleep(2)
                driver.execute_script("arguments[0].click();", load_more_button)

            urls_elements = driver.find_elements(By.CSS_SELECTOR, "article.tease-archive > a")
            for url_element in urls_elements:
                url = url_element.get_attribute('href')
                if url in existing_urls:
                    print(f"Encountered known URL, stopping: {url}")
                    return articles_urls
                if url not in articles_urls:  # Avoid duplicates in the current session
                    articles_urls.append(url)
                    print(len(articles_urls))

    except TimeoutException:
        print("Reached the end of the page or encountered a timeout.")

    finally:
        driver.quit()
        print(f"Total unique articles collected: {len(articles_urls)}")
        return articles_urls
