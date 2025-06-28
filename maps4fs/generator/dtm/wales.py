"""This module contains provider of Wales data."""

import os
from math import floor, ceil

import requests
from pyproj import Transformer

from maps4fs.generator.dtm.dtm import DTMProvider


class WalesProvider(DTMProvider):
    """Provider of Wales data."""

    _code = "wales"
    _name = "Wales 1M"
    _region = "UK"
    _icon = "🏴󠁧󠁢󠁷󠁬󠁳󠁿󠁧󠁢󠁷󠁬󠁳󠁿"
    _resolution = 1
    _author = "[garnshared](https://github.com/garnshared)"
    _is_community = True
    _instructions = None
    _is_base = False
    _extents = [(55.87708724246775, 49.85060473351981, 2.0842821419111135, -7.104775741839742)]

    _url = "https://datamap.gov.wales/geoserver/ows"  # pylint: disable=line-too-long
    _wms_version = "1.1.1"
    _source_crs = "EPSG:27700"
    _size = 1000

    def download_tiles(self):
        download_urls = self.get_download_urls()
        all_tif_files = self.download_tif_files(download_urls, self.shared_tiff_path)
        return all_tif_files

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.shared_tiff_path = os.path.join(self._tile_directory, "shared")
        os.makedirs(self.shared_tiff_path, exist_ok=True)

    def get_download_urls(self) -> list[str]:
        """Get download URLs of the GeoTIFF files from the tile catalogue.

        Returns:
            list: List of download URLs.
        """
        urls = []

        transformer = Transformer.from_crs("EPSG:4326", "EPSG:27700", always_xy=True)


        # Make the GET request
        north, south, east, west = self.get_bbox()

        # Transform the coordinates
        west_transformed, south_transformed = transformer.transform(west, south)
        east_transformed, north_transformed = transformer.transform(east, north)

        # Helper function to snap coordinate to nearest 1000 grid
        def snap_to_grid(value, func):
            return int(func(value * 0.001) * 1000)

        # Snap bounding box coordinates to a 1000-unit grid
        x_min = snap_to_grid(west_transformed, floor)
        y_min = snap_to_grid(south_transformed, floor)
        x_max = snap_to_grid(east_transformed, ceil)
        y_max = snap_to_grid(north_transformed, ceil)

        # Calculate the number of tiles in x and y directions
        x_tiles = abs(x_max - x_min) // 1000
        y_tiles = abs(y_max - y_min) // 1000


        for x_tile in range(x_tiles):
            for y_tile in range(y_tiles):
                b_west = x_min + 1000 * (x_tile + 1) - 855
                b_south = y_min + 1000 * (y_tile + 1) - 855
                b_east = b_west + 145
                b_north = b_south + 145

                try:
                    params = {
                        "service": "WMS",
                        "version": self._wms_version,
                        "request": "GetFeatureInfo",
                        "exceptions": "application/json",
                        "layers": "geonode:welsh_government_lidar_tile_catalogue_2020_2023",
                        "query_layers": "geonode:welsh_government_lidar_tile_catalogue_2020_2023",
                        "styles": "",
                        "x": 51,
                        "y": 51,
                        "height": 101,
                        "width": 101,
                        "srs": self._source_crs,
                        "bbox": f"{b_west},{b_south},{b_east},{b_north}",
                        "feature_count": 10,
                        "info_format": "application/json",
                        "ENV": "mapstore_language:en"
                    }

                    response = requests.get(# pylint: disable=W3101
                        self.url,  # type: ignore
                        params=params,  # type: ignore
                        timeout=60
                    )

                    self.logger.debug("Getting file locations from Welsh Government WMS GetFeatureInfo...")

                    # Check if the request was successful (HTTP status code 200)
                    if response.status_code == 200:
                        json_data = response.json()
                        features = json_data.get("features", [])
                        for feature in features:
                            dtm_link = feature.get("properties", {}).get("dtm_link")
                            if dtm_link:
                                urls.append("https://"+dtm_link)
                    else:
                        self.logger.error("Failed to get data. HTTP Status Code: %s", response.status_code)
                except Exception as e:
                    self.logger.error("Failed to get data. Error: %s", e)

        self.logger.debug("Received %s urls", len(urls))
        return urls
