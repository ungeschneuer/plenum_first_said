from fetch_xml import get_xml
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


def get_current_sitzung():
    return int(r.get("meta:sitzung"))

def increase_current_sitzung():
    r.incr("meta:sitzung")
    return True



def main():

    capture_message("Skript wird gestartet")

    sitzung = str(get_current_sitzung())

    capture_message("Sitzung " + sitzung + " wird gesucht.")
    current_xml, url = get_xml(sitzung)
    #current_xml = get_xml(test=True)

    if current_xml:
        capture_message("Sitzung gefunden")
        wordnum = process_woerter(current_xml, sitzung, url)        
        increase_current_sitzung()
        capture_message("Es wurden " + str(wordnum) + " neue Wörter hinzugefügt.")

    
    capture_message("Skript wird beendet")
    exit


if __name__ == "__main__":
    main()

"""
TODO
- tägliches Abrufen
- Backend zur Wort Kontrolle
- Entfernung von Artikeln und Paragraphen
- Twitter Anbindung"""
