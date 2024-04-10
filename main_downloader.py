import json
import logging
from jta_webscrapper import fetch_all_data_jta
from forward_webscrapper import fetch_all_data_forward
from cjn_webscrapper import fetch_all_data_cjn


def main():
    # Load configuration
    with open('config.json', 'r') as config_file:
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
