
import datetime
from typing import TYPE_CHECKING

from  . import sub_ui
if TYPE_CHECKING:
    from waqd.ui.qt.main_window import WeatherMainUi
    from waqd.settings import Settings

class InfoPane(sub_ui.SubUi):
    """  Infopane segment of the main ui. Displays the date, clock, Options and Shutdown button """
    UPDATE_TIME = 5000  # 5 seconds

    def __init__(self, main_ui: "WeatherMainUi", settings: "Settings"):
        super().__init__(main_ui, main_ui.ui, settings)

        # call once at begin
        self.init_with_cyclic_update()

    def _cyclic_update(self):
        # get time
        current_date_time = datetime.datetime.now()
        # set time
        time = self._get_formatted_time(current_date_time)
        self._ui.time_disp.setText(time)
        # set date
        date = self._get_formatted_date(current_date_time)
        self._ui.date_disp.setText(date)

    @staticmethod
    def _get_formatted_time(current_date_time) -> str:
        """ Return the current time in the format 22:05"""
        return "{:02d}:{:02d}".format(current_date_time.hour,
                                      current_date_time.minute)

    @staticmethod
    def _get_formatted_date(current_date_time) -> str:
        """ Return the current date in the format 14.09.2019"""
        return "{:02d}.{:02d}.{}".format(current_date_time.day,
                                         current_date_time.month,
                                         current_date_time.year)
