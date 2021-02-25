# 
# import os, sys
# import threading
# from freezegun import freeze_time
# from pathlib import Path
# from PyQt5 import QtWidgets

# from piweather.settings import Settings


# def app_loader(daytime_wp, nighttime_wp):
#     qt_app = QtWidgets.QApplication([])

#     from piweather.ui.day_detail_view import DayDetailView
#     dv = DayDetailView(daytime_wp, nighttime_wp)
#     window = QtWidgets.QMainWindow()
#     window.setCentralWidget(dv)
#     window.resize(600, 300)
#     window.show()
#     qt_app.exec_()

# class DayViewTest(base_fixture):
#     repo_root_path = None

#     def setUp(self):
#         self.repo_root_path = Path(__file__).absolute().parent.parent
#         mockup_path = self.repo_root_path / "src" / "mock"
#         sys.path.append(str(mockup_path))
#         self.testdata_path = self.repo_root_path / "test/testdata"
#         Settings.instance = None

#     def testDailyGui(self):
#         # initalize settings
#         settings = Settings(self.repo_root_path / "src")
#         config.DEBUG_LEVEL = 2
#         settings.location = "City2"

#         import piweather.config as config  # need to solve circular imports
#         config.resource_path = self.repo_root_path / "resources"  # for icons
#         import piweather.components.online_weather as online_weather

#         weather = online_weather.OpenWeatherMap()
#         weather._fc_json_file = str(
#             self.testdata_path / "online_weather/ow_forecast.json")
#         weather._cw_json_file = str(self.testdata_path / "online_weather/ow_current_weather.json")

#         # get a date matching with the test data
#         #current_date_time = datetime.datetime(2019, 7, 21, 15)
#         with freeze_time("2019-07-20 20:00:00"):
#             forecast = weather.get_5_day_forecast()
#             [daytime_forecast_points, nighttime_forecast_points] = weather._get_forecast_points()

#         start_thread = threading.Thread(name="gui",
#                                         target=app_loader,
#                                         args=(daytime_forecast_points[1], nighttime_forecast_points[1]),
#                                         daemon=True)
#         start_thread.start()
#         start_thread.join()


