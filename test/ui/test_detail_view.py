
from datetime import timedelta

from freezegun import freeze_time
from PyQt5 import QtWidgets
from waqd.components import OpenWeatherMap
from waqd.settings import LOCATION, Settings
from waqd.ui.qt.sensor_detail_view import SensorDetailView
from waqd.ui.qt.weather_detail_view import WeatherDetailView


def testSensorDetailView(base_fixture, qtbot):
    parent = QtWidgets.QMainWindow()
    parent.resize(800, 480)
    parent.move(0,0,)
    parent.show()
    with freeze_time("2021-03-15 08:25:50"):
        log_file = base_fixture.testdata_path / "sensor_logs" / "temperature.log"
        widget = SensorDetailView(log_file, "Celsius", parent)
    qtbot.addWidget(parent)
    qtbot.addWidget(widget)
    widget.show()
    qtbot.waitExposed(widget)

    while True:
        QtWidgets.QApplication.processEvents()
    assert widget.isVisible()
    assert widget._time_value_pairs[-1][0] - widget._time_value_pairs[0][0] <= timedelta(minutes=180)


def testWeatherDetailView(base_fixture, qtbot):
    parent = QtWidgets.QMainWindow()
    parent.resize(800, 480)
    parent.show()
    # initalize settings
    settings = Settings(base_fixture.testdata_path / "integration")

    weather = OpenWeatherMap("city_id", "abcd") # inputs do not matter
    weather._fc_json_file = str(base_fixture.testdata_path / "online_weather/ow_forecast.json")
    weather._cw_json_file = str(base_fixture.testdata_path / "online_weather/ow_current_weather.json")

    # get a date matching with the test data
    #current_date_time = datetime.datetime(2019, 7, 21, 15)
    with freeze_time("2019-07-21 20:00:00"):
        forecast = weather.get_5_day_forecast()
        [daytime_forecast_points, nighttime_forecast_points] = weather.get_forecast_points()

    widget = WeatherDetailView(daytime_forecast_points[0], settings, parent)
    qtbot.addWidget(parent)
    widget.show()
    qtbot.waitExposed(widget)

    # while True:
    #     QtWidgets.QApplication.processEvents()

    assert widget.isVisible()
    series =  widget._chart.series()
    assert len(series) == 3

    # can't test the point directly, because it depends on the timezone
    assert len(series[0].pointsVector()) == 5
    point = series[0].pointsVector()[0]
    assert point.y()  == 23.32
    assert series[0].pointLabelsVisible
