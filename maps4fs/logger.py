"""This module contains the Logger class for logging to the file and stdout."""

import inspect
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
        **kwargs,
    ):
        print(
            "The maps4fs.logger.Logger class is deprecated and will be removed in future versions. "
            "Switch to maps4fs.generator.monitoring.Logger instead.",
        )

        # Show detailed information from where the instantiation is happening.
        frame = inspect.currentframe()
        if frame is not None:
            caller_frame = frame.f_back
            if caller_frame is not None:
                info = inspect.getframeinfo(caller_frame)
                print(
                    f"Logger instantiated from file: {info.filename}, line: {info.lineno}, function: {info.function}"
                )

        super().__init__(kwargs.pop("name", LOGGER_NAME))
        self.setLevel(level)
        self.stdout_handler = logging.StreamHandler(sys.stdout)
        formatter = "%(name)s | %(levelname)s | %(asctime)s | %(message)s"
        self.fmt = formatter
        self.stdout_handler.setFormatter(logging.Formatter(formatter))
        if to_stdout:
            self.addHandler(self.stdout_handler)
