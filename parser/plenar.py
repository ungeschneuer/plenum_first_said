
# -*- coding: utf-8 -*-


from dpi_api import find_new_doc
from sentry_sdk import capture_message
from database import r
from scrape_functions import process_woerter
import sentry_sdk
from sentry_sdk.integrations.redis import RedisIntegration
from dotenv import load_dotenv
import os 
import json
import requests

load_dotenv()

sentry_sdk.init(
    os.environ.get('SENTRY_AUTH'),
    integrations=[RedisIntegration()],

    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    # We recommend adjusting this value in production.
    traces_sample_rate=0.5,
    release="plenarbot@1.0",
    environment="production"
)


def get_current_id():
    return int(r.get('meta:id'))

def increase_current_id(new_id):
    r.set('meta:id', int(new_id) + 1)
    return True

def send_push(wordnum):
    webhook_URL=  os.environ.get('WEBHOOK_URL')
    message = {'value1': 'Es wurden ein neues Protokoll mit ' + str(wordnum) + ' Woertern hinzugefügt.'}

    response = requests.post(
    webhook_URL, data=json.dumps(message),
    headers={'Content-Type': 'application/json'})

    print(wordnum)

def main():

    old_id = get_current_id()

    xml_file, new_id = find_new_doc(old_id)

    if new_id:
        capture_message('Sitzung mit der ID ' + str(old_id) +  ' gefunden')
        wordnum = process_woerter(xml_file, new_id)
        if wordnum == 0:
            exit   
        increase_current_id(new_id)
        
        send_push(wordnum)
        capture_message("Es wurden " + str(wordnum) + " neue Wörter hinzugefügt.")

    
    exit


if __name__ == "__main__":
    main()


