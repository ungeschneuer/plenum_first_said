import logging
import xml.etree.ElementTree as ET
from dotenv import load_dotenv
import os
from dpi_api import get_url_content




load_dotenv()

# API Key aus dem Environment
api_key = os.environ.get('BUNDESTAG_API_KEY')


# Speichert XML ab nach Download
def save(id, current_xml):

    filename = os.path.dirname(os.path.realpath(__file__)) + "/archive/" + str(id) + ".xml"

    with open (filename, 'wb') as file:
        file.write(current_xml.content)
    
    logging.info('XML gespeichert: ' + filename)
    
    return filename

# XML Dokument bekommen hinter der ID
def get(id):

    url = 'https://search.dip.bundestag.de/api/v1/plenarprotokoll-text/' + str(id) + '?apikey=' + api_key + '&format=xml'

    response = get_url_content(url)
    
    if response and response.status_code == 200:
        filename = save(id, response)
        return parse(filename)
    else:
        return False


#Parse XML
def parse(filename):
    
    tree = ET.parse(filename)
    return tree.getroot()

#  Auf verschiedene Arten der Formatierung eingehen und als String ausgeben.
def getText(xml_file):

    text_array = []
    klassen = ['J', '1','O', 'J_1', 'T']
    
    #Checken ob neues Format und Text rausziehen
    for p in xml_file.iter("p"):
        if any(value in p.attrib.values() for value in klassen):
            text_array.append(p.text)
    
    # Altes Format bekommen
    if not text_array: 
        if xml_file.findall('text'):
            text_array.append(xml_file.find('text').text)
        if xml_file.findall('TEXT'):
            text_array.append(xml_file.find('TEXT').text)

    if not text_array:
        return False
    else:        
        return ''.join(text_array)

