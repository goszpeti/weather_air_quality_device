#!/bin/bash

# Install ngnix
sudo apt update
sudo apt install -y iputils-ping nano micro htop mc

# Setup wireguard
sudo apt install -y wireguard

# Configure
sudo nano /etc/wireguard/wg0.conf

# [Interface]
# Address = 10.0.0.2/24
# PrivateKey = <ServersPrivateKey>

# [Peer]
# PublicKey = <ServersPublicKey>
# Endpoint = <ServerPublicIp>:51820
# AllowedIPs = 10.0.0.1/32
# PersistentKeepalive = 25

# Enable service
sudo systemctl enable wg-quick@wg0
sudo systemctl start wg-quick@wg0

# Install docker
curl -sSL https://get.docker.com | sudo sh

# Install argoncase scripts if applicable
# curl https://download.argon40.com/argon1.sh | bash
# argonone-config