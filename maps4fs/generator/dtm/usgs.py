"""This module contains provider of USGS data."""

import os
from datetime import datetime

import numpy as np
import requests

from maps4fs.generator.dtm.dtm import DTMProvider, DTMProviderSettings


class USGSProviderSettings(DTMProviderSettings):
    """Settings for the USGS provider."""

    dataset: tuple | str = (
        "Digital Elevation Model (DEM) 1 meter",
        "Alaska IFSAR 5 meter DEM",
        "National Elevation Dataset (NED) 1/9 arc-second",
        "National Elevation Dataset (NED) 1/3 arc-second",
        "National Elevation Dataset (NED) 1 arc-second",
        "National Elevation Dataset (NED) Alaska 2 arc-second",
        "Original Product Resolution (OPR) Digital Elevation Model (DEM)",
    )


class USGSProvider(DTMProvider):
    """Provider of USGS."""

    _code = "USGS"
    _name = "USGS"
    _region = "USA"
    _icon = "🇺🇸"
    _resolution = "variable"
    _data: np.ndarray | None = None
    _settings = USGSProviderSettings
    _author = "[ZenJakey](https://github.com/ZenJakey)"
    _contributors = "[kbrandwijk](https://github.com/kbrandwijk)"
    _is_community = True
    _instructions = None
    _extents = (50.0, 17.0, -64.0, -162.0)

    _url = "https://tnmaccess.nationalmap.gov/api/v1/products?prodFormats=GeoTIFF,IMG"

    def download_tiles(self):
        download_urls = self.get_download_urls()
        all_tif_files = self.download_tif_files(download_urls, self.shared_tiff_path)
        return all_tif_files

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.shared_tiff_path = os.path.join(self._tile_directory, "shared")
        os.makedirs(self.shared_tiff_path, exist_ok=True)
        self.output_path = os.path.join(self._tile_directory, f"timestamp_{timestamp}")
        os.makedirs(self.output_path, exist_ok=True)

    def get_download_urls(self) -> list[str]:
        """Get download URLs of the GeoTIFF files from the USGS API.

        Returns:
            list: List of download URLs.
        """
        assert self.url is not None

        urls = []
        try:
            # Make the GET request
            (north, south, east, west) = self.get_bbox()
            response = requests.get(
                self.url
                + f"&datasets={self.user_settings.dataset}"  # type: ignore
                + f"&bbox={west},{north},{east},{south}",
                timeout=60,
            )
            self.logger.debug("Getting file locations from USGS...")

            # Check if the request was successful (HTTP status code 200)
            if response.status_code == 200:
                # Parse the JSON response
                json_data = response.json()
                items = json_data["items"]
                for item in items:
                    urls.append(item["downloadURL"])
                # self.download_tif_files(urls)
            else:
                self.logger.error("Failed to get data. HTTP Status Code: %s", response.status_code)
        except requests.exceptions.RequestException as e:
            self.logger.error("Failed to get data. Error: %s", e)
        self.logger.debug("Received %s urls", len(urls))
        return urls
