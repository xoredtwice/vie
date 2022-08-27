# importing various libraries
from PyQt5.QtWidgets import QPushButton, QInputDialog, QFileDialog
from PyQt5.QtWidgets import QLineEdit, QLabel, QComboBox, QStyle, QSizePolicy
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QApplication

from functools import partial
from src.core.v_globals import getNlpWrapper

from src.core.v_logger import info, error

from src.back.v_mongo import Opinion
from src.utils.v_utils import openPdfFile, findFile

from shutil import copyfile
import os

class PaperEditLayout(QVBoxLayout):

    # constructor
    def __init__(self, parent=None):
        super(PaperEditLayout, self).__init__(None)

        self.parent = parent
        self.edit_labels = []
        self.edit_boxes = {}

        self.view_tags = {}
        self.comboBoxes = {}

        self.cid = None
        self.setContentsMargins(20, 20, 20, 20)

        openPdfButton = QPushButton('Open PDF')
        openPdfButton.setFixedWidth(300)
        openPdfButton.clicked.connect(self.onClicked_openPdfButton)
        self.addWidget(openPdfButton)

        edit_layout = self.setupPaperEditLayout()
        self.addLayout(edit_layout)

        paperApprove_button = QPushButton('Save')
        paperRefresh_button = QPushButton("Refresh")

        hbox = QHBoxLayout()
        hbox.addStretch(1)
        hbox.addWidget(paperApprove_button)
        hbox.addWidget(paperRefresh_button)

        self.addLayout(hbox)
        self.addStretch(2)

        paperApprove_button.clicked.connect(self.onClicked_paperApprove_button)
        paperRefresh_button.clicked.connect(self.onClicked_paperRefresh_button)

    def setupPaperEditLayout(self):
        viewDict = self.parent.active_paper.getViewDict()
        layout = QVBoxLayout()
        print(viewDict)
        for key in viewDict:
            newLabel = QLabel()
            newLabel.setText(key)

            layout.addWidget(newLabel)
            self.edit_labels.append(newLabel)

            # if isinstance(viewDict[key], str):


            if isinstance(viewDict[key], list) \
                    or isinstance(viewDict[key], dict):
                new_combo = QComboBox()
                new_combo.setFixedWidth(300)
                new_combo.setFixedHeight(30)
                new_combo.setSizeAdjustPolicy(new_combo.AdjustToContents)
                new_combo.setSizePolicy(QSizePolicy.Minimum,
                                        QSizePolicy.Fixed)

                self.comboBoxes[key] = new_combo

                if key == "sections":
                    self.comboBoxes[key].activated[str].connect(
                        self.onChanged_sections_comboBox)
                elif key == "references":
                    self.comboBoxes[key].setFixedHeight(50)
                    self.comboBoxes[key].activated[str].connect(
                        self.onChanged_references_comboBox)
                elif key == "citations":
                    self.comboBoxes[key].setFixedHeight(50)
                    self.comboBoxes[key].activated[str].connect(
                        self.onChanged_citations_comboBox)
                elif key == "flags":
                    self.comboBoxes[key].activated[str].connect(
                        self.onChanged_flags_comboBox)

                layout.addWidget(new_combo)

                # for flags we do not need fail/approve button
                if key != "flags":
                    reextract_button = QPushButton('')
                    reextract_button.setIcon(
                        QApplication.style().standardIcon(
                            QStyle.SP_BrowserReload))
                    reextract_button.clicked.connect(
                        partial(self.onClicked_combo_reextract_button, key))

                    approve_button = QPushButton('')
                    approve_button.setIcon(
                        QApplication.style().standardIcon(
                            QStyle.SP_DialogSaveButton))
                    approve_button.clicked.connect(
                        partial(self.addPaperFlag, key + "_approved"))

                    reject_button = QPushButton('')
                    reject_button.setIcon(
                        QApplication.style().standardIcon(
                            QStyle.SP_BrowserStop))
                    reject_button.clicked.connect(
                        partial(self.addPaperFlag, key + "_failed"))

                    hbox = QHBoxLayout()
                    hbox.addWidget(reextract_button)
                    hbox.addWidget(approve_button)
                    hbox.addStretch(1)
                    hbox.addWidget(reject_button)
                    layout.addLayout(hbox)
            else:
                newTextBox = QLineEdit()
                newTextBox.setFixedWidth(300)
                newTextBox.setFixedHeight(30)
                newTextBox.setText(viewDict[key])

                self.edit_boxes[key] = newTextBox

                layout.addWidget(newTextBox)
        layout.addStretch(1)
        return layout

    def addPaperFlag(self, text):
        if self.parent.active_paper is not None:
            if text not in self.parent.active_paper.raw.flags:
                self.parent.active_paper.raw.flags.append(text)
                self.parent.active_paper.save()
                self.update()

    def addNewOpinionFromRawReference(self, ref, group="references"):
        if self.parent.active_paper is not None:

            new_opinion = Opinion()
            if group == "references":
                new_opinion.in_paper_id = self.parent.active_paper.id
            elif group == "citations":
                new_opinion.about_paper_id = self.parent.active_paper.id
            new_opinion.reference_id = ref["tag"]
            new_opinion.reference_string = ref["text"]
            new_opinion.candidate_bib = ref["candidate_bib"]
            info("addEditPaperOpinion: new_opinion.save()")
            new_opinion.save()

            self.parent.active_paper.save()
            info("addEditPaperOpinion: paper.save()")
            self.update()

    def update(self, viewDict=None):
        # self.parent.active_paper.reload()
        if viewDict is None:
            viewDict = self.parent.active_paper.getViewDict()

        print(viewDict)
        for key in viewDict:
            try:
                if isinstance(viewDict[key], str):
                    self.edit_boxes[key].setText(viewDict[key])

                elif isinstance(viewDict[key], list):
                    if key in ["references", "citations"]:
                        self.comboBoxes[key].clear()
                        for opinion in viewDict[key]:
                            op_string = "[" + opinion.reference_id + "]" + opinion.reference_string
                            self.comboBoxes[key].addItem(op_string)
                        self.comboBoxes[key].addItem("")
                    elif key == "sections":
                        self.comboBoxes[key].clear()
                        for item in viewDict[key]:
                            self.comboBoxes[key].addItem(item["text"])
                        self.comboBoxes[key].addItem("")

                    elif key == "flags":
                        self.comboBoxes[key].clear()
                        for item in viewDict[key]:
                            self.comboBoxes[key].addItem(item)
                        self.comboBoxes[key].addItem("")
            except Exception as e:
                error(e)

    def showEditOrUpdateDialog(self, text, label_text):
        # Adding new flag
        if text == "":
            return_text, ok = QInputDialog.getText(
                self.parent, "Add " + label_text,
                "New " + label_text, QLineEdit.Normal)
        else:
            return_text, ok = QInputDialog.getText(
                self.parent, "Edit" + label_text,
                "current " + label_text, QLineEdit.Normal, text)
        if ok:
            return return_text
        else:
            return None

    def onChanged_sections_comboBox(self, text):
        return False
        # print(self.arrows[self.referenceCombo.currentIndex()])

    def onChanged_flags_comboBox(self, text):
        new_text = self.showEditOrUpdateDialog(text, "flag")
        if new_text is not None and new_text != text:
            if text != "":
                if text in self.parent.active_paper.raw.flags:
                    self.parent.active_paper.raw.flags.remove(text)
            if new_text not in self.parent.active_paper.raw.flags:
                self.parent.active_paper.raw.flags.append(new_text)
            self.parent.active_paper.save()
            self.update()

        # print(self.arrows[self.referenceCombo.currentIndex()])

    def onChanged_references_comboBox(self, text):
        selected_index = self.comboBoxes["references"].currentIndex()
        self.parent.updateOpinionView(selected_index, "references")

    def onChanged_citations_comboBox(self, text):
        selected_index = self.comboBoxes["citations"].currentIndex()
        self.parent.updateOpinionView(selected_index, "citations")

        # new_text = self.showEditOrUpdateDialog(text, "reference")
        # print(self.arrows[self.referenceCombo.currentIndex()])

    def onClicked_combo_reextract_button(self, text):
        try:
            nlpWrapper = getNlpWrapper()

            if text in ["references", "citations"]:
                return_text, ok = QInputDialog.getMultiLineText(
                    self.parent, "Import " + text + " manually ",
                    "Reference Strings of " + text)
                if ok:
                    logger.info(
                        "importing " + text + " from string: " + return_text)
                    for line in return_text.split("\n\n"):
                        ref = nlpWrapper.extractReferenceEntryManually(line)
                        self.addNewOpinionFromRawReference(ref, text)
        except Exception as e:
            error(e, show_error_dialog=True)

    def onClicked_paperApprove_button(self):
        try:
            viewDict = self.parent.active_paper.getViewDict()
            if "bib_approved" not in viewDict["flags"]:
                self.parent.active_paper.title = self.edit_boxes[
                    "title"].text()
                self.parent.active_paper.year = self.edit_boxes[
                    "year"].text()
                self.parent.active_paper.save()
                self.parent.update()

        except Exception as e:
            error(e, show_error_dialog=True)

    def onClicked_paperRefresh_button(self):
        self.update()

    def onClicked_openPdfButton(self):
        try:
            filename = self.parent.active_paper.file_name
            repo_path = "data/firstgen"
            file_path = findFile(
                self.parent.active_paper.file_name, repo_path)
            if file_path is None:
                info("File not found... opening import dialog")
                options = QFileDialog.Options()
                options |= QFileDialog.DontUseNativeDialog
                file_path, _ = QFileDialog.getOpenFileName(
                    self.parent, "QFileDialog.getOpenFileName()",
                    "", "All Files (*);;Pdf Files (*.pdf)", options=options)
                if file_path:
                    info("Copying file to repo folder")
                    info(file_path)
                    filename = os.path.basename(file_path)
                    dst = repo_path + "/" + filename
                    copyfile(file_path, dst)
                    self.parent.active_paper.file_name = filename
                    self.parent.active_paper.save()
                    info("New file name saved to paper")
                    self.parent.update()
            else:
                info("Openning file: " + file_path)
                openPdfFile(file_path)
        except Exception as e:
            error(e, show_error_dialog=True)
