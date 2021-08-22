import os
from progressbar import printProgressBar
import xml_parse
from scrape_functions import process_woerter
from dotenv import load_dotenv
import requests
from dpi_api import add_protokoll


load_dotenv()


# API Key aus dem Environment
api_key = os.environ.get('BUNDESTAG_API_KEY')
    

wordnum = 0
id = ""
length = 5420

for id in range(897, length):

    url = 'https://search.dip.bundestag.de/api/v1/plenarprotokoll/' + str(id) + '?apikey=' + api_key
    response = requests.get(url)

    if response.status_code == 200:
        if add_protokoll(response):
            xml_file = xml_parse.get(id)
            wordnum += process_woerter(xml_file, id)   
        else:
            continue           

    else:
        continue        

    printProgressBar(id + 1, length, prefix = 'Progress:', suffix = 'Complete', length = 50)

print("Fertig")
print(str(wordnum) + " neue Wörter")