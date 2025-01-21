"""This module contains provider of Antarctic data."""

import os

import requests

from maps4fs.generator.dtm.dtm import DTMProvider


class REMAProvider(DTMProvider):
    """Provider of Antarctic data."""

    _code = "rema"
    _name = "REMA Antarctica"
    _region = "Global"
    _icon = "🌍"
    _resolution = 2
    _author = "[kbrandwijk](https://github.com/kbrandwijk)"
    _is_community = True

    _extents = (-53.5443873459092, -53.5443873459092, 179.99698443265999, -180)

    _instructions = (
        "This provider source includes 2 meter DEM data for the entire Antarctic region below 53 "
        "degrees South. The tiles are very big, around 1 GB each, so downloading and processing "
        "them can take a long time."
    )

    _url = "https://stac.pgc.umn.edu/api/v1/collections/rema-mosaics-v2.0-2m/items"

    def download_tiles(self):
        download_urls = self.get_download_urls()
        all_tif_files = self.download_tif_files(download_urls, self.shared_tiff_path)
        return all_tif_files

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.shared_tiff_path = os.path.join(self._tile_directory, "shared")
        os.makedirs(self.shared_tiff_path, exist_ok=True)

    def get_download_urls(self) -> list[str]:
        """Get download URLs of the GeoTIFF files from the OGC API.

        Returns:
            list: List of download URLs.
        """
        urls = []

        try:
            # Make the GET request
            north, south, east, west = self.get_bbox()
            print(north, south, east, west)
            response = requests.get(  # pylint: disable=W3101
                self.url,  # type: ignore
                params={
                    "bbox": f"{west},{south},{east},{north}",
                    "limit": "100",
                },
                timeout=60,
            )
            self.logger.debug("Getting file locations from REMA OGC API...")

            # Check if the request was successful (HTTP status code 200)
            if response.status_code == 200:
                # Parse the JSON response
                json_data = response.json()
                items = json_data["features"]
                for item in items:
                    urls.append(item["assets"]["dem"]["href"])
            else:
                self.logger.error("Failed to get data. HTTP Status Code: %s", response.status_code)
        except requests.exceptions.RequestException as e:
            self.logger.error("Failed to get data. Error: %s", e)
        self.logger.debug("Received %s urls", len(urls))
        return urls
