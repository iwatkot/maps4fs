import logging
import os
from typing import Any
from xml.etree import ElementTree as ET

from src.generator.components import Component


class Config(Component):
    def __init__(
        self,
        coordinates: tuple[float, float],
        distance: int,
        map_directory: str,
        logger: Any = None,
    ):
        super().__init__(coordinates, distance, map_directory, logger)
        self.map_xml_path = os.path.join(self.map_directory, "maps", "map", "map.xml")

    def process(self):
        self._set_map_size()

    def _set_map_size(self):
        """Edits map.xml file to set correct map size."""
        if not os.path.isfile(self.map_xml_path):
            self.logger.error(f"Map XML file not found: {self.map_xml_path}.")
            return
        tree = ET.parse(self.map_xml_path)
        self.logger.log(f"Map XML file loaded from: {self.map_xml_path}.")
        root = tree.getroot()
        for map_elem in root.iter("map"):
            map_elem.set("width", str(self.distance * 2))
            map_elem.set("height", str(self.distance * 2))
        tree.write(self.map_xml_path)
        self.logger.log(f"Map XML file saved to: {self.map_xml_path}.")


from rich.console import Console

coordinates = (0.0, 0.0)
distance = 1024
map_directory = "output"
logger = Console()
cfg = Config(coordinates, distance, map_directory, logger)
cfg.process()
