import requests
import json
from database import r
import datetime


# Holt alle Metadaten die existieren von der API

api = 'N64VhW8.yChkBUIJeosGojQ7CSR2xwLf3Qy7Apw464' # Offener Key valid bis 2022
adress = 'https://search.dip.bundestag.de/api/v1/'
ressource = 'plenarprotokoll'
parameters = ['dokumentnummer', 'fundstelle', 'id', 'wahlperiode', 'datum', 'titel' ]



for x in range(5500):
    url = adress + ressource + '/' + str(x) + '?apikey=' + api 
    response = requests.get(url)
    if response.status_code == 200:
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


            pipe.execute()
            print(document_data['titel'])


print("Done")

    








