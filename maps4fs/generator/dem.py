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
DEFAULT_MULTIPLIER = 3
DEFAULT_BLUR_RADIUS = 21


# pylint: disable=R0903
class DEM(Component):
    """Component for map settings and configuration.

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
        self.blur_radius = self.kwargs.get("blur_radius", DEFAULT_BLUR_RADIUS)
        self.logger.debug(
            "DEM multiplier is %s, blur radius is %s.", self.multiplier, self.blur_radius
        )

    # pylint: disable=no-member
    def process(self) -> None:
        """Reads SRTM file, crops it to map size, normalizes and blurs it,
        saves to map directory."""
        north, south, east, west = self.bbox

        dem_height = self.map_height * self.game.dem_multipliyer + 1
        dem_width = self.map_width * self.game.dem_multipliyer + 1
        self.logger.debug(
            "DEM multiplier is %s, DEM height is %s, DEM width is %s.",
            self.game.dem_multipliyer,
            dem_height,
            dem_width,
        )
        dem_output_resolution = (dem_width, dem_height)
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

        resampled_data = resampled_data * self.multiplier
        self.logger.debug(
            "DEM data multiplied by %s. Shape: %s, dtype: %s. Min: %s, max: %s.",
            self.multiplier,
            resampled_data.shape,
            resampled_data.dtype,
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

        resampled_data = cv2.GaussianBlur(resampled_data, (self.blur_radius, self.blur_radius), 0)
        self.logger.debug(
            "Gaussion blur applied to DEM data with kernel size %s.",
            self.blur_radius,
        )

        cv2.imwrite(self._dem_path, resampled_data)
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
        rgb_dem_path = self._dem_path.replace(".png", "_grayscale.png")
        dem_data = cv2.imread(self._dem_path, cv2.IMREAD_GRAYSCALE)
        dem_data_rgb = cv2.cvtColor(dem_data, cv2.COLOR_GRAY2RGB)
        cv2.imwrite(rgb_dem_path, dem_data_rgb)
        return rgb_dem_path

    def colored_preview(self) -> str:
        """Converts DEM image to colored RGB image and saves it to the map directory.
        Returns path to the preview image.

        Returns:
            list[str]: List with a single path to the DEM file
        """

        colored_dem_path = self._dem_path.replace(".png", "_colored.png")
        dem_data = cv2.imread(self._dem_path, cv2.IMREAD_GRAYSCALE)

        # Normalize the DEM data to the range [0, 255]
        # dem_data_normalized = cv2.normalize(dem_data, None, 0, 255, cv2.NORM_MINMAX)

        dem_data_colored = cv2.applyColorMap(dem_data, cv2.COLORMAP_JET)

        cv2.imwrite(colored_dem_path, dem_data_colored)
        return colored_dem_path

    def previews(self) -> list[str]:
        """Get list of preview images.

        Returns:
            list[str]: List of preview images.
        """
        return [self.grayscale_preview(), self.colored_preview()]
