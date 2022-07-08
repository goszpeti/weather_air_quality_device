sudo apt purge openresolv dhcpcd5
wget https://davesteele.github.io/comitup/latest/davesteele-comitup-apt-source_latest.deb
sudo dpkg -i --force-all davesteele-comitup-apt-source_latest.deb
sudo rm davesteele-comitup-apt-source_latest.deb
sudo apt-get install comitup comitup-watch -y
sudo rm /etc/network/interfaces
sudo systemctl mask dnsmasq.service
sudo systemctl mask systemd-resolved.service
sudo systemctl mask dhcpd.service
sudo systemctl mask dhcpcd.service
sudo systemctl mask wpa-supplicant.service
