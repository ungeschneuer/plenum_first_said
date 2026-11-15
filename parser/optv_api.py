import json
import logging
import re
from api_functions import get_url_content
import datetime

# Theme für das Zitat-Bild: 'l' = hell (light), 'd' = dunkel (dark)
QUOTE_IMAGE_THEME = 'l'

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
def double_check_newness(word, protocol):
    datum = protocol['datum']
    
    # Datum entspricht dem Tag vor dem Protokoll
    date_to_check = datetime.datetime.strptime(datum, '%d.%m.%Y') - datetime.timedelta(days=1)
    date = date_to_check.strftime('%Y-%m-%d')
    url = 'https://de.openparliament.tv/api/v1/search/media/?q=' + word + '&dateTo=' + date
    document_data = get_op_response(url)

    if does_exist(document_data):
        return False
    else:
        return True


# Erzeugt einen 4-Zeichen-Hash für ein Wort: erster Buchstabe groß + nächste 3 Buchstaben klein.
# Repliziert das JavaScript: root.substr(0, 1).toUpperCase() + root.substr(1, 3)
def generate_fragment_hash(text):
    # Satzzeichen, Ziffern und Leerzeichen entfernen, in Kleinbuchstaben umwandeln
    root = re.sub(r'[^\w\s]|[_\d]', '', text)
    root = re.sub(r'\s+', '', root).lower().strip()
    
    if len(root) == 0:
        return ''
    
    # Erster Buchstabe groß + nächste 3 Buchstaben
    return root[0].upper() + root[1:4]


# Erzeugt den 'f'-Parameter aus dem Satztext.
# Format: prefix,suffix wobei jeder der Hash der ersten/letzten 3 Wörter ist.
def generate_fragment_param(sentence_text):
    words = sentence_text.strip().split()
    
    if len(words) < 2:
        return None
    
    # Erste 3 Wörter für Präfix
    prefix_words = words[:3]
    prefix = ''.join(generate_fragment_hash(w) for w in prefix_words)
    
    # Letzte 3 Wörter für Suffix
    suffix_words = words[-3:] if len(words) >= 3 else words
    suffix = ''.join(generate_fragment_hash(w) for w in suffix_words)
    
    if prefix and suffix:
        return f"{prefix},{suffix}"
    return None


# Findet den ersten Satz, der das Wort enthält und gibt Timing + Fragment zurück.
# Durchsucht die textContents-Struktur aus der API-Antwort.
def find_word_in_text(media_item, word):
    try:
        # textContents kann direkt im Suchergebnis oder unter 'attributes' sein
        if 'attributes' in media_item:
            text_contents = media_item['attributes'].get('textContents', [])
        else:
            text_contents = media_item.get('textContents', [])
        
        word_lower = word.lower()
        
        for text_content in text_contents:
            text_body = text_content.get('textBody', [])
            for paragraph in text_body:
                for sentence in paragraph.get('sentences', []):
                    sentence_text = sentence.get('text', '')
                    if word_lower in sentence_text.lower():
                        time_start = sentence.get('timeStart')
                        time_end = sentence.get('timeEnd')
                        if time_start is not None and time_end is not None:
                            fragment = generate_fragment_param(sentence_text)
                            if fragment:
                                return {
                                    'timeStart': time_start,
                                    'timeEnd': time_end,
                                    'fragment': fragment
                                }
    except (KeyError, TypeError) as e:
        logging.debug(f'Fehler beim Suchen des Wortes im Text: {e}')
    return None


# Findet den Namen des Hauptredners/der Hauptrednerin aus den textContents.
# Der speakerstatus "main-speaker" ist im textBody der Rede gesetzt.
def find_main_speaker_from_text(media_item):
    text_contents = media_item.get('attributes', {}).get('textContents', [])
    for tc in text_contents:
        for para in tc.get('textBody', []):
            if para.get('speakerstatus') == 'main-speaker' and para.get('speaker'):
                return para['speaker']
    return None


# Findet die Partei für einen Redner/eine Rednerin anhand des Namens aus der Personenliste.
def find_party_for_speaker(people_data, speaker_name):
    for person in people_data:
        if person.get('attributes', {}).get('label') == speaker_name:
            party = person['attributes'].get('party', {})
            if party and party.get('label'):
                return party['label']
    return None


# Checkt zunächst ob Wort gefunden werden kann und sucht dann nach den Infos
def check_for_infos(word, protocol):
    datum = protocol['datum']

    try:
        date = datetime.datetime.strptime(datum, '%d.%m.%Y').strftime('%Y-%m-%d')
        url = 'https://de.openparliament.tv/api/v1/search/media/?q=' + word + '&dateTo=' + date + '&dateFrom=' + date
        document_data = get_op_response(url)

        if does_exist(document_data):
            return get_metadata(document_data, word)
        else:
            logging.info('Das Wort existiert bei OPTV nicht.')
            return False
    except Exception as e:
        logging.info('Es gab Probleme beim Zugriff auf die OPTV API. Das Wort konnte nicht überprüft werden.')
        logging.exception(e)
        return False


# Gibt ein dictionary mit den Metadaten von OPTV aus.
# Nutzt die textContents aus dem Suchergebnis für das Zitat-Bild (kein zusätzlicher API-Aufruf nötig).
# Wenn kein main-speaker gefunden wird, sind speaker und party None.
def get_metadata(document_data, word):
    try:
        media_item = document_data['data'][0]
        type = media_item['type']
        id = media_item['id']

        # Standard-Link ohne Zitat-Parameter
        link = f'https://de.openparliament.tv/{type}/{id}?q={word}'
        
        # Versuche, Timing-Infos aus dem Suchergebnis zu extrahieren (bereits vorhanden, kein extra API-Aufruf)
        sentence_info = find_word_in_text(media_item, word)
        
        if sentence_info:
            # URL mit Timing und Fragment für Zitat-Bild erstellen
            # Parameter: q = Suchwort, t = Zeitstempel, f = Fragment-Hash, c = Theme (l=hell, d=dunkel)
            link = (f'https://de.openparliament.tv/{type}/{id}'
                   f'?q={word}'
                   f'&t={sentence_info["timeStart"]},{sentence_info["timeEnd"]}'
                   f'&f={sentence_info["fragment"]}&c={QUOTE_IMAGE_THEME}')
            logging.info(f'Zitat-Bild URL erstellt: {link}')

        # Suche nach Hauptredner:in über speakerstatus im textBody
        people_data = media_item.get('relationships', {}).get('people', {}).get('data', [])
        speaker = find_main_speaker_from_text(media_item)

        if speaker:
            party = find_party_for_speaker(people_data, speaker)
        else:
            # Hauptredner:in nicht gefunden - speaker und party sind None
            # Der Bot sollte in diesem Fall den "wurde gesagt von" Teil weglassen
            party = None
            logging.info(f'Kein main-speaker für Media {id} gefunden - Sprecher-Info wird weggelassen')

        metadata = {
            'link': link,
            'speaker': speaker,
            'party': party,
        }

        return metadata
    except Exception as e:
        logging.info('Es konnten keine Metadaten von OPTV empfangen werden. Es gab Probleme beim Zugriff auf die OPTV API')
        logging.exception(e)
        return False
