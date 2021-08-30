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
from datetime import datetime, timedelta
import os
from pathlib import Path
from typing import List, Tuple

from file_read_backwards import FileReadBackwards
from PyQt5 import QtChart, QtCore, QtGui, QtWidgets

Qt = QtCore.Qt


class SensorDetailView(QtWidgets.QWidget):
    """ A popup window plotting the sensor values. """
    _layout = None
    TIME_WINDOW_MINUTES = 180

    def __init__(self, log_file: Path, sensor_value_unit: str, main_ui):
        QtWidgets.QWidget.__init__(self)

        # set up  window style and size
        # frameless modal window fullscreen (same as main ui)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setWindowModality(Qt.WindowModal)
        self.setGeometry(main_ui.geometry())

        if not log_file.exists():
            # TODO give some feedback!
            return

        # read log backwards, until we hit the time barrier from TIME_WINDOW_SECONDS - performance!
        current_time = datetime.now()
        self._time_value_pairs: List[Tuple[datetime, float]] = []
        try:
            with FileReadBackwards(str(log_file), encoding="utf-8") as fp:
                # log has format 2021-03-12 18:51:16=55\n...
                for line in fp:
                    time_value_pair = line.split("=")
                    timestamp = datetime.fromisoformat(time_value_pair[0])
                    if (current_time - timestamp) > timedelta(minutes=self.TIME_WINDOW_MINUTES):
                        break
                    self._time_value_pairs.append((timestamp, float(time_value_pair[1].strip())))
        except:
            # delete when file is corrupted
            os.remove(log_file)

        if len(self._time_value_pairs) < 2:  # insufficient data
            return # TODO add message

        # add values to qt graph
        # time values are converted to "- <Minutes>" format
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
        chart.axisY(series).setTitleText(sensor_value_unit)
        chart.axisX(series).setTitleText("Minutes")
        chart.axisX(series).setMin(-180)
        chart.axisX(series).setGridLineVisible(False)
        chart.axisY(series).setGridLineVisible(False)
        chart.layout().setContentsMargins(0, 6, 0, 6)

        chart.legend().setVisible(False)

        gradient = QtGui.QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QtGui.QColor(13, 119, 167))
        gradient.setColorAt(1, QtGui.QColor(115, 158, 201))
        pen = QtGui.QPen()
        pen.setColor(QtGui.QColor(Qt.transparent))
        brush = QtGui.QBrush(gradient)
        brush.setStyle(Qt.LinearGradientPattern)
        chart.setBackgroundBrush(brush)

        # calculate delta of last hour
        last_hour_time_value_pairs = list(filter(lambda time_value_pair:
                                                 (current_time - time_value_pair[0]) < timedelta(minutes=60), self._time_value_pairs))
        last_hour_values: List[float] = [time_value_pair[1] for time_value_pair in last_hour_time_value_pairs]

        delta_label = QtWidgets.QLabel(self)
        if last_hour_values:
            delta_label.setText(
                f"Change: {max(last_hour_values) - min(last_hour_values):.2f} {sensor_value_unit}/hour")

        # chart needs a chartview to be displayed
        sensor_chart_view = QtChart.QChartView(chart)
        sensor_chart_view.setRenderHint(QtGui.QPainter.Antialiasing)
        sensor_chart_view.setSizeAdjustPolicy(QtChart.QChartView.AdjustToContents)
        sensor_chart_view.setMaximumSize(2000, 2000)
        sensor_chart_view.setMinimumSize(600, 300)
        sensor_chart_view.setBackgroundBrush(brush)

        # Button to close
        ok_button = QtWidgets.QPushButton("OK", self)
        ok_button.clicked.connect(self.close)

        # add everything to the qt layout
        self._layout = QtWidgets.QVBoxLayout(self)
        self._layout.setSizeConstraint(QtWidgets.QLayout.SetMinAndMaxSize)
        self._layout.addWidget(sensor_chart_view)
        self._layout.addWidget(delta_label)
        self._layout.addWidget(ok_button)

        # event filter handles closing - one click/touch closes the window
        self.installEventFilter(self)

        self.show()

    def eventFilter(self, source, event):
        """ Click/touch closes the window """
        if event.type() == QtCore.QEvent.MouseButtonPress:
            self.close()
        return super().eventFilter(source, event)
