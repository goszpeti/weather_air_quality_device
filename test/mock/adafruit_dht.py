AVAILABLE = True
TEMP = 28.1
HUM = 55
_USE_PULSEIO = True


class DHT22:

    def __init__(self, pin):
        pass

    @property
    def temperature(self):
        return TEMP

    @property
    def humidity(self):
        return HUM

    def exit(self):
        pass
