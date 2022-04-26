import sys, getopt
import io
import logging

import numpy as np 
import re
sys.path.append('../')

from model.xxPaperModel import PaperModel
from controller.xxParser import pdfParserUsingLayout
from controller.xxNlp import NlpWrapper
from controller.xxMl import MlWrapper
from controller.xxMongo import MongoWrapper

import util.xxUtils

import util.xxGlobals

#from test.crossref import get_bib_from_title

from controller.xxReferenceQuery import ReferenceQuery
from random import randint


def find_paper(query):
    logger = util.xxLogger.getLogger()
    nlpWrapper = util.xxGlobals.getNlpWrapper()
    results = []
    axes = []
    try:
        cursor = Paper.objects()
        for paper in cursor:
            paper_full_text = ""
            for line in paper.raw.x_lines:
                paper_full_text = paper_full_text + line["text"]

            if query in paper_full_text:
                results.append(paper.raw.file_name)

        return results
    except Exception as e:
        print(str(e))
        return []

##xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
if __name__ == '__main__':

    sample_count = 1
    directory = ""
    collection = "papers2"
    experiment_id = "random"
    experiment_flags = ["EASY"]

    try:
        opts, args = getopt.getopt(sys.argv[1:],"hi:c:e:f:",["input=","connection=","exp=","flags="])
    except getopt.GetoptError:
        print('xxInspection.py -i <input> -c <mongo_connection_string> -e <experiment_id> -f <query_flags>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('xxInspection.py -i <input> -c <mongo_connection_string> -e <experiment_id> -f <query_flags>')
            sys.exit()
        elif opt in ("-i", "--input"):
            input_data = arg
        elif opt in ("-c", "--connection"):
            mongo_connection_string = arg
        elif opt in ("-e", "--exp"):
            experiment_id = arg
        elif opt in ("-f", "--flags"):
            experiment_flags = arg.split(",")
    
    util.xxGlobals.initialize()
    logger = util.xxGlobals.getLogger()

    nlpWrapper = NlpWrapper("sm")
    mlWrapper = MlWrapper()
    mongoWrapper = MongoWrapper(util.xxGlobals.DEFAULT_CONNECTION_STRING,"votexx","papers2")
    refQuery = ReferenceQuery(nlpWrapper, mongoWrapper)

    # One random from mongo collection
    if experiment_id == "flag":

        q_next = ""
        while q_next != "q" :
            paper = mongoWrapper.getRandomPaper(flag = experiment_flags[0])
            logger.info(paper)
            file_path = xxUtils.findFile(paper.original_path,"/home/zero/Zotero/storage/")
            xxUtils.openPdfFile(file_path)
            print("current flags: " + str(paper.flags))

            q_next = input("Add a flag ([Enter] to inspect next one, \"q\" to quit): ")

            if q_next != "":
                if q_next == "q":
                    print("quitting")
                    break
                else:
                    paper.flags.append(q_next)
                    mongoWrapper.updateFlags(paper)
                    q_next = ""
    elif experiment_id == "random" or experiment_id == "id":

        if experiment_id == "random" :
            paper = mongoWrapper.getRandomPaper(flag = experiment_flags[0])
        else:
            # reading ID from terminal input
            paper = mongoWrapper.getPaperById(input_data)

        logger.info(paper)
        ref = paper.references[randint(0, len(paper.references))]
        #for ref in paper.references:
        print(ref["text"])
        title = ref["text"]
        iacr_result = refQuery.query(title)
        

##xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
      


