"""This module contains provider of USGS data."""

import os
from datetime import datetime
from zipfile import ZipFile

import numpy as np
import requests

from maps4fs.generator.dtm.dtm import DTMProvider, DTMProviderSettings


class USGSProviderSettings(DTMProviderSettings):
    """Settings for the USGS provider."""

    dataset: tuple | str = (
        'Digital Elevation Model (DEM) 1 meter',
        'Alaska IFSAR 5 meter DEM',
        'National Elevation Dataset (NED) 1/9 arc-second',
        'National Elevation Dataset (NED) 1/3 arc-second',
        'National Elevation Dataset (NED) 1 arc-second',
        'National Elevation Dataset (NED) Alaska 2 arc-second',
        'Original Product Resolution (OPR) Digital Elevation Model (DEM)',
    )


class USGSProvider(DTMProvider):
    """Provider of USGS."""

    _code = "USGS"
    _name = "USGS"
    _region = "USA"
    _icon = "🇺🇸"
    _resolution = 'variable'
    _data: np.ndarray | None = None
    _settings = USGSProviderSettings
    _author = "[ZenJakey](https://github.com/ZenJakey)"
    _contributors = "[kbrandwijk](https://github.com/kbrandwijk)"
    _is_community = True
    _instructions = None

    _url = (
        "https://tnmaccess.nationalmap.gov/api/v1/products?prodFormats=GeoTIFF,IMG"

    )

    def download_tiles(self):
        download_urls = self.get_download_urls()
        all_tif_files = self.download_tif_files(download_urls)
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
        urls = []
        try:
            # Make the GET request
            (north, south, east, west) = self.get_bbox()
            response = requests.get(  # pylint: disable=W3101
                self.url  # type: ignore
                + f"&datasets={self.user_settings.dataset}"  # type: ignore
                + f"&bbox={west},{north},{east},{south}"
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

    def download_tif_files(self, urls: list[str]) -> list[str]:
        """Download GeoTIFF files from the given URLs.

        Arguments:
            urls (list): List of URLs to download GeoTIFF files from.

        Returns:
            list: List of paths to the downloaded GeoTIFF files.
        """
        tif_files = []
        for url in urls:
            file_name = os.path.basename(url)
            self.logger.debug("Retrieving TIFF: %s", file_name)
            file_path = os.path.join(self.shared_tiff_path, file_name)
            if not os.path.exists(file_path):
                try:
                    # Send a GET request to the file URL
                    response = requests.get(url, stream=True)  # pylint: disable=W3101
                    response.raise_for_status()  # Raise an error for HTTP status codes 4xx/5xx

                    # Write the content of the response to the file
                    with open(file_path, "wb") as file:
                        for chunk in response.iter_content(chunk_size=8192):  # Download in chunks
                            file.write(chunk)
                    self.logger.info("File downloaded successfully: %s", file_path)
                    if file_name.endswith('.zip'):
                        with ZipFile(file_path, "r") as f_in:
                            f_in.extract(file_name.replace('.zip', '.img'), self.shared_tiff_path)
                        tif_files.append(file_path.replace('.zip', '.img'))
                    else:
                        tif_files.append(file_path)
                except requests.exceptions.RequestException as e:
                    self.logger.error("Failed to download file: %s", e)
            else:
                self.logger.debug("File already exists: %s", file_name)
                if file_name.endswith('.zip'):
                    if not os.path.exists(file_path.replace('.zip', '.img')):
                        with ZipFile(file_path, "r") as f_in:
                            f_in.extract(file_name.replace('.zip', '.img'), self.shared_tiff_path)
                    tif_files.append(file_path.replace('.zip', '.img'))
                else:
                    tif_files.append(file_path)

        return tif_files
