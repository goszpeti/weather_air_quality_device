from freezegun import freeze_time

from piweather.base.components import ComponentRegistry
from piweather.components.online_weather import OpenWeatherMap
from piweather.settings import LOCATION, Settings


def testOpenWeatherApiCall(base_fixture):
    # initalize settings
    settings = Settings(base_fixture.testdata_path / "integration")
    settings.set(LOCATION, "City2")

    test_json = base_fixture.testdata_path / "online_weather/ow_current_weather.json"

    weather = OpenWeatherMap(settings)
    weather._cw_json_file = str(test_json)
    cw_info = weather._call_ow_api(
        weather.CURRENT_WEATHER_BY_CITY_ID_API_CMD)
    assert cw_info.get("name") == "City1"  # no umlauts
    assert cw_info.get("id") == int(weather._city_id)


def testApiCallForecastFromOw(base_fixture):
    # initalize settings
    settings = Settings(base_fixture.testdata_path / "integration")
    settings.set(LOCATION, "City2")

    test_json = base_fixture.testdata_path / "online_weather/ow_forecast.json"
    weather = OpenWeatherMap(settings)
    weather._fc_json_file = str(test_json)
    cw_info = weather._call_ow_api(
        weather.FORECAST_BY_CITY_ID_API_CMD)
    assert cw_info.get("city").get("name") == "City1"  # no umlauts
    assert cw_info.get("city").get("id") == int(weather._city_id)
    assert cw_info.get("list")[0].get("main").get("humidity") == 69


def testGet3DayForecastFromOw(base_fixture):

    # initalize settings
    settings = Settings(base_fixture.testdata_path / "integration")
    settings.location = "City2"

    weather = OpenWeatherMap(settings)
    weather._fc_json_file = str(base_fixture.testdata_path / "online_weather/ow_forecast.json")
    weather._cw_json_file = str(base_fixture.testdata_path / "online_weather/ow_current_weather.json")

    # get a date matching with the test data
    #current_date_time = datetime.datetime(2019, 7, 21, 15)
    with freeze_time("2019-07-20 20:00:00"):
        forecast = weather.get_5_day_forecast()
    # sunrise: 20. July 2019 03:10:08
    # sunset 20. July 2019 18:36:18

        assert forecast[0].temp_min is None
        assert forecast[0].temp_max is None
        assert forecast[0].temp_night_min == 19.77
        assert forecast[0].temp_night_max == 23.87
        assert forecast[0].description == "light rain"

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
        assert forecast[3].description == "clear sky"
