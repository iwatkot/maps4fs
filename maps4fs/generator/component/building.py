"""Component for map buildings processing and generation."""

import os

import cv2
import numpy as np

from maps4fs.generator.component.i3d import I3d


def building_category_type_to_pixel_value(building_category: str) -> int | None:
    """Returns the pixel value representation of the building category.
    If not found, returns None.

    Arguments:
        building_category (str): name of the building category

    Returns:
        int | None: pixel value of the building category or None if not found.
    """
    area_types = {
        "residential": 10,
        "commercial": 20,
        "industrial": 30,
        "retail": 40,
        "farmyard": 50,
        "religious": 60,
        "recreation": 70,
    }
    return area_types.get(building_category)


class Building(I3d):
    """Component for map buildings processing and generation.

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
        buildings_directory = os.path.join(self.map.map_directory, "buildings")
        self.buildings_map_path = os.path.join(buildings_directory, "building_categories.png")
        os.makedirs(buildings_directory, exist_ok=True)

        texture_component = self.map.get_texture_component()
        if not texture_component:
            self.logger.warning("Texture component not found in the map.")
            return

        # Creating empty single-channel image for building categories.
        buildings_map_image = np.zeros((self.map.size, self.map.size), dtype=np.uint8)

        for layer in texture_component.get_building_category_layers():
            self.logger.info(
                f"Processing building category layer: {layer.name} ({layer.building_category})"
            )
            pixel_value = building_category_type_to_pixel_value(layer.building_category)  # type: ignore
            if pixel_value is None:
                self.logger.warning(
                    f"Unknown building category '{layer.building_category}' for layer '{layer.name}'. Skipping."
                )
                continue

            layer_path = layer.path(self.game.weights_dir_path(self.map.map_directory))
            if not layer_path or not os.path.isfile(layer_path):
                self.logger.warning(f"Layer texture file not found: {layer_path}. Skipping.")
                continue

            layer_image = cv2.imread(layer_path, cv2.IMREAD_UNCHANGED)
            if layer_image is None:
                self.logger.warning(f"Failed to read layer image: {layer_path}. Skipping.")
                continue

            mask = layer_image > 0
            buildings_map_image[mask] = pixel_value

        # Save the buildings map image
        cv2.imwrite(self.buildings_map_path, buildings_map_image)
        self.logger.info(f"Building categories map saved to: {self.buildings_map_path}")

    def process(self) -> None:
        if not hasattr(self, "buildings_map_path") or not os.path.isfile(self.buildings_map_path):
            self.logger.warning(
                "Buildings map path is not set or file does not exist. Skipping process step."
            )
            return

        self.logger.info("Buildings map categories file found, processing...")

    def info_sequence(self) -> dict[str, dict[str, str | float | int]]:
        return {}
