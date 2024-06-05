import gzip
import math
import os
import shutil
from typing import Any

import cv2
import numpy as np
import osmnx as ox
import rasterio
import requests

import maps4fs.globals as g
from maps4fs.generator import Component


class DEM(Component):
    """Component for map settings and configuration.

    Args:
        coordinates (tuple[float, float]): The latitude and longitude of the center of the map.
        distance (int): The distance from the center to the edge of the map.
        map_directory (str): The directory where the map files are stored.
        logger (Any, optional): The logger to use. Must have at least three basic methods: debug,
            info, warning. If not provided, default logging will be used.
    """

    def __init__(
        self,
        coordinates: tuple[float, float],
        distance: int,
        map_directory: str,
        logger: Any = None,
        **kwargs,
    ):
        super().__init__(coordinates, distance, map_directory, logger)
        self._dem_path = os.path.join(self.map_directory, "maps", "map", "data", "map_dem.png")
        self.temp_dir = "temp"
        self.hgt_dir = os.path.join(self.temp_dir, "hgt")
        self.gz_dir = os.path.join(self.temp_dir, "gz")
        os.makedirs(self.hgt_dir, exist_ok=True)
        os.makedirs(self.gz_dir, exist_ok=True)

        self._blur_seed = kwargs.get("blur_seed")
        self._max_height = kwargs.get("max_height")

    def process(self) -> None:
        """Reads SRTM file, crops it to map size, normalizes and blurs it, saves to map directory."""
        north, south, east, west = ox.utils_geo.bbox_from_point(
            self.coordinates, dist=self.distance
        )
        self.logger.debug(
            f"Processing DEM. North: {north}, south: {south}, east: {east}, west: {west}."
        )

        dem_output_resolution = (self.distance + 1, self.distance + 1)

        tile_path = self._srtm_tile()
        if not tile_path:
            self.logger.warning("Tile was not downloaded, DEM file will be filled with zeros.")
            self._save_empty_dem(dem_output_resolution)
            return

        with rasterio.open(tile_path) as src:
            self.logger.debug(f"Opened tile, shape: {src.shape}, dtype: {src.dtypes[0]}.")
            window = rasterio.windows.from_bounds(west, south, east, north, src.transform)
            self.logger.debug(
                f"Window parameters. Column offset: {window.col_off}, row offset: {window.row_off}, "
                f"width: {window.width}, height: {window.height}."
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
            f"DEM data was resampled. Shape: {resampled_data.shape}, dtype: {resampled_data.dtype}. "
            f"Min: {resampled_data.min()}, max: {resampled_data.max()}."
        )

        blurred_data = cv2.GaussianBlur(resampled_data, (self._blur_seed, self._blur_seed), 0)
        cv2.imwrite(self._dem_path, blurred_data)
        self.logger.debug(f"DEM data was blurred and saved to {self._dem_path}.")

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

        self.logger.debug(f"Detected tile name: {tile_name} for coordinates: lat {lat}, lon {lon}.")
        return latitude_band, tile_name

    def _download_tile(self) -> str | None:
        """Downloads SRTM tile from Amazon S3 using coordinates.

        Returns:
            str: Path to compressed tile or None if download failed.
        """
        latitude_band, tile_name = self._tile_info(*self.coordinates)
        compressed_file_path = os.path.join(self.gz_dir, f"{tile_name}.hgt.gz")
        url = g.SRTM.format(latitude_band=latitude_band, tile_name=tile_name)
        self.logger.debug(f"Trying to get response from {url}...")
        response = requests.get(url, stream=True)

        if response.status_code == 200:
            self.logger.debug(f"Response received. Saving to {compressed_file_path}...")
            with open(compressed_file_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            self.logger.debug("Compressed tile successfully downloaded.")
        else:
            self.logger.error(f"Response was failed with status code {response.status_code}.")
            return

        return compressed_file_path

    def _srtm_tile(self) -> str | None:
        """Determines SRTM tile name from coordinates downloads it if necessary, and decompresses it.

        Returns:
            str: Path to decompressed tile or None if download failed.
        """
        latitude_band, tile_name = self._tile_info(*self.coordinates)
        self.logger.debug(f"SRTM tile name {tile_name} from latitude band {latitude_band}.")

        decompressed_file_path = os.path.join(self.hgt_dir, f"{tile_name}.hgt")
        if os.path.isfile(decompressed_file_path):
            self.logger.info(
                f"Decompressed tile already exists: {decompressed_file_path}, skipping download."
            )
            return decompressed_file_path

        compressed_file_path = self._download_tile()
        if not compressed_file_path:
            self.logger.error("Download from SRTM failed, DEM file will be filled with zeros.")
            return
        with gzip.open(compressed_file_path, "rb") as f_in:
            with open(decompressed_file_path, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)
        self.logger.debug(f"Tile decompressed to {decompressed_file_path}.")
        return decompressed_file_path

    def _save_empty_dem(self, dem_output_resolution: tuple[int, int]) -> None:
        """Saves empty DEM file filled with zeros."""
        dem_data = np.zeros(dem_output_resolution, dtype="uint16")
        cv2.imwrite(self._dem_path, dem_data)
        self.logger.warning(f"DEM data filled with zeros and saved to {self._dem_path}.")

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
