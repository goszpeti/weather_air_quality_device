#!/bin/bash
# Setup Github Runner
mkdir actions-runner && cd actions-runner# Download the latest runner package
curl -o actions-runner-linux-arm-2.278.0.tar.gz -L https://github.com/actions/runner/releases/download/v2.278.0/actions-runner-linux-arm-2.278.0.tar.gz# Extract the installer
tar xzf ./actions-runner-linux-arm-2.278.0.tar.gz

# Create the runner and start the configuration experience
./config.sh --url https://github.com/goszpeti/WeatherAirQualityDevice --token <TOKEN>

sudo ./svc.sh install
sudo ./svc.sh start
sudo reboot
