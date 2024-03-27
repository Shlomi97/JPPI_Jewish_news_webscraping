import logging
import time
import pandas as pd
from bs4 import BeautifulSoup

# Assuming get_html_content and read_existing_data are defined in 'utills.py' correctly
from utills import get_html_content


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
    paragraphs = article_page.find_all("p")
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


