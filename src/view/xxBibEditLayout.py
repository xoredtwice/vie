# importing various libraries
from PyQt5.QtWidgets import QDialog, QApplication, QMessageBox, QPushButton, QLineEdit, QLabel, QComboBox
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QInputDialog, QWidget

from src.back.v_mongo import Paper, BibRecord

from src.core.v_globals import getReferenceQueryManager

from src.core.v_logger import info, error

class BibEditLayout(QVBoxLayout):

    # constructor
    def __init__(self, parent=None, bib_model=None):
        super(BibEditLayout, self).__init__(None)

        self.parent = parent
        self.edit_labels = []
        self.edit_boxes = {}
        self.cid = None
        self.setContentsMargins(20, 20, 20, 20)

        if bib_model is not None:
            self.active_bib = bib_model
        else:
            self.active_bib = BibRecord()

        edit_layout = self.setupBibEditLayout()
        self.addLayout(edit_layout)

        bibApprove_button = QPushButton('Approve')
        bibRefresh_button = QPushButton("Refresh")

        hbox = QHBoxLayout()
        hbox.addStretch(1)
        hbox.addWidget(bibApprove_button)
        hbox.addWidget(bibRefresh_button)

        self.addLayout(hbox)

        bibApprove_button.clicked.connect(self.onClicked_bibApprove_button)
        bibRefresh_button.clicked.connect(self.onClicked_bibRefresh_button)

    def setupBibEditLayout(self):
        layout = QVBoxLayout()
        viewDict = self.active_bib.getViewDict()
        for key in viewDict:
            newLabel = QLabel()
            newLabel.setText(key)
            layout.addWidget(newLabel)
            # self.edit_labels.append(newLabel)
            if key == "query":
                self.query_label = QLineEdit()
                self.query_label.setText(viewDict[key])
                self.query_label.setFixedWidth(300)
                layout.addWidget(self.query_label)

                bibQuery_button = QPushButton('Query')
                bibQuery_button.clicked.connect(self.onClicked_bibQuery_button)
                bibQuery_button.setFixedHeight(30)

                bibImport_button = QPushButton("Import")
                bibImport_button.setFixedHeight(30)
                bibImport_button.clicked.connect(
                    self.onClicked_bibImport_button)

                hbox = QHBoxLayout()
                hbox.addWidget(bibQuery_button)
                hbox.addStretch(1)
                hbox.addWidget(bibImport_button)

                layout.addLayout(hbox)
            elif key == "authors":
                new_combo = QComboBox()
                new_combo.setFixedWidth(300)
                new_combo.setFixedHeight(30)
                # TODO:: backend not implemented
                self.authors_comboBox = new_combo

                self.authors_comboBox.activated[str].connect(
                    self.onChanged_authors_comboBox)
                layout.addWidget(new_combo)
            else:
                newTextBox = QLineEdit()
                newTextBox.setFixedWidth(300)
                newTextBox.setFixedHeight(30)
                newTextBox.setText(str(viewDict[key]))

                self.edit_boxes[key] = newTextBox

                layout.addWidget(newTextBox)

        layout.addStretch(1)
        return layout

    def update(self, query_string="", new_bib=None):
        if new_bib is not None:
            self.active_bib = new_bib

        viewDict = self.active_bib.getViewDict()
        for key in viewDict:
            if key == "query":
                if query_string != "":
                    self.query_label.setText(query_string)
                else:
                    self.query_label.setText(self.active_bib.query_string)
            elif key == "authors":
                self.authors_comboBox.clear()
                for author in viewDict[key]:
                    self.authors_comboBox.addItem(author.name)
            else:
                if self.edit_boxes[key] is not None:
                    self.edit_boxes[key].setText(str(viewDict[key]))

    def onChanged_authors_comboBox(self, text):
        return False
        # print(self.arrows[self.referenceCombo.currentIndex()])

    def onClicked_bibApprove_button(self):
        try:
            self.active_bib.query_string = self.query_label.text()
            self.active_bib.article_type = self.edit_boxes[
                "article_type"].text()
            self.active_bib.title = self.edit_boxes["title"].text()
            self.active_bib.year = self.edit_boxes["year"].text()
            self.active_bib.doi = self.edit_boxes["doi"].text()
            self.active_bib.venue = self.edit_boxes["venue"].text(
            )
            self.active_bib.url = self.edit_boxes["url"].text()

            self.active_bib.save()
            info("bib record updated: " + self.active_bib.title)

            if "bib_approved" not in self.parent.active_paper.flags:
                self.parent.active_paper.flags.append("bib_approved")
            self.parent.active_paper.bib = self.active_bib
            self.parent.active_paper.save()
            info("Paper updated!!")
            self.parent.update()
        except Exception as e:
            error(e, True)

    def onClicked_bibImport_button(self):
        try:

            window_pointer = self.parent
            while not isinstance(window_pointer, QWidget):
                window_pointer = window_pointer.parent
            return_text, ok = QInputDialog.getMultiLineText(
                window_pointer, "Import BibRecord from string ",
                "Bibtex String")
            if ok:
                info("importing bib from string: " + return_text)
                try:
                    ref_manager = getReferenceQueryManager()
                    bibtex_entry = ref_manager.bibtexEntryFromString(return_text)
                    new_bib = ref_manager.bibtexResultToBibModel(
                        {"difference": 0.0, "result": bibtex_entry,
                         "source": "MANUAL"})
                    self.update(self.query_label.text(), new_bib)
                except Exception as e:
                    info("Trying to parse based on id")
                    ref_paper = Paper.objects().get(id=return_text)
                    if ref_paper is not None:
                        self.parent.active_paper = ref_paper
                        self.update(self.query_label.text(), ref_paper.bib)
                        self.parent.update()
                finally:
                    pass

        except Exception as e:
            error(e, True)

    def onClicked_bibRefresh_button(self):
        self.update()

    def onClicked_bibQuery_button(self):
        try:
            self.active_bib = getReferenceQueryManager().query(
                self.query_label.text())
            ref_paper = Paper.objects(bib=self.active_bib).first()
            if ref_paper is not None:
                info("bibQuery found existing paper in database")
                self.parent.active_paper = ref_paper
                self.update(self.query_label.text(), ref_paper.bib)
                self.parent.update()
        except Exception as e:
            error(e, True)
