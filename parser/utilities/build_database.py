import os
from bs4 import BeautifulSoup
from database import r
from string import punctuation
from progressbar import printProgressBar
import re

# directory = '/Users/marcel/Downloads/Periode_19' # neue Dokumente 
directory = './Plenardokumente' # alte Dokumente


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

# Funktion zur Verarbeitung und beifügung des Wortes
def check_word(word):
    norm_word = normalize(word)

    if ok_word(norm_word):
        if add_word(norm_word):
            return True
    
    return False


# Filtert aus XML Datei die tatsächlichen Wortbeiträge
def get_wortbeitraege(current_xml):
    
    raw_results = []
    
    results = [i.text.strip() for i in current_xml.select('TEXT')] #alte dokumente
    # results = current_xml.find_all("p", {'klasse' : ['J', '1','O', 'J_1', 'T']}) # neue dokumente

    for result in results:
        # Encoding funktioniert nicht komplett, darum sanitizing
        sanitized = result.replace(u'\xa0', u' ') # alte dokumente
        # sanitized = result.text.replace(u'\xa0', u' ') # neue dokumente
        raw_results.append(sanitized)

    return raw_results


def process_woerter (current_xml):


    words = []
    first_half = ""
    possible_hyphenation = False
    regexp = re.compile('([A-Z])|([a-z])\w+')
    wordnum = 0


    raw_results = get_wortbeitraege(current_xml)

    for sentence in raw_results:
        words += sentence.split()

    for word in words:
        if len(word) > 3 and regexp.search(word) and not ('http' in word):

# Checkt ob Silbentrennung Wörter getrennt hat
            if possible_hyphenation:

                # Wenn zweite Hälfte groß geschrieben ist, ist es ein neues Wort und beide werden einzelnd weiter geschickt.
                if word[0].isupper() or word.startswith('-'):
                    check_word(first_half)
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

            if check_word(word):
                wordnum += 1
    
    return wordnum
    

total = len(os.listdir(directory))
wordnum = 0



for i, filename in enumerate(os.listdir(directory)):
    if filename.endswith(".xml"):
        with open(directory + "/" + filename, 'r') as f:
            data = f.read()
            data_raw = BeautifulSoup(data, features="html5lib")
            wordnum =+ process_woerter(data_raw)
        
    printProgressBar(i + 1, total, prefix = 'Progress:', suffix = 'Complete', length = 50)

print("Fertig")
print(str(wordnum) + " neue Wörter")