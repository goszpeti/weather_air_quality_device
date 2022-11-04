#!/bin/bash
# Setup Github Runner
mkdir actions-runner && cd actions-runner
curl -o actions-runner-linux-arm64-2.293.0.tar.gz -L https://github.com/actions/runner/releases/download/v2.293.0/actions-runner-linux-arm64-2.293.0.tar.gz
echo "003fde87923900ae85d3a28f8b364936725bbd0f7eb9afeb73c40f3e117cc9c9  actions-runner-linux-arm64-2.293.0.tar.gz" | shasum -a 256 -c
tar xzf ./actions-runner-linux-arm64-2.293.0.tar.gz

# Create the runner and start the configuration experience
./config.sh --url https://github.com/goszpeti/WeatherAirQualityDevice --token <TOKEN>
# Create the runner and start the configuration experience

sudo ./svc.sh install
sudo ./svc.sh start
sudo reboot
