import json
CO2 = 734
TEMP = 21

serial_dev = ""
partial_serial_dev = ""


def read_all():
    return {'SS': 232, 'UhUl': 10738, 'TT': 61, 'co2': CO2, 'temperature': TEMP}


def read():
    return {"co2": CO2}


if __name__ == "__main__":
    value = {"co2": CO2}
    print(json.dumps(value))
