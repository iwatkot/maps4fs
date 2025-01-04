"""This module contains provider of Shuttle Radar Topography Mission (SRTM) 30m data."""

# Author: https://github.com/iwatkot

import gzip
import math
import os
import shutil

import numpy as np

from maps4fs.generator.dtm.dtm import DTMProvider, DTMProviderSettings


class SRTM30ProviderSettings(DTMProviderSettings):
    """Settings for SRTM 30m provider."""

    normalize_data: bool = True
    expected_maximum_height: int = 200


class SRTM30Provider(DTMProvider):
    """Provider of Shuttle Radar Topography Mission (SRTM) 30m data."""

    _code = "srtm30"
    _name = "SRTM 30 m"
    _region = "Global"
    _icon = "🌎"
    _resolution = 30.0

    _url = "https://elevation-tiles-prod.s3.amazonaws.com/skadi/{latitude_band}/{tile_name}.hgt.gz"

    _author = "[iwatkot](https://github.com/iwatkot)"

    _instructions = (
        "ℹ️ If you want the data to be normalized to a specific maximum height, "
        "check the **Normalize data** checkbox and enter the **Expected maximum height** in "
        "meters. The expected maximum height is a maximum height of the terrain in meters in "
        "real world. It is not necessary it should be very "
        "precise, just an approximate value. If you want to receive the DEM data in an original "
        "format, where pixel values will be in meters, uncheck the **Normalize data** checkbox. "
        "Note, that if you disable the normalization, you probably get completely flat terrain "
        "and you need to adjust the height scale paramter in the Giants Editor."
    )

    _settings = SRTM30ProviderSettings

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hgt_directory = os.path.join(self._tile_directory, "hgt")
        self.gz_directory = os.path.join(self._tile_directory, "gz")
        os.makedirs(self.hgt_directory, exist_ok=True)
        os.makedirs(self.gz_directory, exist_ok=True)

    def get_tile_parameters(self, *args, **kwargs) -> dict[str, str]:
        """Returns latitude band and tile name for SRTM tile from coordinates.

        Arguments:
            lat (float): Latitude.
            lon (float): Longitude.

        Returns:
            dict: Tile parameters.
        """
        lat, lon = args

        tile_latitude = math.floor(lat)
        tile_longitude = math.floor(lon)

        latitude_band = f"N{abs(tile_latitude):02d}" if lat >= 0 else f"S{abs(tile_latitude):02d}"
        if lon < 0:
            tile_name = f"{latitude_band}W{abs(tile_longitude):03d}"
        else:
            tile_name = f"{latitude_band}E{abs(tile_longitude):03d}"

        self.logger.debug(
            "Detected tile name: %s for coordinates: lat %s, lon %s.", tile_name, lat, lon
        )
        return {"latitude_band": latitude_band, "tile_name": tile_name}

    def get_numpy(self) -> np.ndarray:
        """Get numpy array of the tile.

        Returns:
            np.ndarray: Numpy array of the tile.
        """
        tile_parameters = self.get_tile_parameters(*self.coordinates)
        tile_name = tile_parameters["tile_name"]
        decompressed_tile_path = os.path.join(self.hgt_directory, f"{tile_name}.hgt")

        if not os.path.isfile(decompressed_tile_path):
            compressed_tile_path = os.path.join(self.gz_directory, f"{tile_name}.hgt.gz")
            if not self.get_or_download_tile(compressed_tile_path, **tile_parameters):
                raise FileNotFoundError(f"Tile {tile_name} not found.")

            with gzip.open(compressed_tile_path, "rb") as f_in:
                with open(decompressed_tile_path, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)

        data = self.extract_roi(decompressed_tile_path)

        if (
            self.user_settings.normalize_data  # type: ignore
            and self.user_settings.expected_maximum_height  # type: ignore
        ):
            try:
                data = self.normalize_dem(
                    data, self.user_settings.expected_maximum_height  # type: ignore
                )
            except Exception as e:  # pylint: disable=W0718
                self.logger.error(
                    "Failed to normalize DEM data. Error: %s. Using original data.", e
                )

        return data

    def normalize_dem(self, data: np.ndarray, max_height: int) -> np.ndarray:
        """Normalize DEM data to 16-bit unsigned integer using max height from settings.

        Args:
            data (np.ndarray): DEM data from SRTM file after cropping.

        Returns:
            np.ndarray: Normalized DEM data.
        """
        max_dev = data.max() - data.min()
        scaling_factor = max_dev / max_height if max_dev < max_height else 1
        adjusted_max_height = int(65535 * scaling_factor)
        self.logger.debug(
            "Maximum deviation: %s. Scaling factor: %s. Adjusted max height: %s.",
            max_dev,
            scaling_factor,
            adjusted_max_height,
        )
        normalized_data = (
            (data - data.min()) / (data.max() - data.min()) * adjusted_max_height
        ).astype("uint16")
        self.logger.debug(
            "DEM data was normalized to %s - %s.",
            normalized_data.min(),
            normalized_data.max(),
        )
        return normalized_data
