import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import logging

def get_url_content(url):
    try:
        s = requests.Session()
        retries = Retry(total=5, backoff_factor=1, status_forcelist=[ 502, 503, 504, 54 ])
        s.mount('https://', HTTPAdapter(max_retries=retries))
        response = s.get(url)
        return response
    except Exception as e:
        logging.exception(e)
        return False
