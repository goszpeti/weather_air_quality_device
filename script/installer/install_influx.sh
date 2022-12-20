
sudo systemctl status --no-pager influxdb
retVal=$?
if  [ $retVal -eq 0 ];then
    echo "InfluxDB already installed, skipping install"
    exit 0
fi

curl https://repos.influxdata.com/influxdb.key | gpg --dearmor | sudo tee /usr/share/keyrings/influxdb-archive-keyring.gpg >/dev/null
sudo tee /etc/apt/sources.list.d/influxdb.list <<< "deb [signed-by=/usr/share/keyrings/influxdb-archive-keyring.gpg] https://repos.influxdata.com/debian $(lsb_release -cs) stable"
sudo apt-get update # needed, so sources are updaed with the new key!
sudo apt-get install influxdb2 -y
sudo systemctl unmask influxdb
sudo systemctl enable influxdb
sudo systemctl start influxdb
