import sys
import argparse
import pathlib
import json
from PyQt5.QtWidgets import QApplication
import os
from src.utils.yaml_wrapper import load_configuration
from src.core.v_logger import info, error
from src.core.v_globals import initialize
from src.core.v_parser import pdfParserUsingLayout
from src.back.v_mongo import Paper

from src.v_import import import_pdf_files
from src.v_extract import prepare_bows
###############################################################################
root_path = str(pathlib.Path(__file__).parent.resolve())

parser = argparse.ArgumentParser(description='Automated SoK on Voting Literature')
parser.add_argument('-f', dest='conf_path', type=ascii, default=os.path.join(root_path, "conf", "01_local_configuration.yaml"),
                    help='configuration YAML file path')
parser.add_argument('-c', dest='commands', type=ascii, nargs='+',
                    default='import',
                    help='list of commands to execute from: import, prepare, extract, lda and visualize.')

args = parser.parse_args()

conf = load_configuration(os.path.abspath(args.conf_path[1:-1]))

initialize(root_path, conf)

if "'import'" in args.commands:
    info("[[IMPORT]] {")
    import_pdf_files(conf["data"]["path"])
    info("[[IMPORT]] }")

if "'prepare'" in args.commands:
    info("[[PREPARE]] {")
    prepare_bows()
    info("[[PREPARE]] }")

if "'extract'" in args.commands:
    info("[[EXTRACT]] {")
    info("[[EXTRACT]] }")

if "'lda'" in args.commands:
    info("[[LDA]] {")
    run_lda()
    info("[[LDA]] }")

if "'visualize'" in args.commands:
    info("[[VISUALIZE]] {")
    # creating apyqt5 application
    app = QApplication(sys.argv)

    # creating a window object
    main = InspectionDialog()

    # showing the window
    main.show()

    # loop
    sys.exit(app.exec_())

    info("[[VISUALIZE]] }")