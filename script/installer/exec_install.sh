#!/bin/bash
CURRENT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
SRC_DIR=${CURRENT_DIR}/../../src
echo "##### Start updater process #####" 

# additional args to not fail on wrong clock time and enable update to newer distro releases
sudo apt-get -o Acquire::Check-Valid-Until=false -o Acquire::Check-Date=false update  --allow-releaseinfo-change
echo "##### Install feh and zenity #####" 
# zenity for dialog and feh background screen - xdotool and wmctrl for x-window manipulation
sudo apt install feh zenity xdotool wmctrl -y
# assure desktop manager is running
pcmanfm --desktop --profile LXDE-pi </dev/null &>/dev/null &
# kill zenity - need exactly one proc for grep later
pkill zenity || true
# stop sensor db for possible update
sudo systemctl stop influxdb || true

echo "##### Starting installer #####" 

function waqd_install() {
    # kill all necessary running applications
    # kill the application itself
    pkill waqd || true
    pkill python3 || true

    echo "# Install needed system libraries... (Step 1/6)"
    # python dependencies
    # sudo apt -y install python3-apt # TODO: if apt via python is used
    sudo apt -y install python3-libgpiod python3-venv python3-pyrsistent python3-pyqt5 python3-pyqt5.qtmultimedia python3-pyqt5.qtsvg python3-pyqt5.qtchart
    # install pipx for venv based app creation
    python3 -m pip install --user pipx==1.1.0
    python3 -m pipx ensurepath
    # xscreensaver - for no auto screen turn off
    sudo apt -y install xscreensaver

    echo "# Full system update... (Step 2/6)"
    sudo apt full-upgrade -y --force-yes
    sudo apt autoremove -y
    # Install security updates daily - see https://wiki.debian.org/UnattendedUpgrades
    sudo apt-get install unattended-upgrades -y

    echo "# Installing InfluxDB Database... (Step 3/6)"
    cd $CURRENT_DIR
    chmod +x ./install_influx.sh
    ./install_influx.sh

    echo "# Install Wifi Connector... (Step 4/5)"
    # TODO can'T do this in the middle of an update, only after it?
	# resets network 1st time installed
    cd $CURRENT_DIR
    chmod +x ./install_wifi-connect.sh
    ./install_wifi-connect.sh -y

    echo "# Setting up the system (Step 5/6)"
    sudo PYTHONPATH=${SRC_DIR} python3 -m installer --setup_system
    echo "# Installing application... (Step 6/6)"
    sudo PYTHONPATH=${SRC_DIR} python3 -m installer --install
    # needs installed app
    export PYTHONPATH=${SRC_DIR}
    python3 -m installer --set_wallpaper
    sudo reboot
    echo "# Waiting for restart..."
}