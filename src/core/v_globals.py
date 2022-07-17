import logging
import os
from datetime import datetime
from src.core.v_logger import setup_logger
from src.back.v_mongo import MongoWrapper
from src.core.v_nlp import NlpWrapper
from src.core.v_reference import ReferenceQuery

def initialize(root_path, conf):
    global MONGO
    global NLP
    global REF_QUERY
    
    log_path = os.path.join(root_path, conf["logging"]["path"])
    if not os.path.exists(log_path):
        os.makedirs(log_path)
    setup_logger(log_path, conf["id"])
    MONGO = MongoWrapper(
        conf["mongo"]["connection-string"], conf["mongo"]["database"])
    NLP = NlpWrapper("sm")
    REF_QUERY = ReferenceQuery(os.path.join(root_path, conf["data"]["bib-path"]))

def getMongoWrapper():
    global MONGO
    return MONGO

def getNlpWrapper():
    global NLP
    return NLP

def getReferenceQueryManager():
    global REF_QUERY
    return REF_QUERY
