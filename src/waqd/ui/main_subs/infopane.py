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
import datetime

from waqd.ui.main_subs import sub_ui


class InfoPane(sub_ui.SubUi):
    """  Infopane segment of the main ui. Displays the date, clock, Options and Shutdown button """
    UPDATE_TIME = 5000  # 5 seconds

    def __init__(self, main_ui, settings):
        super().__init__(main_ui, settings)
        # call once at begin
        self._cyclic_update()

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
