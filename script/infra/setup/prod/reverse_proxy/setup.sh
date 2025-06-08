#!/bin/bash

# Install ngnix
sudo apt update
sudo apt install -y nginx
sudo apt install -y iputils-ping nano micro htop mc

# Enable and start nginx service
sudo systemctl enable nginx
sudo systemctl start nginx

# Install SSH certificates

sudo apt install python3 python3-dev python3-venv libaugeas-dev gcc
sudo python3 -m venv /opt/certbot/
sudo /opt/certbot/bin/pip install --upgrade pip
sudo /opt/certbot/bin/pip install certbot certbot-nginx
sudo ln -s /opt/certbot/bin/certbot /usr/bin/certbot
sudo certbot --nginx

# Configure nginx to reverse proxy to local server
# Use the correct config from the SSL setup for the correct server block.
# sudo nano /etc/nginx/sites-enabled/default
#  location / {
#           proxy_pass http://10.0.0.2:80;
#           proxy_set_header Host $host;
#           proxy_set_header X-Real-IP $remote_addr;
#           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
#           proxy_set_header X-Forwarded-Proto $scheme;
#         }

# Setup wireguard
sudo apt install -y wireguard

# Configure
sudo nano /etc/wireguard/wg0.conf

# [Interface]
# Address = 10.0.0.1/24
# ListenPort = 51820
# PrivateKey = <ServersPrivateKey>
# [Peer]
# PublicKey = <ClientPublicKey>
# AllowedIPs = 10.0.0.2/32

# Setup Ipv4 forwarding
sudo sysctl -w net.ipv4.ip_forward=1
# /etc/sysctl.conf
# net.ipv4.ip_forward=1

# Enable service
sudo systemctl enable wg-quick@wg0
sudo systemctl start wg-quick@wg0

