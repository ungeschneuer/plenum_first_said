from ctypes import sizeof
import logging
import re
from string import punctuation
import xml_processing
from database import add_to_queue, check_newness, twittRedis
import difflib


# Normalisierungfunktion von nyt_first_said
def normalize(raw_word):

    # Ausfiltern von weiteren Zeichen im Testlauf
    regexexp = re.compile('-{2,}')

    # Entfernen von Zeichen (Wie schwer kann das sein??!!)
    punctuation = r"""#"!$%&'())*+,‚."/:;<=>?@[\]^_`{|}~“”„"""
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

    if stripped_word.endswith('ʼ'):
        stripped_word = stripped_word.strip('ʼ')

    return stripped_word


# Check ob ein valides Wort und weitere Korrigierung
def ok_word(s):
# Entfernung hier von html, bzw, und, oder, weil Aufzählungen mit Bindestrich und domains nicht gut rausgefiltert werden.
    if len(s) < 5 or s.endswith(('ts', 'html', 'de', 'bzw', 'oder', 'und', 'wie')) or s.startswith('www') or s[-1].isupper(): 
        return False

    return (not any(i.isdigit() or i in '(.@/#-_§ ' for i in s))

# Normalisiert das Wort, überprüft ob es schon im Speicher ist und fügt es der Queue hinzu
def check_word(word, id):
    norm_word = normalize(word)

    if ok_word(norm_word):
        if check_newness(norm_word, id):
            return True
        else:
            return False
    else:
        return False


# Filtert aus XML Datei die tatsächlichen Wortbeiträge
def get_wortbeitraege(xml_file):
    
    text = xml_processing.getText(xml_file)
    if not text:
        return False

    sanitized = []
    regex_url = '(http|ftp|https)://([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?'

    for sentence in text:
        # Encoding funktioniert nicht komplett, darum sanitizing
        sentence = sentence.replace(u'\xa0', u' ') # Sonderzeichen entfernen
        sentence = sentence.replace('\n', ' ') # Zeilenumbrüche
        sentence = sentence.replace('  ', ' ') # Doppelte Leerzeichen
        sentence = re.sub(regex_url, '', sentence) # URL-Filter
        sanitized.append(sentence)

    return sanitized


# TODO Dehyphenation auf Line Level
# https://stackoverflow.com/questions/43666790/python-how-do-i-merge-hyphenated-words-with-newlines
def wordsplitter(text):
    words = []

    try:
        for sentence in text:
            sentence_words = sentence.split()

            # When uppercase letter in word split it
            for word in sentence_words:
                words += re.split('(?=[A-Z])', word)

        if 'Beginn:' in words:
            words = words[words.index('Beginn:')+1:]
        elif 'Beginn' in words:
            words = words[words.index('Beginn')+1:]
    except Exception as e:
        logging.exception(e)
        exit()
    
    return words


def wordsfilter(words, id):  
    new_words = []
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
                        new_words.append(first_half)
                    possible_hyphenation = False
                    #Gleich aussortieren, wenn Wort mit Strich anfängt
                    if word.startswith('-'):
                        continue
                # Aufzählung raus sortieren    
                elif word == 'und' or word == 'oder' or word == 'bzw':
                    if check_word(first_half, id):
                        new_words.append(first_half)
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
                    new_words.append(splitted[1])

            
            if check_word(word, id):
                new_words.append(word)
    
    return new_words

# Filtert Sprechanteile aus Protokoll, splittete und filtert sie. 
def process_woerter (xml_file, id):

    raw_results = get_wortbeitraege(xml_file)

    if not raw_results:
        return raw_results
        
    words = wordsplitter(raw_results)

    return(wordsfilter(words, id))


def prune(new_words, id):
    
    pruned_words = find_matches(new_words)

    for word in pruned_words:
        add_to_queue(word, id)



# Recursive match finding der Liste, um Index-Fehler zu vermeiden
def find_matches(new_words):
    for word in new_words:
        matches = difflib.get_close_matches(word, new_words, n=4)
        
        if matches and len(matches) > 1:
            for match in matches:
                if match == word:
                    continue
                new_words.remove(match)
            find_matches(new_words)
            break
    return new_words
        




if __name__ == "__main__":
    file = '/Users/marcel/Documents/2021/plenum_first_said.nosync/parser/archive/5445.xml'
    root = xml_processing.parse(file)
    text = get_wortbeitraege(root)
    words = wordsplitter(text)

