from time import sleep
import logging

DHT22  = 22
H = 55.43
T = 22.30234

def read_retry(type, pin):
    logging.debug("Reading mockup values for DHT")
    return [H, T]