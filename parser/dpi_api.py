from dotenv import load_dotenv
import os
import requests
import json
from database import r
import datetime
import xml_parse
from sentry_sdk import capture_exception


load_dotenv()


# Directory für XML Speichern und Abrufen anpassen
script_dir = os.path.dirname(os.path.realpath(__file__))
os.chdir(script_dir)

# API Key aus dem Environment
api_key = os.environ.get('BUNDESTAG_API_KEY')

def add_protokoll(response):

    parameters = ['dokumentnummer', 'fundstelle', 'id', 'wahlperiode', 'datum', 'titel' ]

    document_data = json.loads(response.text)
    if document_data['herausgeber'] == 'BT':

        redis_id = 'protokoll:' + document_data['id']

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

        try:
            pipe.execute()
            return True
        except Exception as e:
            capture_exception(e)
    
    else:
        return False


def find_new_doc(id):
    new_id = ""

    for x in range(id, id + 20):

        url = 'https://search.dip.bundestag.de/api/v1/plenarprotokoll/' + str(x) + '?apikey=' + api_key
        response = requests.get(url)

        if response.status_code == 200:
            if add_protokoll(response):
                new_id = x
                break
    if new_id:
        return (xml_parse.get(new_id), new_id)
    else:
        return (None, False) 