import html

from pint import Quantity
import waqd.app as base_app
from waqd.components.server import SensorApi_0_1
import waqd.app as app
from waqd.ui import format_unit_disp_value


class SensorRetrieval:

    def __init__(self) -> None:
        self._comps = base_app.comp_ctrl.components

    def _get_exterior_sensor_values(self, units=False):
        temp = self._comps.remote_exterior_sensor.get_temperature()
        hum = self._comps.remote_exterior_sensor.get_humidity()

        if temp is None or hum is None:
            current_weather = self._comps.weather_info.get_current_weather()
            if current_weather:
                temp = app.unit_reg.Quantity(current_weather.temp, "degC")
                hum = current_weather.humidity
        if units:  # format non unit values
            temp = self._format_sensor_disp_value(temp, True)
            hum = self._format_sensor_disp_value(hum, "%", 0)
        else:
            temp = self._format_sensor_disp_value(temp)
            hum = self._format_sensor_disp_value(hum, "")
        data: SensorApi_0_1 = {"api_ver": "0.1",
                                "temp": temp, "hum": hum,
                                "baro": "N/A", "co2": "N/A"
                                }
        return data

    def _format_sensor_disp_value(self, quantity: Quantity, unit=None, precision=1):
        disp_value = format_unit_disp_value(quantity, unit, precision)
        return html.escape(disp_value)

    def _get_interior_sensor_values(self, units=False):
        temp = self._comps.temp_sensor.get_temperature()
        hum = self._comps.humidity_sensor.get_humidity()
        pres = self._comps.pressure_sensor.get_pressure()
        co2 = self._comps.co2_sensor.get_co2()
        temp_disp = self._format_sensor_disp_value(temp, units)

        if units:
            hum = self._format_sensor_disp_value(hum, "%", 0)
            pres = self._format_sensor_disp_value(pres, "hPa", 0)
            co2 = self._format_sensor_disp_value(co2, "ppm", 0)
        else:
            hum = self._format_sensor_disp_value(hum, "", 0)
            pres = self._format_sensor_disp_value(pres, "", 0)
            co2 = self._format_sensor_disp_value(co2, "", 0)
        data: SensorApi_0_1 = {"api_ver": "0.1",
                            "temp": temp_disp, "hum": hum,
                            "baro": pres, "co2": co2
                            }
        return data