# importing various libraries
from PyQt5.QtWidgets import QApplication, QListWidget, QPushButton, QLineEdit, QLabel, QComboBox
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QInputDialog, QStyle

from src.core.v_logger import info, error
from src.core.v_globals import getNlpWrapper

from src.view.xxBibEditLayout import BibEditLayout

from src.back.v_mongo import BibRecord, Paper, Opinion
from functools import partial

class OpinionEditLayout(QHBoxLayout):

    # constructor
    def __init__(self, parent=None):
        super(OpinionEditLayout, self).__init__(None)

        self.parent = parent
        self.edit_labels = []
        self.edit_boxes = {}

        self.setContentsMargins(20, 20, 20, 20)

        self.active_paper = None
        self.active_opinion = None
        self.bib_edit_view = BibEditLayout(self)

        self.updateModels()

        edit_layout = self.setupOpinionEditLayout()
        self.addLayout(edit_layout)
        self.addLayout(self.bib_edit_view)

    def setupOpinionEditLayout(self):
        layout = QVBoxLayout()
        viewDict = self.active_opinion.getViewDict()
        for key in viewDict:
            newLabel = QLabel()
            newLabel.setText(key)
            layout.addWidget(newLabel)
            # self.edit_labels.append(newLabel)
            if key == "texts":
                self.opinions_list = QListWidget()
                self.opinions_list.setFixedWidth(300)
                self.opinions_list.setFixedHeight(600)
                self.opinions_list.setWordWrap(True)
                self.opinions_list.setSpacing(5)
                self.opinions_list.itemClicked.connect(self.onClicked_opinionListItem)

                layout.addWidget(self.opinions_list)
                add_button = QPushButton('')
                add_button.setIcon(
                    QApplication.style().standardIcon(
                        QStyle.SP_BrowserReload))
                add_button.clicked.connect(
                    partial(self.onClicked_opinions_add_button, key))
                self.addWidget(add_button)
            else:
                newTextBox = QLineEdit()
                newTextBox.setFixedWidth(300)
                newTextBox.setFixedHeight(30)
                newTextBox.setText(str(viewDict[key]))

                self.edit_boxes[key] = newTextBox

                layout.addWidget(newTextBox)

        layout.addStretch(1)
        opiApprove_button = QPushButton('Approve')
        opiRefresh_button = QPushButton("Refresh")

        hbox = QHBoxLayout()
        hbox.addStretch(1)
        hbox.addWidget(opiApprove_button)
        hbox.addWidget(opiRefresh_button)

        layout.addLayout(hbox)

        opiApprove_button.clicked.connect(self.onClicked_opiApprove_button)
        opiRefresh_button.clicked.connect(self.onClicked_opiRefresh_button)

        return layout

    def updateModels(self, opinion=None, query_string=""):
        # first time, making new null useless models
        if opinion is None and query_string is "":
            if self.active_opinion is None:
                self.active_paper = Paper()
                self.active_paper.bib = BibRecord()
                self.active_opinion = Opinion()
                self.direction = "in"
        else:
            # updating based on new opinion
            if opinion is not None:
                self.active_opinion = opinion

                adj_paper = None
                if opinion.in_paper_id is not None or opinion.about_paper_id is not None:
                    # Reference
                    if self.parent.active_paper.id == opinion.in_paper_id:
                        self.direction = "in"
                        if opinion.about_paper_id is not None:
                            adj_paper = Paper.objects(
                                id=opinion.about_paper_id).first()
                        else:
                            info("Searching for opinion about_paper by bib candidate")
                            info(opinion.candidate_bib)
                            if "title" in opinion.candidate_bib.keys():
                                candidate_title = opinion.candidate_bib[
                                    "title"].strip()
                                if candidate_title != "":
                                    bib_record = BibRecord.objects(
                                        title__icontains=candidate_title).first()
                                    adj_paper = Paper.objects(bib=bib_record).first()
                                    self.active_opinion.about_paper_id = adj_paper
                                    self.active_opinion.save()
                    else:  # Citations
                        self.direction = "about"
                        if opinion.in_paper_id is not None:
                            adj_paper = Paper.objects(
                                id=opinion.in_paper_id).first()
                        else:
                            info("Searching for opinion about_paper by bib candidate")
                            info(opinion.candidate_bib)
                            if "title" in opinion.candidate_bib.keys():
                                candidate_title = opinion.candidate_bib[
                                    "title"].strip()
                                if candidate_title != "":
                                    bib_record = BibRecord.objects(
                                        title__icontains=candidate_title).first()
                                    adj_paper = Paper.objects(bib=bib_record).first()
                                    self.active_opinion.in_paper_id = adj_paper
                                    self.active_opinion.save()
                # found the paper that must be shown
                if adj_paper is not None:
                    info("adjacent paper found")
                    self.active_paper = adj_paper
                    if self.active_paper.bib is None:
                        info("adjacent paper bib is none")
                        self.active_paper.bib = BibRecord()
                        query_string = opinion.reference_string
                else:
                    self.active_paper = Paper()
                    self.active_paper.bib = BibRecord()
                    nlpWrapper = getNlpWrapper()
                    ref_dict = nlpWrapper.referenceStringToBibtex(opinion.reference_string)
                    if ref_dict is None:
                        query_string = opinion.reference_string
                    else:
                        if "title" in ref_dict.keys():
                            query_string = ref_dict["title"]
                        if "year" in ref_dict.keys():
                            self.active_paper.bib.year = ref_dict["year"]
                        if "venue" in ref_dict.keys():
                            self.active_paper.bib.venue = ref_dict["venue"]
                    if self.direction == "in":
                        self.active_opinion.about_paper_id = self.active_paper.id
                    else:
                        self.active_opinion.in_paper_id = self.active_paper.id
            # Generating new opinion and paper if needed
            else:
                if self.active_paper is None:
                    info("opinion's active paper is none")
                    self.active_paper = Paper()
                    self.active_paper.bib = BibRecord()

                if self.active_opinion is None:
                    info("active opinion is none")
                    self.active_opinion = Opinion()
                    self.direction = "in"
                    self.active_opinion.about_paper_id = self.active_paper.id

        self.bib_edit_view.update(query_string, self.active_paper.bib)

    def update(self, new_opinion=None, query_string=""):
        self.updateModels(new_opinion, query_string)

        viewDict = self.active_opinion.getViewDict()
        for key in viewDict:
            if key == "texts":
                self.opinions_list.clear()
                for text in viewDict[key]:
                    self.opinions_list.addItem(text.replace('\n', ' ').replace('\r', ''))
            else:
                self.edit_boxes[key].setText(viewDict[key])


    def onClicked_opinions_add_button(self, text):
        return_text, ok = QInputDialog.getMultiLineText(
            self.parent, "Import citation string",
            "citations")
        if ok:
            info(
                "importing citations from string: " + return_text)
            for line in return_text.split("\n\n"):
                self.active_opinion.texts.append(line)
            self.active_opinion.save()
            info("opinion updated")
            self.update()

    def onClicked_opiApprove_button(self):
        try:

            if self.direction is "in":
                self.active_opinion.about_paper_id = self.active_paper.id
            elif self.direction is "about":
                self.active_opinion.in_paper_id = self.active_paper.id

            self.active_opinion.reference_id = self.edit_boxes[
                "reference_id"].text()

            self.active_opinion.save()
            self.active_paper.save()
            info("Approving opinion")
            self.parent.update()
        except Exception as e:
            error(e, True)

    def onClicked_opiRefresh_button(self):
        self.update(self.parent.active_paper.title)

    def onClicked_opinionListItem(self):
        current_paper_index = self.opinions_list.currentRow()
        # self.parent.update(self.query_papers[current_paper_index])
        # logger.info("Loading new paper")