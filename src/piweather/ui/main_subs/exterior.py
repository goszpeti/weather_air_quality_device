import datetime

from PyQt5 import QtCore, QtGui

from piweather.resources import get_rsc_file
from piweather.ui import common, sub_ui

Qt = QtCore.Qt


class Exterior(sub_ui.SubUi):
    """
    Exterior segment of the main ui.
    Displays the outside temperature, current-day forecast and temperature icon.
    """
    UPDATE_TIME = 600 * 1000  # 10 minutes in microseconds

    def __init__(self, main_ui, settings):
        super().__init__(main_ui, settings)

        self._online_info_date_time = None  # date when last online update occured

        # save default text to restore formatting
        self._default_temp_text = self._ui.exterior_temp_value.text()

        day_icon = get_rsc_file("weather_icons", "day-800")
        common.draw_svg(self._ui.exterior_forecast_icon, day_icon, scale=3)

        # set day temps to NA
        self._default_min_max_text = self._ui.exterior_forecast_temps_value.text()
        self._ui.exterior_forecast_temps_value.setText(
            common.format_temp_text_minmax(self._default_min_max_text, None, None))
        # call once at begin
        self._cyclic_update()

        self._ui.exterior_forecast_icon.clicked.connect(self.show_detail)

    def show_detail(self):
        """ Placholder for daily detail view popup """
        # self.det = day_detail_view.DayDetailView()
        # self.det.show()
        return

    def _cyclic_update(self):
        self._logger.debug("ExteriorGui: update")
        if not self._comps.weather_info:
            return
        forecast = self._comps.weather_info.get_5_day_forecast()
        current_weather = self._comps.weather_info.get_current_weather()

        if not current_weather:  # handling for no connection - throw away value after an hour
            if not self._online_info_date_time:  # never got any value
                online_temp_value = None
            else:  # look, if last value is older than one hour
                current_date_time = datetime.datetime.now()
                time_delta = current_date_time - self._online_info_date_time
                if time_delta.seconds > 3600:  # 1 h
                    online_temp_value = None
                else:
                    return  # forecast still valid, don't change displayed value
        else:
            self._online_info_date_time = current_weather.fetch_time
            online_temp_value = current_weather.current_temp  # for later use
            online_weather_desc = current_weather.description
            self._logger.debug("ExteriorGui: Current weather condition is %s",
                               online_weather_desc)

            # set weather description specific background image
            online_weather_category = current_weather.main.lower()
            cloudiness = current_weather.clouds

            if cloudiness > 65 and online_weather_category == "clouds":
                online_weather_category = "heavy_clouds"

            if current_weather.is_daytime():
                bg_name = "bg_day_" + online_weather_category
            else:
                bg_name = "bg_night_" + online_weather_category

            self._ui.exterior_background.set_image(str(get_rsc_file("weather_bgrs", bg_name)))

            # set todays forecast
            if not forecast[0]:
                return
            common.draw_svg(self._ui.exterior_forecast_icon, forecast[0].icon, scale=3)

            if not current_weather.is_daytime():
                temp_min = forecast[0].temp_night_min
                temp_max = forecast[0].temp_night_max
                if not (temp_min or temp_max):
                    temp_min = forecast[0].temp_min
                    temp_max = forecast[0].temp_max
            else:
                temp_min = forecast[0].temp_min
                temp_max = forecast[0].temp_max
                if not (temp_min or temp_max):
                    temp_min = forecast[0].temp_night_min
                    temp_max = forecast[0].temp_night_max

            self._ui.exterior_forecast_temps_value.setText(
                common.format_temp_text_minmax(self._default_min_max_text,
                                               temp_min, temp_max))

        # if sensor is not available switch to online data
        temp_value = online_temp_value
        if self._comps.remote_temp_sensor and self._comps.remote_temp_sensor.is_active:
            temp_value = self._comps.remote_temp_sensor.get_temperature()

        # format and set values to temperature display
        temp_val_text = common.format_float_temp_text(
            self._default_temp_text, temp_value)
        self._ui.exterior_temp_value.setText(temp_val_text)

        # set temperature icon
        self._ui.exterior_temp_icon.setPixmap(QtGui.QPixmap(
            str(common.get_temperature_icon(temp_value))))
