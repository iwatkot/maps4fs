import logging
import os
import shutil
from typing import Any

import osmnx as ox

import maps4fs as mfs


class Map:
    def __init__(
        self,
        coordinates: tuple[float, float],
        distance: int,
        map_directory: str,
        blur_seed: int,
        max_height: int,
        map_template: str = None,
        logger: Any = None,
    ):
        self.coordinates = coordinates
        self.distance = distance
        self.map_directory = map_directory

        if not logger:
            logger = logging.getLogger(__name__)
        self.logger = logger

        os.makedirs(self.map_directory, exist_ok=True)
        if map_template:
            shutil.unpack_archive(map_template, self.map_directory)
            self.logger.info(f"Map template {map_template} unpacked to {self.map_directory}")
        else:
            self.logger.warning(
                "Map template not provided, if directory does not contain required files, "
                "it may not work properly in Giants Editor."
            )

        self._read_parameters()
        self._add_components()

    def _add_components(self):
        self.logger.debug("Starting adding components...")
        active_components = []
        for component in mfs.generator.BaseComponents:
            active_components.append(
                component(self.coordinates, self.distance, self.map_directory, self.logger)
            )
        self._components = active_components
        self.logger.debug(f"Added {len(self._components)} components.")

    def _read_parameters(self) -> None:
        """Reads map parameters from OSM data, such as:
        - minimum and maximum coordinates in UTM format
        - map dimensions in meters
        - map coefficients (meters per pixel)
        """
        north, south, east, west = ox.utils_geo.bbox_from_point(
            self.coordinates, dist=self.distance, project_utm=True
        )
        # Parameters of the map in UTM format (meters).
        self.minimum_x = min(west, east)
        self.minimum_y = min(south, north)
        self.maximum_x = max(west, east)
        self.maximum_y = max(south, north)
        self.logger.debug(f"Map minimum coordinates (XxY): {self.minimum_x} x {self.minimum_y}.")
        self.logger.debug(f"Map maximum coordinates (XxY): {self.maximum_x} x {self.maximum_y}.")

        self.height = abs(north - south)
        self.width = abs(east - west)
        self.logger.info(f"Map dimensions (HxW): {self.height} x {self.width}.")

        self.height_coef = self.height / (self.distance * 2)
        self.width_coef = self.width / (self.distance * 2)
        self.logger.debug(f"Map coefficients (HxW): {self.height_coef} x {self.width_coef}.")

        self.easting = self.minimum_x < 500000
        self.northing = self.minimum_y < 10000000
        self.logger.debug(f"Map is in {'east' if self.easting else 'west'} of central meridian.")
        self.logger.debug(f"Map is in {'north' if self.northing else 'south'} hemisphere.")

    def generate(self):
        for component in self._components:
            component.process()


# region debug
cwd = os.getcwd()
coordinates = (45.260215643628264, 19.808635347472343)
distance = 2048
map_directory = os.path.join(cwd, "output")
map_template = os.path.join(cwd, "data", "map-template.zip")
blur_seed = 5
max_height = 800

from rich.console import Console


class CConsole(Console):
    def __init__(self):
        super().__init__()

    def debug(self, msg):
        self.log(msg)

    def info(self, msg):
        self.log(msg)

    def warning(self, msg):
        self.log(msg)


if __name__ == "__main__":
    mp = Map(
        coordinates, distance, map_directory, blur_seed, max_height, map_template, logger=CConsole()
    )
    mp.generate()

# endregion
