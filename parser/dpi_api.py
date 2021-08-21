from dotenv import load_dotenv
import os
import requests
import json
from database import r
import datetime
from bs4 import BeautifulSoup


load_dotenv()


# Directory für XML Speichern und Abrufen anpassen
script_dir = os.path.dirname(os.path.realpath(__file__))
os.chdir(script_dir)

# API Key aus dem Environment
api_key = os.environ.get('BUNDESTAG_API_KEY')

def find_new_doc(id):

    parameters = ['dokumentnummer', 'fundstelle', 'id', 'wahlperiode', 'datum', 'titel' ]
    new_id = ""

    for x in range(id, id + 20):

        url = 'https://search.dip.bundestag.de/api/v1/plenarprotokoll/' + str(x) + '?apikey=' + api_key
        response = requests.get(url)

        if response.status_code == 200:
            document_data = json.loads(response.text)
            if document_data['herausgeber'] == 'BT':

                redis_id = 'sitzung:' + document_data['dokumentnummer']

                pipe = r.pipeline()

                for parameter in parameters:
                    if parameter in document_data:
                        if parameter == 'fundstelle':
                            if 'pdf_url' in document_data[parameter]:
                                pipe.hset(redis_id, 'pdf_url', document_data[parameter]['pdf_url'])
                        elif parameter == 'datum':
                            pipe.hset(redis_id, parameter, datetime.datetime.strptime(document_data[parameter], '%Y-%m-%d').strftime('%d.%m.%Y'))
                        else:
                            pipe.hset(redis_id, parameter, document_data[parameter])


                pipe.execute()
                
                new_id = document_data['id']
                break
    
    return get_xml(id)

def get_xml(id):

    url = 'https://search.dip.bundestag.de/api/v1/plenarprotokoll-text/' + str(id) + '?apikey=' + api_key + '&format=xml'

    response = requests.get(url)

    if response.status_code == 200:
        save_xml(id, response)
        current_xml = BeautifulSoup(response.content.decode('utf-8', 'ignore'), features="html5lib")

        return (current_xml)

        
    else:
        return False

    return (current_xml)


# Speichert XML ab nach Download
def save_xml(id, current_xml):

    with open ( "archive/" + id + ".xml", 'wb') as file:
        file.write(current_xml.content)
        return True




