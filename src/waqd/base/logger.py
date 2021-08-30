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
import sys
import os
from datetime import datetime, timedelta

from typing import Optional

class Logger(logging.Logger):
    """
    Singleton instance for the global dual logger (file/console)
    """
    _instance: Optional[logging.Logger] = None

    def __new__(cls) -> logging.Logger:
        if cls._instance is None:
            # the user excepts a logger
            cls._instance = cls._init_logger()
        return cls._instance

    def __init__(self, name="", level=0) -> None:
        return None

    @staticmethod
    def _init_logger() -> logging.Logger:
        """ Set up format and a debug level and register loggers. """
        from waqd import config # can change after import

        # restrict root logger
        root = logging.getLogger()
        root.setLevel(logging.ERROR)

        # set up file logger - log everything in file and stdio
        logger = logging.getLogger(config.PROG_NAME)
        logger.setLevel(logging.DEBUG)
        log_debug_level = logging.INFO
        if config.DEBUG_LEVEL > 0:
            log_debug_level = logging.DEBUG

        # Create user config dir
        if not config.user_config_dir.exists():
            os.makedirs(config.user_config_dir)

        file_handler = logging.FileHandler(str(config.user_config_dir / "waqd.log"), encoding="utf-8")
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

    @staticmethod
    def sensor_logger(sensor_name):
        """ Logger used by sensors to store values to display in detail view """
        from waqd import config  # can change after import

        logger = logging.getLogger(sensor_name)

        # return already initalized logger when calling multiple times
        if len(logger.handlers) > 0:
            return logger

        logger.setLevel(logging.DEBUG)

        os.makedirs(config.user_config_dir / "sensor_logs", exist_ok=True)
        log_file_path = config.user_config_dir / "sensor_logs" / (sensor_name + ".log")

        # delete logs if older then 6 weeks
        if log_file_path.exists():
            created =  os.stat(str(log_file_path)).st_ctime
            file_date_time = datetime.fromtimestamp(created)
            current_date_time = datetime.now()
            if current_date_time - file_date_time > timedelta(days=5):
                os.remove(log_file_path)

        file_handler = logging.FileHandler(str(log_file_path), encoding="utf-8")
        formatter = logging.Formatter(r"%(asctime)s=%(message)s", "%Y-%m-%d %H:%M:%S")
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)
        logger.addHandler(file_handler)
        logger.propagate = False
        return logger
