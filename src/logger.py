import logging
import os
import sys
from datetime import datetime

LOG_FORMATTER = "%(name)s | %(asctime)s | %(levelname)s | %(message)s"
working_directory = os.getcwd()
log_directory = os.path.join(working_directory, "logs")
os.makedirs(log_directory, exist_ok=True)


class Logger(logging.getLoggerClass()):
    """Handles logging to the file and stroudt with timestamps."""

    def __init__(self, name: str):
        super().__init__(name)
        self.setLevel(logging.DEBUG)
        self.stdout_handler = logging.StreamHandler(sys.stdout)
        self.file_handler = logging.FileHandler(
            filename=self.log_file(), mode="a", encoding="utf-8"
        )
        self.fmt = LOG_FORMATTER
        self.stdout_handler.setFormatter(logging.Formatter(LOG_FORMATTER))
        self.file_handler.setFormatter(logging.Formatter(LOG_FORMATTER))
        self.addHandler(self.stdout_handler)
        self.addHandler(self.file_handler)

    def log_file(self):
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = os.path.join(log_directory, f"{today}.txt")
        return log_file

    def log(self, message: str):
        return self.info(message)
