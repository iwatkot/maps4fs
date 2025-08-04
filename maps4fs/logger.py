"""This module contains the Logger class for logging to the file and stdout."""

import logging
import sys
from typing import Literal

LOGGER_NAME = "maps4fs"


class Logger(logging.Logger):
    """Handles logging to stdout with timestamps."""

    def __init__(
        self,
        level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO",
        to_stdout: bool = True,
    ):
        super().__init__(LOGGER_NAME)
        self.setLevel(level)
        self.stdout_handler = logging.StreamHandler(sys.stdout)
        formatter = "%(name)s | %(levelname)s | %(asctime)s | %(message)s"
        self.fmt = formatter
        self.stdout_handler.setFormatter(logging.Formatter(formatter))
        if to_stdout:
            self.addHandler(self.stdout_handler)
