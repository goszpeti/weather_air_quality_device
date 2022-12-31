#
# Copyright (c) 2019-2021 Péter Gosztolya & Contributors.
#
# This file is part of WAQD
# (see https://github.com/goszpeti/WeatherAirQualityDevice).
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

import threading
from waqd.ui.qt.widgets.splashscreen import SplashScreen
from datetime import datetime
from typing import TYPE_CHECKING
from waqd.base.system import RuntimeSystem

from PyQt5 import QtChart, QtCore, QtGui, QtWidgets

from waqd import LOCAL_TIMEZONE, SELECTEBLE_LOGGER_INTERVAL_VIEW
from waqd.ui.qt.widgets.jumpslider import JumpSlider
from waqd.base.translation import Translation
from waqd.settings import LANG
from waqd.base.db_logger import InfluxSensorLogger
Qt = QtCore.Qt
if TYPE_CHECKING:
    from waqd.ui.qt.main_ui import WeatherMainUi
class SensorDetailView(QtWidgets.QDialog):
    """ A popup window plotting the sensor values. """
    _layout = None
    TIME_WINDOW_MINUTES = 180

    def __init__(self, sensor_location: str, sensor_type: str, sensor_value_unit: str,
                 main_ui: "WeatherMainUi", logger_class=InfluxSensorLogger):
        super().__init__(parent=None)
        self._main_ui = main_ui
        self._sensor_location = sensor_location
        self._sensor_type = sensor_type
        self._sensor_value_unit = sensor_value_unit
        self._logger_class = logger_class

        # set up  window style and size
        # frameless modal window fullscreen (same as main ui)
        self.setWindowFlags(Qt.WindowType(Qt.FramelessWindowHint))
        self.setWindowModality(Qt.WindowModal)
        self.setGeometry(self._main_ui.geometry())

        # start fader - variable must be held otherwise gc will claim it
        # initialize splash screen for the closing of the UI and make a screenshot
        self._splash_screen = SplashScreen(background=False)
        # this splash screen works only in full screen under RPI - god knows why...
        self._runtime_system = RuntimeSystem()
        self._ready = False
        if self._runtime_system.is_target_system:
            self._splash_screen.showFullScreen()
            self._splash_screen.setFocus()
        else:
            self._splash_screen.show()

        self._update_thread = threading.Thread(name=self.__class__.__name__,
                                               target=self.load,
                                               daemon=True)
        self._update_thread.start()
        while not self._ready:
            QtWidgets.QApplication.processEvents()

        if not self._time_value_pairs:
            self._splash_screen.finish(self._main_ui)
            self.not_enough_values_dialog(self._main_ui)
            return
        # chart needs a chartview to be displayed
        sensor_chart_view = QtChart.QChartView()
        sensor_chart_view.setRenderHint(QtGui.QPainter.Antialiasing)
        sensor_chart_view.setSizeAdjustPolicy(QtChart.QChartView.AdjustToContents)
        sensor_chart_view.setBackgroundBrush(self._get_background_brush())
        self._sensor_chart_view = sensor_chart_view

        self._draw_chart()
        # Button to close
        ok_button = QtWidgets.QPushButton("OK", self)
        ok_button.clicked.connect(self.close)

        # Jumpslider for setting timespan
        # TODO Use dropdown or modal with fixed valueys
        if SELECTEBLE_LOGGER_INTERVAL_VIEW:
            self._time_slider = JumpSlider(self)
            self._time_slider.setOrientation(QtCore.Qt.Horizontal)
            self._time_slider.setMinimum(60)
            self._time_slider.setMaximum(48*60)
            self._time_slider.setSliderPosition(self.TIME_WINDOW_MINUTES)
            self._time_slider.valueChanged.connect(self.on_slider_changed)
            self._time_slider.setTickInterval(30)
            self._time_slider.setTickPosition(QtWidgets.QSlider.NoTicks)

        # add everything to the qt layout
        self._layout = QtWidgets.QVBoxLayout(self)
        self._layout.setSizeConstraint(QtWidgets.QLayout.SetMinAndMaxSize)
        if SELECTEBLE_LOGGER_INTERVAL_VIEW:
            self._layout.addWidget(self._time_slider)
        self._layout.addWidget(sensor_chart_view)
        #self._layout.addWidget(delta_label)
        self._layout.addWidget(ok_button)

        # event filter handles closing - one click/touch closes the window
        self.installEventFilter(self)
        self.show()
        self._splash_screen.finish(self._main_ui)

    def load(self):
        # add values to qt graph
        # time values are converted to "- <Minutes>" format
        self._time_value_pairs = self._logger_class.get_sensor_values(
            self._sensor_location, self._sensor_type, self.TIME_WINDOW_MINUTES)
        self._ready = True
    
    def _draw_chart(self):
        current_time = datetime.now(LOCAL_TIMEZONE)

        series = QtChart.QLineSeries()
        series.setPen(QtGui.QPen(Qt.white))
        series.setColor(Qt.white)
        for timestamp, value in self._time_value_pairs:
            if (current_time - timestamp).days == 0:
                series.append(
                    QtCore.QPointF(-1 * (current_time - timestamp).seconds / 60, value))

        chart = QtChart.QChart()
        chart.addSeries(series)
        chart.setAnimationOptions(QtChart.QChart.SeriesAnimations)
        chart.createDefaultAxes()
        chart.axisY(series).setTitleText(self._sensor_value_unit)
        chart.axisX(series).setTitleText("Minutes")
        chart.axisX(series).setMin(-self.TIME_WINDOW_MINUTES)
        chart.axisX(series).setGridLineVisible(False)
        chart.axisY(series).setMin(0)
        chart.axisY(series).setTickCount(10)
        chart.axisY(series).setMinorTickCount(4)
        chart.axisY(series).applyNiceNumbers()
        chart.axisX(series).applyNiceNumbers()

        chart.axisY(series).setMinorGridLinePen(QtGui.QPen(Qt.gray, 1, Qt.PenStyle.DashLine))
        chart.axisY(series).setGridLineColor(Qt.gray)
        chart.layout().setContentsMargins(0, 0, 0, 0)

        chart.legend().setVisible(False)

        chart.setBackgroundBrush(self._get_background_brush())
        self._sensor_chart_view.setChart(chart)

    def on_slider_changed(self):
        new_time = self._time_slider.sliderPosition()
        if new_time > self.TIME_WINDOW_MINUTES:
            self._time_value_pairs = InfluxSensorLogger.get_sensor_values(
                self._sensor_location, self._sensor_type, new_time)
        self.TIME_WINDOW_MINUTES = new_time
        self._draw_chart()

    def _get_background_brush(self):
        gradient = QtGui.QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QtGui.QColor(13, 119, 167))
        gradient.setColorAt(1, QtGui.QColor(115, 158, 201))
        pen = QtGui.QPen()
        pen.setColor(QtGui.QColor(Qt.transparent))
        brush = QtGui.QBrush(gradient)
        brush.setStyle(Qt.LinearGradientPattern)
        return brush

    def not_enough_values_dialog(self, main_ui):
        msg = QtWidgets.QMessageBox(parent=main_ui)
        msg.setWindowFlags(Qt.WindowType(Qt.CustomizeWindowHint))
        msg.setWindowTitle("Nothing to display!")
        msg.setText(Translation().get_localized_string(
            "base", "ui_dict", "cant_disp_sensor_logs", main_ui._settings.get_string(LANG))) # TODO
        msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
        msg.setIcon(QtWidgets.QMessageBox.Information)
        msg.adjustSize()
        msg.move(int((main_ui.geometry().width() - msg.width()) / 2),
                 int((main_ui.geometry().height() - msg.height()) / 2))
        msg.exec_()
        msg.deleteLater()
        self.deleteLater()
