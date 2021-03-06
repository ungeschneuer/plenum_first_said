
# -*- coding: utf-8 -*-
import logging
from dpi_api import find_new_doc
from database import r
from text_parse import process_woerter, prune
from dotenv import load_dotenv
import xml_processing

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
        
        xml_file = xml_processing.get(new_id)

        if xml_file:
            logging.info('Sitzung mit der ID ' + str(new_id) +  ' gefunden')
            new_words = process_woerter(xml_file, new_id)
            if len(new_words) == 0:
                logging.debug('Es wurde kein neues Wort hinzugefügt.')
                exit   
            else:
                prune(new_words, new_id)
                increase_current_id(new_id)
             
            logging.info("Es wurden " + str(len(new_words)) + " neue Wörter hinzugefügt.")

        else:
            logging.debug('Fehler im XML File.')

    else:
        logging.info('Keine neue Sitzung gefunden.')
    
    exit


if __name__ == "__main__":
    logging.basicConfig(
        filename='bundestagbot/parser/plenarlog.log',
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S')
    logging.info('Starte Plenar-Parser')
    main()
    logging.info('Beende Plenar-Parser')

 