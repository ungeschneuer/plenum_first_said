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
    punctuation = r"""!"#$%&'()*+,‚./:;<=>?@[\]^_`{|}~“„"""
    stripped_word = raw_word.translate(str.maketrans('', '', punctuation))



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


# Check ob ein valides Wort und weitere Korrigierung
def ok_word(s):
    while s.endswith('.') or s.endswith('’'):  # trim trailing
        s = s[:-1]

    if s.endswith('ts'):
        return False

    return (not any(i.isdigit() or i in '(.@/#-_§ ' for i in s))


# Wort abgleichen und zur Datenbank hinzufügen
def add_word(word):

    pipe = r.pipeline()
    
    # Checken ob Kleinschreibung, Großschreibung oder Plural schon existieren
    pipe.get("word:" + word)
    pipe.get("word:" + word.lower())
    pipe.get("word:" + word.capitalize())

    if word.endswith('s'):
        pipe.get("word:" + word[:-1])

    if word.endswith('’s') or word.endswith('in'):
        pipe.get("word:" + word[:-2])

    if not any(pipe.execute()):
        r.set("word:" + word, '1')
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
    
    # Wort hat Buchstaben
    regchar = re.compile('([A-Z])|([a-z])\w+')
    # Wort hat nicht gleiche Zeichen hintereinander
    regmul = re.compile('([A-z])\1{3,}')

    raw_results = get_wortbeitraege(current_xml)

    for sentence in raw_results:
        words += sentence.split()

    for word in words:
        if len(word) > 5 and regchar.search(word) and not regmul.search(word) and not ('http' in word):

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

            # Wortaufzählung entfernen
            if word.startswith('-') or word.startswith('‑'):
                continue


            # Zusammefassung oder binäre Ansprache
            if '/' in word:
                splitted = word.split('/')
                word = splitted[0]

                if check_word(splitted[1], sitzung, url):
                    wordnum += 1



            
            if check_word(word, sitzung, url):
                wordnum += 1
    
    return wordnum