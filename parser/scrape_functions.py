from string import punctuation
import regex as re
from sentry_sdk import capture_message
from database import r
from string import punctuation
from twitter_queue import add_to_queue


# Normalisierungfunktion von nyt_first_said
def normalize(raw_word):
    # Ausfiltern von weiteren Zeichen im Testlauf
    regexexp = re.compile('-{2,}')

    # Entfernen von Zeichen (Wie schwer kann das sein??!!)
    stripped_word = re.sub(r'[^\P{P}-]+', '', raw_word)


    # Check ob Spiegelstrich einen Silbentrennung ist oder tatsächlich ganzes Wort
    if '-' in stripped_word and not (stripped_word.endswith('-') or stripped_word.startswith('-')):
        if regexexp.search(stripped_word):
            replaced = re.sub(regexexp, '-', stripped_word)
            return normalize(replaced)

    return stripped_word


# Noramlisiert das Wort, überprüft ob es schon im Speicher ist und fügt es der Queue hinzu
def check_word(word, sitzung, url):
    norm_word = normalize(word)

    if ok_word(norm_word):
        if add_word(norm_word):
            add_to_queue(norm_word,sitzung,url)
            return True
    
    return False


# Check ob ein valides Wort 
def ok_word(s):
    if s.endswith('.') or s.endswith('’'):  # trim trailing
        s = s[:-1]
    return (not any(i.isdigit() or i in '(.@/#-_§ ' for i in s))


# Wort zur Datenbank hinzufügen
def add_word(word):
    wkey = "word:" + word
    if not r.get(wkey):
        r.set(wkey, '1')
        return True
    return False

# Filtert aus XML Datei die tatsächlichen Wortbeiträge
def get_wortbeitraege(current_xml):
    
    raw_results = []
    
    results = current_xml.find_all("p", {'klasse' : ['J', '1','O', 'J_1', 'T']})

    for result in results:
        # Encoding funktioniert nicht komplett, darum sanitizing
        sanitized = result.text.replace(u'\xa0', u' ')
        raw_results.append(sanitized)

    return raw_results


def process_woerter (current_xml, sitzung, url):

    wordnum = 0
    words = []
    first_half = ""
    possible_hyphenation = False
    regexp = re.compile('([A-Z])|([a-z])\w+')

    raw_results = get_wortbeitraege(current_xml)

    for sentence in raw_results:
        words += sentence.split()

    for word in words:
        if len(word) > 3 and regexp.search(word) and not ('http' in word):

# Checkt ob Silbentrennung Wörter getrennt hat
            if possible_hyphenation:

                # Wenn zweite Hälfte groß geschrieben ist, ist es ein neues Wort und beide werden einzelnd weiter geschickt.
                if word[0].isupper() or word.startswith('-'):
                    if check_word(first_half, sitzung, url):
                        wordnum += 1
                    possible_hyphenation = False
                    if word.startswith('-'):
                        continue
                else:
                    # Wenn zweite Hälfte klein, dann kombinieren der beiden Wörter
                    combined = first_half + word
                    possible_hyphenation = False

                    # TODO Check ob es ein tatsächliches Wort ist

                    word = combined


            # Wenn Wort mit Spiegelstrich endet dann zurückhalten und in der nächsten Iteration testen ob Silbentrennung
            if word.endswith('-') and word.count('-') < 2:
                first_half = word
                possible_hyphenation = True
                continue

            
            if check_word(word, sitzung, url):
                wordnum += 1
    
    return wordnum