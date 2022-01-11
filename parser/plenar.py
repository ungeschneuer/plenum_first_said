
# -*- coding: utf-8 -*-


import logging
from dpi_api import find_new_doc
from database import r
from scrape_functions import process_woerter
from dotenv import load_dotenv
import xml_parse

load_dotenv()

def get_current_id():
    return int(r.get('meta:id'))

def increase_current_id(new_id):
    r.set('meta:id', int(new_id) + 1)
    return True

def main():

    old_id = get_current_id()

    logging.info('Starte suche nach Dokument mit ID ' + str(old_id))

    new_id = find_new_doc(old_id)

    if new_id:
        xml_file = xml_parse.get(new_id)
    else:
        logging.info('Keine neue Sitzung gefunden.')
        exit


    if xml_file:
        logging.info('Sitzung mit der ID ' + str(new_id) +  ' gefunden')
        wordnum = process_woerter(xml_file, new_id)
        if wordnum == 0:
            logging.debug('Es wurde kein neues Wort hinzugefügt.')
            exit   
        else:
            increase_current_id(new_id)
        
        logging.info("Es wurden " + str(wordnum) + " neue Wörter hinzugefügt.")

    else:
        logging.debug('Fehler im XML File.')
    
    exit


if __name__ == "__main__":
    logging.basicConfig(filename='plenarlog.log', level=logging.DEBUG)
    logging.info('Starte Plenar-Parser')
    main()
    logging.info('Beende Plenar-Parser')

