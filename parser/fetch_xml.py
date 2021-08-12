from bs4 import BeautifulSoup
import httplib2
import requests
import regex as re
from sentry_sdk import capture_message
from datetime import datetime
import pytz

#Timezone
tz = pytz.timezone('Europe/Berlin')


archive_link = 'https://www.bundestag.de/ajax/filterlist/de/services/opendata/543410-543410'



# Nimmt Sitzungsnummer und sucht danach in der Datenbankliste
def get_current_xml(sitzung):
    http = httplib2.Http()
    
    # Abfrage der Seite
    status, response = http.request(archive_link)


    # Seite ist erreichbar
    if status.status == 200:
        soup = BeautifulSoup(response, features="html5lib")
        current_doc = soup.find("a", href=re.compile(sitzung))

        # URL ist auf der Seite
        if not current_doc:
            capture_message("Sitzungsprotokoll zu Sitzung " + sitzung + " wurde nicht gefunden")
            return (False, None)

        current_url = 'https://www.bundestag.de' + current_doc['href']
        response = requests.get(current_url)
        return (response, current_url)


    else:
        capture_message("Seite konnte nicht erreicht werden. Status:" + status.status)
        return (False, None)

# Speichert XML ab nach Download
def save_xml(sitzung, current_xml):
    with open ( "archive/" + sitzung + ".xml", 'wb') as file:
        file.write(current_xml.content)
        return True

# Test File um Server nicht zu belasten
def get_test_xml(sitzung):
    with open("archive/" + sitzung + ".xml", 'r') as f:
        data = f.read()
        return BeautifulSoup(data, features="html5lib")

# Haupt-Funktion
def get_xml(sitzung=str(0), test=False):

    url=""

    if test:
        current_xml = get_test_xml(str(234))
    else: 
        current_xml, url = get_current_xml(sitzung)

        if current_xml:
            save_xml(sitzung, current_xml)
            current_xml = BeautifulSoup(current_xml.content.decode('utf-8', 'ignore'), features="html5lib")
        
        else:
            return (False, url)

    return (current_xml, url)



