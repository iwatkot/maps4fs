"""This module contains the Config class for map settings and configuration."""

from __future__ import annotations

import os
from xml.etree import ElementTree as ET

from maps4fs.generator.component import Component

DEFAULT_HEIGHT_SCALE = 2000
DEFAULT_MAX_LOD_DISTANCE = 10000
DEFAULT_MAX_LOD_OCCLUDER_DISTANCE = 10000


# pylint: disable=R0903
class I3d(Component):
    """Component for map i3d file settings and configuration.

    Args:
        coordinates (tuple[float, float]): The latitude and longitude of the center of the map.
        map_height (int): The height of the map in pixels.
        map_width (int): The width of the map in pixels.
        map_directory (str): The directory where the map files are stored.
        logger (Any, optional): The logger to use. Must have at least three basic methods: debug,
            info, warning. If not provided, default logging will be used.
    """

    _map_i3d_path: str | None = None

    def preprocess(self) -> None:
        """Gets the path to the map I3D file from the game instance and saves it to the instance
        attribute. If the game does not support I3D files, the attribute is set to None."""
        try:
            self._map_i3d_path = self.game.i3d_file_path(self.map_directory)
            self.logger.debug("Map I3D path: %s.", self._map_i3d_path)
        except NotImplementedError:
            self.logger.info("I3D file processing is not implemented for this game.")
            self._map_i3d_path = None

    def process(self) -> None:
        """Updates the map I3D file with the default settings."""
        self._update_i3d_file()

    def _update_i3d_file(self) -> None:
        """Updates the map I3D file with the default settings."""
        if not self._map_i3d_path:
            self.logger.info("I3D is not obtained, skipping the update.")
            return
        if not os.path.isfile(self._map_i3d_path):
            self.logger.warning("I3D file not found: %s.", self._map_i3d_path)
            return

        tree = ET.parse(self._map_i3d_path)

        self.logger.debug("Map I3D file loaded from: %s.", self._map_i3d_path)

        root = tree.getroot()
        for map_elem in root.iter("Scene"):
            for terrain_elem in map_elem.iter("TerrainTransformGroup"):
                terrain_elem.set("heightScale", str(DEFAULT_HEIGHT_SCALE))
                self.logger.debug(
                    "heightScale attribute set to %s in TerrainTransformGroup element.",
                    DEFAULT_HEIGHT_SCALE,
                )
                terrain_elem.set("maxLODDistance", str(DEFAULT_MAX_LOD_DISTANCE))
                self.logger.debug(
                    "maxLODDistance attribute set to %s in TerrainTransformGroup element.",
                    DEFAULT_MAX_LOD_DISTANCE,
                )

                terrain_elem.set("occMaxLODDistance", str(DEFAULT_MAX_LOD_OCCLUDER_DISTANCE))
                self.logger.debug(
                    "occMaxLODDistance attribute set to %s in TerrainTransformGroup element.",
                    DEFAULT_MAX_LOD_OCCLUDER_DISTANCE,
                )

                self.logger.debug("TerrainTransformGroup element updated in I3D file.")

        tree.write(self._map_i3d_path)
        self.logger.debug("Map I3D file saved to: %s.", self._map_i3d_path)

    def previews(self) -> list[str]:
        """Returns a list of paths to the preview images (empty list).
        The component does not generate any preview images so it returns an empty list.

        Returns:
            list[str]: An empty list.
        """
        return []
