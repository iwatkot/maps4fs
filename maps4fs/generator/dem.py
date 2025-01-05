"""This module contains DEM class for processing Digital Elevation Model data."""

import os
from typing import Any

import cv2
import numpy as np

# import rasterio  # type: ignore
from pympler import asizeof  # type: ignore

from maps4fs.generator.component import Component
from maps4fs.generator.dtm.dtm import DTMProvider


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

        self.dtm_provider: DTMProvider = self.map.dtm_provider(  # type: ignore
            coordinates=self.coordinates,
            user_settings=self.map.dtm_provider_settings,
            size=self.map_rotated_size,
            directory=self.temp_dir,
            logger=self.logger,
            map=self.map,
        )

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

        dem_output_resolution = self.output_resolution
        self.logger.debug("DEM output resolution: %s.", dem_output_resolution)

        try:
            data = self.dtm_provider.get_numpy()
        except Exception as e:  # pylint: disable=W0718
            self.logger.error("Failed to get DEM data from SRTM: %s.", e)
            self._save_empty_dem(dem_output_resolution)
            return

        if len(data.shape) != 2:
            self.logger.error("DTM provider returned incorrect data: more than 1 channel.")
            self._save_empty_dem(dem_output_resolution)
            return

        if data.dtype not in ["int16", "uint16"]:
            self.logger.error("DTM provider returned incorrect data type: %s.", data.dtype)
            self._save_empty_dem(dem_output_resolution)
            return

        self.logger.debug(
            "DEM data was retrieved from DTM provider. Shape: %s, dtype: %s. Min: %s, max: %s.",
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

        if self.multiplier != 1:
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

    def info_sequence(self) -> dict[Any, Any] | None:  # type: ignore
        """Returns the information sequence for the component. Must be implemented in the child
        class. If the component does not have an information sequence, an empty dictionary must be
        returned.

        Returns:
            dict[Any, Any]: The information sequence for the component.
        """
        provider_info_sequence = self.dtm_provider.info_sequence()
        if provider_info_sequence is None:
            return {}
        return provider_info_sequence
