#!/bin/bash
# hide mouse in wayland raspbian

sudo apt install -y interception-tools interception-tools-compat
sudo apt install -y cmake
cd ~
git clone https://gitlab.com/interception/linux/plugins/hideaway.git
cd hideaway
cmake -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build
sudo cp /home/$USER/hideaway/build/hideaway /usr/bin
sudo chmod +x /usr/bin/hideaway

cd ~
wget https://raw.githubusercontent.com/ugotapi/wayland-pagepi/main/config.yaml
sudo cp /home/$USER/config.yaml /etc/interception/udevmon.d/config.yaml
sudo systemctl restart udevmon