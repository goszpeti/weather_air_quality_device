import logging
import sys

# import multiprocessing_logging

from piweather.config import DEBUG_LEVEL, PROG_NAME, base_path


class Logger(logging.Logger):
    """
    Singleton instance for the global dual logger (file/console)
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            # the user excepts a logger
            cls._instance = cls._init_logger()
        return cls._instance

    @staticmethod
    def _init_logger() -> logging.Logger:
        """ Set up format and a debug level and register loggers. """
        # restrict root logger
        root = logging.getLogger()
        root.setLevel(logging.ERROR)

        # set up file logger - log everything in file and stdio
        logger = logging.getLogger(PROG_NAME)
        logger.setLevel(logging.DEBUG)
        log_debug_level = logging.INFO
        if DEBUG_LEVEL > 0:
            log_debug_level = logging.DEBUG

        file_handler = logging.FileHandler(str(base_path / "piweather.log"), encoding="utf-8")
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

        # start logger for multiprocess compatibility / DOES NOT WORK IN WINDOWS
        # TODO: Currently unused
        # multiprocessing_logging.install_mp_handler(logger)
        return logger
