
class I2C():
    def __init__(self, SCL, SDA, FREQ=0):
        pass

    def scan(self):
        return [0x5A] # CCS811
    
    def writeto_then_readfrom(self, addr, buffer_out, buffer_in,
                                        out_start, out_end, in_start, in_end):
        pass

    def writeto(self, addr, full_cmd):
        pass

