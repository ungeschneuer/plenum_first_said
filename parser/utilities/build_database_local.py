import os
from progressbar import printProgressBar
import xml_parse
from scrape_functions import process_woerter




    

wordnum = 0
directory = 'parser/archive/'
total = len(os.listdir(directory))

for i, filename in enumerate(os.listdir(directory)):
    if filename.endswith(".xml"):
        filepath = directory + filename
        xml_file = xml_parse.parse(filepath)
        wordnum += process_woerter(xml_file, filename.strip('.xml'))   

    printProgressBar(i + 1, total, prefix = 'Progress:', suffix = 'Complete', length = 50)

print("Fertig")
