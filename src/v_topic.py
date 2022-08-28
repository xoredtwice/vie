import sys
import os

from bson.objectid import ObjectId
from pymongo import MongoClient
import re


from gensim.models.phrases import Phrases, ENGLISH_CONNECTOR_WORDS
import gensim
from gensim import corpora, models
from gensim.parsing.porter import PorterStemmer

import time

from src.core.v_logger import info, error
from src.core.v_globals import getNlpWrapper
from src.back.v_mongo import Paper

import pyLDAvis.gensim_models
##########################################################################
def stem(word):
    p = PorterStemmer()
    new_word = str(p.stem(word))
    return new_word
##########################################################################
def prepare_corpus():
    bows = []

    stopwords = ["cid", "e.g.", "example"]
    try:
        cursor = Paper.objects()
        for paper in cursor:
            nbow = []
            for t in paper.bow:
                if stem(t) not in stopwords and not t.isnumeric() and re.search('[a-zA-Z]', t) != None:
                    st = stem(t.lower())
                    if len(st) > 3:
                        nbow.append(st)
            bows.append(nbow)

    except Exception as e:
        print(str(e))

    bigram = gensim.models.Phrases(bows, min_count=2, threshold=5, connector_words=ENGLISH_CONNECTOR_WORDS, delimiter='_')
    bigram_mod = gensim.models.phrases.Phraser(bigram)

    bigram_bows = []
    for bow in bows:
        bigram_bows.append(bigram_mod[bow])

    new_bows = []
    stopwords2 = ["code","nition", "server", "use", "case", "value", "type", "system", "rate", "design", "calculation", "unit", "value", "point", "cid", "ability", "process", "protocol", "security", "paper", "study", "research", "number", "candidate", "scheme"]
    for bow in bigram_bows:
        new_bow = []
        for t in bow:
            if "_" in t:
                if "ability" in t:
                    if "ver" in t:
                        new_bow.append("verifiability")
                    elif "us" in t:
                        new_bow.append("usability")
                elif "tion" in t:
                    if "con" in t:
                        new_bow.append("confirmation")
                    elif "ver" in t:
                        new_bow.append("verification")
            elif t not in stopwords2:
                new_bow.append(t)
        new_bows.append(new_bow)

    print(new_bows)
    return new_bows
##########################################################################
def run_lda():
    num_topics = 4

    new_bows = prepare_corpus()
    lda_model = my_lda_model(new_bows, num_topics)
    for i,topic in lda_model.show_topics(formatted=True, num_topics=num_topics, num_words=10):
        info(str(i) + ": " + topic)
 
    lda_model.save("local/trained/lda")
##########################################################################
def my_lda_model(bows, num_topics): # generate LDAs from smart contract Bag-of-Words
    nlpWrapper = getNlpWrapper()
    results = []


    dictionary_LDA = corpora.Dictionary(bows)
    info("LDA dictionary generated")

    corpus = [dictionary_LDA.doc2bow(bow) for bow in bows]
    info("Compus generated")

    lda_model = models.LdaModel(corpus, num_topics=num_topics, \
                                  id2word=dictionary_LDA, \
                                  passes=1200, alpha='auto', eta='auto')
    # eta=[0.01]*len(dictionary_LDA.keys()))


    return lda_model 
##########################################################################
def visualize_lda():
    lda_model =  models.LdaModel.load('local/trained/lda')
    bows = prepare_corpus()

    dictionary_LDA = corpora.Dictionary(bows)
    info("LDA dictionary generated")

    corpus = [dictionary_LDA.doc2bow(bow) for bow in bows]
    info("Compus generated")
    visualisation = pyLDAvis.gensim_models.prepare(lda_model, corpus, lda_model.id2word)
    pyLDAvis.save_html(visualisation, 'LDA_Visualization.html')
##########################################################################
def sort_document():
    lda_model =  models.LdaModel.load('local/trained/lda')
    results = []
    try:
        cursor = Paper.objects()
        for paper in cursor:
            other_corpus = [common_dictionary.doc2bow(text) for text in other_texts]
            results.append([paper.raw.file_name,lda_model[paper.raw.bow]])
            print(results[-1])
                

    except Exception as e:
        error(e, True)
