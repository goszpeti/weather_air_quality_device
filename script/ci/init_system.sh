#!/bin/bash

# Updated to Raspi Bullseye ARM64
# use global noninteractive mode, no -y flags needed
export DEBIAN_FRONTEND=noninteractive DEBCONF_NONINTERACTIVE_SEEN=true

sudo apt-get -o Acquire::Check-Valid-Until=false -o Acquire::Check-Date=false update
sudo apt full-upgrade -y --force-yes

sudo raspi-config nonint do_serial 2  # console off, serial on
sudo raspi-config nonint do_i2c 0
sudo raspi-config nonint do_spi 0
sudo raspi-config nonint do_vnc 0

# Install docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo apt-get install -y uidmap
dockerd-rootless-setuptool.sh install
systemctl --user start docker.service
sudo loginctl enable-linger $USER

export PATH=/usr/bin:$PATH
export DOCKER_HOST=unix:///run/user/1000/docker.sock

######### HW specific settings

# Setup Waveshare display
sudo raspi-config nonint set_config_var hdmi_group 2 /boot/firmware/config.txt
sudo raspi-config nonint set_config_var hdmi_mode 87 /boot/firmware/config.txt
sudo raspi-config nonint set_config_var hdmi_cvt "800 480 60 6 0 0 0" /boot/firmware/config.txt
sudo apt-get install xserver-xorg-input-evdev xinput-calibrator
# can't use 32bit driver setup anymore!

# ArgonOne case
#curl https://download.argon40.com/argon1.sh | bash 

# If there is a WiFi dongle used
# sudo iwconfig wlan0 txpower off

######### System Monitor

# Install dry for Docker management, atop for disk usage and tmux vor terminal man.
curl -sSf https://moncho.github.io/dry/dryup.sh | sudo sh
sudo chmod 755 /usr/local/bin/dry
sudo apt install atop tmux -y

cat > ~/start_monitor.sh << EOF
SESSION="monitor"
tmux kill-session -t \$SESSION
tmux new-session -d -s \$SESSION
tmux split-window -h -t \$SESSION
tmux split-window -v -t \$SESSION
tmux send-keys -t \$SESSION:0.0 "sudo atop" Enter
#tmux send-keys -t \$SESSION:0.1 "htop" Enter
tmux send-keys -t \$SESSION:0.2 "sudo dry" Enter
lxterminal --geometry=200x100 -e "tmux attach-session -t \$SESSION"
EOF
chmod +x start_monitor.sh

cat > ~/crons.txt << EOF
@reboot ~/start_monitor.sh
EOF

crontab ~/crons.txt

# Reboot!