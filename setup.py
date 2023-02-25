#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Note: To use the 'upload' functionality of this file, you must:
#   $ pipenv install twine --dev

import waqd
import io
import os
import platform
from glob import glob
from os.path import basename, splitext
import sys
from setuptools import find_packages, setup

# Package meta-data.
NAME = 'waqd'
DESCRIPTION = 'Weather Air Quality Device - base package'
URL = 'https://github.com/goszpeti/WeatherAirQualityDevice'
AUTHOR = 'Peter Gosztolya'
REQUIRES_PYTHON = '>=3.9.0'

# What packages are required for this module to be executed?
REQUIRED = [
    "wheel",  # for pep 517 legacy setup.py mode
    # Backend
    "htmlmin==0.1.12",  # BSD License - HTML minifier (removes comments and whitespace)
    "js.jquery==3.6.1",  # BSD License - Offline jquery resource and helper
    "plotly==5.10.0",  # MIT License - web graph plotting
    "influxdb-client==1.30.0",  # MIT License - influxdb API
    "bcrypt>=4.0.0, <5.0.0",  # Apache License, Version 2.0 - Password hashing
    "DebugPy==1.5.0",  # MS VSCode debugger for dynamic debugging
    "JsonSchema==4.16.0",  # MIT License - for events json schema validation
    "Bottle==0.12.23",  # MIT License - webserver for remote sensors
    "Jinja2==3.1.2",
    "paste==3.5.0",  # server backend for bottle
    "pint==0.19.2",  # BSD 3-clause style license - physical units for sensors
    "Python-DateUtil==2.8.2",  # Apache License - for date parse and relative delta
    "APScheduler==3.9.1",  # MIT License - Scheduler for Events function
    "PyGithub==1.55",  # LGPL - Access to GitHub in AutoUpdater
    "File-Read-Backwards==2.0.0",  # MIT License - for performance in DetailView
    # Sound
    "gTTS==2.2.4",  # MIT License -Google TTS for speech
    "Python-VLC==3.0.16120",  # LGPLv2+ - use VLC for playing sounds
    # HW
    "RPi-Backlight==2.4.1",  # MIT License
    "Adafruit-Blinka==7.1.1",  # For all other Adafruit drivers
    # "Adafruit-PlatformDetect==2.4.0",  # MIT License - target and model detection - up to 3.10 not working with BMP280
    "Adafruit-CircuitPython-DHT==3.7.1",  # MIT License - temp/hum sensor
    "Adafruit-CircuitPython-CCS811==1.3.4",  # MIT License - co2/tvoc sensor
    "Adafruit-CircuitPython-BME280==2.6.10",  # MIT License - temp/hum/baro sensor
    "Adafruit-CircuitPython-BMP280==3.2.15",  # MIT License - temp/baro sensor
    "Adafruit-Circuitpython-BH1750==1.0.7",  # MIT License - light sensor
    "Adafruit-Circuitpython-ADS1x15==2.2.8",  # MIT License - currently only this ADC is used for analog sensors
    # QT Widgets
    "QtWidgets==0.18",  # MIT License - for touch friendly Toggle Switch
    "PyQtSpinner==0.1.1"  # MIT License - a loading Spinner
]
REQUIRED_NON_RPI = [
    # UI
    "PyQt5>=5.12.0",  # GPLv3 - Must be compiled on RPi (takes an eternity) - so use system libs
    "PyQtChart>=5.12.0",  # GPLv3 - for DetailView
]

REQUIRED_LINUX = [  # this package does not install on windows, because of RPi.GPIO dependency
    "MH-Z19==3.1.3",  # MIT License
]

# epd-library=0.2.3 GPL v3GPLv3 - Waveshare 2.9 inch epaper 296×128
machine = platform.machine()
if not (machine.startswith("armv") or machine.startswith("aarch64")):
    REQUIRED += REQUIRED_NON_RPI
if platform.system() == "Linux":
    REQUIRED += REQUIRED_LINUX

here = os.path.abspath(os.path.dirname(__file__))

# Import the README and use it as the long-description.
# Note: this will only work if 'README.md' is present in your MANIFEST.in file!
try:
    with io.open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
        long_description = '\n' + f.read()
except FileNotFoundError:
    long_description = DESCRIPTION

# Load the package's __version__.py module as a dictionary.
project_slug = NAME.lower().replace("-", "_").replace(" ", "_")
sys.path.insert(0, os.path.join(here, "src"))
about = waqd


# Where the magic happens:
setup(
    name=NAME,
    version=waqd.__version__,
    description=DESCRIPTION,
    long_description=long_description,
    author=AUTHOR,
    python_requires=REQUIRES_PYTHON,
    url=URL,
    packages=find_packages("src"),
    package_dir={'': 'src'},
    py_modules=[splitext(basename(path))[0] for path in glob('src/*.py')],
    package_data={"": ["ui/**/*.ui", "ui/**/*.in", "ui/web/**/*.*", "ui/qt/**/*.qm", "assets/**/*.*"]},
    install_requires=REQUIRED,
    include_package_data=True,
    license='AGPL',
    classifiers=[
        # Trove classifiers
        # Full list: https://pypi.python.org/pypi?%3Aaction=list_classifiers
        "License:: OSI Approved:: GNU Affero General Public License v3"
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: Implementation :: CPython'
    ],
    entry_points={
        'gui_scripts': [
            'waqd=waqd.__main__:main',
        ]
    }
)
