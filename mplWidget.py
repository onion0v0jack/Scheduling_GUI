from PySide2.QtGui import *
import matplotlib.pyplot as plt
from PySide2.QtCore import *
from PySide2.QtWidgets import *
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import (
        FigureCanvas, NavigationToolbar2QT as NavigationToolbar)

plt.style.use('ggplot')

class MplWidget(QWidget):
    
    def __init__(self, parent = None):
        self.plt_rows = None
        
        QWidget.__init__(self, parent)
        
        self.canvas = FigureCanvas(Figure())
        
        vertical_layout = QVBoxLayout()
        vertical_layout.addWidget(self.canvas)
        vertical_layout.addWidget(NavigationToolbar(self.canvas, self))
        
        self.setLayout(vertical_layout)

    def setRows(self, row, col, vratio = None, hratio = None):
        self.canvas.figure.clf()
        if (row > 1) & (col > 1):
            gridspec_kw_dict = {'width_ratios': hratio, 'height_ratios': vratio}
        elif (row == 1) & (col > 1):
            gridspec_kw_dict = {'width_ratios': hratio}
        elif (row > 1) & (col == 1):
            gridspec_kw_dict = {'height_ratios': vratio}
        else:
            gridspec_kw_dict = {}
        self.canvas.ax = self.canvas.figure.subplots(
            row, col, subplot_kw = {'facecolor':'#EEEEEE'}, gridspec_kw = gridspec_kw_dict
            )  