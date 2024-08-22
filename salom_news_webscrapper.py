import logging
import requests
import time
import os
import pandas as pd
from requests.adapters import HTTPAdapter
from bs4 import BeautifulSoup
from requests.packages.urllib3.util.retry import Retry
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')