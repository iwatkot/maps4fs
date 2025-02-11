"""Module for sending settings to the statistics server."""

import os
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
    print("STATS_HOST not set in environment")
API_TOKEN = os.getenv("API_TOKEN")
if not API_TOKEN:
    print("API_TOKEN not set in environment")


def send_settings(endpoint: str, data: dict[str, Any]) -> None:
    """Send settings to the statistics server.

    Arguments:
        endpoint (str): The endpoint to send the settings to.
        data (dict[str, Any]): The settings to send.
    """
    headers = {"Authorization": f"Bearer {API_TOKEN}", "Content-Type": "application/json"}
    response = requests.post(endpoint, headers=headers, json=data, timeout=10)
    if response.status_code != 200:
        logger.error("Failed to send settings: %s", response.text)
    else:
        logger.info("Settings sent successfully")


def send_main_settings(data: dict[str, Any]) -> None:
    """Send main settings to the statistics server.

    Arguments:
        data (dict[str, Any]): The main settings to send.
    """
    endpoint = f"{STATS_HOST}/receive_main_settings"
    send_settings(endpoint, data)


def send_advanced_settings(data: dict[str, Any]) -> None:
    """Send advanced settings to the statistics server.

    Arguments:
        data (dict[str, Any]): The advanced settings to send.
    """
    endpoint = f"{STATS_HOST}/receive_advanced_settings"
    send_settings(endpoint, data)
