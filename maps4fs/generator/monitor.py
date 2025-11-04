"""Module for performance monitoring during map generation."""

import functools
import logging
import os
import sys
import threading
import uuid
from collections import defaultdict
from contextlib import contextmanager
from datetime import datetime
from time import perf_counter
from typing import Callable, Generator, Literal

from maps4fs.generator.utils import Singleton

_local = threading.local()
MFS_LOG_LEVEL = "MFS_LOG_LEVEL"
SUPPORTED_LOG_LEVELS = {
    10: "DEBUG",
    20: "INFO",
    30: "WARNING",
    40: "ERROR",
}


class Logger(logging.Logger):
    """Handles logging to stdout with timestamps and session tracking."""

    def __init__(
        self,
        name: str = "MAPS4FS",
        level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO",
        **kwargs,
    ):
        log_level = os.getenv(MFS_LOG_LEVEL, level)
        if log_level not in SUPPORTED_LOG_LEVELS.values():
            log_level = "INFO"
        super().__init__(name)
        self.setLevel(level)

        # Standard stdout handler
        self.stdout_handler = logging.StreamHandler(sys.stdout)
        formatter = "%(name)s | %(levelname)s | %(asctime)s | %(message)s"
        self.fmt = formatter
        self.stdout_handler.setFormatter(logging.Formatter(formatter))
        self.addHandler(self.stdout_handler)

        # Session storage - simple dict of lists
        self.session_logs: dict[str, list[dict[str, str]]] = defaultdict(list)

    # pylint: disable=arguments-differ
    def _log(self, level: int, msg: str, args, **kwargs) -> None:  # type: ignore
        """Override _log to capture session logs."""
        super()._log(level, msg, args, **kwargs)

        try:
            session_id = get_current_session()
            if session_id:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]
                formatted_msg = msg % args if args else str(msg)
                level_name = SUPPORTED_LOG_LEVELS.get(level, "INFO")
                log_entry = {"level": level_name, "timestamp": timestamp, "message": formatted_msg}
                self.session_logs[session_id].append(log_entry)
        except Exception:
            pass

    def pop_session_logs(self, session_id: str) -> list[dict[str, str]]:
        """Pop logs for a specific session.

        Arguments:
            session_id (str): The session ID.

        Returns:
            list[dict[str, str]]: List of log entries for the session.
        """
        return self.session_logs.pop(session_id, [])


logger = Logger(name="MAPS4FS_MONITOR")


def get_current_session() -> str | None:
    """Get the current session name from thread-local storage."""
    return getattr(_local, "current_session", None)


@contextmanager
def performance_session(session_id: str | None = None) -> Generator[str, None, None]:
    """Context manager for performance monitoring session.

    Arguments:
        session_id (str, optional): Custom session ID. If None, generates UUID.
    """
    if session_id is None:
        session_id = str(uuid.uuid4())

    _local.current_session = session_id

    try:
        yield session_id
    finally:
        _local.current_session = None


class PerformanceMonitor(metaclass=Singleton):
    """Singleton class for monitoring performance metrics."""

    def __init__(self) -> None:
        self.sessions: dict[str, dict[str, dict[str, float]]] = defaultdict(
            lambda: defaultdict(lambda: defaultdict(float))
        )

    def add_record(self, session: str, component: str, function: str, time_taken: float) -> None:
        """Add a performance record.

        Arguments:
            session (str): The session name.
            component (str): The component/class name.
            function (str): The function/method name.
            time_taken (float): Time taken in seconds.
        """
        self.sessions[session][component][function] += time_taken

    def get_session_json(self, session: str) -> dict[str, dict[str, float]]:
        """Get performance data for a session in JSON-serializable format.

        Arguments:
            session (str): The session name.

        Returns:
            dict[str, dict[str, float]]: Performance data.
        """
        return self.sessions.get(session, {})


def monitor_performance(func: Callable) -> Callable:
    """Decorator to monitor performance of methods/functions.

    Arguments:
        func (callable) -- The function to be monitored.

    Returns:
        callable -- The wrapped function with performance monitoring.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if args and hasattr(args[0], "__class__"):
            class_name = args[0].__class__.__name__
        elif args and hasattr(args[0], "__name__"):
            class_name = args[0].__name__
        elif "." in func.__qualname__:
            class_name = func.__qualname__.split(".")[0]
        else:
            class_name = None

        function_name = func.__name__

        start = perf_counter()
        result = func(*args, **kwargs)
        end = perf_counter()
        time_taken = round(end - start, 5)

        session_name = get_current_session()

        try:
            if session_name and time_taken > 0.001 and class_name:
                PerformanceMonitor().add_record(session_name, class_name, function_name, time_taken)
                logger.debug(
                    "[PERFORMANCE] %s | %s | %s | %s",
                    session_name,
                    class_name,
                    function_name,
                    time_taken,
                )
        except Exception:
            pass

        return result

    return wrapper
