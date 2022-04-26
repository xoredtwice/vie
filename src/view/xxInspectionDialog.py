# importing various libraries
from PyQt5.QtWidgets import QDialog, QPushButton, QLineEdit
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout
from PyQt5.QtGui import QIcon

import util.xxGlobals

from model.xxMongoModels import Paper, BibRecord, Opinion

import util.xxUtils
import util.xxLogger

from view.xxGraphLayout import GraphLayout
from view.xxPaperEditLayout import PaperEditLayout
from view.xxBibEditLayout import BibEditLayout
from view.xxOpinionEditLayout import OpinionEditLayout
from view.xxControlPanelLayout import ControlPanelLayout

import random

# main window
# which inherits QDialog
class InspectionDialog(QDialog):

    # constructor
    def __init__(self, parent=None):
        super(InspectionDialog, self).__init__(parent)
        png_files = util.xxUtils.findFilesByExtention(
            "~/Pictures/Wallpapers/", "png")

        self.setWindowIcon(QIcon(random.choice(png_files)))
        self.setWindowTitle("Voting Literature made Z3")
        self.setMinimumSize(800, 1300)

        self.active_paper = Paper()
        self.control_panel_view = ControlPanelLayout(self)
        self.graph_view = GraphLayout(self)
        self.paper_edit_view = PaperEditLayout(self)
        self.bib_edit_view = BibEditLayout(self)
        self.opinion_edit_view = OpinionEditLayout(self)
        # Constructing the layout, adding the components
        main_layout = QVBoxLayout()

        # l2 is a Horizontal layout. Custom components are here
        h1_layout = QHBoxLayout()

        l2_v1_layout = QVBoxLayout()
        l2_v1_layout.addLayout(self.control_panel_view)
        h1_layout.addLayout(l2_v1_layout)

        l2_v2_layout = QVBoxLayout()
        l2_v2_layout.addLayout(self.paper_edit_view)
        l2_v2_layout.addLayout(self.bib_edit_view)
        h1_layout.addLayout(l2_v2_layout)

        l2_v3_layout = QVBoxLayout()
        # l3_layout.addWidget(self.pdf_view)
        l2_v3_layout.addLayout(self.graph_view)

        l2_v3_layout.addLayout(self.opinion_edit_view)

        h1_layout.addLayout(l2_v3_layout)

        # ----------------------------------------------------
        main_layout.addLayout(h1_layout)

        # self.pdf_view.resize(900, 500)
        # self.pdf_view.loadPdf("/home/zero/workspace/votexx/vie/test/data/2007.civitas-tr.pdf")
        # self.pdf_view.show()

        # setting layout to the main window
        self.setLayout(main_layout)

    def update(self, new_paper=None, update_only_graph=False):
        logger = util.xxLogger.getLogger()
        logger.info("Updating view from main paper....")
        if new_paper is not None:
            self.active_paper = new_paper
            # TODO:: Temporary, remove it
            # self.active_paper.deleteOpinions()
        viewDict = self.active_paper.getViewDict()
        if not update_only_graph:
            self.paper_edit_view.update(viewDict)
            if "bib_approved" in self.active_paper.raw.flags:
                self.bib_edit_view.update(
                    self.active_paper.getViewDict()["title"],
                    self.active_paper.bib)
            else:
                self.bib_edit_view.update(
                    self.active_paper.getViewDict()["title"],
                    BibRecord())
        self.graph_view.update(viewDict)

    def updateOpinionView(self, index, group):
        viewDict = self.active_paper.getViewDict()
        opinion = viewDict[group][index]
        self.opinion_edit_view.update(opinion)
