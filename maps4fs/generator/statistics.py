"""Module for sending settings to the statistics server."""

import os
import threading
from typing import Any

import requests

from maps4fs.logger import Logger

logger = Logger()

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

    thread = threading.Thread(target=_post_thread, daemon=True)
    thread.start()


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
