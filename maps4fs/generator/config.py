"""This module contains the Config class for map settings and configuration."""

from __future__ import annotations

import os
from xml.etree import ElementTree as ET

from maps4fs.generator.component import Component


# pylint: disable=R0903
class Config(Component):
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
            map_elem.set("width", str(self.map_width))
            map_elem.set("height", str(self.map_height))
            self.logger.debug(
                "Map size set to %sx%s in Map XML file.", self.map_width, self.map_height
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
        bbox = self.get_bbox(distance=self.map_height)
        south, west, north, east = bbox
        epsg3857_string = self.get_epsg3857_string(bbox=bbox)

        overview_data = {
            "epsg3857_string": epsg3857_string,
            "south": south,
            "west": west,
            "north": north,
            "east": east,
            "height": self.map_height * 2,
            "width": self.map_width * 2,
        }

        data = {
            "Overview": overview_data,
        }

        return data  # type: ignore
