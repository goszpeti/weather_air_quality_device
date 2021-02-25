import datetime
import time

from PyQt5 import QtGui

from piweather.resources import get_rsc_file
from piweather.settings import FORECAST_ENABLED
from piweather.ui import common, sub_ui


class Forecast(sub_ui.SubUi):
    """  Forecast segment of the main ui. Displays the forecast for 3 days. """
    UPDATE_TIME = 600 * 1000  # 10 minutes in microseconds

    def __init__(self, qtui, settings):
        super().__init__(qtui, settings)
        self._default_min_max_text = self._ui.forecast_d1_day_temps_value.text()

        # placeholder for daily detail view
        # self._ui.forecast_d1_icon.pressed.connect(self.show_detail)
        # self._ui.forecast_d2_icon.pressed.connect(self.show_detail)
        # self._ui.forecast_d3_icon.pressed.connect(self.show_detail)

        # set default day night icons - sunny clear
        day_icon = get_rsc_file("weather_icons", "day-800")
        # night-clear
        night_icon = get_rsc_file("weather_icons", "night-800")

        common.draw_svg(self._ui.forecast_d1_day_icon, day_icon)
        common.draw_svg(self._ui.forecast_d2_day_icon, day_icon)
        common.draw_svg(self._ui.forecast_d3_day_icon, day_icon)

        common.draw_svg(self._ui.forecast_d1_night_icon, night_icon)
        common.draw_svg(self._ui.forecast_d2_night_icon, night_icon)
        common.draw_svg(self._ui.forecast_d3_night_icon, night_icon)

        self._init_dummy_values()
        # call once at begin
        self._cyclic_update()

    def _init_dummy_values(self):
        dummy_icon = str(get_rsc_file("gui_base", "dummy"))
        self._ui.forecast_d1_icon.setPixmap(QtGui.QPixmap(dummy_icon))
        self._ui.forecast_d2_icon.setPixmap(QtGui.QPixmap(dummy_icon))
        self._ui.forecast_d3_icon.setPixmap(QtGui.QPixmap(dummy_icon))

        # set day temps to NA
        self._ui.forecast_d1_day_temps_value.setText(
            common.format_temp_text_minmax(self._default_min_max_text, None, None))

        self._ui.forecast_d2_day_temps_value.setText(
            common.format_temp_text_minmax(self._default_min_max_text, None, None))

        self._ui.forecast_d3_day_temps_value.setText(
            common.format_temp_text_minmax(self._default_min_max_text, None, None))

        # set night temps to NA
        self._ui.forecast_d1_night_temps_value.setText(
            common.format_temp_text_minmax(self._default_min_max_text, None, None))

        self._ui.forecast_d2_night_temps_value.setText(
            common.format_temp_text_minmax(self._default_min_max_text, None, None))

        self._ui.forecast_d3_night_temps_value.setText(
            common.format_temp_text_minmax(self._default_min_max_text, None, None))

    def show_detail(self):
        """ Placeholder for detail view. """
        #self.det = exterior.DayDetailView()
        # self.det.show()
        return

    def _cyclic_update(self):
        self._logger.debug("ForecastGui: update")

        if not self._settings.get(FORECAST_ENABLED):
            self._logger.debug("ForecastGui: forecast disabled")
            return

        # set up titles
        current_date_time = datetime.datetime.now()

        disp_date = common.get_localized_date(
            current_date_time + datetime.timedelta(days=1), self._settings)
        label_text = self._ui.forecast_d1_title.text()
        self._ui.forecast_d1_title.setText(
            common.format_text(label_text, disp_date, "string"))

        disp_date = common.get_localized_date(
            current_date_time + datetime.timedelta(days=2), self._settings)
        label_text = self._ui.forecast_d2_title.text()
        self._ui.forecast_d2_title.setText(
            common.format_text(label_text, disp_date, "string"))

        disp_date = common.get_localized_date(
            current_date_time + datetime.timedelta(days=3), self._settings)
        label_text = self._ui.forecast_d3_title.text()
        self._ui.forecast_d3_title.setText(
            common.format_text(label_text, disp_date, "string"))

        # try three times to get weather info object
        i = 0
        while not self._comps.weather_info and i <= 3:
            i += 1
            time.sleep(1)
        if not self._comps.weather_info:
            return

        # get forecast info
        forecast = self._comps.weather_info.get_5_day_forecast()
        if not forecast or len(forecast) == 1:
            self._logger.debug("ForecastGui: No forecast information available")
            return

        # set icons
        common.draw_svg(self._ui.forecast_d1_icon, forecast[1].icon, scale=3.5)
        common.draw_svg(self._ui.forecast_d2_icon, forecast[2].icon, scale=3.5)
        common.draw_svg(self._ui.forecast_d3_icon, forecast[3].icon, scale=3.5)

        # set day temps
        self._ui.forecast_d1_day_temps_value.setText(
            common.format_temp_text_minmax(self._default_min_max_text, forecast[1].temp_min,
                                           forecast[1].temp_max))

        label_text = self._ui.forecast_d2_day_temps_value.text()
        self._ui.forecast_d2_day_temps_value.setText(
            common.format_temp_text_minmax(self._default_min_max_text, forecast[2].temp_min,
                                           forecast[2].temp_max))

        self._ui.forecast_d3_day_temps_value.setText(
            common.format_temp_text_minmax(self._default_min_max_text, forecast[3].temp_min,
                                           forecast[3].temp_max))

        # set night temps
        self._ui.forecast_d1_night_temps_value.setText(
            common.format_temp_text_minmax(self._default_min_max_text, forecast[1].temp_night_min,
                                           forecast[1].temp_night_max))

        self._ui.forecast_d2_night_temps_value.setText(
            common.format_temp_text_minmax(self._default_min_max_text, forecast[2].temp_night_min,
                                           forecast[2].temp_night_max))

        self._ui.forecast_d3_night_temps_value.setText(
            common.format_temp_text_minmax(self._default_min_max_text, forecast[3].temp_night_min,
                                           forecast[3].temp_night_max))
