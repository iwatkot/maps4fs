"""This module contains the GRLE class for generating InfoLayer PNG files based on GRLE schema."""

import json
import os

import cv2
import numpy as np

from maps4fs.generator.component import Component


# pylint: disable=W0223
class GRLE(Component):
    """Component for to generate InfoLayer PNG files based on GRLE schema.

    Arguments:
        coordinates (tuple[float, float]): The latitude and longitude of the center of the map.
        map_height (int): The height of the map in pixels.
        map_width (int): The width of the map in pixels.
        map_directory (str): The directory where the map files are stored.
        logger (Any, optional): The logger to use. Must have at least three basic methods: debug,
            info, warning. If not provided, default logging will be used.
    """

    _grle_schema: dict[str, float | int | str] | None = None

    def preprocess(self) -> None:
        """Gets the path to the map I3D file from the game instance and saves it to the instance
        attribute. If the game does not support I3D files, the attribute is set to None."""
        try:
            grle_schema_path = self.game.grle_schema
        except ValueError:
            self.logger.info("GRLE schema processing is not implemented for this game.")
            return

        try:
            with open(grle_schema_path, "r", encoding="utf-8") as file:
                self._grle_schema = json.load(file)
            self.logger.debug("GRLE schema loaded from: %s.", grle_schema_path)
        except (json.JSONDecodeError, FileNotFoundError) as error:
            self.logger.error("Error loading GRLE schema from %s: %s.", grle_schema_path, error)
            self._grle_schema = None

    def process(self) -> None:
        """Generates InfoLayer PNG files based on the GRLE schema."""
        if not self._grle_schema:
            self.logger.info("GRLE schema is not obtained, skipping the processing.")
            return

        for info_layer in self._grle_schema:
            if isinstance(info_layer, dict):
                file_path = os.path.join(
                    self.game.weights_dir_path(self.map_directory), info_layer["name"]
                )

                height = int(self.map_height * info_layer["height_multiplier"])
                width = int(self.map_width * info_layer["width_multiplier"])
                data_type = info_layer["data_type"]

                # Create the InfoLayer PNG file with zeros.
                info_layer_data = np.zeros((height, width), dtype=data_type)
                print(info_layer_data.shape)
                cv2.imwrite(file_path, info_layer_data)  # pylint: disable=no-member
                self.logger.info("InfoLayer PNG file %s created.", file_path)
            else:
                self.logger.warning("Invalid InfoLayer schema: %s.", info_layer)

    def previews(self) -> list[str]:
        """Returns a list of paths to the preview images (empty list).
        The component does not generate any preview images so it returns an empty list.

        Returns:
            list[str]: An empty list.
        """
        return []
