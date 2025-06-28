"""This module contains provider of Wales data."""

import os

import numpy as np
import rasterio
import requests

from tqdm import tqdm

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
    _source_crs = "EPSG:4326"

    def download_tiles(self):
        download_urls = self.get_download_urls()
        all_tif_files = self.download_tif_files(download_urls, self.shared_tiff_path)
        self.normalise_tif_files(all_tif_files)
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

        try:
            # Make the GET request
            north, south, east, west = self.get_bbox()

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
                "bbox": f"{west},{south},{east},{north}",
                "feature_count": 10,
                "info_format": "application/json",
                "ENV": "mapstore_language:en"
            }

            response = requests.get(# pylint: disable=W3101
                self.url,  # type: ignore
                params=params,
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
                        print(dtm_link)
            else:
                self.logger.error("Failed to get data. HTTP Status Code: %s", response.status_code)
        except Exception as e:
            self.logger.error("Failed to get data. Error: %s", e)

        self.logger.debug("Received %s urls", len(urls))
        return urls

    def normalise_tif_files(self, paths: list):
        """Normalise GeoTIFF files from the given file paths.

        Arguments:
            paths (list): List of file paths to normalise GeoTIFF files from.
        """

        for file_path in paths:
            try:
                self.logger.debug("Normalising: %s", file_path)

                with rasterio.open(file_path) as src:
                    data = src.read(1)
                    transform = src.transform
                    crs = src.crs
                    original_nodata = src.nodata
                    profile = src.profile.copy()

                # Replace original nodata with something valid
                NODATA_UINT16 = 0
                data = np.where(data == original_nodata, NODATA_UINT16, data)

                # Normalize to uint16 range
                data_min = data.min()
                data_max = data.max()
                if data_max == data_min:
                    normalized = np.zeros_like(data, dtype=np.uint16)
                else:
                    normalized = ((data - data_min) / (data_max - data_min)) * 65535
                    normalized = normalized.astype(np.uint16)

                # Ensure all necessary metadata is present
                profile.update({
                    "dtype": rasterio.uint16,
                    "transform": transform,
                    "crs": crs,
                    "nodata": NODATA_UINT16,
                    "count": 1
                })

                with rasterio.open(file_path, 'w', **profile) as dst:
                    dst.write(normalized, 1)

                self.logger.info("Successfully normalised: %s", file_path)

            except Exception as e:
                self.logger.error("Failed to normalise file: %s", e)
