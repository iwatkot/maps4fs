"""Module for performance monitoring during map generation."""

import functools
import threading
import uuid
from collections import defaultdict
from contextlib import contextmanager
from time import perf_counter
from typing import Callable, Generator

from maps4fs.generator.utils import Singleton
from maps4fs.logger import Logger

logger = Logger(name="MAPS4FS_MONITOR")

_local = threading.local()


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
