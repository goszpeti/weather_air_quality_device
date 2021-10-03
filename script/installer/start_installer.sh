#!/bin/bash
CURRENT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
SRC_DIR=${CURRENT_DIR}/../../src
# additional args to not fail on wrong clock time
sudo apt-get -o Acquire::Check-Valid-Until=false -o Acquire::Check-Date=false update

echo "##### Install feh and zenity #####" 
# zenity for dialog and feh background screen - xdotool and wmctrl for x-window manipulation
sudo apt install feh zenity xdotool wmctrl -y
# assure desktop manager is running
pcmanfm --desktop --profile LXDE-pi </dev/null &>/dev/null &
# kill zenity - need exactlys one proc for grep later
pkill zenity || true

# show update background screen
feh -F -x $SRC_DIR/waqd/assets/gui_base/update_screen.png &

echo "##### Starting installer #####" 

function updater() {
    # kill all necessary running applications
    # first the application, which are most likely to hold an open handle on files
    pkill leafpad || true
    # kill the application itself
    pkill waqd || true
    pkill python3 || true

    echo "# Install needed system libraries..."
    echo "Install needed system libraries..."
    # python dependencies
    sudo apt -y install python3-libgpiod python3-venv 
    # PyQt doesnt work with pip on raspi - SVG and Charts are needed, too
    # It does compile - but it takes several hours...
    sudo apt -y install qt5-default python3-pyqt5 python3-pyqt5.qtsvg python3-pyqt5.qtchart
    # install pipx for venv based app creation
    python3 -m pip install --user pipx==0.16.3
    python3 -m pipx ensurepath
    # xscreensaver - for no auto screen turn off 
    sudo apt -y install xscreensaver

    echo "# Full system update..."
    echo "Full system update... (Step 1/3)"
    sudo apt full-upgrade -y --force-yes

    echo "# Setting up the system (Step 2/3)"
    sudo PYTHONPATH=${SRC_DIR} python3 -m installer --setup_system

    echo "# Installing application... (Step 3/3)"
    sudo PYTHONPATH=${SRC_DIR} python3 -m installer --install
    # needs installed app
    export PYTHONPATH=${SRC_DIR}
    python3 -m installer --set_wallpaper

    echo "# Waiting for restart..."
}

# start Updater function and pass output to zenity. Echos starting with '#' wil be visible in the dialog.
# Pulsating means, that we have a bouncing loading bar, without actually displaying progress.
updater | zenity --progress --pulsate --width 250 --no-cancel --title "Updating..." --auto-close &

# move the window between the text on the background image (src\waqd\assets\gui_base\update_screen.png)
if timeout 1s xset q &>/dev/null; then # only if xserver is running
    until [[ $(wmctrl -lp | grep $(pidof zenity) | cut -d' ' -f1) ]] # wait until there is a window
    do
    sleep 0.1
    done
    xdotool windowmove $(wmctrl -lp | grep $(pidof zenity) | cut -d' ' -f1) 260 265
fi
