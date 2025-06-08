AVAILABLE = True
TEMP = 22.45
TVOC = 55
CO2 = 1002


class CCS811:

    def __init__(self, i2c):
        pass

    def set_environmental_data(self, humidity, temperature):
        pass
    
    def data_ready(self):
        return AVAILABLE
    
    def reset(self):
        pass

    @property
    def temperature(self):
        return TEMP

    @property
    def tvoc(self):  # pylint: disable=invalid-name
        return TVOC

    @property
    def eco2(self):  # pylint: disable=invalid-name
        return CO2
