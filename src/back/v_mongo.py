from mongoengine import connect, disconnect

from bson.objectid import ObjectId

import src.core.v_globals

import mongoengine

from src.core.v_logger import info, error
from mongoengine.queryset.visitor import Q

class MongoWrapper:

    def __init__(self, connection_string, database_name):
        self.client = self.connect(connection_string)
        self.database = database_name

    def connect(self, connection_string):
        try:
            client = connect(host=connection_string)
            info("Mongo.connect() ... OK")
            return client
        except Exception as e:
            error(e)
            return None

    def getRandomPaper(self, flag=""):
        try:
            # print(self.client.objects())

            if flag != "":
                cursor = Paper.objects().aggregate([
                    {"$match": {"raw.flags": flag}},
                    {"$sample": {"size": 1}}
                ])
            else:
                cursor = Paper.objects().aggregate([
                    {"$sample": {"size": 1}}
                ])

            for m_paper in cursor:
                # print(m_paper)
                temp = Paper.objects(id=m_paper["_id"])
                for t in temp:
                    return t

        except Exception as e:
            error(e)
            return None

    def getPaperById(self, paper_id):
        try:
            papers = self.client[self.database][self.collection]

            cursor = papers.find({"_id": ObjectId(paper_id)})
            for m_paper in cursor:
                paper = RawPaper(m_paper)
                return paper
        except Exception as e:
            raise e
            return False

    def getPaperReferenceOpinions(self, paper_id):
        try:

            opinions = []
            cursor = Opinion.objects(in_paper_id=paper_id)
            for opinion in cursor:
                opinions.append(opinion)

            return opinions
        except Exception as e:
            raise e
            return False

    def getPaperCitationOpinions(self, paper_id):
        try:
            opinions = []
            cursor = Opinion.objects(about_paper_id=paper_id)
            for opinion in cursor:
                opinions.append(opinion)
            return opinions
        except Exception as e:
            raise e
            return False

    # def getPaperByBibName(self, query_string):
    #     try:

    #     except Exception as e:
    #         raise e
    #         return False

    def updateFlags(self, paper):
        try:
            papers = self.client[self.database][self.collection]
            myquery = {"origin": paper.origin}
            newvalues = {"$set": {"flags": paper.flags}}

            x = papers.update_one(myquery, newvalues)
            info(f"{x.modified_count} documents updated.")
            return True
        except Exception as e:
            raise e
            return False

    def updatePaperMeta(self, paper):
        try:
            papers = self.client[self.database][self.collection]
            info(paper.origin)
            myquery = {"origin": paper.origin}
            newvalues = {"$set": {"year": paper.year,
                                  "title": paper.title, "flags": paper.flags}}

            x = papers.update_one(myquery, newvalues)
            info(f"{x.modified_count} documents updated.")
            return True
        except Exception as e:
            raise e
            return False

class Author(mongoengine.Document):
    name = mongoengine.StringField()
    code = mongoengine.StringField()
    firstname = mongoengine.StringField()
    middlename = mongoengine.StringField()
    lastname = mongoengine.StringField()

class Opinion(mongoengine.Document):
    in_paper_id = mongoengine.ObjectIdField()
    about_paper_id = mongoengine.ObjectIdField()
    texts = mongoengine.ListField(mongoengine.StringField())
    reference_id = mongoengine.StringField()
    reference_string = mongoengine.StringField()
    view_id = mongoengine.StringField()
    candidate_bib = mongoengine.DictField()

    meta = {'indexes': [
            {'fields': ['$reference_string', '$texts'],
             'default_language': 'english',
             'weights': {'reference_string': 10, 'texts': 2}}]}

    def getViewDict(self):
        vd = {}
        vd["reference_id"] = self.reference_id
        vd["reference_string"] = self.reference_string
        vd["texts"] = self.texts

        return vd

class BibRecord(mongoengine.Document):
    query_string = mongoengine.StringField()
    title = mongoengine.StringField()
    authors = mongoengine.ListField(mongoengine.ReferenceField(Author))
    year = mongoengine.StringField()
    doi = mongoengine.StringField()
    url = mongoengine.StringField()
    article_type = mongoengine.StringField()
    venue = mongoengine.StringField()
    article_meta = mongoengine.DictField()
    cites = mongoengine.IntField()
    abstract = mongoengine.StringField()

    meta = {'indexes': [
            {'fields': ['$title', '$query_string'],
             'default_language': 'english',
             'weights': {'title': 2, 'query_string': 1}}]}

    def getViewDict(self):
        vd = {}
        vd["query"] = self.query_string
        vd["article_type"] = self.article_type
        vd["title"] = self.title
        vd["authors"] = self.authors
        vd["year"] = self.year
        vd["venue"] = self.venue
        vd["doi"] = self.doi
        vd["url"] = self.url

        return vd

class Paper(mongoengine.Document):

    file_name = mongoengine.StringField()

    title = mongoengine.StringField()
    year = mongoengine.StringField()

    x_lines = mongoengine.ListField()
    main_font = mongoengine.StringField()

    references = mongoengine.DictField()
    mentions = mongoengine.DictField()
    sections = mongoengine.ListField()
    flags = mongoengine.ListField()
    warnings = mongoengine.ListField()

    bow = mongoengine.ListField(mongoengine.StringField())

    bib = mongoengine.ReferenceField(BibRecord)


    meta = {'strict': False, 'collection': 'evoteid2022',
            'indexes': [
            {'fields': ['$title', '$bow'],
             'default_language': 'english',
             'weights': {'title': 2, 'bow': 1}}]}

    def deleteOpinions(self):
        info("Removing All opinions")
        self.references.clear()
        self.citations.clear()
        self.references.clear()
        self.mentions.clear()
        self.save()

    def getViewDict(self):
        vd = {}
        if "bib_approved" in vd["flags"]:
            vd["title"] = self.bib.title
            vd["year"] = self.bib.year
        else:
            vd["title"] = self.title
            vd["year"] = self.year            

        vd["id"] = str(self.id)
        vd["file_name"] = self.file_name

        vd["sections"] = self.sections
        vd["references"] = self.references
        vd["mentions"] = self.mentions
        vd["flags"] = self.flags

        vd["references"] = []
        vd["citations"] = []
        if self.id is not None:
            cursor = Opinion.objects(Q(in_paper_id=self.id) | Q(
                about_paper_id=self.id))
            for opinion in cursor:
                if opinion.in_paper_id == self.id:
                    vd["references"].append(opinion)
                else:
                    vd["citations"].append(opinion)

        return vd

    def getBibViewDict(self):
        if self.bib is not None:
            return self.bib.getViewDict()
        else:
            vd = {}
            vd["query"] = ""
            vd["article_type"] = ""
            vd["title"] = ""
            vd["authors"] = []
            vd["year"] = ""
            vd["venue"] = ""
            vd["doi"] = ""
            vd["url"] = ""

            return vd
