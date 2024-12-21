"""This module contains the GRLE class for generating InfoLayer PNG files based on GRLE schema."""

import json
import os
from random import choice, randint
from xml.etree import ElementTree as ET

import cv2
import numpy as np

from maps4fs.generator.component import Component

ISLAND_SIZE_MIN = 10
ISLAND_SIZE_MAX = 200


# pylint: disable=W0223
class GRLE(Component):
    """Component for to generate InfoLayer PNG files based on GRLE schema.

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

    _grle_schema: dict[str, float | int | str] | None = None

    def preprocess(self) -> None:
        """Gets the path to the map I3D file from the game instance and saves it to the instance
        attribute. If the game does not support I3D files, the attribute is set to None."""

        self.farmland_margin = self.kwargs.get("farmland_margin", 0)

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

                height = int(self.map_size * info_layer["height_multiplier"])
                width = int(self.map_size * info_layer["width_multiplier"])
                channels = info_layer["channels"]
                data_type = info_layer["data_type"]

                # Create the InfoLayer PNG file with zeros.
                if channels == 1:
                    info_layer_data = np.zeros((height, width), dtype=data_type)
                else:
                    info_layer_data = np.zeros((height, width, channels), dtype=data_type)
                self.logger.debug("Shape of %s: %s.", info_layer["name"], info_layer_data.shape)
                cv2.imwrite(file_path, info_layer_data)  # pylint: disable=no-member
                self.logger.debug("InfoLayer PNG file %s created.", file_path)
            else:
                self.logger.warning("Invalid InfoLayer schema: %s.", info_layer)

        self._add_farmlands()
        if self.game.code == "FS25":
            self.logger.info("Game is %s, plants will be added.", self.game.code)
            self._add_plants()
        else:
            self.logger.warning("Adding plants it's not supported for the %s.", self.game.code)

    def previews(self) -> list[str]:
        """Returns a list of paths to the preview images (empty list).
        The component does not generate any preview images so it returns an empty list.

        Returns:
            list[str]: An empty list.
        """
        return []

    # pylint: disable=R0801, R0914
    def _add_farmlands(self) -> None:
        """Adds farmlands to the InfoLayer PNG file."""

        textures_info_layer_path = self.get_infolayer_path("textures")
        if not textures_info_layer_path:
            return

        with open(textures_info_layer_path, "r", encoding="utf-8") as textures_info_layer_file:
            textures_info_layer = json.load(textures_info_layer_file)

        fields: list[list[tuple[int, int]]] | None = textures_info_layer.get("fields")
        if not fields:
            self.logger.warning("Fields data not found in textures info layer.")
            return

        self.logger.info("Found %s fields in textures info layer.", len(fields))

        info_layer_farmlands_path = os.path.join(
            self.game.weights_dir_path(self.map_directory), "infoLayer_farmlands.png"
        )

        self.logger.info(
            "Adding farmlands to the InfoLayer PNG file: %s.", info_layer_farmlands_path
        )

        if not os.path.isfile(info_layer_farmlands_path):
            self.logger.warning("InfoLayer PNG file %s not found.", info_layer_farmlands_path)
            return

        # pylint: disable=no-member
        image = cv2.imread(info_layer_farmlands_path, cv2.IMREAD_UNCHANGED)
        farmlands_xml_path = os.path.join(self.map_directory, "map/config/farmlands.xml")
        if not os.path.isfile(farmlands_xml_path):
            self.logger.warning("Farmlands XML file %s not found.", farmlands_xml_path)
            return

        tree = ET.parse(farmlands_xml_path)
        farmlands_xml = tree.find("farmlands")

        # Not using enumerate because in case of the error, we do not increment
        # the farmland_id. So as a result we do not have a gap in the farmland IDs.
        farmland_id = 1

        for field in fields:
            try:
                fitted_field = self.fit_polygon_into_bounds(
                    field, self.farmland_margin, angle=self.rotation
                )
            except ValueError as e:
                self.logger.warning(
                    "Farmland %s could not be fitted into the map bounds with error: %s",
                    farmland_id,
                    e,
                )
                continue

            self.logger.debug("Fitted field %s contains %s points.", farmland_id, len(fitted_field))

            field_np = np.array(fitted_field, np.int32)
            field_np = field_np.reshape((-1, 1, 2))

            self.logger.debug(
                "Created a numpy array and reshaped it. Number of points: %s", len(field_np)
            )

            # Infolayer image is 1/2 of the size of the map image, that's why we need to divide
            # the coordinates by 2.
            field_np = field_np // 2
            self.logger.debug("Divided the coordinates by 2.")

            # pylint: disable=no-member
            try:
                cv2.fillPoly(image, [field_np], farmland_id)  # type: ignore
            except Exception as e:  # pylint: disable=W0718
                self.logger.warning(
                    "Farmland %s could not be added to the InfoLayer PNG file with error: %s",
                    farmland_id,
                    e,
                )
                continue

            # Add the field to the farmlands XML.
            farmland = ET.SubElement(farmlands_xml, "farmland")  # type: ignore
            farmland.set("id", str(farmland_id))
            farmland.set("priceScale", "1")
            farmland.set("npcName", "FORESTER")

            farmland_id += 1

        tree.write(farmlands_xml_path)

        self.logger.info("Farmlands added to the farmlands XML file: %s.", farmlands_xml_path)

        cv2.imwrite(info_layer_farmlands_path, image)  # pylint: disable=no-member
        self.logger.info(
            "Farmlands added to the InfoLayer PNG file: %s.", info_layer_farmlands_path
        )

    def _add_plants(self) -> None:
        """Adds plants to the InfoLayer PNG file."""
        # 1. Get the path to the densityMap_fruits.png.
        # 2. Get the path to the base layer (grass).
        # 3. Detect non-zero areas in the base layer (it's where the plants will be placed).
        base_image_path = self.game.base_image_path(self.map_directory)
        if not base_image_path or not os.path.isfile(base_image_path):
            self.logger.warning("Base image not found in %s.", base_image_path)
            return

        density_map_fruit_path = os.path.join(
            self.game.weights_dir_path(self.map_directory), "densityMap_fruits.png"
        )

        if not os.path.isfile(density_map_fruit_path):
            self.logger.warning("Density map for fruits not found in %s.", density_map_fruit_path)
            return

        # Single channeled 8-bit image, where non-zero values (255) are where the grass is.
        base_image = cv2.imread(base_image_path, cv2.IMREAD_UNCHANGED)  # pylint: disable=no-member

        # Density map of the fruits is 2X size of the base image, so we need to resize it.
        # We'll resize the base image to make it bigger, so we can compare the values.
        base_image = cv2.resize(  # pylint: disable=no-member
            base_image,
            (base_image.shape[1] * 2, base_image.shape[0] * 2),
            interpolation=cv2.INTER_NEAREST,  # pylint: disable=no-member
        )

        # B and G channels remain the same (zeros), while we change the R channel.
        possible_R_values = [33, 65, 97, 129, 161, 193, 225]  # pylint: disable=C0103

        # 1st approach: Change the non zero values in the base image to 33 (for debug).
        # And use the base image as R channel in the density map.

        # pylint: disable=no-member
        def create_island_of_plants(image: np.ndarray, count: int) -> np.ndarray:
            """Create an island of plants in the image.

            Arguments:
                image (np.ndarray): The image where the island of plants will be created.
                count (int): The number of islands of plants to create.

            Returns:
                np.ndarray: The image with the islands of plants.
            """
            for _ in range(count):
                # Randomly choose the value for the island.
                plant_value = choice(possible_R_values)
                # Randomly choose the size of the island.
                island_size = randint(ISLAND_SIZE_MIN, ISLAND_SIZE_MAX)
                # Randomly choose the position of the island.
                # x = np.random.randint(0, image.shape[1] - island_size)
                # y = np.random.randint(0, image.shape[0] - island_size)
                x = randint(0, image.shape[1] - island_size)
                y = randint(0, image.shape[0] - island_size)

                # Randomly choose the shape of the island.
                shapes = ["circle", "ellipse", "polygon"]
                shape = choice(shapes)

                try:
                    if shape == "circle":
                        center = (x + island_size // 2, y + island_size // 2)
                        radius = island_size // 2
                        cv2.circle(image, center, radius, plant_value, -1)  # type: ignore
                    elif shape == "ellipse":
                        center = (x + island_size // 2, y + island_size // 2)
                        axes = (island_size // 2, island_size // 4)
                        angle = 0
                        cv2.ellipse(  # type: ignore
                            image, center, axes, angle, 0, 360, plant_value, -1
                        )
                    elif shape == "polygon":
                        nodes_count = randint(20, 50)
                        nodes = []
                        for _ in range(nodes_count):
                            node = (randint(x, x + island_size), randint(y, y + island_size))
                            nodes.append(node)
                        nodes = np.array(nodes, np.int32)  # type: ignore
                        cv2.fillPoly(image, [nodes], plant_value)  # type: ignore
                except Exception:  # pylint: disable=W0703
                    continue

            return image

        updated_base_image = base_image.copy()
        # Set all the non-zero values to 33.
        updated_base_image[base_image != 0] = 33

        # Add islands of plants to the base image.
        island_count = self.map_size
        self.logger.info("Adding %s islands of plants to the base image.", island_count)
        updated_base_image = create_island_of_plants(updated_base_image, island_count)
        self.logger.debug("Islands of plants added to the base image.")

        # Remove the values where the base image has zeros.
        updated_base_image[base_image == 0] = 0
        self.logger.debug("Removed the values where the base image has zeros.")

        # Value of 33 represents the base grass plant.
        # After painting it with base grass, we'll create multiple islands of different plants.
        # On the final step, we'll remove all the values which in pixels
        # where zerons in the original base image (so we don't paint grass where it should not be).

        # Three channeled 8-bit image, where non-zero values are the
        # different types of plants (only in the R channel).
        density_map_fruits = cv2.imread(density_map_fruit_path, cv2.IMREAD_UNCHANGED)
        self.logger.debug("Density map for fruits loaded, shape: %s.", density_map_fruits.shape)

        # Put the updated base image as the B channel in the density map.
        density_map_fruits[:, :, 0] = updated_base_image
        self.logger.debug("Updated base image added as the B channel in the density map.")

        # Save the updated density map.
        # Ensure that order of channels is correct because CV2 uses BGR and we need RGB.
        density_map_fruits = cv2.cvtColor(density_map_fruits, cv2.COLOR_BGR2RGB)
        cv2.imwrite(density_map_fruit_path, density_map_fruits)
        self.logger.info("Updated density map for fruits saved in %s.", density_map_fruit_path)
