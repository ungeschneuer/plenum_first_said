# sourcery skip: merge-duplicate-blocks
import os
# from progressbar import printProgressBar
import xml_processing
from text_parse import process_woerter, prune
from dotenv import load_dotenv
import requests
from dpi_api import add_protokoll
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
    

wordnum = 0
id = ""
length = 5502

for id in range(0 , length):

    if id % 10 == 0 and id != 0:
        time.sleep(5)  

    url = 'https://search.dip.bundestag.de/api/v1/plenarprotokoll-text/' + str(id) + '?apikey=' + api_key
    response = requests.get(url)
    logging.info(url)
   
    if response.status_code == 200:
        logging.info("Start Adding Protokoll")
        if add_protokoll(response):
            xml_file = xml_processing.get(id)
            new_words = process_woerter(xml_file, id) 
            wordnum += len(new_words)
            logging.info(str(wordnum) + ' Wörter hinzugefügt.')
        else:
            logging.info("not possible to find protokoll - skip id: " + str(id))
            continue
    else:
        logging.info("no status 200 - skip id: " + str(id))
        continue      

    # printProgressBar(id + 1, length, prefix = 'Progress:', suffix = 'Complete', length = 50)

logging.info("Fertig")
logging.info(str(wordnum) + " neue Wörter insgesamt.")