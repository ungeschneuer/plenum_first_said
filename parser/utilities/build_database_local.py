import os
#from progressbar import printProgressBar
import xml_processing
from text_parse import process_woerter


wordnum = 0
directory = 'parser/archive/'
files = os.listdir(directory)
total = len(files)

files.sort(key=lambda x: int(x.split('.')[0]))

for i, filename in enumerate(files):
    if filename.endswith(".xml"):
        filepath = directory + filename
        xml_file = xml_processing.parse(filepath)
        wordnum += process_woerter(xml_file, filename.strip('.xml'))   
    print(filename)
    # printProgressBar(i + 1, total, prefix = 'Progress:', suffix = 'Complete', length = 50)

print("Fertig")
