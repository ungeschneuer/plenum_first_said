from dpi_api import find_new_doc
from sentry_sdk import capture_message
from database import r
from scrape_functions import process_woerter
import sentry_sdk
from sentry_sdk.integrations.redis import RedisIntegration
from dotenv import load_dotenv
import os 


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



def main():

    capture_message("Skript wird gestartet")

    old_id = get_current_id()

    capture_message("Sitzung mit der ID " + str(old_id) + " wird gesucht.")
    xml_file, new_id = find_new_doc(old_id)

    if new_id:
        capture_message("Sitzung gefunden")
        wordnum = process_woerter(xml_file, new_id)        
        increase_current_id(new_id)
        capture_message("Es wurden " + str(wordnum) + " neue Wörter hinzugefügt.")

    
    capture_message("Skript wird beendet")
    exit


if __name__ == "__main__":
    main()

"""
TODO
- Backend zur Wort Kontrolle
"""
