import sys

import pdfminer
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.converter import XMLConverter, HTMLConverter, TextConverter
from pdfminer.layout import LAParams
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LTChar

from pdfminer.layout import LTTextBoxHorizontal
from pdfminer.layout import LTTextContainer

import io

from src.back.v_mongo import Paper
from src.core.v_logger import info,error

import numpy as np
import math
import os
import collections


def pdfParser(file_path, page_no=''):
    logger = util.xxLogger.getLogger()
    logger.debug("... Using PDFMiner version: " + pdfminer.__version__)
    logger.debug("... Start parsing PDF")

    paper = PaperModel(file_path)
    fp = open(file_path, 'rb')
    rsrcmgr = PDFResourceManager()
    retstr = io.StringIO()
    codec = 'utf-8'
    laparams = LAParams()
    device = TextConverter(rsrcmgr, retstr, laparams=laparams)
    # Create a PDF interpreter object.
    interpreter = PDFPageInterpreter(rsrcmgr, device)

    # Process each page contained in the document.
    counter = 0
    for page in PDFPage.get_pages(fp):
        if page_no == '' or counter == int(page_no) - 1:
            interpreter.process_page(page)
            paper.new_page(retstr.getvalue())
        counter = counter + 1

    logger.debug("... Done parsing PDF")

    return paper
# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx


def getElementData(element):
    logger = util.xxLogger.getLogger()
    element_dict = {}
    element_dict["page_no"] = element[0]
    element_dict["data"] = element[1]
    element_dict["size"] = element[2]
    element_dict["size_key"] = round(element[2], 2)
    element_dict["text"] = ""
    if hasattr(element[1], "get_text"):
        element_dict["text"] = element[1].get_text()

    return element_dict

# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
def compareFontStrings(font1, font2):

    if font1 == font2:
        return 0
    else:
        # split the added size
        font1_size = float(font1.split("-")[-1])
        font2_size = float(font2.split("-")[-1])

        if math.isclose(font1_size, font2_size):
            if "bold" in font2.lower() or "-medi-" in font2.lower():
                return 1
            else:
                return -1
        elif font1_size > font2_size:
            return -1
        else:
            return 1
# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx


def pdfParserUsingLayout(file_path):
    # a test code to see how Layout detection works.
    logger = util.xxLogger.getLogger()
    logger.debug("... Using PDFMiner version: " + pdfminer.__version__)
    logger.debug("... Start parsing PDF using Layout")

    paper = RawPaper(file_name=os.path.basename(file_path))
    fp = open(file_path, 'rb')
    rsrcmgr = PDFResourceManager()
    codec = 'utf-8'
    laparams = LAParams()

    device = PDFPageAggregator(rsrcmgr, laparams=laparams)
    interpreter = PDFPageInterpreter(rsrcmgr, device)

    # max_size will help us finding the title
    max_size = 0
    line_counter = 0
    cool_counter = 0
    whole_fonts = {}

    for page in PDFPage.get_pages(fp):
        interpreter.process_page(page)
        layout = device.get_result()

        lines = []
        elements = []

        for element in layout:

            counter = 1
            if isinstance(element, LTTextContainer):

                for text_line in element:

                    is_mixed = False
                    main_font = ""
                    fonts = {}
                    line_counter += 1

                    try:
                        iterator = iter(text_line)
                    except TypeError:
                        iterator = [text_line]
                        # not iterable

                    for character in iterator:
                        if isinstance(character, LTChar):
                            # print(character)
                            # print(character.__dict__)
                            # print(character.fontname)
                            size_key = round(character.size, 2)
                            font_key = character.fontname + "-" + str(size_key)

                            if font_key in fonts:
                                fonts[font_key] += 1
                            else:
                                fonts[font_key] = 1

                            if font_key in whole_fonts:
                                whole_fonts[font_key] += 1
                            else:
                                whole_fonts[font_key] = 1

                    #fonts = dict(sorted(fonts.items(), key=lambda item: item[1], reverse=True))
                    #sizes = dict(sorted(sizes.items(), key=lambda item: item[1], reverse=True))

                    if len(fonts) != 0:
                        main_font = max(fonts, key=fonts.get)
                        if len(fonts) > 1:
                            is_mixed = True

                        lines.append({"text": text_line.get_text(),
                                      "mixed": is_mixed, "font": main_font})

            elements.append(element)

        paper.newPage(lines)

    #print("lines = " + str(line_counter))

    # print(whole_fonts)
    #paper.fonts = whole_fonts
    paper.main_font = max(whole_fonts, key=whole_fonts.get)
    logger.debug("main_font = " + paper.main_font)

    max_font = ""
    for font in whole_fonts:
        if max_font == "":
            max_font = font
        else:
            if compareFontStrings(max_font, font) == 1:
                max_font = font

    logger.debug("max_font = " + max_font)

    title = ""
    for line in paper.x_lines:
        if line["font"] == max_font:
            title += line["text"]

    paper.title = title
    logger.debug("paper.title = " + title)
    if len(title) < 10 or len(title) > 100:
        paper.warnings.append("[WARNING] title size")

    logger.debug("... Done parsing PDF")

    return paper
