import logging
from dotenv import load_dotenv
import os
import requests
import json
from database import r
import datetime
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry


load_dotenv()


# API Key aus dem Environment
api_key = os.environ.get('BUNDESTAG_API_KEY')


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


def add_protokoll(response):

    parameters = ['dokumentnummer', 'fundstelle', 'id', 'wahlperiode', 'datum', 'titel']

    # Erst checken ob es ein Protokoll des Bundestags ist und dann, ob es einen Text hat. 

    document_data = json.loads(response.text)
    if document_data['herausgeber'] == 'BT':

        if 'text' in document_data:
            if len(document_data['text']) > 2:
                
                # Datenbankeintrag für das Protokoll erstellen

                redis_id = 'protokoll:' + document_data['id']

                pipe = r.pipeline()

                for parameter in parameters:
                    if parameter in document_data:
                        if parameter == 'fundstelle':
                            if 'pdf_url' in document_data[parameter]:
                                pipe.hset(redis_id, 'pdf_url', document_data[parameter]['pdf_url'])
                        elif parameter == 'datum':
                            pipe.hset(redis_id, parameter, datetime.datetime.strptime(document_data[parameter], '%Y-%m-%d').strftime('%d.%m.%Y'))
                        elif parameter == 'dokumentnummer':
                            pipe.hset(redis_id, 'dokumentnummer', document_data['dokumentnummer'])
                            pipe.hset(redis_id, 'protokollnummer', document_data[parameter].split('/')[1])
                        else:
                            pipe.hset(redis_id, parameter, document_data[parameter])

                try:
                    pipe.execute()
                    return True
                except Exception as e:
                    logging.exception(e)
                    return False
            else:
                logging.info('Dokument mit ID ' + document_data['id'] + ' hat keinen Text')
                return False
        else:
            logging.info('Kein Text gefunden')
            return False
    else:
        logging.info('Dokument mit ID ' + document_data['id'] + ' ist kein Bundestagsprotokoll')
        return False


def find_new_doc(id):

    for x in range(id, id + 20):

        url = 'https://search.dip.bundestag.de/api/v1/plenarprotokoll-text/' + str(x) + '?apikey=' + api_key
        
        response = get_url_content(url)

        if response and response.status_code == 200:
            if add_protokoll(response):
                logging.info('Neue Sitzung mit Text gefunden unter der URL ' + url)
                return x
        else:
            logging.debug('Response für ID ' + str(x) + ' war nicht gültig.')

    
    logging.info('Keine neue Sitzung gefunden')
    return False 