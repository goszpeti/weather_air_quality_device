import html
from typing import Optional

from pint.facets.plain import PlainQuantity as Quantity

import waqd.app as base_app
import waqd.app as app
from waqd.web.helper import format_unit_disp_value

from .model import SensorApi_v1, TempHumSensorApi_v1


class SensorRetrieval:
    def __init__(self) -> None:
        assert base_app.comp_ctrl
        self._comps = base_app.comp_ctrl.components

    def get_exterior_sensor_values(self, units=False):
        temp = self._comps.remote_exterior_sensor.get_temperature()
        hum = self._comps.remote_exterior_sensor.get_humidity()

        if temp is None or hum is None:
            current_weather = self._comps.weather_info.get_current_weather()
            if current_weather:
                temp = app.unit_reg.Quantity(current_weather.temp, "degC")
                hum = app.unit_reg.Quantity(current_weather.humidity, "percent")
        temp = self._format_sensor_disp_value(temp, units)
        hum = self._format_sensor_disp_value(hum, units, 0)

        data = TempHumSensorApi_v1(
            temp=temp,
            hum=hum,
        )
        return data

    def _format_sensor_disp_value(self, quantity: Optional[Quantity], unit=False, precision=1):
        disp_value = format_unit_disp_value(quantity, unit, precision)
        return html.escape(disp_value)

    def get_interior_sensor_values(self, units=False):
        temp = self._comps.temp_sensor.get_temperature()
        hum = self._comps.humidity_sensor.get_humidity()
        pres = self._comps.pressure_sensor.get_pressure()
        co2 = self._comps.co2_sensor.get_co2()

        temp_disp = self._format_sensor_disp_value(temp, units)
        hum = self._format_sensor_disp_value(hum, units, 0)
        pres = self._format_sensor_disp_value(pres, units, 0)
        co2 = self._format_sensor_disp_value(co2, units, 0)

        return SensorApi_v1(
            temp=temp_disp,
            hum=hum,
            baro=pres,
            co2=co2,
        )
    
class SensorWriter():
    def __init__(self) -> None:
        assert base_app.comp_ctrl
        self._comps = base_app.comp_ctrl.components

    def write_sensor_values(self, value: SensorApi_v1):
        self._comps.remote_exterior_sensor.read_callback(
            value.temp, value.hum, value.baro, value.co2
        )
