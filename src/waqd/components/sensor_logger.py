from datetime import datetime
from time import sleep

from influxdb_client import InfluxDBClient, Point, WritePrecision, AuthorizationsApi
from influxdb_client.client.write_api import SYNCHRONOUS
#setup client:
# influx setup -org waqd-local --bucket waqd-test --username waqd-local-user --password ExAmPl3PA55W0rD --force

# TODO Password?

# influx auth create --org waqd-local --all-access
#TODO get default token from .influxdbv2 config
# TODO set http bind-address = "127.0.0.1:8088" to only expose on localhost
# config.yml in cwd for database
# You can generate an API token from the "API Tokens Tab" in the UI
token = "SssT-lmMEUW6CRKMOHUBBPpXJwba5SJ6hYIXGssKb2GAw_qj7mCBqR42RfgmizdepCtwcSEGYRunKlYCyRzrHQ=="
org = "waqd-local"
bucket = "waqd-test"

with InfluxDBClient(url="http://localhost:8086", token=token, org=org) as client:
    write_api = client.write_api(write_options=SYNCHRONOUS)

    data = "mem,host=host1 used_percent=23.43234543"
    write_api.write(bucket, org, data)
    
    # limit sensor recording to 1 sample per minute

    for i in range(10):
        sleep(1)
        point = Point("air_quality") \
        .tag("type", "interior") \
        .field("temp_deg_c", 23.43234543+i) \
        .field("pressure_hPa", 23.43234543+i) \
            .time(datetime.utcnow(), WritePrecision.S)

    #     write_api.write(bucket, org, point)
    query = 'from(bucket: "waqd") |> range(start: -10m) |> filter(fn: (r) => r["type"] == "interior")' \
  '|> filter(fn: (r) => r["_field"] == "deg_c")' \
  '|> filter(fn: (r) => r["_measurement"] == "temp")'
    tables = client.query_api().query(query, org=org)
    for table in tables:
        for record in table.records:
            print(record)
#client.close()
