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

import logging
from typing import List

from PyQt5 import QtChart, QtCore, QtGui, QtWidgets
from waqd import PROG_NAME, SCREEN_HEIGHT, SCREEN_WIDTH
from waqd.components.online_weather import Weather
from waqd.settings import LOCATION

from . import common
from waqd.ui import get_localized_date

logger = logging.getLogger(PROG_NAME)

Qt = QtCore.Qt


class WeatherDetailView(QtWidgets.QDialog):
    AREA_COLOR = "#2B438C"
    MAX_POINTS = 5

    def __init__(self, weather_points: List[Weather], settings, main_ui):
        super().__init__(main_ui)
        # set up  window style and size
        # frameless modal window fullscreen (same as main ui)
        self.setWindowFlags(Qt.WindowType(Qt.FramelessWindowHint))
        self.setWindowModality(Qt.WindowModal)
        self.setGeometry(main_ui.geometry())
        self.move(0,0)
        # create series from weather points
        series = QtChart.QLineSeries(self)
        self._weather_points = weather_points

        # sort weather points dataset?

        for point in weather_points:
            series.append(QtCore.QPointF(point.date_time.timestamp() * 1000, point.temp))

        self.begin_hour = (min([point.date_time for point in weather_points])).timestamp() * 1000
        self.end_hour = (max([point.date_time for point in weather_points])).timestamp() * 1000
        # get min and max temp
        min_temp = min([point.temp for point in weather_points])
        max_temp = max([point.temp for point in weather_points])

        # start displaying from -20 - so that the icons have enough space
        begin_temp = min_temp - 20

        # this is a dummy which marks the bottom of the areas series - so we can color the whole thing
        series_dummy = QtChart.QLineSeries(self)
        series_dummy.append(self.begin_hour, begin_temp)
        series_dummy.append(self.end_hour, begin_temp)

        area = QtChart.QAreaSeries(series, series_dummy)
        area.setBrush(QtGui.QColor(self.AREA_COLOR))

        # init a generic font
        font = QtGui.QFont()
        font.setPixelSize(16)

        # PointLabels do not work on area - we need to draw both
        series.setPointLabelsVisible(True)
        series.setPointLabelsColor(Qt.white)
        series.setPointLabelsFont(font)
        series.setPointLabelsFormat("@yPoint")
        series.setPointLabelsClipping(True)

        # draw a dashed line at the first tick of y axis
        pen = QtGui.QPen(Qt.DashLine)
        pen.setColor(Qt.white)
        pen.setStyle(Qt.DashLine)
        dashed_line_series = QtChart.QLineSeries(self)  # QSplineSeries()
        dashed_line_series.setPen(pen)
        self.first_tick = round((max_temp - round(begin_temp)) / (5 - 1) +
                                round(begin_temp), 1)  # chart.axisY().tickCount()

        dashed_line_series.append(QtCore.QPointF(self.begin_hour, self.first_tick))
        dashed_line_series.append(QtCore.QPointF(self.end_hour, self.first_tick))

        # chart setup
        chart = QtChart.QChart()
        self._chart = chart
        chart.addSeries(series)
        chart.addSeries(area)
        chart.addSeries(dashed_line_series)

        # visual style
        chart.legend().setVisible(False)
        chart.setTitle(f"{settings.get(LOCATION)} " +
                       get_localized_date(weather_points[0].date_time, settings))
        font.setPixelSize(24)
        chart.setTitleBrush(QtGui.QBrush(QtGui.QColor("white")))
        chart.setTitleFont(font)

        # chart axis
        chart.createDefaultAxes()
        chart.axisY().setTitleText("Temperature [Celsius]")
        chart.axisY().setGridLineVisible(False)
        chart.axisY().setVisible(False)
        chart.axisY().setLineVisible(False)

        chart.axisY(series).setRange(begin_temp, round(max_temp) + 5)

        chart.axisX().setRange(self.begin_hour - 1800000, self.end_hour + 1800000)
        axisX = QtChart.QDateTimeAxis()
        axisX.setFormat("h:mm")
        chart.setAxisX(axisX, series)
        chart.axisX().setGridLineVisible(False)

        # gradient for background
        gradient = QtGui.QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QtGui.QColor(13, 119, 167))  # light blue
        gradient.setColorAt(1, QtGui.QColor(115, 158, 201))  # lighetr blue
        brush = QtGui.QBrush(gradient)
        brush.setStyle(Qt.LinearGradientPattern)
        chart.setBackgroundBrush(brush)
        # removes margins
        chart.layout().setContentsMargins(0, 0, 0, 0)
        chart.setBackgroundRoundness(0)
        geo = main_ui.geometry()
        chart.setGeometry(geo.x(), geo.y(), SCREEN_WIDTH, SCREEN_HEIGHT)

        # display on a chart view
        chart_view = QtChart.QChartView(chart)
        self._chart_view = chart_view
        chart_view.setRenderHint(QtGui.QPainter.Antialiasing)
        chart_view.setSizeAdjustPolicy(QtChart.QChartView.AdjustToContents)
        chart_view.setAttribute(Qt.WA_TranslucentBackground, True)
        # Button to close
        ok_button = QtWidgets.QPushButton("OK", self)
        ok_button.clicked.connect(self.close)

        self._layout = QtWidgets.QVBoxLayout(self)
        self._layout.setGeometry(geo)
        self._layout.setSizeConstraint(QtWidgets.QLayout.SetMinAndMaxSize)

        self._layout.addWidget(chart_view)
        self._layout.addWidget(ok_button)

        self.installEventFilter(self)

    def eventFilter(self, source, event) -> bool:
        """ Draw the Weather icons.
        Only possible after object is drawn, to calculate absolute pos on the screen.
        """
        if event.type() == QtCore.QEvent.Show:
            icon_width = int(77)
            icon_height = int(70)
            scale = 2.8
            for point in self._weather_points:
                if not (self.begin_hour <= point.date_time.timestamp() * 1000 < self.end_hour):
                    continue
                abs_point_pos = self._chart.mapToPosition(QtCore.QPointF(
                    (point.date_time.timestamp() * 1000) + 3600000, self.first_tick))
                icon_label = QtWidgets.QLabel(self._chart_view)
                icon_label.setGeometry(int(abs_point_pos.x()), int(abs_point_pos.y() - icon_height/2),
                                       icon_width, icon_height)
                common.draw_svg(icon_label, point.icon, shadow=False, scale=scale)
                icon_label.setStyleSheet(f"QLabel{{background-color: {self.AREA_COLOR}}}")
                icon_label.show()

        return super().eventFilter(source, event)

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        self.deleteLater()
        return super().closeEvent(a0)
