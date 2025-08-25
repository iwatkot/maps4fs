"""This module contains DEM class for processing Digital Elevation Model data."""

import math
from typing import Any

import cv2
import numpy as np
from pydtmdl import DTMProvider

import maps4fs.generator.config as mfscfg
from maps4fs.generator.component.base.component_image import ImageComponent


# pylint: disable=R0903, R0902
class DEM(ImageComponent):
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

        self.logger.debug("Map size: %s x %s.", self.map_size, self.map_size)
        self.logger.debug(
            "Map rotated size: %s x %s.", self.map_rotated_size, self.map_rotated_size
        )

        self.output_resolution = self.get_output_resolution()
        self.logger.debug("Output resolution for DEM data: %s.", self.output_resolution)

        self.dtm_provider: DTMProvider = self.map.dtm_provider(  # type: ignore
            coordinates=self.coordinates,
            user_settings=self.map.dtm_provider_settings,
            size=self.map_rotated_size,
            directory=mfscfg.DTM_CACHE_DIR,
            logger=self.logger,
        )

        self.info: dict[str, Any] = {}

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

    def update_info(self, state: str, data: np.ndarray) -> None:
        """Update info dictionary with additional information about DEM data.

        Arguments:
            data (np.ndarray): DEM data.
        """

        try:
            entry = {
                "min": float(data.min()),
                "max": float(data.max()),
                "deviation": float(data.max() - data.min()),
                "dtype": str(data.dtype),
                "shape": str(data.shape),
            }
            self.info[state] = entry
        except Exception as e:
            self.logger.warning("Failed to update DEM info: %s.", e)

    def process(self) -> None:
        """Reads DTM file, crops it to map size, normalizes and blurs it,
        saves to map directory."""

        dem_output_resolution = self.output_resolution
        self.logger.debug("DEM output resolution: %s.", dem_output_resolution)

        try:
            data = self.dtm_provider.get_numpy()
        except Exception as e:  # pylint: disable=W0718
            self.logger.error("Failed to get DEM data from DTM provider: %s.", e)
            raise ValueError(
                f"Failed to get DEM data from DTM provider: {e}. "
                "Try using different DTM provider."
            ) from e

        if len(data.shape) != 2:
            self.logger.error("DTM provider returned incorrect data: more than 1 channel.")
            raise ValueError(
                "DTM provider returned incorrect data: more than 1 channel. "
                "Try using different DTM provider."
            )

        if data.dtype not in ["int16", "uint16", "float", "float32"]:
            self.logger.error("DTM provider returned incorrect data type: %s.", data.dtype)
            raise ValueError(
                f"DTM provider returned incorrect data type: {data.dtype}. "
                "Try using different DTM provider."
            )

        self.logger.debug(
            "DEM data was retrieved from DTM provider. Shape: %s, dtype: %s. Min: %s, max: %s.",
            data.shape,
            data.dtype,
            data.min(),
            data.max(),
        )

        self.update_info("original", data)

        # Check if the data contains any non-zero values, otherwise raise an error.
        if not np.any(data):
            self.logger.error("DTM provider returned empty data.")
            raise ValueError("DTM provider returned empty data. Try using different DTM provider.")

        # 1. Resize DEM data to the output resolution.
        resampled_data = self.resize_to_output(data)

        # 2. Apply multiplier (-10 to 120.4 becomes -20 to 240.8)
        resampled_data = self.apply_multiplier(resampled_data)
        self.update_info("multiplied", resampled_data)

        # 3. Raise terrain, and optionally lower to plateau level+water depth
        # e.g. -20 to 240.8m becomes 20 to 280.8m
        resampled_data = self.raise_or_lower(resampled_data)
        self.update_info("raised_lowered", resampled_data)

        # 4. Determine actual height scale value using ceiling
        # e.g. 255 becomes 280.8+10 = 291
        height_scale_value = self.determine_height_scale(resampled_data)

        # 5. Normalize DEM data to 16-bit unsigned integer range (0 to 65535)
        # e.g. multiply by 65535/291, clip and return as uint16
        resampled_data = self.normalize_data(resampled_data, height_scale_value)
        self.update_info("normalized", resampled_data)

        # 6. Blur DEM data.
        resampled_data = self.apply_blur(resampled_data, blur_radius=self.get_blur_radius())

        cv2.imwrite(self._dem_path, resampled_data)
        self.logger.debug("DEM data was saved to %s.", self._dem_path)

        if self.rotation:
            self.rotate_dem()

    def normalize_data(self, data: np.ndarray, height_scale_value: int) -> np.ndarray:
        """Normalize DEM data to 16-bit unsigned integer range (0 to 65535).

        Arguments:
            data (np.ndarray): DEM data.
            height_scale_value (int): Height scale value.

        Returns:
            np.ndarray: Normalized DEM data.
        """
        normalized_data = np.clip((data / height_scale_value) * 65535, 0, 65535).astype(np.uint16)
        self.logger.debug(
            "DEM data was normalized and clipped to 16-bit unsigned integer range. "
            "Min: %s, max: %s.",
            normalized_data.min(),
            normalized_data.max(),
        )
        return normalized_data

    def determine_height_scale(self, data: np.ndarray) -> int:
        """Determine height scale value using ceiling.

        Arguments:
            data (np.ndarray): DEM data.

        Returns:
            int: Height scale value.
        """
        height_scale = self.map.dem_settings.minimum_height_scale
        adjusted_height_scale = math.ceil(
            max(height_scale, data.max() + self.map.dem_settings.ceiling)
        )

        self.map.shared_settings.height_scale_value = adjusted_height_scale  # type: ignore
        self.map.shared_settings.mesh_z_scaling_factor = 65535 / adjusted_height_scale
        self.map.shared_settings.height_scale_multiplier = adjusted_height_scale / 255
        self.map.shared_settings.change_height_scale = True  # type: ignore

        try:
            entry = {
                "height_scale_from_settings": height_scale,
                "adjusted_height_scale": adjusted_height_scale,
                "mesh_z_scaling_factor": self.map.shared_settings.mesh_z_scaling_factor,
                "height_scale_multiplier": self.map.shared_settings.height_scale_multiplier,
            }
            self.info["height_scale"] = entry
        except Exception as e:
            self.logger.warning("Failed to update DEM info: %s.", e)

        self.logger.debug("Height scale value is %s.", adjusted_height_scale)
        return adjusted_height_scale

    def raise_or_lower(self, data: np.ndarray) -> np.ndarray:
        """Raise or lower terrain to the level of plateau+water depth."""

        if not self.map.dem_settings.adjust_terrain_to_ground_level:
            return data

        desired_ground_level = self.map.dem_settings.plateau + self.map.dem_settings.water_depth
        current_ground_level = data.min()

        data = data + (desired_ground_level - current_ground_level)

        self.logger.debug(
            "Array was shifted to the ground level %s. Min: %s, max: %s.",
            desired_ground_level,
            data.min(),
            data.max(),
        )
        return data

    def apply_multiplier(self, data: np.ndarray) -> np.ndarray:
        """Apply multiplier to DEM data.

        Arguments:
            data (np.ndarray): DEM data.

        Returns:
            np.ndarray: Multiplied DEM data.
        """
        multiplier = self.map.dem_settings.multiplier
        if multiplier == 1:
            return data

        multiplied_data = data * multiplier
        self.logger.debug(
            "DEM data was multiplied by %s. Min: %s, max: %s.",
            multiplier,
            multiplied_data.min(),
            multiplied_data.max(),
        )
        return multiplied_data

    def resize_to_output(self, data: np.ndarray) -> np.ndarray:
        """Resize DEM data to the output resolution.

        Arguments:
            data (np.ndarray): DEM data.

        Returns:
            np.ndarray: Resized DEM data.
        """
        resampled_data = cv2.resize(data, self.output_resolution, interpolation=cv2.INTER_LINEAR)

        return resampled_data

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

    def info_sequence(self) -> dict[Any, Any] | None:  # type: ignore
        """Returns the information sequence for the component.

        Returns:
            dict[Any, Any]: The information sequence for the component.
        """
        return self.info
