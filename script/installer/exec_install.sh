#!/bin/bash
CURRENT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
SRC_DIR=${CURRENT_DIR}/../../src
echo "##### Start updater process #####" 

# additional args to not fail on wrong clock time and enable update to newer distro releases
sudo apt-get -o Acquire::Check-Valid-Until=false -o Acquire::Check-Date=false update
echo "##### Install feh and zenity #####" 
# zenity for dialog and feh background screen - xdotool and wmctrl for x-window manipulation
sudo apt-get install feh zenity xdotool wmctrl -y
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
    sudo apt-get -y install python3-venv xscreensaver network-manager
    # install pipx for venv based app creation
    python3 -m pip install --user pipx==1.7.1 --break-system-packages
    python3 -m pipx ensurepath

    echo "# Full system update... (Step 2/6)"
    sudo apt-get upgrade -y --force-yes
    sudo apt-get autoremove -y
    # Install security updates daily - see https://wiki.debian.org/UnattendedUpgrades
    sudo apt-get install unattended-upgrades -y

    echo "# Installing InfluxDB Database... (Step 3/6)"
    cd $CURRENT_DIR
    chmod +x ./setup/install_influx.sh
    ./setup/install_influx.sh

    echo "# Configuring system languages (Step 4/6)"
    sudo PYTHONPATH=${SRC_DIR} python3 -m installer --configure_languages

    echo "# Setting up the system (Step 5/6)"

    chmod +x ./setup/setup_firewall.sh
    ./setup/setup_firewall.sh

    # set volume to max
    amixer sset 'Master' 100%

    # Enable HW access (serial, i2c and spi)
    
    sudo raspi-config nonint do_serial_hw 0 # console off, serial on
    sudo raspi-config nonint do_serial_cons 1
    sudo raspi-config nonint do_i2c 0
    sudo raspi-config nonint do_spi 0
    sudo raspi-config nonint do_squeekboard S3 # disable
    sudo raspi-config nonint do_wayland W1 # X11

    sudo PYTHONPATH=${SRC_DIR} python3 -m waqd_installer --setup_system

    echo "# Installing application... (Step 6/6)"
    sudo PYTHONPATH=${SRC_DIR} python3 -m waqd_installer --install
    # needs installed app
    export PYTHONPATH=${SRC_DIR}
    python3 -m waqd_installer --set_wallpaper
    
    echo "# Waiting for restart..."
    sudo reboot
}