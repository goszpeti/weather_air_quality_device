#!/bin/bash

cd src/waqd/ui/qt

#pyuic5 weather.ui -o weather_ui.py
#pyuic5 options.ui -o options_ui.py
pylupdate5 weather.ui options.ui -ts german.ts
pylupdate5 weather.ui options.ui -ts hungarian.ts

# lrelease english.ts