"""Module for sending settings to the statistics server."""

from __future__ import annotations

import os
import threading
from typing import Any

import requests

from maps4fs.generator.monitor import Logger

try:
    from dotenv import load_dotenv

    load_dotenv("local.env")
except Exception:
    pass


class StatisticsClient:
    """Client for sending telemetry to the statistics server.

    Credentials are read from environment variables at construction time.
    All requests are fire-and-forget daemon threads — never blocking generation.
    """

    def __init__(self) -> None:
        self._host = os.getenv("STATS_HOST")
        self._token = os.getenv("API_TOKEN")
        self._logger = Logger(name="MAPS4FS.STATISTICS")
        if not self._host:
            self._logger.debug("STATS_HOST not set in environment")
        if not self._token:
            self._logger.debug("API_TOKEN not set in environment")

    def _post(self, endpoint: str, data: dict[str, Any]) -> None:
        """Fire-and-forget POST in a daemon thread.

        Arguments:
            endpoint (str): Full URL of the endpoint.
            data (dict[str, Any]): JSON body.
        """

        def _thread() -> None:
            try:
                if not self._host or not self._token:
                    self._logger.debug("STATS_HOST or API_TOKEN not set, can't send settings.")
                    return
                headers = {
                    "Authorization": f"Bearer {self._token}",
                    "Content-Type": "application/json",
                }
                response = requests.post(endpoint, headers=headers, json=data, timeout=10)
                if response.status_code != 200:
                    self._logger.warning("Failed to send settings: %s", response.text)
                    return
                self._logger.debug("Settings sent successfully")
            except Exception as e:
                self._logger.warning("Error while trying to send settings: %s", e)

        threading.Thread(target=_thread, daemon=True).start()

    def send_main_settings(self, data: dict[str, Any]) -> None:
        """Send main settings telemetry payload.

        Arguments:
            data (dict[str, Any]): Main settings payload.
        """
        self._post(f"{self._host}/receive_main_settings", data)

    def send_advanced_settings(self, data: dict[str, Any]) -> None:
        """Send advanced settings telemetry payload.

        Arguments:
            data (dict[str, Any]): Advanced settings payload.
        """
        self._post(f"{self._host}/receive_advanced_settings", data)

    def send_survey(self, data: dict[str, Any]) -> None:
        """Send survey telemetry payload.

        Arguments:
            data (dict[str, Any]): Survey payload.
        """
        self._post(f"{self._host}/receive_survey", data)

    def send_performance_report(self, data: dict[str, Any]) -> None:
        """Send performance report telemetry payload.

        Arguments:
            data (dict[str, Any]): Performance report payload.
        """
        self._post(f"{self._host}/receive_performance_report", data)
