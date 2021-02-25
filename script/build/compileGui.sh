cd src/piweather/ui/qt

pyuic5 weather.ui  -o weather_ui.py
pyuic5 options.ui  -o options_ui.py
pylupdate5 weather_ui.py options_ui.py -ts english.ts
pylupdate5 weather_ui.py options_ui.py -ts hungarian.ts

# lrelease english.ts