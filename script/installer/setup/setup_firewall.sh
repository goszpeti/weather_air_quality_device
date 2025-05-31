sudo apt install ufw -y
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
# vnc
sudo ufw allow 5900
sudo ufw allow http
sudo ufw allow https
# dhcpd
sudo ufw allow bootps
sudo ufw allow 53

sudo ufw enable
# sudo ufw status verbose