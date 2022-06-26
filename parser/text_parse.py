from ctypes import sizeof
import logging
import re
from string import punctuation
import xml_processing
import difflib
from database import add_to_queue, check_newness

# Beginn des Dokumentes finden mit Rechtschreibfehlern. 
def find_beginn(text):

    if text.find('Beginn:') == -1:
        text = text[text.find('Beginn'):]
    else:
        text = text[text.find('Beginn'):]
    
    return text

# Silbentrennung rückgängig machen. 
def dehyphenate(text):

    lines = text.split('\n')
    for num, line in enumerate(lines):
        if line.endswith('-') or line.endswith('–'):
            # the end of the word is at the start of next line
            end = lines[num+1].split()[0]
            # we remove the - and append the end of the word
            lines[num] = line[:-1] + end
            # and remove the end of the word and possibly the 
            # following space from the next line
            lines[num+1] = lines[num+1][len(end)+1:]

    return '\n'.join(lines)

# Cleaning vor dem Wordsplitting
def pre_split_clean(text):

    # Encoding funktioniert nicht komplett, darum sanitizing
    text = text.replace(u'\xa0', u' ') # Sonderzeichen entfernen
    text = text.replace('  ', ' ') # Doppelte Leerzeichen

    regex_url = '(http|ftp|https|http)://([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?'
    text = re.sub(regex_url, '', text) # URL-Filter

    return text

# Wörter splitten am Leerzeichen
def wordsplitter(text):
    words = []

    try:
        words = text.split()

    except Exception as e:
        logging.exception(e)
        exit()
    
    return words

# Wenn Aufzählung, werden die nächsten zwei Worte entfernt.
def de_enumaration(words):

    clean_words = []
    skip = 0

    for word in words:
        if skip > 0:
            skip -= 1
            continue
        
        if word.endswith('-') or word.endswith('–'):
            skip = 2
        else:
            clean_words.append(word)
    
    return clean_words


def wordsfilter(words, id):  
    new_words = []
    
    # Wort hat Buchstaben
    regchar = re.compile('([A-Z])|([a-z])\w+')
    # Wort hat gleiche Zeichen hintereinander
    regmul = re.compile('([A-z])\1{3,}')
    # Wort hat nicht nur am Anfag Großbuchstaben
    regsmall = re.compile('[A-z]{1}[a-z]*[A-Z]+[a-z]*')

    for word in words:
        if regchar.search(word) and not regmul.search(word) and not regsmall.search(word):

            # Enfernen von sonst nicht filterbaren Aufzählungen
            if word.endswith('-,') or word.endswith('-') or word.endswith('–') or word.startswith('-'):
                continue

            # Trennung von Bundestrich-Kompositionen
            if '/' in word:
                splitted = word.split('/')
                word = splitted[0]

                if check_word(splitted[1], id):
                    new_words.append(splitted[1])
            
            if check_word(word, id):
                new_words.append(word)
    
    return new_words

# Hauptfunktion des Moduls für die Aufbereitung und Trennung der Wörter
def process_woerter (xml_file, id):

    raw_text = xml_processing.getText(xml_file)

    if not raw_text:
        return False
    
    # Verarbeitung des String
    text = find_beginn(raw_text)
    text = pre_split_clean(text)
    text = dehyphenate(text)

    # Verarbeitung des Wort-Arrays
    words = wordsplitter(text)
    words = de_enumaration(words)

    return(wordsfilter(words, id))


# Normalisierung vor Datenbank-Abgleich des Wortes
def normalize(raw_word):

    # Ausfiltern von weiteren Zeichen im Testlauf
    regexexp = re.compile('-{2,}')

    # Entfernen von Zeichen (Wie schwer kann das sein??!!)
    punctuation = r"""#"!$%&'())*+,‚.":;<=>?@[\]^_`{|}~“”„"""
    stripped_word = raw_word.translate(str.maketrans('', '', punctuation))

    if stripped_word.endswith('ʼ') or stripped_word.endswith('’'):
        stripped_word = stripped_word[:-1]

    return stripped_word


# Check ob es ein valides Wort ist
def ok_word(s):
# Entfernung hier von html, bzw, und, oder, weil Aufzählungen mit Bindestrich und domains nicht gut rausgefiltert werden.
    if len(s) < 5 or s.endswith(('ts', 'html', 'de', 'bzw', 'oder', 'und', 'wie', 'pdf')) or s.startswith('www') or s[-1].isupper(): 
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
    file = '#'
    root = xml_processing.parse(file)
    text = xml_processing.getText(root)
    text = find_beginn(text)
    text = dehyphenate(text)
    text = pre_split_clean(text)
    words = wordsplitter(text)
