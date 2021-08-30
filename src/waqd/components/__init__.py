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
"""
This module contains all interfaces to HW (OS, sensors, etc.) and online interface functions.
Settings need to be already set up for usage.
"""

from waqd.components.display import Display
from waqd.components.events import EventHandler
from waqd.components.online_weather import OpenWeatherMap
from waqd.components.power import ESaver
from waqd.components.sensors import (BMP280, BME280, DHT22, CCS811, MH_Z19, Prologue433, 
                                     SR501, GP2Y1010AU0F, BH1750,
                                     TempSensor, HumiditySensor, TvocSensor, CO2Sensor, 
                                     BarometricSensor, DustSensor, LightSensor)
from waqd.components.sound import Sound
from waqd.components.speech import TextToSpeach
from waqd.components.updater import OnlineUpdater
