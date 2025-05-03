import waqd.app as base_app


class WeatherRetrieval:
    def __init__(self) -> None:
        assert base_app.comp_ctrl
        self._comps = base_app.comp_ctrl.components

    def get_current_weather(self):
        return self._comps.weather_info.get_current_weather()

    def get_5_day_forecast(self):
        return self._comps.weather_info.get_5_day_forecast()
