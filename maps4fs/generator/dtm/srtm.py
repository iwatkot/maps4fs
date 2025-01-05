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

    easy_mode: bool = True
    power_factor: int = 0


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
        "ℹ️ If you don't know how to work with DEM data, it is recommended to use the "
        "**Easy mode** option. It will automatically change the values in the image, so the "
        "terrain will be visible in the Giants Editor. If you're an experienced modder, it's "
        "recommended to disable this option and work with the DEM data in a usual way.  \n"
        "ℹ️ If the terrain height difference in the real world is bigger than 255 meters, "
        "the [Height scale](https://github.com/iwatkot/maps4fs/blob/main/docs/dem.md#height-scale)"
        " parameter in the **map.i3d** file will be changed automatically.  \n"
        "⚡ If the **Easy mode** option is disabled, you will probably get completely flat "
        "terrain, unless you adjust the DEM Multiplier Setting or the Height scale parameter in "
        "the Giants Editor.  \n"
        "💡 You can use the **Power factor** setting to make the difference between heights "
        "bigger. Be extremely careful with this setting, and use only low values, otherwise your "
        "terrain may be completely broken.  \n"
    )

    _settings = SRTM30ProviderSettings

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hgt_directory = os.path.join(self._tile_directory, "hgt")
        self.gz_directory = os.path.join(self._tile_directory, "gz")
        os.makedirs(self.hgt_directory, exist_ok=True)
        os.makedirs(self.gz_directory, exist_ok=True)
        self.data_info: dict[str, int | str | float] | None = None

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

        self.data_info = {}
        self.add_numpy_params(data, "original")

        data = self.signed_to_unsigned(data)
        self.add_numpy_params(data, "grounded")

        original_deviation = self.data_info["original_deviation"]
        in_game_maximum_height = 65535 // 255
        if original_deviation > in_game_maximum_height:
            suggested_height_scale_multiplier = original_deviation / in_game_maximum_height
            suggested_height_scale_value = int(255 * suggested_height_scale_multiplier)
        else:
            suggested_height_scale_multiplier = 1
            suggested_height_scale_value = 255

        self.data_info["suggested_height_scale_multiplier"] = suggested_height_scale_multiplier
        self.data_info["suggested_height_scale_value"] = suggested_height_scale_value

        self.map.shared_settings.height_scale_multiplier = suggested_height_scale_multiplier
        self.map.shared_settings.height_scale_value = suggested_height_scale_value

        if self.user_settings.easy_mode:  # type: ignore
            try:
                data = self.normalize_dem(data)
                self.add_numpy_params(data, "normalized")

                normalized_deviation = self.data_info["normalized_deviation"]
                z_scaling_factor = normalized_deviation / original_deviation
                self.data_info["z_scaling_factor"] = z_scaling_factor

                self.map.shared_settings.mesh_z_scaling_factor = z_scaling_factor
                self.map.shared_settings.change_height_scale = True

            except Exception as e:  # pylint: disable=W0718
                self.logger.error(
                    "Failed to normalize DEM data. Error: %s. Using original data.", e
                )

        return data

    def add_numpy_params(
        self,
        data: np.ndarray,
        prefix: str,
    ) -> None:
        """Add numpy array parameters to the data_info dictionary.

        Arguments:
            data (np.ndarray): Numpy array of the tile.
            prefix (str): Prefix for the parameters.
        """
        self.data_info[f"{prefix}_minimum_height"] = int(data.min())
        self.data_info[f"{prefix}_maximum_height"] = int(data.max())
        self.data_info[f"{prefix}_deviation"] = int(data.max() - data.min())
        self.data_info[f"{prefix}_unique_values"] = int(np.unique(data).size)

    def signed_to_unsigned(self, data: np.ndarray, add_one: bool = True) -> np.ndarray:
        """Convert signed 16-bit integer to unsigned 16-bit integer.

        Arguments:
            data (np.ndarray): DEM data from SRTM file after cropping.

        Returns:
            np.ndarray: Unsigned DEM data.
        """
        data = data - data.min()
        if add_one:
            data = data + 1
        return data.astype(np.uint16)

    def normalize_dem(self, data: np.ndarray) -> np.ndarray:
        """Normalize DEM data to 16-bit unsigned integer using max height from settings.

        Arguments:
            data (np.ndarray): DEM data from SRTM file after cropping.

        Returns:
            np.ndarray: Normalized DEM data.
        """
        maximum_height = int(data.max())
        minimum_height = int(data.min())
        deviation = maximum_height - minimum_height
        self.logger.debug(
            "Maximum height: %s. Minimum height: %s. Deviation: %s.",
            maximum_height,
            minimum_height,
            deviation,
        )
        self.logger.debug("Number of unique values in original DEM data: %s.", np.unique(data).size)

        adjusted_maximum_height = maximum_height * 255
        adjusted_maximum_height = min(adjusted_maximum_height, 65535)
        scaling_factor = adjusted_maximum_height / maximum_height
        self.logger.debug(
            "Adjusted maximum height: %s. Scaling factor: %s.",
            adjusted_maximum_height,
            scaling_factor,
        )
        # * | 1000 * 255 = 255000 or maximum real world value / 255 | 1000 / 257 = 3.89
        # * | 255000 / 65535 = 3.89
        # * | 255 * 3.89 = 991.95

        # TODO 1. Infosequence
        # TODO 2. Save original max height and max height after scaling to know z_factor scale for obj
        # TODO 3. Get maximum deviation and put it into the i3d file

        # ? Pydantic allow mutation model SharedSettings for Map

        if self.user_settings.power_factor:  # type: ignore
            power_factor = 1 + self.user_settings.power_factor / 10
            self.logger.debug(
                "Applying power factor: %s to the DEM data.",
                power_factor,
            )
            data = np.power(data, power_factor).astype(np.uint16)

        normalized_data = np.round(data * scaling_factor).astype(np.uint16)
        self.logger.debug(
            "Normalized data maximum height: %s. Minimum height: %s. Number of unique values: %s.",
            normalized_data.max(),
            normalized_data.min(),
            np.unique(normalized_data).size,
        )
        return normalized_data
