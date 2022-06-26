from dotenv import load_dotenv
from database import r
from requests.adapters import HTTPAdapter
from dpi_api import get_url_content, add_protokoll
import os
import time
import logging

logging.basicConfig(
        filename='dbcreate.log',
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S')

load_dotenv()


# API Key aus dem Environment
api_key = os.environ.get('BUNDESTAG_API_KEY')


for x in range(4500, 5502):
    print(x)
    url = 'https://search.dip.bundestag.de/api/v1/plenarprotokoll-text/' + str(x) + '?apikey=' + api_key
    
    response = get_url_content(url)

    if response and response.status_code == 200:
        if add_protokoll(response):
            logging.info(str(x) + " gefunden")
    
    if x % 10 == 0:
        time.sleep(5) 