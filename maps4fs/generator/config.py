"""This module contains the Config class for map settings and configuration."""

import os
from typing import Any
from xml.etree import ElementTree as ET

from maps4fs.generator.component import Component


# pylint: disable=R0903
class Config(Component):
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
        self._map_xml_path = os.path.join(self.map_directory, "maps", "map", "map.xml")

    def process(self):
        self._set_map_size()

    def _set_map_size(self):
        """Edits map.xml file to set correct map size."""
        if not os.path.isfile(self._map_xml_path):
            self.logger.warning("Map XML file not found: %s.", self._map_xml_path)
            return
        tree = ET.parse(self._map_xml_path)
        self.logger.debug("Map XML file loaded from: %s.", self._map_xml_path)
        root = tree.getroot()
        for map_elem in root.iter("map"):
            width = height = str(self.distance * 2)
            map_elem.set("width", width)
            map_elem.set("height", height)
            self.logger.debug("Map size set to %sx%s in Map XML file.", width, height)
        tree.write(self._map_xml_path)
        self.logger.debug("Map XML file saved to: %s.", self._map_xml_path)
