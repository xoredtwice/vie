from src.core.v_globals import getNlpWrapper
from src.core.v_logger import info, error
from src.utils.v_utils import findFilesByExtention
from src.back.v_mongo import Paper
from src.core.v_parser import pdfParserUsingLayout

def import_pdf_files(input_path):
    nlpWrapper = getNlpWrapper()

    count = 0
    failed_count = 0

    files = findFilesByExtention(input_path)
    for pdf_path in files:

        try:
            info(str(count + 1) + "...." + pdf_path)
            paper = Paper()
            paper = pdfParserUsingLayout(pdf_path)

            # paper = nlpWrapper.extractPaperStructure(paper)
            # paper = nlpWrapper.extract_sentences_by_reference(paper)
            # paper.raw = nlpWrapper.extractSections(paper.raw)
            # paper = nlpWrapper.extractBow(paper)

            paper.save()

        except Exception as e:
            info("\n")
            info(str(count + 1) + ". " + pdf_path + " FAILED")
            error(e)
            failed_count = failed_count + 1

        count = count + 1

    info(str(count) + " papers processed")
    info(str(failed_count) + " papers failed")