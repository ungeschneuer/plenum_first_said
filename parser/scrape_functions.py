import re
from string import punctuation

from sentry_sdk import capture_exception

import xml_parse
from database import add_to_queue, add_word


# Normalisierungfunktion von nyt_first_said
def normalize(raw_word):

    # Ausfiltern von weiteren Zeichen im Testlauf
    regexexp = re.compile('-{2,}')

    # Entfernen von Zeichen (Wie schwer kann das sein??!!)
    punctuation = r"""#"!$%&'()*+,‚."/:;<=>?@[\]^_`{|}~“„"""
    stripped_word = raw_word.translate(str.maketrans('', '', punctuation))


    # Check ob Spiegelstrich einen Silbentrennung ist oder tatsächlich ganzes Wort
    if (
        '-' in stripped_word
        and not stripped_word.endswith('-')
        and not stripped_word.startswith('-')
        and regexexp.search(stripped_word)
    ):
        replaced = re.sub(regexexp, '-', stripped_word)
        return normalize(replaced)

    return stripped_word


# Check ob ein valides Wort und weitere Korrigierung
def ok_word(s):

    if s.endswith('ts') or len(s) < 4: 
        return False

    return (not any(i.isdigit() or i in '(.@/#-_§ ' for i in s))

# Normalisiert das Wort, überprüft ob es schon im Speicher ist und fügt es der Queue hinzu
def check_word(word, id):  # sourcery skip: merge-nested-ifs
    norm_word = normalize(word)

    if ok_word(norm_word):
        if add_word(norm_word, id):
            add_to_queue(norm_word, id)
            return True
    
    return False


# Filtert aus XML Datei die tatsächlichen Wortbeiträge
def get_wortbeitraege(xml_file):
    
    text = xml_parse.getText(xml_file)
    sanitized = []

    for sentence in text:
        # Encoding funktioniert nicht komplett, darum sanitizing
        sentence = sentence.replace(u'\xa0', u' ')
        sentence = sentence.replace('\n', ' ')
        sanitized.append(sentence)

    return sanitized

def wordsplitter(text):
    words = []

    try:
        for sentence in text:
            words += sentence.split()
        if 'Beginn:' in words:
            words = words[words.index('Beginn:')+1:]
        if 'Beginn' in words:
            words = words[words.index('Beginn')+1:]
    except Exception as e:
        capture_exception(e)
        exit()
    
    return words


def wordsfilter(words, id):  # sourcery skip: de-morgan, hoist-statement-from-if
    wordnum = 0
    first_half = ""
    skip = False
    possible_hyphenation = False
    
    # Wort hat Buchstaben
    regchar = re.compile('([A-Z])|([a-z])\w+')
    # Wort hat nicht gleiche Zeichen hintereinander
    regmul = re.compile('([A-z])\1{3,}')

    for word in words:
        if skip:
            skip = False
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




def process_woerter (xml_file, id):

    raw_results = get_wortbeitraege(xml_file)
        
    words = wordsplitter(raw_results)

    return(wordsfilter(words, id))
