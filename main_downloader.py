import json
import logging
from jta_webscrapper import fetch_all_data_jta
from forward_webscrapper import fetch_all_data_forward
from cjn_webscrapper import fetch_all_data_cjn
from jewish_news_webscrapper import fetch_all_data_jewish_news
from jewish_ru import  fetch_all_data_jewish_ru
from jewish_report_webscrapper import fetch_all_data_jewish_report
from jewish_link_webscrapper import fetch_all_data_jewish_link
from salom_news_webscrapper import fetch_all_data_salom_news

def main():
    # Load configuration
    with open('config_2.json', 'r') as config_file:
        config = json.load(config_file)

    # Set up logging configurations
    logging.basicConfig(level=getattr(logging, config["logging_level"]))

    # Iterate through each website configuration
    for key, site in config["websites"].items():
        base_url = site["base_url"]
        output_path = site["output_path"]
        print(output_path)
        n = config["n"]

        if key == 'jta':
            fetch_all_data_jta(base_url, n, output_path)
        if key == 'forward':
            fetch_all_data_forward(base_url, output_path)
        if key == 'cjn':
            fetch_all_data_cjn(base_url, output_path)
        if key == 'jewish_news':
            fetch_all_data_jewish_news(base_url, output_path)
        if key == "australian_jewish_news":
            fetch_all_data_jewish_news(base_url, output_path)
        if key == "jewish_ru":
            fetch_all_data_jewish_ru(base_url, output_path)
        if key == "jewish_report":
            fetch_all_data_jewish_report(base_url, output_path)
        if key == "jewish_link":
            fetch_all_data_jewish_link(base_url,n,output_path)
        if key == "salom_news":
            fetch_all_data_salom_news(base_url,output_path)