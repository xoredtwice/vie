# In this script I am extracting bag-of-word model from parsed AST
# Developer: Mehdi Nejadgholi m_nejadg@encs.concordia.com
#_______________________________________________________________________________________
import sys
import os

from bson.objectid import ObjectId
from pymongo import MongoClient
import re


import gensim
from gensim import corpora, models

import time

#__________________________________________________________
def main(argv):
    
    TEST_COUNT = -1
    mongo_connection_string = 'mongodb://votexx-admin:##1BGU8iGSKy5@192.168.4.1/'

    print(time.strftime("%Y-%m-%d %H:%M"))
    
    client = init_mongo_connection(mongo_connection_string)
    collection = client['votexx']['papers']


    bows = []
    index = 0
    err_count = 0
    err_list = []

    bows = mongo_get_bows(collection, TEST_COUNT)

    print("************************************************")
    print("Generating LDA model...")

    predefined_topics = ["coercion resistance", "verifiability"]
    num_topics = 20
    lda_model = generate_lda(bows, num_topics)
    for i,topic in lda_model.show_topics(formatted=True, num_topics=num_topics, num_words=10):
        print(str(i)+": "+ topic)
        print()

    lda_model.save("../exp/trained/lda_" + time.strftime("%Y-%m-%d-%H-%M"))


#________________________________________________________________________________________
def generate_lda(bows, num_topics): # generate LDAs from smart contract Bag-of-Words

    print("\n\n\n")

    dictionary_LDA = corpora.Dictionary(bows)
    print("LDA dictionary generated")

    corpus = [dictionary_LDA.doc2bow(bow) for bow in bows]
    print("Compus generated")

    lda_model = models.LdaModel(corpus, num_topics=num_topics, \
                                  id2word=dictionary_LDA, \
                                  passes=50, alpha=[0.01]*num_topics, \
                                  eta=[0.01]*len(dictionary_LDA.keys()))


    return lda_model    

#________________________________________________________________________________________
def mongo_get_bows(papers, docs_count):
    cursor = papers.find({})
    index = 0
    err_count = 0
    err_list = []
    bows = []
    for paper in cursor:
        index = index + 1
        try:
            print(str(index) + "  " + str(paper["filename"]))
            for bow in paper["sections"]:
                bows.append(bow)
        except Exception as e:
            print(str(e))
            err_count = err_count + 1
            err_list.append(f)
            
        if docs_count != -1 and index >= docs_count:
            break
    return bows
#________________________________________________________________________________________
def init_mongo_connection(connection_string):
    try:
        client = MongoClient(connection_string)
        print("Mongo Connection .... OK")
        return client
    except:
        print("Mongo Connection ... ERROR")
        return None

def stem(word):
    new_word = str(singularize(word))
    return new_word

def prepare_corpus():
    bows = []

    stopwords = ["cid", "e.g.", "example"]
    try:
        cursor = Paper.objects()
        for paper in cursor:
            nbow = []
            for t in paper.raw.bow:
                found = False
                if stem(t) not in stopwords and not t.isnumeric():
                    nbow.append(stem(t.lower()))
            bows.append(nbow)

    except Exception as e:
        print(str(e))

    bigram = gensim.models.Phrases(bows, min_count=2, threshold=5, connector_words=ENGLISH_CONNECTOR_WORDS, delimiter='_')
    bigram_mod = gensim.models.phrases.Phraser(bigram)

    bigram_bows = []
    for bow in bows:
        bigram_bows.append(bigram_mod[bow])

    new_bows = []
    stopwords2 = ["code","nition", "server", "use", "case", "value", "type", "system", "voter", "vote", "voting", "election", "ballot", "cid", "ability", "process", "protocol", "security", "paper", "study", "research", "number", "candidate", "scheme"]
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
    return new_bows

def run_lda():
    num_topics = 5

    new_bows = prepare_corpus()
    lda_model = my_lda_model(new_bows, num_topics)
    for i,topic in lda_model.show_topics(formatted=True, num_topics=num_topics, num_words=30):
        print(str(i) + ": " + topic)
 
    lda_model.save("../exp/vie/trained/lda_" + time.strftime("%Y-%m-%d-%H-%M"))
#________________________________________________________________________________________
def my_lda_model(bows, num_topics): # generate LDAs from smart contract Bag-of-Words
    logger = util.xxLogger.getLogger()
    nlpWrapper = util.xxGlobals.getNlpWrapper()
    results = []


    dictionary_LDA = corpora.Dictionary(bows)
    print("LDA dictionary generated")

    corpus = [dictionary_LDA.doc2bow(bow) for bow in bows]
    print("Compus generated")

    lda_model = models.LdaModel(corpus, num_topics=num_topics, \
                                  id2word=dictionary_LDA, \
                                  passes=1200, alpha='auto', eta='auto')
    # eta=[0.01]*len(dictionary_LDA.keys()))


    return lda_model 

def visualize_lda():
    lda_model =  models.LdaModel.load('local/trained/lda_2022')
    bows = prepare_corpus()

    dictionary_LDA = corpora.Dictionary(bows)
    print("LDA dictionary generated")

    corpus = [dictionary_LDA.doc2bow(bow) for bow in bows]
    print("Compus generated")
    visualisation = pyLDAvis.gensim_models.prepare(lda_model, corpus, lda_model.id2word)
    pyLDAvis.save_html(visualisation, 'LDA_Visualization.html')

def sort_document():
    lda_model =  models.LdaModel.load('local/trained/lda_2022')
    results = []
    try:
        cursor = Paper.objects()
        for paper in cursor:
            other_corpus = [common_dictionary.doc2bow(text) for text in other_texts]
            results.append([paper.raw.file_name,lda_model[paper.raw.bow]])
            print(results[-1])
                

    except Exception as e:
        print(str(e))
#________________________________________________________________________________________
if __name__ == '__main__':
    main(sys.argv[1:])
