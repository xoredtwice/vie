# importing various libraries
from PyQt5.QtWidgets import QDialog, QApplication, QMessageBox, QPushButton, QLineEdit, QLabel, QComboBox
from PyQt5.QtWidgets import QListWidget, QVBoxLayout, QFileDialog

from src.core.v_globals import getNlpWrapper,getMongoWrapper

from src.core.v_logger import info, error

from src.back.v_mongo import Paper, BibRecord, Opinion
from src.core.v_parser import pdfParserUsingLayout
from mongoengine.queryset.visitor import Q

class ControlPanelLayout(QVBoxLayout):

    # constructor
    def __init__(self, parent=None):
        super(ControlPanelLayout, self).__init__(None)

        self.parent = parent
        self.query_papers = {}
        self.query_papers_list = []
        self.setContentsMargins(20, 20, 20, 20)

        self.addLayout(self.setupControlPanelLayout())
        # self.addStretch(2)

    def setupControlPanelLayout(self):
        layout = QVBoxLayout()
        self.query_textbox = QLineEdit()
        self.query_textbox.move(20, 20)
        self.query_textbox.setFixedWidth(300)

        # Just some button connected to 'plot' method
        self.query_button = QPushButton('Query')
        self.query_button.setFixedWidth(300)
        self.query_button.clicked.connect(self.onClicked_query)

        self.random_button = QPushButton('Random paper')
        self.random_button.setFixedWidth(300)
        self.random_button.clicked.connect(self.onClicked_random)

        self.import_button = QPushButton('Import from PDF')
        self.import_button.setFixedWidth(300)
        self.import_button.clicked.connect(self.onClicked_import)

        self.query_list = QListWidget()
        self.query_list.setFixedHeight(800)
        self.query_list.setWordWrap(True)
        self.query_list.setSpacing(5)
        self.query_list.itemClicked.connect(self.onClicked_queryItem)

        # Layout setup
        layout.addWidget(self.random_button)
        layout.addWidget(self.import_button)
        layout.addStretch(1)
        layout.addWidget(self.query_textbox)
        layout.addWidget(self.query_button)
        layout.addWidget(self.query_list)
        layout.addStretch(1)
        return layout

    def onClicked_query(self):
        try:
            self.query_list.clear()
            self.query_papers.clear()
            self.query_papers_list.clear()
            query_string = self.query_textbox.text()
            #query_string = "Scantegrity"

            # query_bibs = BibRecord.objects.search_text(query_string)
            # #query_bibs = BibRecord.objects(title__icontains=query_string)
            # for bib_record in query_bibs:
            #     query = Paper.objects(bib=bib_record.id)
            #     for paper in query:
            #         if str(paper.id) not in self.query_papers.keys():
            #             self.query_list.addItem("[" + paper.bib.year + "] " + str(paper.bib.title))
            #             self.query_papers_list.append(paper)
            #             self.query_papers[str(paper.id)] = paper

            # query_opinions = Opinion.objects.search_text(query_string)
            # #query_opinions = Opinion.objects(texts__icontains=query_string)
            # for opinion in query_opinions:
            #     query = Paper.objects(id=opinion.in_paper_id)
            #     for paper in query:
            #         if str(paper.id) not in self.query_papers.keys():
            #             self.query_list.addItem("[" + paper.bib.year + "] " + str(paper.bib.title))
            #             self.query_papers_list.append(paper)
            #             self.query_papers[str(paper.id)] = paper

            query = Paper.objects.search_text(query_string)
            for paper in query:
                if str(paper.id) not in self.query_papers.keys():
                    self.query_list.addItem("[" + paper.bib.year + "] " + str(paper.bib.title))
                    self.query_papers_list.append(paper)
                    self.query_papers[str(paper.id)] = paper

            if self.query_list.count() > 0:
                self.query_list.setCurrentRow(0)
                self.onClicked_queryItem()

        except Exception as e:
            error(e, True)

    def onClicked_import(self):
        nlpWrapper = getNlpWrapper()

        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(
            self.parent, "QFileDialog.getOpenFileName()",
            "", "All Files (*);;Pdf Files (*.pdf)", options=options)
        if fileName:
            raw_paper = pdfParserUsingLayout(fileName)
            raw_paper = nlpWrapper.extractSections(raw_paper)

            vote_found = False
            for line in raw_paper.x_lines:
                if "vote" in line["text"].lower():
                    vote_found = True
                    break

            if vote_found:
                info("voting paper: " + fileName)
                paper = Paper()
                paper.x_lines = raw_paper.x_lines
                paper.save()
                self.parent.update(paper)
            else:
                info("non-voting paper: " + fileName)

    def onClicked_random(self):
        info("Querying a random paper")
        random_paper = getMongoWrapper().getRandomPaper()
        # if str(random_paper.id) not in self.query_papers.keys():
        self.query_papers_list.append(random_paper)
        self.query_list.addItem(str(random_paper.file_name))
        self.query_papers[str(random_paper.id)] = random_paper
        self.query_list.setCurrentRow(self.query_list.count() - 1)
        self.onClicked_queryItem()

    def onClicked_queryItem(self):
        current_paper_index = self.query_list.currentRow()
        info("Loading new paper")
        self.parent.update(self.query_papers_list[current_paper_index])
