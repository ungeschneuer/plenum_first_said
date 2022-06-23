# sourcery skip: merge-duplicate-blocks
import os
# from progressbar import printProgressBar
import xml_processing
from text_parse import process_woerter
from dotenv import load_dotenv
import requests
from dpi_api import add_protokoll
import time


load_dotenv()


# API Key aus dem Environment
api_key = os.environ.get('BUNDESTAG_API_KEY')
    

wordnum = 0
id = ""
length = 5476

for id in range(5467 , length):

    if id % 10 == 0 and id != 0:
        time.sleep(5)  

    url = 'https://search.dip.bundestag.de/api/v1/plenarprotokoll-text/' + str(id) + '?apikey=' + api_key
    response = requests.get(url)
    print(url)
   
    if response.status_code == 200:
        print("Start Adding Protokoll")
        if add_protokoll(response):
            xml_file = xml_processing.get(id)
            wordnum += process_woerter(xml_file, id) 
            print("Document added with id: " + str(id))
        else:
            print("not possible to find protokoll - skip id: " + str(id))
            continue
    else:
        print("no status 200 - skip id: " + str(id))
        continue      

    # printProgressBar(id + 1, length, prefix = 'Progress:', suffix = 'Complete', length = 50)

print("Fertig")
print(str(wordnum) + " neue Wörter")