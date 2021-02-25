from time import sleep
import logging


AVAILABLE = True
ERROR = False
TEMP = 28.45
TVOC = 55
CO2 = 1002


class Adafruit_CCS811:
    tempOffset = 0

    def __init__(self):
        pass

    def available(self):
        return AVAILABLE

    def setEnvironmentalData(self, humidity, temperature):
        pass

    def calculateTemperature(self):
        return TEMP

    def readData(self):
        sleep(1)
        return False

    def geteCO2(self):
        return CO2

    def getTVOC(self):
        return TVOC

    def checkError(self):
        return ERROR
    
    def SWReset(self):
        return True
