"""This module contains the Config class for map settings and configuration."""

from __future__ import annotations

import os
from xml.etree import ElementTree as ET

from maps4fs.generator.component import Component


# pylint: disable=R0903
class Config(Component):
    """Component for map settings and configuration.

    Arguments:
        game (Game): The game instance for which the map is generated.
        coordinates (tuple[float, float]): The latitude and longitude of the center of the map.
        map_size (int): The size of the map in pixels (it's a square).
        map_rotated_size (int): The size of the map in pixels after rotation.
        rotation (int): The rotation angle of the map.
        map_directory (str): The directory where the map files are stored.
        logger (Any, optional): The logger to use. Must have at least three basic methods: debug,
            info, warning. If not provided, default logging will be used.
    """

    def preprocess(self) -> None:
        """Gets the path to the map XML file and saves it to the instance variable."""
        self._map_xml_path = self.game.map_xml_path(self.map_directory)
        self.logger.debug("Map XML path: %s.", self._map_xml_path)

    def process(self) -> None:
        """Sets the map size in the map.xml file."""
        self._set_map_size()

    def _set_map_size(self) -> None:
        """Edits map.xml file to set correct map size."""
        if not os.path.isfile(self._map_xml_path):
            self.logger.warning("Map XML file not found: %s.", self._map_xml_path)
            return
        tree = ET.parse(self._map_xml_path)
        self.logger.debug("Map XML file loaded from: %s.", self._map_xml_path)
        root = tree.getroot()
        for map_elem in root.iter("map"):
            map_elem.set("width", str(self.map_size))
            map_elem.set("height", str(self.map_size))
            self.logger.debug(
                "Map size set to %sx%s in Map XML file.",
                self.map_size,
                self.map_size,
            )
        tree.write(self._map_xml_path)
        self.logger.debug("Map XML file saved to: %s.", self._map_xml_path)

    def previews(self) -> list[str]:
        """Returns a list of paths to the preview images (empty list).
        The component does not generate any preview images so it returns an empty list.

        Returns:
            list[str]: An empty list.
        """
        return []

    def info_sequence(self) -> dict[str, dict[str, str | float | int]]:
        """Returns information about the component.
        Overview section is needed to create the overview file (in-game map).

        Returns:
            dict[str, dict[str, str | float | int]]: Information about the component.
        """
        # The overview file is exactly 2X bigger than the map size, does not matter
        # if the map is 2048x2048 or 4096x4096, the overview will be 4096x4096
        # and the map will be in the center of the overview.
        # That's why the distance is set to the map height not as a half of it.
        bbox = self.get_bbox(distance=self.map_size)
        south, west, north, east = bbox
        epsg3857_string = self.get_epsg3857_string(bbox=bbox)
        epsg3857_string_with_margin = self.get_epsg3857_string(bbox=bbox, add_margin=True)

        self.qgis_sequence()

        overview_data = {
            "epsg3857_string": epsg3857_string,
            "epsg3857_string_with_margin": epsg3857_string_with_margin,
            "south": south,
            "west": west,
            "north": north,
            "east": east,
            "height": self.map_size * 2,
            "width": self.map_size * 2,
        }

        data = {
            "Overview": overview_data,
        }

        return data  # type: ignore

    def qgis_sequence(self) -> None:
        """Generates QGIS scripts for creating bounding box layers and rasterizing them."""
        bbox = self.get_bbox(distance=self.map_size)
        espg3857_bbox = self.get_espg3857_bbox(bbox=bbox)
        espg3857_bbox_with_margin = self.get_espg3857_bbox(bbox=bbox, add_margin=True)

        qgis_layers = [("Overview_bbox", *espg3857_bbox)]
        qgis_layers_with_margin = [("Overview_bbox_with_margin", *espg3857_bbox_with_margin)]

        layers = qgis_layers + qgis_layers_with_margin

        self.create_qgis_scripts(layers)
