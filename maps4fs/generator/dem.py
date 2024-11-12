"""This module contains DEM class for processing Digital Elevation Model data."""

import gzip
import math
import os
import shutil

import cv2
import numpy as np
import osmnx as ox  # type: ignore
import rasterio  # type: ignore
import requests

from maps4fs.generator.component import Component

SRTM = "https://elevation-tiles-prod.s3.amazonaws.com/skadi/{latitude_band}/{tile_name}.hgt.gz"


# pylint: disable=R0903
class DEM(Component):
    """Component for map settings and configuration.

    Args:
        coordinates (tuple[float, float]): The latitude and longitude of the center of the map.
        distance (int): The distance from the center to the edge of the map.
        map_directory (str): The directory where the map files are stored.
        logger (Any, optional): The logger to use. Must have at least three basic methods: debug,
            info, warning. If not provided, default logging will be used.
    """

    def preprocess(self) -> None:
        self._blur_seed: int = self.kwargs.get("blur_seed") or 5
        self._max_height: int = self.kwargs.get("max_height") or 200

        self._dem_path = self.game.dem_file_path(self.map_directory)
        self.temp_dir = "temp"
        self.hgt_dir = os.path.join(self.temp_dir, "hgt")
        self.gz_dir = os.path.join(self.temp_dir, "gz")
        os.makedirs(self.hgt_dir, exist_ok=True)
        os.makedirs(self.gz_dir, exist_ok=True)

    # pylint: disable=no-member
    def process(self) -> None:
        """Reads SRTM file, crops it to map size, normalizes and blurs it,
        saves to map directory."""
        north, south, east, west = ox.utils_geo.bbox_from_point(  # pylint: disable=W0632
            self.coordinates, dist=self.distance
        )
        self.logger.debug(
            f"Processing DEM. North: {north}, south: {south}, east: {east}, west: {west}."
        )

        dem_output_size = self.distance * self.game.dem_multipliyer + 1
        self.logger.debug(
            "DEM multiplier is %s, DEM output size is %s.",
            self.game.dem_multipliyer,
            dem_output_size,
        )
        dem_output_resolution = (dem_output_size, dem_output_size)
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
            f"DEM data was read from SRTM file. Shape: {data.shape}, dtype: {data.dtype}. "
            f"Min: {data.min()}, max: {data.max()}."
        )

        normalized_data = self._normalize_dem(data)

        resampled_data = cv2.resize(
            normalized_data, dem_output_resolution, interpolation=cv2.INTER_LINEAR
        )
        self.logger.debug(
            f"DEM data was resampled. Shape: {resampled_data.shape}, "
            f"dtype: {resampled_data.dtype}. "
            f"Min: {resampled_data.min()}, max: {resampled_data.max()}."
        )

        blurred_data = cv2.GaussianBlur(resampled_data, (self._blur_seed, self._blur_seed), 0)
        cv2.imwrite(self._dem_path, blurred_data)
        self.logger.debug("DEM data was saved to %s.", self._dem_path)

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
                f"Decompressed tile already exists: {decompressed_file_path}, skipping download."
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

    def _normalize_dem(self, data: np.ndarray) -> np.ndarray:
        """Normalize DEM data to 16-bit unsigned integer using max height from settings.

        Args:
            data (np.ndarray): DEM data from SRTM file after cropping.

        Returns:
            np.ndarray: Normalized DEM data.
        """
        max_dev = data.max() - data.min()
        scaling_factor = max_dev / self._max_height if max_dev < self._max_height else 1
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
