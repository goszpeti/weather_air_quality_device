#!/bin/bash
CURRENT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
sudo apt-get install feh

# first the 2 application, which are most likely to hold an open handle on files
pkill leafpad
pkill pcmanfm
# kill the application itself
pkill -f pyweather
pkill -f main.py

feh -F -x ${CURRENT_DIR}/../../resources/gui_base/update_screen.png &

# PyQt doesnt work with pip on raspi
sudo apt-get update
sudo apt-get --yes --force-yes install qt5-default pyqt5-dev python3-pyqt5.qtsvg python3-pyqt5.qtchart python3-libgpiod

#python3 -m ensurepip --upgrade
pip3 install --upgrade pip
pip3 install -r ${CURRENT_DIR}/requirements.txt

# copy splash screen to /usr/share/plymouth/themes/pix
sudo cp ${CURRENT_DIR}/../../resources/gui_base/splash_screen.png /usr/share/plymouth/themes/pix/splash.png
pcmanfm --desktop --profile LXDE-pi </dev/null &>/dev/null &
# set wallpaper
lxterminal -e pcmanfm --set-wallpaper="/usr/share/plymouth/themes/pix/splash.png"

python3 ${CURRENT_DIR}/installer.py
exit