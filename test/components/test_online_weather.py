from freezegun import freeze_time

from waqd.base.component_reg import ComponentRegistry
from waqd.components.online_weather import OpenTopoData, OpenWeatherMap
from waqd.settings import LOCATION, Settings

def testOpenTopo(base_fixture):
    op = OpenTopoData()
    alt = op.get_altitude(48.2085, 12.3989)
    assert alt > 439 and alt < 440
    op._altitude_info["elevation"] = 0
    alt = op.get_altitude(48.2085, 12.3989)
    assert alt == 0

def testOpenWeatherCurrentWeatherApiCall(base_fixture):
    test_json = base_fixture.testdata_path / "online_weather/ow_current_weather.json"

    weather = OpenWeatherMap("city_id", "no_api_key_needed")
    weather._cw_json_file = str(test_json)
    cw_info = weather._call_ow_api(weather.CURRENT_WEATHER_BY_CITY_ID_API_CMD)
    assert cw_info.get("name") == "Location"  # no umlauts

def testOpenWeatherForecastApiCall(base_fixture):
    test_json = base_fixture.testdata_path / "online_weather/ow_forecast.json"
    weather = OpenWeatherMap("city_id", "no_api_key_needed")
    weather._fc_json_file = str(test_json)
    cw_info = weather._call_ow_api(
        weather.FORECAST_BY_CITY_ID_API_CMD)
    assert cw_info.get("city").get("name") == "Location"  # no umlauts
    assert cw_info.get("list")[0].get("main").get("humidity") == 69


def testOpenWeatherNewDayForecast(base_fixture):
    weather = OpenWeatherMap("city_id", "no_api_key_needed")
    weather._fc_json_file = str(base_fixture.testdata_path / "online_weather/ow_new_day_forecast.json")
    weather._cw_json_file = str(base_fixture.testdata_path / "online_weather/ow_new_day_cw.json")

    # get a date matching with the test data
    #current_date_time = datetime.datetime(2019, 7, 21, 15)
    with freeze_time("2021-05-10 01:00:00"):
        forecast = weather.get_5_day_forecast()
    # sunrise: 20. July 2019 03:10:08
    # sunset 20. July 2019 18:36:18

        assert forecast[0].temp_min == 13.39
        assert forecast[0].temp_max == 23.71
        assert forecast[0].temp_night_min == 11.25
        assert forecast[0].temp_night_max == 13.03
        assert forecast[0].description == "broken clouds"


def testOpenWeatherGet3DayForecast(base_fixture):
    weather = OpenWeatherMap("city_id", "no_api_key_needed")
    weather._fc_json_file = str(base_fixture.testdata_path / "online_weather/ow_forecast.json")
    weather._cw_json_file = str(base_fixture.testdata_path / "online_weather/ow_current_weather.json")

    # get a date matching with the test data
    #current_date_time = datetime.datetime(2019, 7, 21, 15)
    with freeze_time("2019-07-20 20:00:00"):
        forecast = weather.get_5_day_forecast()
        # sunrise: 20. July 2019 03:10:08
        # sunset 20. July 2019 18:36:18

        assert forecast[0].temp_min == -float("inf")
        assert forecast[0].temp_max == float("inf")
        assert forecast[0].temp_night_min == 19.77
        assert forecast[0].temp_night_max == 23.87
        assert forecast[0].description == "broken clouds"

        assert forecast[1].temp_min == 21.65
        assert forecast[1].temp_max == 30.15
        assert forecast[1].temp_night_min == 17.86
        assert forecast[1].temp_night_max == 19.65
        assert forecast[1].description == "light rain"

        assert forecast[2].temp_min == 21.15
        assert forecast[2].temp_max == 26.85
        assert forecast[2].temp_night_min == 15.65
        assert forecast[2].temp_night_max == 19.16
        assert forecast[2].description == "overcast clouds"

        assert forecast[3].temp_min == 19.76
        assert forecast[3].temp_max == 26.69
        assert forecast[3].temp_night_min == 16.16
        assert forecast[3].temp_night_max == 18.81
        assert forecast[3].description == "broken clouds"
