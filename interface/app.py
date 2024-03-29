import io
import sys

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
from PIL.ImageQt import ImageQt
from PyQt5 import QtWidgets, uic, QtCore
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtWidgets import QTableWidgetItem

from models.evaluator import Evaluator
from models.vector_space_model import VectorSpaceModel, SimilarityFunctions
from utils import read_cacm_query, read_cacm, preprocess_cacm


class App(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        uic.loadUi("query_interface.ui", self)

        dictionary = read_cacm('../CACM/cacm.all')
        dictionary = preprocess_cacm(dictionary)
        self.query_dict, self.qrels_dict = read_cacm_query('../CACM/query.text', '../CACM/qrels.text')
        self.vm = VectorSpaceModel(dictionary, sparse=True)
        self.evaluator = Evaluator(self.vm, self.query_dict, self.qrels_dict)

        self.queryTable: QtWidgets.QTableWidget
        self.lineEditPrecisionNoInterpolate: QtWidgets.QLineEdit
        self.lineEditPrecisionInterpolate: QtWidgets.QLineEdit
        self.lineEditRecall: QtWidgets.QLineEdit
        self.sliderF: QtWidgets.QSlider
        self.labelF: QtWidgets.QLabel
        self.graphicsViewPR: QtWidgets.QLabel
        self.graphicsViewPRI: QtWidgets.QLabel
        self.sliderF_2: QtWidgets.QSlider
        self.labelF_2: QtWidgets.QLabel
        self.radioButton: QtWidgets.QRadioButton
        self.radioButton_2: QtWidgets.QRadioButton
        self.radioButton_3: QtWidgets.QRadioButton

        self.sim2lineEdit = {
            SimilarityFunctions.DOT: [self.lineEditRecall_2, self.lineEditRecall_7, self.lineEditRecall_11,
                                      self.lineEditRecall_14, self.lineEditRecall_18],
            SimilarityFunctions.COSINUS: [self.lineEditRecall_3, self.lineEditRecall_8, self.lineEditRecall_10,
                                          self.lineEditRecall_17, self.lineEditRecall_21],
            SimilarityFunctions.DICE: [self.lineEditRecall_4, self.lineEditRecall_6, self.lineEditRecall_13,
                                       self.lineEditRecall_16, self.lineEditRecall_20],
            SimilarityFunctions.JACCARD: [self.lineEditRecall_5, self.lineEditRecall_9, self.lineEditRecall_12,
                                          self.lineEditRecall_15, self.lineEditRecall_19]
        }

        self.graphicsViewPR.setScaledContents(True)
        self.graphicsViewPRI.setScaledContents(True)

        plt.figure(figsize=(7, 4))

        image = np.ones((100, 100, 3), dtype=np.uint8) * 255
        PIL_image = Image.fromarray(image).convert('RGB')
        self.graphicsViewPRI.setPixmap(QPixmap.fromImage(ImageQt(PIL_image)).copy())
        self.graphicsViewPR.setPixmap(QPixmap.fromImage(ImageQt(PIL_image)).copy())

        # Init queryTable
        self.queryTable.setRowCount(len(self.query_dict))
        self.queryTable.setColumnCount(2)
        self.queryTable.setHorizontalHeaderItem(0, QTableWidgetItem('ID'))
        self.queryTable.setHorizontalHeaderItem(1, QTableWidgetItem('Requête'))
        self.queryTable.horizontalHeader().setStretchLastSection(True)

        font = QFont()
        font.setBold(True)
        for i, (id, query) in enumerate(self.query_dict.items()):
            self.queryTable.setItem(i, 1, QTableWidgetItem(query))
            self.queryTable.setItem(i, 0, QTableWidgetItem(str(id)))
            self.queryTable.item(i, 0).setFont(font)
            self.queryTable.item(i, 0).setTextAlignment(QtCore.Qt.AlignCenter)
        self.queryTable.setColumnWidth(0, 15)
        self.queryTable.resizeRowsToContents()

        # Slider Change
        def f():
            self.labelF.setText(str(self.sliderF.value() / 100))

        self.sliderF.valueChanged.connect(f)

        def f():
            r = self.queryTable.currentRow()
            query_id = int(self.queryTable.item(r, 0).text())
            self.select_action(query_id)

        self.queryTable.cellClicked.connect(f)

        def f():
            self.labelF_2.setText(str(self.sliderF_2.value()))

        self.sliderF_2.valueChanged.connect(f)

        def f():
            self.sliderF_2.setEnabled(False)
            self.labelF_2.setEnabled(False)
            self.sliderF.setEnabled(False)
            self.labelF.setEnabled(False)

        self.radioButton.toggled.connect(f)

        def f():
            self.sliderF_2.setEnabled(False)
            self.labelF_2.setEnabled(False)
            self.sliderF.setEnabled(True)
            self.labelF.setEnabled(True)

        self.radioButton_2.toggled.connect(f)

        def f():
            self.sliderF_2.setEnabled(True)
            self.labelF_2.setEnabled(True)
            self.sliderF.setEnabled(False)
            self.labelF.setEnabled(False)

        self.radioButton_3.toggled.connect(f)

        self.setFixedSize(self.size())

    def select_action(self, query_id):
        params = {}
        if self.radioButton_2.isChecked():
            params['f'] = self.sliderF.value() / 100
        elif self.radioButton_3.isChecked():
            params['k'] = self.sliderF_2.value()

        def f(interpolate, qt):
            plt.figure(0)
            plt.xlabel('Recall')
            plt.ylabel('Precision')
            plt.grid(True)
            for sim in SimilarityFunctions:
                d = self.sim2lineEdit[sim]
                precision, recall = self.evaluator.precision_recall_query(query_id, sim, **params,
                                                                          option=(
                                                                              'interpolate' if interpolate else 'no_interpolate'))
                if not interpolate:
                    p, r = self.evaluator.precision_recall_query(query_id, sim, **params,
                                                                 option='simple')
                    d[0].setText(str(np.array(precision).mean())[:7] if len(precision) else '0')
                    d[2].setText(str(r)[:7])
                    d[3].setText(str(p)[:7])
                    f1score = 2 * p * r / (p + r) if p + r != 0 else 0
                    d[4].setText(str(f1score)[:7])
                else:
                    d[1].setText(str(np.array(precision).mean())[:7] if len(precision) else '0')

                plt.plot(recall, precision, label=str(sim).split('.')[-1])
            plt.legend()

            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=150)
            buf.seek(0)
            img = Image.open(buf)
            qt.setPixmap(QPixmap.fromImage(ImageQt(img)).copy())
            plt.clf()
            buf.close()

        f(False, self.graphicsViewPR)
        f(True, self.graphicsViewPRI)


app = QtWidgets.QApplication(sys.argv)
window = App()
window.show()
app.exec_()
