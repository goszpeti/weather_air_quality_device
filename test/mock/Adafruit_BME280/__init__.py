
AVAILABLE = True
ERROR = False
TEMP = 28.45
PRESSURE = 1100
HUMIDITY = 55


class BME280():
    def read_humidity(self):
        return HUMIDITY

    def read_temperature(self):
        return TEMP

    def read_pressure(self):
        return PRESSURE * 100  # hPa to Pa
