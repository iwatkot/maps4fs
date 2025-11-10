"""Module for sending settings to the statistics server."""

import os
import threading
from typing import Any

import requests

from maps4fs.generator.monitor import Logger

logger = Logger(name="MAPS4FS.STATISTICS")

try:
    from dotenv import load_dotenv

    load_dotenv("local.env")
except Exception:
    pass

STATS_HOST = os.getenv("STATS_HOST")
if not STATS_HOST:
    logger.debug("STATS_HOST not set in environment")
API_TOKEN = os.getenv("API_TOKEN")
if not API_TOKEN:
    logger.debug("API_TOKEN not set in environment")


def post(endpoint: str, data: dict[str, Any]) -> None:
    """Make a POST request to the statistics server in a separate thread.

    Arguments:
        endpoint (str): The endpoint to send the request to.
        data (dict[str, Any]): The data to send.
    """

    def _post_thread():
        try:
            if not STATS_HOST or not API_TOKEN:
                logger.debug("STATS_HOST or API_TOKEN not set in environment, can't send settings.")
                return

            headers = {"Authorization": f"Bearer {API_TOKEN}", "Content-Type": "application/json"}
            response = requests.post(endpoint, headers=headers, json=data, timeout=10)
            if response.status_code != 200:
                logger.warning("Failed to send settings: %s", response.text)
                return
            logger.debug("Settings sent successfully")
        except Exception as e:
            logger.warning("Error while trying to send settings: %s", e)

    # Use non-daemon thread and wait for completion to ensure critical data is sent
    thread = threading.Thread(target=_post_thread, daemon=False)
    thread.start()
    # Wait up to 15 seconds for the request to complete
    thread.join(timeout=15)

    # If thread is still alive, log a warning but don't block
    if thread.is_alive():
        logger.warning("Statistics request taking longer than expected, continuing without waiting")


def send_main_settings(data: dict[str, Any]) -> None:
    """Send main settings to the statistics server.

    Arguments:
        data (dict[str, Any]): The main settings to send.
    """
    endpoint = f"{STATS_HOST}/receive_main_settings"
    post(endpoint, data)


def send_advanced_settings(data: dict[str, Any]) -> None:
    """Send advanced settings to the statistics server.

    Arguments:
        data (dict[str, Any]): The advanced settings to send.
    """
    endpoint = f"{STATS_HOST}/receive_advanced_settings"
    post(endpoint, data)


def send_survey(data: dict[str, Any]) -> None:
    """Send survey data to the statistics server.

    Arguments:
        data (dict[str, Any]): The survey data to send.
    """
    endpoint = f"{STATS_HOST}/receive_survey"
    post(endpoint, data)


def send_performance_report(data: dict[str, Any]) -> None:
    """Send performance report to the statistics server.

    Arguments:
        data (dict[str, Any]): The performance report data to send.
    """
    endpoint = f"{STATS_HOST}/receive_performance_report"
    post(endpoint, data)
