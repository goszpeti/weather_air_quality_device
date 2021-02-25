import datetime
#from piweather.resources import get_rsc_file
import logging
import time

from PyQt5 import QtChart, QtCore, QtGui, QtWidgets

from piweather.config import PROG_NAME
from piweather.ui import common, sub_ui

logger = logging.getLogger(PROG_NAME)

Qt = QtCore.Qt


class DayDetailView(QtWidgets.QWidget):
    qw = None

    def __init__(self, daytime_wp, nighttime_wp):
        QtWidgets.QWidget.__init__(self)

        #low = QtChart.QBarSet("Min")
        #high = QtChart.QBarSet("Max")
        #low << -52 << -50 << -45.3 << -37.0 << -25.6 << -8.0 << - \
        #    6.0 << -11.8

        #high << 11.9 << 12.8 << 18.5 << 26.5 << 32.0 << 34.8 << 38.2 << 34.8

        series = QtChart.QSplineSeries() # QBarSeries()  # Stacked
        #series.append(low)
        series.append(QtCore.QPointF(0,40))
        series.append(QtCore.QPointF(6,18))
        series.append(QtCore.QPointF(12,20))
        series.append(QtCore.QPointF(15, 30))
        series.append(QtCore.QPointF(18, 28))
        series.append(QtCore.QPointF(21, 12))


        self.qw = QtWidgets.QFormLayout(parent=self)
        #self.graphicsView = QtWidgets.QGraphicsView(self.qw)

        chart = QtChart.QChart()
        chart.addSeries(series)
        chart.setTitle("Temperature records in celcius")
        chart.setAnimationOptions(QtChart.QChart.SeriesAnimations)

        chart.createDefaultAxes()
        chart.axisY(series).setRange(0, 40)
        chart.axisY(series).setTitleText("Temperatur [Celsius]")
        chart.axisX(series).setTitleText("Stunden")
        chart.axisX(series).setRange(0,24)

        #chart.legend().setVisible(True)
        #chart.legend().setAlignment(Qt.AlignBottom)
        chart.setTheme(QtChart.QChart.ChartThemeBlueCerulean)

        chartView = QtChart.QChartView(chart)
        chartView.setRenderHint(QtGui.QPainter.Antialiasing)
        self.qw.addWidget(chartView)
        self.setWindowFlags(Qt.WindowStaysOnTopHint)  # | Qt.FramelessWindowHint)
        self.resize(600, 300)
        self.installEventFilter(self)

    #def eventFilter(self, source, event):
    #    """Turns on the display on touch"""
    #    if event.type() == QtCore.QEvent.MouseButtonPress:
    #        self.close()
