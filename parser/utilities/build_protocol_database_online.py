from dotenv import load_dotenv
from database import r
from requests.adapters import HTTPAdapter
from dpi_api import get_url_content, add_protokoll
import os
import time

load_dotenv()


# API Key aus dem Environment
api_key = os.environ.get('BUNDESTAG_API_KEY')


for x in range(351, 5468):
    print(x)
    url = 'https://search.dip.bundestag.de/api/v1/plenarprotokoll-text/' + str(x) + '?apikey=' + api_key
    
    response = get_url_content(url)

    if response and response.status_code == 200:
        if add_protokoll(response):
            print("gefunden")
    
    if x % 50 == 0:
        time.sleep(10)