import requests
import xml.etree.ElementTree as ET
from dotenv import load_dotenv
import os



load_dotenv()

# API Key aus dem Environment
api_key = os.environ.get('BUNDESTAG_API_KEY')


# Speichert XML ab nach Download
def save(id, current_xml):

    filename = "archive/" + str(id) + ".xml"

    with open (filename, 'wb') as file:
        file.write(current_xml.content)
    
    return filename


def get(id):

    url = 'https://search.dip.bundestag.de/api/v1/plenarprotokoll-text/' + str(id) + '?apikey=' + api_key + '&format=xml'

    response = requests.get(url)

    if response.status_code == 200:
        filename = save(id, response)
        xml = parse(filename)
        return xml
    else:
        return False


#Parse XML
def parse(filename):
    
    tree = ET.parse(filename)
    root = tree.getroot()
    return root


def getText(xml_file):

    text = []
    klassen = ['J', '1','O', 'J_1', 'T']
    
    for p in xml_file.iter("p"):
        if any(key in p.attrib for key in klassen):
            text.append(p.text)
    
    if not text: 
        text.append(xml_file.find('text').text)
    
    return text
