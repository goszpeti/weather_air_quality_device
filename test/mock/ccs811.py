from time import sleep
import logging


AVAILABLE = True
ERROR = False
READINGS_STABILIZED = False

TEMP = 28.45
TVOC = 55
CO2 = 1002


class CCS811:
    tempOffset = 0

    def __init__(self):
        pass

    def read_ready(self):
        return AVAILABLE

    def readings_stabilized(self):
        return READINGS_STABILIZED

    def get_temp(self):
        return TEMP

    def get_co2(self):
        return CO2

    def get_tvoc(self):
        return TVOC

    def check_for_error(self):
        return ERROR
    
    def set_environmental_data(self, humidity, temp):
        return True
