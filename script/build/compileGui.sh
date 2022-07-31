#!/bin/bash

cd src/waqd/ui/qt

pylupdate5 weather.ui options.ui ../widgets/calibration.ui ../widgets/value_test.ui -ts german.ts -noobsolete
pylupdate5 weather.ui options.ui ../widgets/calibration.ui ../widgets/value_test.ui -ts hungarian.ts -noobsolete

# lrelease english.ts