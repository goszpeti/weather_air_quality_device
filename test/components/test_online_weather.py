import json
from pathlib import Path
from freezegun import freeze_time

from waqd.components.weather import OpenTopoData, OpenWeatherMap, OpenMeteo


class MockOpenMeteo(OpenMeteo):
    daily_test_json = Path()
    hourly_test_json = Path()

    def _call_api(self, command: str, **kwargs):
        if "&hourly" in command:
            with open(self.hourly_test_json) as fp:
                return json.load(fp)
        elif "&daily" in command:
            with open(self.daily_test_json) as fp:
                return json.load(fp)
        return {}


def test_open_meteo_geocoder(base_fixture, mocker):
    test_json: Path = base_fixture.testdata_path / "online_weather/om_search_berlin.json"
    om = OpenMeteo()
    mock_call = mocker.Mock()
    mock_call.return_value = json.loads(test_json.read_text())
    mocker.patch("waqd.components.online_weather.OpenMeteo._call_api", mock_call)
    ret = om.find_location_candidates("Berlin", "de")
    assert len(ret) == 10
    assert ret[0].name == "Berlin"
    assert ret[0].country == "Deutschland"
    assert ret[0].state == "Berlin"
    assert ret[0].county == ""
    assert ret[0].postcodes == ['10967', '13347']
    assert ret[0].altitude == 74
    assert ret[0].longitude == 13.41053
    assert ret[0].latitude == 52.52437


def test_open_meteo(base_fixture, mocker):
    daily_test_json: Path = base_fixture.testdata_path / "online_weather/om_current_weather.json"
    hourly_test_json: Path = base_fixture.testdata_path / "online_weather/om_hourly_weather.json"

    om = MockOpenMeteo(13.41053, 52.52437)
    om.daily_test_json = daily_test_json
    om.hourly_test_json = hourly_test_json
    ret = om.get_current_weather()
    assert ret
    ret = om.get_5_day_forecast()
    assert ret
    assert om.nighttime_forecast_points
    assert om.daytime_forecast_points


class MockOpenWeatherMap(OpenWeatherMap):
    cw_json_file = Path()
    fc_json_file = Path()

    def _call_api(self, command: str):
        if command == OpenWeatherMap.CURRENT_WEATHER_BY_CITY_ID_API_CMD:
            with open(self.cw_json_file) as fp:
                return json.load(fp)
        elif command == OpenWeatherMap.FORECAST_BY_CITY_ID_API_CMD:
            with open(self.fc_json_file) as fp:
                return json.load(fp)
        return {}


def test_open_topo():
    op = OpenTopoData()
    alt = op.get_altitude(48.2085, 12.3989)
    assert alt > 439 and alt < 440
    op._altitude_info["elevation"] = 0
    alt = op.get_altitude(48.2085, 12.3989)
    assert alt == 0


def test_open_weather_forecast_api_call(base_fixture):
    """
    Simply tests call api correct return for Forecats (mocked by file)
    This ensures, that further tests work correctly.
    """
    cw_test_json: Path = base_fixture.testdata_path / "online_weather/ow_current_weather.json"
    MockOpenWeatherMap.cw_json_file = cw_test_json
    fc_test_json = base_fixture.testdata_path / "online_weather/ow_forecast.json"
    MockOpenWeatherMap.fc_json_file = fc_test_json
    weather = MockOpenWeatherMap("city_id", "no_api_key_needed")
    forecast_info = weather._call_api(
        weather.FORECAST_BY_CITY_ID_API_CMD)
    assert forecast_info.get("city").get("name") == "Location"  # no umlauts
    assert forecast_info.get("list")[0].get("main").get("humidity") == 69


def test_open_weather_new_day_forecast(base_fixture):
    MockOpenWeatherMap.fc_json_file = str(
        base_fixture.testdata_path / "online_weather/ow_new_day_forecast.json")
    MockOpenWeatherMap.cw_json_file = str(base_fixture.testdata_path / "online_weather/ow_new_day_cw.json")
    weather = MockOpenWeatherMap("city_id", "no_api_key_needed")

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


def test_open_weather_get3_day_forecast(base_fixture):
    MockOpenWeatherMap.fc_json_file = str(base_fixture.testdata_path / "online_weather/ow_forecast.json")
    MockOpenWeatherMap.cw_json_file = str(
        base_fixture.testdata_path / "online_weather/ow_current_weather.json")

    weather = MockOpenWeatherMap("city_id", "no_api_key_needed")

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
