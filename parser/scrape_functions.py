from string import punctuation
import re
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


# Normalisiert das Wort, überprüft ob es schon im Speicher ist und fügt es der Queue hinzu
def check_word(word, id):
    norm_word = normalize(word)

    if len(word) > 5 and ok_word(norm_word):
        if add_word(norm_word, id):
            add_to_queue(norm_word, id)
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
def add_word(word, id):
    pipe = r.pipeline()
    
    # Checken ob Kleinschreibung, Großschreibung oder Plural schon existieren
    pipe.type("word:" + word)
    pipe.type("word:" + word.lower())
    pipe.type("word:" + word.capitalize())

    if word.endswith('s'):
        pipe.type("word:" + word[:-1])

    if word.endswith('’s') or word.endswith('in'):
        pipe.type("word:" + word[:-2])

    result = pipe.execute()

    if all(x == b'none' for x in result):
        r.hset("word:" + word, "word", word)
        r.hset("word:" + word, "id", id)
        print(word)
        return True


    return False

# Filtert aus XML Datei die tatsächlichen Wortbeiträge
def get_wortbeitraege(current_xml):
    
    raw_results = []
    
    result = current_xml.text


    # Encoding funktioniert nicht komplett, darum sanitizing
    sanitized = result.replace(u'\xa0', u' ')
    sanitized = result.replace('\n', ' ')

    return sanitized


def process_woerter (current_xml, id):

    wordnum = 0
    words = []
    first_half = ""
    skip = False
    possible_hyphenation = False
    
    # Wort hat Buchstaben
    regchar = re.compile('([A-Z])|([a-z])\w+')
    # Wort hat nicht gleiche Zeichen hintereinander
    regmul = re.compile('([A-z])\1{3,}')
    raw_results = get_wortbeitraege(current_xml)

    
    words += raw_results.split()
    words = words[words.index('Beginn:')+1:]


    for word in words:
        if skip:
            continue
        if regchar.search(word) and not regmul.search(word) and not ('http' in word):

# Checkt ob Silbentrennung Wörter getrennt hat
            if possible_hyphenation:

                # Wenn zweite Hälfte groß geschrieben ist, ist es ein neues Wort und beide werden einzelnd weiter geschickt.
                if word[0].isupper() or word.startswith('-'):
                    if check_word(first_half, id):
                        wordnum += 1
                    possible_hyphenation = False
                    #Gleich aussortieren, wenn Wort mit Strich anfängt
                    if word.startswith('-'):
                        continue
                # Aufzählung raus sortieren    
                elif word == 'und':
                    if check_word(first_half, id):
                        wordnum += 1
                    possible_hyphenation = False
                    # Nächsten Teil der Aufzählung gleich mit entfernen
                    skip = True
                    continue
                else:
                    # Wenn zweite Hälfte klein, dann kombinieren der beiden Wörter
                    combined = first_half.strip('-') + word
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

                if check_word(splitted[1], id):
                    wordnum += 1



            
            if check_word(word, id):
                wordnum += 1
    
    return wordnum