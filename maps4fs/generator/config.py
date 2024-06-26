import os
from typing import Any
from xml.etree import ElementTree as ET

from maps4fs.generator import Component


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
            self.logger.warning(f"Map XML file not found: {self._map_xml_path}.")
            return
        tree = ET.parse(self._map_xml_path)
        self.logger.debug(f"Map XML file loaded from: {self._map_xml_path}.")
        root = tree.getroot()
        for map_elem in root.iter("map"):
            width = height = str(self.distance * 2)
            map_elem.set("width", width)
            map_elem.set("height", height)
            self.logger.debug(f"Map size set to {width}x{height} in Map XML file.")
        tree.write(self._map_xml_path)
        self.logger.debug(f"Map XML file saved to: {self._map_xml_path}.")
