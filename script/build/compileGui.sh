#!/bin/bash

cd src/waqd/ui/qt

pylupdate5 weather.ui options.ui -ts german.ts
pylupdate5 weather.ui options.ui -ts hungarian.ts

# lrelease english.ts