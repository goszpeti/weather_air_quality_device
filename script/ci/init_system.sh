#!/bin/bash

sudo apt-get -o Acquire::Check-Valid-Until=false -o Acquire::Check-Date=false update
sudo apt full-upgrade -y --force-yes

curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

sudo raspi-config nonint do_serial 2  # console off, serial on
sudo raspi-config nonint do_i2c 0
sudo raspi-config nonint do_spi 0

# Setup Waveshare display
sudo raspi-config nonint set_config_var hdmi_group 2 /boot/config.txt
sudo raspi-config nonint set_config_var hdmi_mode 87 /boot/config.txt
sudo raspi-config nonint set_config_var hdmi_cvt "800 480 60 6 0 0 0" /boot/config.txt
git clone https://github.com/waveshare/LCD-show.git
sudo ./LCD-show/LCD5-show # reboots