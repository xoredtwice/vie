import logging
import os
from datetime import datetime
from src.core.v_logger import setup_logger
from src.back.v_mongo import MongoWrapper
from src.core.v_nlp import NlpWrapper
from src.core.xxReferenceQuery import ReferenceQuery

def initialize(root_path, conf):
    global MONGO
    global NLP
    global REF_QUERY
    
    log_path = os.path.join(root_path, conf["logging"]["path"])
    if not os.path.exists(log_path):
        os.makedirs(log_path)
    setup_logger(log_path, conf["id"])

    DEFAULT_CONNECTION_STRING = 'mongodb://we2:zPhiD8unwJ@localhost/vie'
    DEFAULT_DATABASE_NAME = "vie"
    MONGO = MongoWrapper(
        DEFAULT_CONNECTION_STRING, DEFAULT_DATABASE_NAME)
    NLP = NlpWrapper("sm")
    REF_QUERY = ReferenceQuery()


def getMongoWrapper():
    global MONGO
    return MONGO


def getNlpWrapper():
    global NLP
    return NLP


def getReferenceQueryManager():
    global REF_QUERY
    return REF_QUERY
