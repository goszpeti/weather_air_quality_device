from configparser import ConfigParser
from datetime import datetime
import os
from pathlib import Path
from typing import List, Optional, Tuple
from waqd.base.logger import Logger
from waqd import LOCAL_TIMEZONE


# setup client:
#
#

# TODO get default token from .influxdbv2 config
# TODO set http bind-address = "127.0.0.1:8088" to only expose on localhost
# config.yml in cwd for database
# You can generate an API token from the "API Tokens Tab" in the UI
org = "waqd-local"
bucket = "waqd-test"


class InfluxSensorLogger():
    _token = ""
    _enabled = True
    _initialized = False
    """ Emulate Logger class with info to log and get_sensor_values"""

    @classmethod
    def __init__(cls):
        if not cls._enabled or cls._initialized:
            return
        config_file = Path().home() / ".influxdbv2" / "configs"
        if not config_file.is_file():
            cls.setup_db()
        parser = ConfigParser()
        try:
            parser.read(config_file)
            default_entry = parser["default"]
            org = default_entry.get("org").replace('"', "")
            assert org == 'waqd-local'
            assert default_entry.get("active") == "true"
            cls._token = default_entry.get("token").replace('"', "")
        except Exception as e:
            Logger().error(f"SensorDB: {str(e)}")
            cls._enabled = False
            return
        # Try bucket

        from influxdb_client import InfluxDBClient
        with InfluxDBClient(url="http://localhost:8086", token=cls._token, org=org) as client:
            try:
                if not client.buckets_api().find_bucket_by_name(bucket):
                    client.buckets_api().create_bucket(bucket)
            except Exception as e:
                Logger().error(f"SensorDB: {str(e)}")
                cls._enabled = False
        cls._initialized = True

    @staticmethod
    def setup_db():
        os.system(
            "influx setup -org waqd-local --bucket waqd-test --username waqd-local-user --password ExAmPl3PA55W0rD --force")
# influx auth create - -org waqd-local - -all-access

    @classmethod
    def set_value(cls, sensor_location: str, sensor_type: str, value: Optional[float], time=None):
        if not cls._enabled:
            return
        if value is None:
            return
        if time is None:
            time = datetime.now(LOCAL_TIMEZONE)
        from influxdb_client import InfluxDBClient, Point, WritePrecision
        from influxdb_client.client.write_api import SYNCHRONOUS
        with InfluxDBClient(url="http://localhost:8086", token=cls._token, org=org) as client:
            write_api = client.write_api(write_options=SYNCHRONOUS)
            point = Point("air_quality") \
                .tag("type", sensor_location) \
                .field(sensor_type, float(value)) \
                .time(time, WritePrecision.S)
            try:
                write_api.write(bucket, org, point)
            except Exception as e:
                Logger().error(f"SensorDB: {str(e)}")
            write_api.close()

    @classmethod
    def get_sensor_values(cls, sensor_location: str, sensor_type: str, minutes_to_read: int = 180, last_value=False) -> List[Tuple[datetime, float]]:
        # zero reads the last value
        if not cls._enabled:
            return []
        tables = None
        try:
            from influxdb_client import InfluxDBClient
            with InfluxDBClient(url="http://localhost:8086", token=cls._token, org=org) as client:
                filter_expression = f"range(start: -{str(minutes_to_read)}m)"
                if last_value:
                    filter_expression += " |> last()"
                query = f'from(bucket: "{bucket}") |> {filter_expression}' \
                    f'|> filter(fn: (r) => r["type"] == "{sensor_location}")' \
                    f'|> filter(fn: (r) => r["_field"] == "{sensor_type}")' \
                    '|> filter(fn: (r) => r["_measurement"] == "air_quality")'
                tables = client.query_api().query(query, org=org)
        except Exception as e:
            Logger().error(f"Error while quering {sensor_location} {sensor_type} from InfluxDB: {str(e)}")
            return []
        time_value_pairs: List[Tuple[datetime, float]] = []
        for table in tables:
            for record in table.records:
                time_value_pairs.append((record.get_time(), float(record.get_value())))

        return time_value_pairs
