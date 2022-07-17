from datetime import datetime
import logging
import os
from PyQt5.QtWidgets import QMessageBox
import traceback

def setup_logger(path, name):
    time_tag = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    log_level = logging.DEBUG

    log_path = os.path.join(path, name + "-" + time_tag + '.log')

    logger = logging.getLogger("VIE-LOGGER")
    formatter = logging.Formatter('%(asctime)s : %(message)s')
    fileHandler = logging.FileHandler(log_path, mode='w')
    fileHandler.setFormatter(formatter)
    streamHandler = logging.StreamHandler()
    streamHandler.setFormatter(formatter)

    logger.setLevel(log_level)
    logger.addHandler(fileHandler)
    logger.addHandler(streamHandler)

    logger.info("Logger started...")

def info(text):
    logger = logging.getLogger("VIE-LOGGER")
    logger.info(text)

def error(ex, show_error_dialog = False):
    logger = logging.getLogger("VIE-LOGGER")
    logger.error(str(ex))
    logger.error(traceback.format_exc())

    if show_error_dialog:
        mb = QMessageBox()
        mb.setWindowTitle("Error")
        mb.setText(str(ex))
        mb.exec_()

def lsection(text, level = 0):
    indent = "    " * level
    if level == 0 :
        lprint("***********************************")
    else:
        lprint("")
        lprint("")
    lprint(f"{indent}{text}")
    if level == 0:
        lprint("***********************************")
#*******************************************************************************