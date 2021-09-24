#
# Copyright (c) 2019-2021 Péter Gosztolya & Contributors.
#
# This file is part of WAQD
# (see https://github.com/goszpeti/WeatherAirQualityDevice).
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Tuple

from file_read_backwards import FileReadBackwards
from waqd import config  # can change after import


class Logger(logging.Logger):
    """
    Singleton instance for the global dual logger (file/console)
    """
    GLOBAL_LOGFILE_NAME = "waqd.log"

    _instance: Optional[logging.Logger] = None

    def __new__(cls, name:str=config.PROG_NAME, level:int=config.DEBUG_LEVEL, output_path: Path = config.user_config_dir) -> logging.Logger:
        if cls._instance is None:
            cls._instance = cls._init_logger(output_path)
        return cls._instance

    def __init__(self, output_path: Path = config.user_config_dir) -> None:
        return None

    @classmethod
    def _init_logger(cls, output_path) -> logging.Logger:
        """ Set up format and a debug level and register loggers. """
        from waqd import config  # can change after import

        # restrict root logger
        root = logging.getLogger()
        root.setLevel(logging.ERROR)

        # set up file logger - log everything in file and stdout
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
        log_debug_level = logging.INFO
        if config.DEBUG_LEVEL > 0:
            log_debug_level = logging.DEBUG

        # Create user config dir
        if not output_path.exists():
            os.makedirs(output_path)

        file_handler = logging.FileHandler(
            str(output_path / cls.GLOBAL_LOGFILE_NAME), encoding="utf-8")
        file_handler.setLevel(log_debug_level)

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_debug_level)

        formatter = logging.Formatter(r"%(asctime)s :: %(levelname)s :: %(message)s")
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)

        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

        # otherwise messages appear twice
        logger.propagate = False

        return logger


class SensorLogger(logging.Logger):
    _instance: Optional[logging.Logger] = None

    def __new__(cls, name: str, output_path: Path = config.user_config_dir / "sensor_logs") -> logging.Logger:
        if cls._instance is None:
            # the user excepts a logger
            cls._instance = cls._init_logger(name, output_path)
        return cls._instance

    def __init__(self, name: str, output_path: Path = config.user_config_dir) -> None:
        return None

    @staticmethod
    def get_sensor_logfile_path(sensor_name) -> Path:
        logger = SensorLogger(sensor_name)
        if logger.handlers == 0:
            return Path("InvalidPath")
        try:
            filename = Path("NonExistant")
            if isinstance(logger.handlers[0], logging.FileHandler):
                filename = Path(logger.handlers[0].baseFilename) # can be any type of handler
            return filename
        except Exception as e:
            print(f"WARNING: Can't find file handler for {sensor_name} logger.")
            return Path("InvalidPath")

    @staticmethod
    # zero reads the last value
    def read_sensor_file(sensor_name: str, minutes_to_read: int = 0) -> List[Tuple[datetime, float]]:

        log_file_path = SensorLogger.get_sensor_logfile_path(sensor_name)
        if not log_file_path.exists():
            return []
        current_time = datetime.now()
        time_value_pairs: List[Tuple[datetime, float]] = []
        try:
            with FileReadBackwards(str(log_file_path), encoding="utf-8") as fp:
                # log has format 2021-03-12 18:51:16=55\n...
                for line in fp:
                    time_value_pair = line.split("=")
                    timestamp = datetime.fromisoformat(time_value_pair[0])
                    if not minutes_to_read:
                        time_value_pair[1] = float(time_value_pair[1])  # always cast to float
                        return [time_value_pair]
                    if (current_time - timestamp) > timedelta(minutes=minutes_to_read):
                        break
                    time_value_pairs.append((timestamp, float(time_value_pair[1].strip())))
        except:
            # try to delete when file is corrupted
            SensorLogger.delete_log_file(log_file_path)
        return time_value_pairs
    
    @staticmethod
    def delete_log_file(log_file_path: Path)-> bool:
        try:
            os.remove(log_file_path)
            return True
        except Exception as e:
            print(f"WARNING: Can't delete sensor logfile {log_file_path}: {str(e)}; will not log.")
            return False

    @staticmethod
    def _init_logger(sensor_name: str, output_path: Path) -> logging.Logger:
        """ Logger used by sensors to store values to display in detail view """
        from waqd import config  # can change after import

        logger = logging.getLogger(sensor_name)

        # return already initalized logger when calling multiple times
        if len(logger.handlers) > 0:
            return logger

        logger.setLevel(logging.DEBUG)

        os.makedirs(output_path, exist_ok=True)
        log_file_path = output_path / (sensor_name + ".log")

        # delete logs if older then 6 weeks
        if log_file_path.exists():
            created = os.stat(str(log_file_path)).st_ctime
            file_date_time = datetime.fromtimestamp(created)
            current_date_time = datetime.now()
            if current_date_time - file_date_time > timedelta(days=5):
                if not SensorLogger.delete_log_file(log_file_path):
                    logger.disabled = True
                    return logger

        file_handler = logging.FileHandler(str(log_file_path), encoding="utf-8")
        formatter = logging.Formatter(r"%(asctime)s=%(message)s", "%Y-%m-%d %H:%M:%S")
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)
        logger.addHandler(file_handler)
        logger.propagate = False
        return logger
