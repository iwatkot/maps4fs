"""This module contains the GRLE class for generating InfoLayer PNG files based on GRLE schema."""

import json
import os
from xml.etree import ElementTree as ET

import cv2
import numpy as np

from maps4fs.generator.component import Component


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
