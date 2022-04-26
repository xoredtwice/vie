import pybtex
from pybtex.database.input import bibtex

parser = bibtex.Parser()
iacr = parser.parse_file("../iacr.bib")

counter = 0
found_counter = 0
keywords = ["vote", "voting", "ballot", "coerc"]
for entry in iacr.entries.keys():
    entry_title = iacr.entries[entry].fields["title"]
    counter = counter + 1
    #print(entry_title)
    for keyword in keywords:
        if keyword in entry_title.lower():
            print(entry_title)
            found_counter = found_counter + 1
            break

print(str(found_counter) + " in " + str(counter))
