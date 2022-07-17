import src.core.v_globals
from src.core.v_logger import info, error
from src.back.v_mongo import BibRecord, Author

import pybtex
from pybtex.database.input import bibtex
from scholarly import scholarly

import src.utils.crossref
from src.utils.v_utils import hashString
import random

class ReferenceQuery:

    def __init__(self, iacr_path="iacr.bib"):
        self.parser = bibtex.Parser()
        self.iacr = self.parser.parse_file(iacr_path)
        # pg = ProxyGenerator()
        # pg.FreeProxies()
        # scholarly.use_proxy(pg)
        info("IACR dataset loaded... " + str(
            len(self.iacr.entries)) + " entries")

    def getBibFromLocalDatabase(self, paper_title):
        cursor = None
        info("Querying bib database for " + paper_title)
        title_words = src.core.v_globals.getNlpWrapper().extractInformativeWords(
            paper_title)
        if len(title_words) != 0:
            random_word = random.choice(title_words)
            info("Random word to query: " + random_word)
            cursor = BibRecord.objects(title__icontains=random_word)
            min_diff = 1.0
            min_entry = None
            for bib in cursor:
                entry_title = bib.title
                print(entry_title)
                diff = src.core.v_globals.getNlpWrapper().compare(
                    paper_title, entry_title)
                if diff < min_diff:
                    min_entry = bib
                    min_diff = diff
            return {"difference": min_diff, "result": min_entry, "source": "CACHE"}
        else:
            info("No informative word has been returned")
            return {"difference": 1.0, "result": None, "source": "CACHE"}

    def query(self, paper_title, cache_flag=True,
              iacr_flag=True, scholarly_flag=False,
              crossref_flag=True):
        try:
            results = []

            if cache_flag:
                results.append(self.getBibFromLocalDatabase(paper_title))
                info("Cache Result: " + str(results[-1]))

            if (not cache_flag) or results[0]["difference"] > 0.01:
                if iacr_flag:
                    results.append(self.queryIACR(paper_title))
                    info("IACR Result: " + str(results[-1]))

                if scholarly_flag and results[-1]["difference"] > 0.01:
                    results.append(self.queryScholarly(paper_title))
                    info("Scholarly Result: " + str(results[-1]))

                if crossref_flag and results[-1]["difference"] > 0.01:
                    results.append(self.queryCrossRef(paper_title))
                    info("CrossRef Result: " + str(results[-1]))

            min_result = min(results, key=lambda x: x["difference"])

            if min_result["source"] == "CACHE":
                bib_record = min_result["result"]
                info("Loading bib record from cache")
            else:
                if min_result["source"] != "SCHOLARLY":
                    bib_record = self.bibtexResultToBibModel(min_result)
                else:
                    bib_record = self.scholarlyToBibModel(min_result)

                bib_record.save()
                info("New bib record saved to database")
                info(bib_record.title)
            return bib_record
        except Exception as e:
            error(e)
            raise e

    def queryIACR(self, paper_title):
        min_diff = 1.0
        min_entry = None

        for entry in self.iacr.entries.keys():
            entry_title = self.iacr.entries[entry].fields["title"]
            diff = src.core.v_globals.getNlpWrapper().compare(
                paper_title, entry_title)
            if diff < min_diff:
                min_entry = self.iacr.entries[entry]
                min_diff = diff

        return {"difference": min_diff, "result": min_entry, "source": "IACR"}

    def queryScholarly(self, paper_title):
        query_obj = scholarly.search_pubs(paper_title)
        result = next(query_obj).bib

        diff = src.core.v_globals.getNlpWrapper().compare(
            paper_title, result["title"])

        info("Scholarly result : " + result["title"])

        return {"difference": diff, "result": result, "source": "SCHOLARLY"}

    def queryCrossRef(self, paper_title):
        result = util.crossref.get_bib_from_title(paper_title, get_first=True)

        if result is not None and result[0]:
            bib_string = result[1]
            bibtex_entry = self.bibtexEntryFromString(bib_string)
            diff = src.core.v_globals.getNlpWrapper().compare(
                paper_title, bibtex_entry.fields["title"])
        else:
            diff = 1.0
            bibtex_entry = None
            info("CrossRef Failed to find " + paper_title)

        return {"difference": diff, "result": bibtex_entry, "source": "CROSSREF"}

    def bibtexEntryFromString(self, bib_string):
        parsed_bibtex = pybtex.database.parse_string(bib_string, "bibtex")
        for entry in parsed_bibtex.entries.values():
            return entry

    def bibtexResultToBibModel(self, result):
        entry = result["result"]
        bib_record = BibRecord()

        if hasattr(entry, "type"):
            bib_record.article_type = entry.type
        else:
            try:
                bib_record.article_type = entry[0]
            except:
                pass

        bib_record.title = entry.fields["title"]
        bib_record.year = entry.fields["year"]
        if "url" in entry.fields:
            bib_record.url = entry.fields["url"]
        if "doi" in entry.fields:
            bib_record.doi = entry.fields["doi"]
        if "abstract" in entry.fields:
            bib_record.abstract = entry.fields["abstract"]


        bib_record.article_meta = {"source": result["source"]}

        for key in entry.persons.keys():
            if key == "author" or key == "editor":
                for person in entry.persons[key]:
                    query_string = ""
                    firstname = " ".join(person.first_names)
                    for word in person.first_names:
                        res = [char for char in word if char.isupper()]
                        for char in res:
                            query_string += char

                    middlename = " ".join(person.middle_names)
                    for word in person.middle_names:
                        res = [char for char in word if char.isupper()]
                        for char in res:
                            query_string += char
                    lastname = " ".join(person.last_names)
                    for word in person.last_names:
                        query_string += " "
                        query_string += word
                    info(
                        "Searching Author database for: " + query_string)

                    authors = Author.objects(name=query_string)
                    if authors.count() == 0:
                        info("Author not found. Adding new author")
                        new_author = Author()
                        new_author.firstname = firstname
                        new_author.middlename = middlename
                        new_author.lastname = lastname
                        new_author.name = query_string
                        new_author.code = hashString(
                            src.core.v_globals.getNlpWrapper().cleanString(
                                query_string))
                    elif authors.count() == 1:
                        info("Author found.")
                        new_author = authors.first()
                        new_author.firstname = firstname
                        new_author.middlename = middlename
                        new_author.lastname = lastname
                    else:
                        raise Exception("two authors with same name")
                    new_author.save()
                    bib_record.authors.append(new_author)

        return bib_record

    def scholarlyToBibModel(self, result):
        entry = result["result"]
        bib_record = BibRecord()
        for author_name, author_id in zip(entry["author"], entry["author_id"]):
            if author_name is not None:
                if author_id is None:
                    info(f"Author with null code {author_name}")
                    author_id = hashString(
                        src.core.v_globals.getNlpWrapper().cleanString(
                            author_name))
                found_count = Author.objects(code=author_id).count()
                if found_count == 0:
                    new_author = Author()
                    new_author.code = author_id
                    new_author.name = author_name
                    new_author.save()
                    info(f"New Author saved to database.: {author_name}")
                    bib_record.authors.append(new_author)
                elif found_count == 1:
                    logger.info(f"Author found in database. {author_name}")
                    bib_record.authors.append(
                        Author.objects(code=author_id)[0])
                else:
                    raise Exception(
                        "duplicate authors with the same code")
            else:
                raise Exception("author_name field is empty")

        bib_record.title = entry["title"]
        bib_record.year = entry["year"]
        bib_record.article_meta = {"source": "SCHOLARLY"}
        bib_record.venue = entry["venue"]
        bib_record.cites = entry["cites"]
        bib_record.abstract = entry["abstract"]
        if "url" in entry:
            bib_record.url = entry["url"]
