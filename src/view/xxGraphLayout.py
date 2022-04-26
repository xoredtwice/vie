# importing various libraries
from PyQt5.QtWidgets import QRadioButton, QVBoxLayout, QHBoxLayout
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt
import numpy as np

import util.xxGlobals

from model.xxMongoModels import RawPaper, Paper

import util.xxUtils
import util.xxLogger


# main window
# which inherits QDialog
class GraphLayout(QVBoxLayout):

    # constructor
    def __init__(self, parent=None):
        super(GraphLayout, self).__init__(None)

        self.parent = parent
        self.arrows = []

        self.active_sentiment = "vader"

        # a figure instance to plot on
        self.figure = plt.figure(figsize=[5, 5])

        # this is the Canvas Widget that
        # displays the 'figure'it takes the
        # 'figure' instance as a parameter to __init__
        self.canvas = FigureCanvas(self.figure)

        # this is the Navigation widget
        # it takes the Canvas widget and a parent
        self.toolbar = NavigationToolbar(self.canvas, self.parent)

        self.cid = None

        h1_layout = QHBoxLayout()

        radiobutton = QRadioButton("Vader")
        radiobutton.setChecked(True)
        radiobutton.tag = "vader"
        radiobutton.toggled.connect(self.onClicked_sentiment_radio)

        radiobutton2 = QRadioButton("TextBlob")
        radiobutton2.tag = "textblob"
        radiobutton2.toggled.connect(self.onClicked_sentiment_radio)

        self.addWidget(self.toolbar)
        h1_layout.addWidget(radiobutton)
        h1_layout.addWidget(radiobutton2)
        h1_layout.addStretch(1)
        self.addLayout(h1_layout)
        self.addWidget(self.canvas)
        # self.setWindowFlags(Qt.WindowCloseButtonHint | Qt.WindowType_Mask)

    def onClicked_sentiment_radio(self):
        radioButton = self.sender()
        if radioButton.isChecked():
            self.active_sentiment = radioButton.tag
            self.parent.update(update_only_graph=True)

    def update(self, paper_view_dict):
        logger = util.xxLogger.getLogger()
        nlpWrapper = util.xxGlobals.getNlpWrapper()

        def cart2pol(x, y):
            rho = np.sqrt(x**2 + y**2)
            phi = np.arctan2(y, x)
            return(rho, phi)

        def pol2cart(rho, phi):
            x = rho * np.cos(phi)
            y = rho * np.sin(phi)
            return(x, y)

        def onclick_graphNodes(event):

            if event.artist.get_picker() == "main":
                print("main")
            elif event.artist.get_picker() in ["references", "citations"]:
                self.parent.updateOpinionView(
                    event.ind[0], event.artist.get_picker())

        def drawArrow(x1, y1, x2, y2, ax, dynamic_color=True, reverse=False):

            if dynamic_color:
                arrow_color = ((abs(y1 - y2) + (y1 - y2)) / 2,
                               (abs(y2 - y1) + (y2 - y1)) / 2, 0.0)
            else:
                arrow_color = "black"

            self.arrows.append(
                ax.arrow(x1, y1, x2 - x1, y2 - y1, head_width=0.01,
                         head_length=0.05, color=arrow_color,
                         length_includes_head=True, width=0.001,
                         head_starts_at_zero=reverse))

        # clearing old figure
        if self.cid is not None:
            self.canvas.mpl_disconnect(self.cid)
            self.cid = None
        self.figure.clear()
        # create an axis
        ax = self.figure.add_subplot(111)
        plt.xlim([1980, 2022])
        plt.ylim([-1, 1])
        self.arrows = []

        paper_year = 2015

        # if self.parent.active_paper is not None:
        #     if self.parent.active_paper.bib is not None:
        #         paper_year = int(self.parent.active_paper.bib.year)
        #     # angle = np.pi / 12
        #     for key in paper_view_dict:
        #         if key in ["references", "citations"]:
        #             ref_xs = []
        #             ref_ys = []
        #             for opinion in paper_view_dict[key]:
        #                 # (x2,y2) = pol2cart(1, angle)
        #                 # angle += ( 2 * np.pi / len(model.references))

        #                 adj_id = None
        #                 if key == "references":
        #                     adj_id = opinion.about_paper_id
        #                 else:
        #                     adj_id = opinion.in_paper_id

        #                 if adj_id is not None:

        #                     ref_paper = Paper.objects(
        #                         id=adj_id).first()
        #                     if ref_paper is not None:
        #                         if ref_paper.bib is not None:
        #                             x2 = int(ref_paper.bib.year)
        #                         else:
        #                             x2 = int(ref_paper.raw.year)
        #                 else:
        #                     x2 = int(nlpWrapper.getReferenceYear(
        #                         opinion.reference_string))
        #                 y2 = 0.0
        #                 if len(opinion.texts) != 0:
        #                     for text in opinion.texts:
        #                         if self.active_sentiment == "vader":
        #                             sentiment = nlpWrapper.getVaderSentiment(text)
        #                             y2 = y2 + float(sentiment["compound"])
        #                         elif self.active_sentiment == "textblob":
        #                             sentiment = nlpWrapper.getTextBlobSentiment(text)
        #                             y2 = y2 + float(sentiment.polarity)
        #                     y2 = y2 / float(len(opinion.texts))
        #                 # y2 = (random.random() * 2) - 1
        #                 drawArrow(paper_year, 0, x2, y2, ax)
        #                 # ax.plot([0, x2], [0,y2], 'b-')
        #                 ref_xs.append(x2)
        #                 ref_ys.append(y2)

        #             facecolor = 'white'
        #             if key == "citations":
        #                 facecolor = 'orange'
        #                 try:
        #                     ax.plot(
        #                         ref_xs, ref_ys, 'o', picker=key, markersize=8,
        #                         markerfacecolor=facecolor, markeredgecolor='black')
        #                 except:
        #                     print("exception")

        x = [paper_year]
        y = [0]
        # ax.plot(x, y, 'o-', picker="main", markersize=10,
        #         markerfacecolor='black', markeredgecolor='white')

        # refresh canvas
        self.cid = self.canvas.mpl_connect('pick_event', onclick_graphNodes)
        self.canvas.draw()
