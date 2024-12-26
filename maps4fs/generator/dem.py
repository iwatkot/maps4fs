"""This module contains DEM class for processing Digital Elevation Model data."""

import gzip
import math
import os
import shutil

import cv2
import numpy as np
import rasterio  # type: ignore
import requests
from pympler import asizeof  # type: ignore

from maps4fs.generator.component import Component

SRTM = "https://elevation-tiles-prod.s3.amazonaws.com/skadi/{latitude_band}/{tile_name}.hgt.gz"


# pylint: disable=R0903, R0902
class DEM(Component):
    """Component for processing Digital Elevation Model data.

    Arguments:
        game (Game): The game instance for which the map is generated.
        coordinates (tuple[float, float]): The latitude and longitude of the center of the map.
        map_size (int): The size of the map in pixels.
        map_rotated_size (int): The size of the map in pixels after rotation.
        rotation (int): The rotation angle of the map.
        map_directory (str): The directory where the map files are stored.
        logger (Any, optional): The logger to use. Must have at least three basic methods: debug,
            info, warning. If not provided, default logging will be used.
    """

    def preprocess(self) -> None:
        self._dem_path = self.game.dem_file_path(self.map_directory)
        self.temp_dir = "temp"
        self.hgt_dir = os.path.join(self.temp_dir, "hgt")
        self.gz_dir = os.path.join(self.temp_dir, "gz")
        os.makedirs(self.hgt_dir, exist_ok=True)
        os.makedirs(self.gz_dir, exist_ok=True)

        self.logger.debug("Map size: %s x %s.", self.map_size, self.map_size)
        self.logger.debug(
            "Map rotated size: %s x %s.", self.map_rotated_size, self.map_rotated_size
        )

        self.output_resolution = self.get_output_resolution()
        self.logger.debug("Output resolution for DEM data: %s.", self.output_resolution)

        blur_radius = self.map.dem_settings.blur_radius
        if blur_radius is None or blur_radius <= 0:
            # We'll disable blur if the radius is 0 or negative.
            blur_radius = 0
        elif blur_radius % 2 == 0:
            blur_radius += 1
        self.blur_radius = blur_radius
        self.multiplier = self.map.dem_settings.multiplier
        self.logger.debug(
            "DEM value multiplier is %s, blur radius is %s.",
            self.multiplier,
            self.blur_radius,
        )

        self.auto_process = self.map.dem_settings.auto_process

    @property
    def dem_path(self) -> str:
        """Returns path to the DEM file.

        Returns:
            str: Path to the DEM file.
        """
        return self._dem_path

    # pylint: disable=W0201
    def set_dem_path(self, dem_path: str) -> None:
        """Set path to the DEM file.

        Arguments:
            dem_path (str): Path to the DEM file.
        """
        self._dem_path = dem_path

    # pylint: disable=W0201
    def set_output_resolution(self, output_resolution: tuple[int, int]) -> None:
        """Set output resolution for DEM data (width, height).

        Arguments:
            output_resolution (tuple[int, int]): Output resolution for DEM data.
        """
        self.output_resolution = output_resolution

    def get_output_resolution(self, use_original: bool = False) -> tuple[int, int]:
        """Get output resolution for DEM data.

        Arguments:
            use_original (bool, optional): If True, will use original map size. Defaults to False.

        Returns:
            tuple[int, int]: Output resolution for DEM data.
        """
        map_size = self.map_size if use_original else self.map_rotated_size

        dem_size = int((map_size / 2) * self.game.dem_multipliyer)

        self.logger.debug(
            "DEM size multiplier is %s, DEM size: %sx%s, use original: %s.",
            self.game.dem_multipliyer,
            dem_size,
            dem_size,
            use_original,
        )
        return dem_size, dem_size

    def to_ground(self, data: np.ndarray) -> np.ndarray:
        """Receives the signed 16-bit integer array and converts it to the ground level.
        If the min value is negative, it will become zero value and the rest of the values
        will be shifted accordingly.
        """
        # For examlem, min value was -50, it will become 0 and for all values we'll +50.

        if data.min() < 0:
            self.logger.debug("Array contains negative values, will be shifted to the ground.")
            data = data + abs(data.min())

        self.logger.debug(
            "Array was shifted to the ground. Min: %s, max: %s.", data.min(), data.max()
        )
        return data

    # pylint: disable=no-member
    def process(self) -> None:
        """Reads SRTM file, crops it to map size, normalizes and blurs it,
        saves to map directory."""
        north, south, east, west = self.bbox

        dem_output_resolution = self.output_resolution
        self.logger.debug("DEM output resolution: %s.", dem_output_resolution)

        tile_path = self._srtm_tile()
        if not tile_path:
            self.logger.warning("Tile was not downloaded, DEM file will be filled with zeros.")
            self._save_empty_dem(dem_output_resolution)
            return

        with rasterio.open(tile_path) as src:
            self.logger.debug("Opened tile, shape: %s, dtype: %s.", src.shape, src.dtypes[0])
            window = rasterio.windows.from_bounds(west, south, east, north, src.transform)
            self.logger.debug(
                "Window parameters. Column offset: %s, row offset: %s, width: %s, height: %s.",
                window.col_off,
                window.row_off,
                window.width,
                window.height,
            )
            data = src.read(1, window=window)

        if not data.size > 0:
            self.logger.warning("DEM data is empty, DEM file will be filled with zeros.")
            self._save_empty_dem(dem_output_resolution)
            return

        self.logger.debug(
            "DEM data was read from SRTM file. Shape: %s, dtype: %s. Min: %s, max: %s.",
            data.shape,
            data.dtype,
            data.min(),
            data.max(),
        )

        data = self.to_ground(data)

        resampled_data = cv2.resize(
            data, dem_output_resolution, interpolation=cv2.INTER_LINEAR
        ).astype("uint16")

        size_of_resampled_data = asizeof.asizeof(resampled_data) / 1024 / 1024
        self.logger.debug("Size of resampled data: %s MB.", size_of_resampled_data)

        self.logger.debug(
            "Maximum value in resampled data: %s, minimum value: %s. Data type: %s.",
            resampled_data.max(),
            resampled_data.min(),
            resampled_data.dtype,
        )

        if self.auto_process:
            self.logger.debug("Auto processing is enabled, will normalize DEM data.")
            resampled_data = self._normalize_dem(resampled_data)
        else:
            self.logger.debug("Auto processing is disabled, DEM data will not be normalized.")
            resampled_data = resampled_data * self.multiplier

            self.logger.debug(
                "DEM data was multiplied by %s. Min: %s, max: %s. Data type: %s.",
                self.multiplier,
                resampled_data.min(),
                resampled_data.max(),
                resampled_data.dtype,
            )

            size_of_resampled_data = asizeof.asizeof(resampled_data) / 1024 / 1024
            self.logger.debug("Size of resampled data: %s MB.", size_of_resampled_data)

            # Clip values to 16-bit unsigned integer range.
            resampled_data = np.clip(resampled_data, 0, 65535)
            resampled_data = resampled_data.astype("uint16")
            self.logger.debug(
                "DEM data was multiplied by %s and clipped to 16-bit unsigned integer range. "
                "Min: %s, max: %s.",
                self.multiplier,
                resampled_data.min(),
                resampled_data.max(),
            )

        self.logger.debug(
            "DEM data was resampled. Shape: %s, dtype: %s. Min: %s, max: %s.",
            resampled_data.shape,
            resampled_data.dtype,
            resampled_data.min(),
            resampled_data.max(),
        )

        if self.blur_radius > 0:
            resampled_data = cv2.GaussianBlur(
                resampled_data, (self.blur_radius, self.blur_radius), sigmaX=40, sigmaY=40
            )
            self.logger.debug(
                "Gaussion blur applied to DEM data with kernel size %s.",
                self.blur_radius,
            )

        self.logger.debug(
            "DEM data was blurred. Shape: %s, dtype: %s. Min: %s, max: %s.",
            resampled_data.shape,
            resampled_data.dtype,
            resampled_data.min(),
            resampled_data.max(),
        )

        if self.map.dem_settings.plateau:
            # Plateau is a flat area with a constant height.
            # So we just add this value to each pixel of the DEM.
            # And also need to ensure that there will be no values with height greater than
            # it's allowed in 16-bit unsigned integer.

            resampled_data += self.map.dem_settings.plateau
            resampled_data = np.clip(resampled_data, 0, 65535)

            self.logger.debug(
                "Plateau with height %s was added to DEM data. Min: %s, max: %s.",
                self.map.dem_settings.plateau,
                resampled_data.min(),
                resampled_data.max(),
            )

        cv2.imwrite(self._dem_path, resampled_data)
        self.logger.debug("DEM data was saved to %s.", self._dem_path)

        if self.rotation:
            self.rotate_dem()

    def rotate_dem(self) -> None:
        """Rotate DEM image."""
        self.logger.debug("Rotating DEM image by %s degrees.", self.rotation)
        output_width, output_height = self.get_output_resolution(use_original=True)

        self.logger.debug(
            "Output resolution for rotated DEM: %s x %s.", output_width, output_height
        )

        self.rotate_image(
            self._dem_path,
            self.rotation,
            output_height=output_height,
            output_width=output_width,
        )

    def _tile_info(self, lat: float, lon: float) -> tuple[str, str]:
        """Returns latitude band and tile name for SRTM tile from coordinates.

        Arguments:
            lat (float): Latitude.
            lon (float): Longitude.

        Returns:
            tuple[str, str]: Latitude band and tile name.
        """
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
        return latitude_band, tile_name

    def _download_tile(self) -> str | None:
        """Downloads SRTM tile from Amazon S3 using coordinates.

        Returns:
            str: Path to compressed tile or None if download failed.
        """
        latitude_band, tile_name = self._tile_info(*self.coordinates)
        compressed_file_path = os.path.join(self.gz_dir, f"{tile_name}.hgt.gz")
        url = SRTM.format(latitude_band=latitude_band, tile_name=tile_name)
        self.logger.debug("Trying to get response from %s...", url)
        response = requests.get(url, stream=True, timeout=10)

        if response.status_code == 200:
            self.logger.debug("Response received. Saving to %s...", compressed_file_path)
            with open(compressed_file_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            self.logger.debug("Compressed tile successfully downloaded.")
        else:
            self.logger.error("Response was failed with status code %s.", response.status_code)
            return None

        return compressed_file_path

    def _srtm_tile(self) -> str | None:
        """Determines SRTM tile name from coordinates downloads it if necessary, and decompresses.

        Returns:
            str: Path to decompressed tile or None if download failed.
        """
        latitude_band, tile_name = self._tile_info(*self.coordinates)
        self.logger.debug("SRTM tile name %s from latitude band %s.", tile_name, latitude_band)

        decompressed_file_path = os.path.join(self.hgt_dir, f"{tile_name}.hgt")
        if os.path.isfile(decompressed_file_path):
            self.logger.debug(
                "Decompressed tile already exists: %s, skipping download.",
                decompressed_file_path,
            )
            return decompressed_file_path

        compressed_file_path = self._download_tile()
        if not compressed_file_path:
            self.logger.error("Download from SRTM failed, DEM file will be filled with zeros.")
            return None
        with gzip.open(compressed_file_path, "rb") as f_in:
            with open(decompressed_file_path, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)
        self.logger.debug("Tile decompressed to %s.", decompressed_file_path)
        return decompressed_file_path

    def _save_empty_dem(self, dem_output_resolution: tuple[int, int]) -> None:
        """Saves empty DEM file filled with zeros."""
        dem_data = np.zeros(dem_output_resolution, dtype="uint16")
        cv2.imwrite(self._dem_path, dem_data)
        self.logger.warning("DEM data filled with zeros and saved to %s.", self._dem_path)

    def previews(self) -> list:
        """This component does not have previews, returns empty list.

        Returns:
            list: Empty list.
        """
        return []

    def _get_scaling_factor(self, maximum_deviation: int) -> float:
        """Calculate scaling factor for DEM data normalization.
        NOTE: Needs reconsideration for the implementation.

        Arguments:
            maximum_deviation (int): Maximum deviation in DEM data.

        Returns:
            float: Scaling factor for DEM data normalization.
        """
        ESTIMATED_MAXIMUM_DEVIATION = 1000  # pylint: disable=C0103
        scaling_factor = maximum_deviation / ESTIMATED_MAXIMUM_DEVIATION
        return scaling_factor if scaling_factor < 1 else 1

    def _normalize_dem(self, data: np.ndarray) -> np.ndarray:
        """Normalize DEM data to 16-bit unsigned integer using max height from settings.
        Arguments:
            data (np.ndarray): DEM data from SRTM file after cropping.
        Returns:
            np.ndarray: Normalized DEM data.
        """
        self.logger.debug("Starting DEM data normalization.")
        # Calculate the difference between the maximum and minimum values in the DEM data.

        max_height = data.max()
        min_height = data.min()
        max_dev = max_height - min_height
        self.logger.debug(
            "Maximum deviation: %s with maximum at %s and minimum at %s.",
            max_dev,
            max_height,
            min_height,
        )

        scaling_factor = self._get_scaling_factor(max_dev)
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
