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
    logger.debug("STATS_HOST not set in environment")
API_TOKEN = os.getenv("API_TOKEN")
if not API_TOKEN:
    logger.debug("API_TOKEN not set in environment")


def post(endpoint: str, data: dict[str, Any]) -> dict[str, Any] | None:
    """Make a POST request to the statistics server.

    Arguments:
        endpoint (str): The endpoint to send the request to.
        data (dict[str, Any]): The data to send.

    Returns:
        dict[str, Any]: The response from the server.
    """
    if not STATS_HOST or not API_TOKEN:
        logger.info("STATS_HOST or API_TOKEN not set in environment, can't send settings.")
        return None

    headers = {"Authorization": f"Bearer {API_TOKEN}", "Content-Type": "application/json"}
    response = requests.post(endpoint, headers=headers, json=data, timeout=10)
    if response.status_code != 200:
        logger.error("Failed to send settings: %s", response.text)
        return None
    logger.info("Settings sent successfully")
    return response.json()


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


def get_main_settings(fields: list[str], limit: int | None = None) -> list[dict[str, Any]] | None:
    """Get main settings from the statistics server.

    Arguments:
        fields (list[str]): The fields to get.
        limit (int | None): The maximum number of settings to get.

    Returns:
        list[dict[str, Any]]: The settings from the server.
    """
    endpoint = f"{STATS_HOST}/get_main_settings"
    data = {"fields": fields, "limit": limit}
    result = post(endpoint, data)
    if not result:
        return None
    return result.get("settings")
