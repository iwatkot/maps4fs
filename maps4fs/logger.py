"""This module contains the Logger class for logging to the file and stdout."""

import logging
import os
import sys
from datetime import datetime
from logging import getLogger
from time import perf_counter
from typing import Any, Callable, Literal

LOGGER_NAME = "maps4fs"
log_directory = os.path.join(os.getcwd(), "logs")
os.makedirs(log_directory, exist_ok=True)


class Logger(logging.Logger):
    """Handles logging to the file and stroudt with timestamps."""

    def __init__(
        self,
        level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "ERROR",
        to_stdout: bool = True,
        to_file: bool = True,
    ):
        super().__init__(LOGGER_NAME)
        self.setLevel(level)
        self.stdout_handler = logging.StreamHandler(sys.stdout)
        self.file_handler = logging.FileHandler(
            filename=self.log_file(), mode="a", encoding="utf-8"
        )
        formatter = "%(name)s | %(levelname)s | %(asctime)s | %(message)s"
        self.fmt = formatter
        self.stdout_handler.setFormatter(logging.Formatter(formatter))
        self.file_handler.setFormatter(logging.Formatter(formatter))
        if to_stdout:
            self.addHandler(self.stdout_handler)
        if to_file:
            self.addHandler(self.file_handler)

    def log_file(self) -> str:
        """Returns the path to the log file.

        Returns:
            str: The path to the log file.
        """
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = os.path.join(log_directory, f"{today}.txt")
        return log_file


def timeit(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to log the time taken by a function to execute.

    Args:
        func (function): The function to be timed.

    Returns:
        function: The timed function.
    """

    def timed(*args, **kwargs):
        logger = getLogger("maps4fs")
        start = perf_counter()
        result = func(*args, **kwargs)
        end = perf_counter()
        if logger is not None:
            logger.info("Function %s took %s seconds to execute", func.__name__, end - start)
        return result

    return timed
