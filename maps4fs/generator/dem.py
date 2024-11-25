"""This module contains DEM class for processing Digital Elevation Model data."""

import gzip
import math
import os
import shutil

import cv2
import numpy as np
import rasterio  # type: ignore
import requests

from maps4fs.generator.component import Component

SRTM = "https://elevation-tiles-prod.s3.amazonaws.com/skadi/{latitude_band}/{tile_name}.hgt.gz"
DEFAULT_MULTIPLIER = 1
DEFAULT_BLUR_RADIUS = 35


# pylint: disable=R0903
class DEM(Component):
    """Component for processing Digital Elevation Model data.

    Args:
        coordinates (tuple[float, float]): The latitude and longitude of the center of the map.
        map_height (int): The height of the map in pixels.
        map_width (int): The width of the map in pixels.
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

        self.multiplier = self.kwargs.get("multiplier", DEFAULT_MULTIPLIER)
        blur_radius = self.kwargs.get("blur_radius", DEFAULT_BLUR_RADIUS)
        if blur_radius is None or blur_radius <= 0:
            # We'll disable blur if the radius is 0 or negative.
            blur_radius = 0
        elif blur_radius % 2 == 0:
            blur_radius += 1
        self.blur_radius = blur_radius
        self.logger.debug(
            "DEM value multiplier is %s, blur radius is %s.", self.multiplier, self.blur_radius
        )

        self.auto_process = self.kwargs.get("auto_process", False)

    @property
    def dem_path(self) -> str:
        """Returns path to the DEM file.

        Returns:
            str: Path to the DEM file.
        """
        return self._dem_path

    def get_output_resolution(self) -> tuple[int, int]:
        """Get output resolution for DEM data.

        Returns:
            tuple[int, int]: Output resolution for DEM data.
        """
        dem_height = int((self.map_height / 2) * self.game.dem_multipliyer + 1)
        dem_width = int((self.map_width / 2) * self.game.dem_multipliyer + 1)
        self.logger.debug(
            "DEM size multiplier is %s, DEM height is %s, DEM width is %s.",
            self.game.dem_multipliyer,
            dem_height,
            dem_width,
        )
        return dem_width, dem_height

    # pylint: disable=no-member
    def process(self) -> None:
        """Reads SRTM file, crops it to map size, normalizes and blurs it,
        saves to map directory."""
        north, south, east, west = self.bbox

        dem_output_resolution = self.get_output_resolution()
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

        resampled_data = cv2.resize(
            data, dem_output_resolution, interpolation=cv2.INTER_LINEAR
        ).astype("uint16")

        self.logger.debug(
            "Maximum value in resampled data: %s, minimum value: %s.",
            resampled_data.max(),
            resampled_data.min(),
        )

        if self.auto_process:
            self.logger.debug("Auto processing is enabled, will normalize DEM data.")
            resampled_data = self._normalize_dem(resampled_data)
        else:
            self.logger.debug("Auto processing is disabled, DEM data will not be normalized.")
            resampled_data = resampled_data * self.multiplier

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

        cv2.imwrite(self._dem_path, resampled_data)
        self.logger.debug("DEM data was saved to %s.", self._dem_path)

        if self.game.additional_dem_name is not None:
            self.make_copy(self.game.additional_dem_name)

    def make_copy(self, dem_name: str) -> None:
        """Copies DEM data to additional DEM file.

        Args:
            dem_name (str): Name of the additional DEM file.
        """
        dem_directory = os.path.dirname(self._dem_path)

        additional_dem_path = os.path.join(dem_directory, dem_name)

        shutil.copyfile(self._dem_path, additional_dem_path)
        self.logger.debug("Additional DEM data was copied to %s.", additional_dem_path)

    def _tile_info(self, lat: float, lon: float) -> tuple[str, str]:
        """Returns latitude band and tile name for SRTM tile from coordinates.

        Args:
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
            self.logger.info(
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
        cv2.imwrite(self._dem_path, dem_data)  # pylint: disable=no-member
        self.logger.warning("DEM data filled with zeros and saved to %s.", self._dem_path)

    def grayscale_preview(self) -> str:
        """Converts DEM image to grayscale RGB image and saves it to the map directory.
        Returns path to the preview image.

        Returns:
            str: Path to the preview image.
        """
        # rgb_dem_path = self._dem_path.replace(".png", "_grayscale.png")
        grayscale_dem_path = os.path.join(self.previews_directory, "dem_grayscale.png")

        self.logger.debug("Creating grayscale preview of DEM data in %s.", grayscale_dem_path)

        dem_data = cv2.imread(self._dem_path, cv2.IMREAD_GRAYSCALE)
        dem_data_rgb = cv2.cvtColor(dem_data, cv2.COLOR_GRAY2RGB)
        cv2.imwrite(grayscale_dem_path, dem_data_rgb)
        return grayscale_dem_path

    def colored_preview(self) -> str:
        """Converts DEM image to colored RGB image and saves it to the map directory.
        Returns path to the preview image.

        Returns:
            list[str]: List with a single path to the DEM file
        """

        # colored_dem_path = self._dem_path.replace(".png", "_colored.png")
        colored_dem_path = os.path.join(self.previews_directory, "dem_colored.png")

        self.logger.debug("Creating colored preview of DEM data in %s.", colored_dem_path)

        dem_data = cv2.imread(self._dem_path, cv2.IMREAD_GRAYSCALE)

        self.logger.debug(
            "DEM data before normalization. Shape: %s, dtype: %s. Min: %s, max: %s.",
            dem_data.shape,
            dem_data.dtype,
            dem_data.min(),
            dem_data.max(),
        )

        # Create an empty array with the same shape and type as dem_data.
        dem_data_normalized = np.empty_like(dem_data)

        # Normalize the DEM data to the range [0, 255]
        cv2.normalize(dem_data, dem_data_normalized, 0, 255, cv2.NORM_MINMAX)
        self.logger.debug(
            "DEM data after normalization. Shape: %s, dtype: %s. Min: %s, max: %s.",
            dem_data_normalized.shape,
            dem_data_normalized.dtype,
            dem_data_normalized.min(),
            dem_data_normalized.max(),
        )
        dem_data_colored = cv2.applyColorMap(dem_data_normalized, cv2.COLORMAP_JET)

        cv2.imwrite(colored_dem_path, dem_data_colored)
        return colored_dem_path

    def previews(self) -> list[str]:
        """Get list of preview images.

        Returns:
            list[str]: List of preview images.
        """
        self.logger.debug("Starting DEM previews generation.")
        return [self.grayscale_preview(), self.colored_preview()]

    def _get_scaling_factor(self, maximum_deviation: int) -> float:
        """Calculate scaling factor for DEM data normalization.
        NOTE: Needs reconsideration for the implementation.

        Args:
            maximum_deviation (int): Maximum deviation in DEM data.

        Returns:
            float: Scaling factor for DEM data normalization.
        """
        ESTIMATED_MAXIMUM_DEVIATION = 1000  # pylint: disable=C0103
        scaling_factor = maximum_deviation / ESTIMATED_MAXIMUM_DEVIATION
        return scaling_factor if scaling_factor < 1 else 1

    def _normalize_dem(self, data: np.ndarray) -> np.ndarray:
        """Normalize DEM data to 16-bit unsigned integer using max height from settings.
        Args:
            data (np.ndarray): DEM data from SRTM file after cropping.
        Returns:
            np.ndarray: Normalized DEM data.
        """
        self.logger.debug("Starting DEM data normalization.")
        # Calculate the difference between the maximum and minimum values in the DEM data.

        max_height = data.max()  # 1800
        min_height = data.min()  # 1700
        max_dev = max_height - min_height  # 100
        self.logger.debug(
            "Maximum deviation: %s with maximum at %s and minimum at %s.",
            max_dev,
            max_height,
            min_height,
        )

        scaling_factor = self._get_scaling_factor(max_dev)
        adjusted_max_height = int(65535 * scaling_factor)
        self.logger.debug(
            f"Maximum deviation: {max_dev}. Scaling factor: {scaling_factor}. "
            f"Adjusted max height: {adjusted_max_height}."
        )
        normalized_data = (
            (data - data.min()) / (data.max() - data.min()) * adjusted_max_height
        ).astype("uint16")
        self.logger.debug(
            f"DEM data was normalized to {normalized_data.min()} - {normalized_data.max()}."
        )
        return normalized_data
