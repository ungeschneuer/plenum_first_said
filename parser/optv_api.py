import json
import logging
from api_functions import get_url_content
import datetime

# Wenn noch nicht bei OPTV, dann True
def get_op_response(url):
    response = get_url_content(url)
    return json.loads(response.text)

# Wenn Wort in Suche exisitiert return True
def does_exist(document_data):
    if document_data['meta']['results']['count'] > 0:
        return True
    else:
        return False

# Wenn Wort schon im Katalog exisitert return False
def double_check_newness(word, keys):
    datum = keys[b'datum'].decode('UTF-8')
    
    # Datum entspricht dem Tag vor dem Protokoll
    date_to_check = datetime.datetime.strptime(datum, '%d.%m.%Y') - datetime.timedelta(days=1)
    date = date_to_check.strftime('%Y-%m-%d')
    url = 'https://de.openparliament.tv/api/v1/search/media/?q=' + word + '&dateTo=' + date
    document_data = get_op_response(url)

    if does_exist(document_data):
        return False
    else:
        return True

# Checkt zunächst ob Wort gefunden werden kann und sucht dann nach den Infos
def check_for_infos(word, keys):
    datum = keys[b'datum'].decode('UTF-8')

    date = datetime.datetime.strptime(datum, '%d.%m.%Y').strftime('%Y-%m-%d')
    url = 'https://de.openparliament.tv/api/v1/search/media/?q=' + word + '&dateTo=' + date + '&dateFrom=' + date
    document_data = get_op_response(url)

    if does_exist(document_data):
        return get_metadata(document_data, word)
    else:
        logging.info('Es konnten keine Infos von OPTV empfangen werden.')
        return False


# Gibt ein dicitionary mit den Metadaten von OPTV aus. 
def get_metadata(document_data, word):
    
    type = document_data['data'][0]['type']
    id = document_data['data'][0]['id']

    link = 'https://de.openparliament.tv/' + type + '/' + id + '?q=' + word

    speaker = document_data['data'][0]['relationships']['people']['data'][0]['attributes']['label']
    party = document_data['data'][0]['relationships']['people']['data'][0]['attributes']['party']['label']

    metadata = {
        'link': link,
        'speaker' : speaker,
        'party': party,
    }

    return metadata

