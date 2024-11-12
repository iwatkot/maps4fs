"""This module contains the Game class and its subclasses. Game class is used to define
different versions of the game for which the map is generated. Each game has its own map
template file and specific settings for map generation."""

from __future__ import annotations

import os

from maps4fs.generator.config import Config
from maps4fs.generator.dem import DEM
from maps4fs.generator.texture import Texture

working_directory = os.getcwd()


class Game:
    """Class used to define different versions of the game for which the map is generated.

    Arguments:
        map_template_path (str, optional): Path to the map template file. Defaults to None.

    Attributes and Properties:
        code (str): The code of the game.
        components (list[Type[Component]]): List of components used for map generation.
        map_template_path (str): Path to the map template file.

    Public Methods:
        from_code(cls, code: str) -> Game: Returns the game instance based on the game code.
    """

    code: str | None = None
    dem_multipliyer: int = 1
    _map_template_path: str | None = None
    _texture_schema: str | None = None

    components = [Config, Texture, DEM]

    def __init__(self, map_template_path: str | None = None):
        if map_template_path:
            self._map_template_path = map_template_path

    def map_xml_path(self, map_directory: str) -> str:
        """Returns the path to the map.xml file.

        Arguments:
            map_directory (str): The path to the map directory.

        Returns:
            str: The path to the map.xml file.
        """
        return os.path.join(map_directory, "maps", "map", "map.xml")

    @classmethod
    def from_code(cls, code: str) -> Game:
        """Returns the game instance based on the game code.

        Arguments:
            code (str): The code of the game.

        Returns:
            Game: The game instance.
        """
        for game in cls.__subclasses__():
            if game.code and game.code.lower() == code.lower():
                return game()
        raise ValueError(f"Game with code {code} not found.")

    @property
    def template_path(self) -> str:
        """Returns the path to the map template file.

        Raises:
            ValueError: If the map template path is not set.

        Returns:
            str: The path to the map template file."""
        if not self._map_template_path:
            raise ValueError("Map template path not set.")
        return self._map_template_path

    @property
    def texture_schema(self) -> str:
        """Returns the path to the texture layers schema file.

        Raises:
            ValueError: If the texture layers schema path is not set.

        Returns:
            str: The path to the texture layers schema file."""
        if not self._texture_schema:
            raise ValueError("Texture layers schema path not set.")
        return self._texture_schema

    def dem_file_path(self, map_directory: str) -> str:
        """Returns the path to the DEM file.

        Arguments:
            map_directory (str): The path to the map directory.

        Returns:
            str: The path to the DEM file.
        """
        raise NotImplementedError


class FS22(Game):
    """Class used to define the game version FS22."""

    code = "FS22"
    _map_template_path = os.path.join(working_directory, "data", "fs22-map-template.zip")
    _texture_schema = os.path.join(working_directory, "data", "fs22-texture-schema.json")

    def dem_file_path(self, map_directory: str) -> str:
        """Returns the path to the DEM file.

        Arguments:
            map_directory (str): The path to the map directory.

        Returns:
            str: The path to the DEM file."""
        return os.path.join(map_directory, "maps", "map", "data", "map_dem.png")


class FS25(Game):
    """Class used to define the game version FS25."""

    code = "FS25"
    dem_multipliyer: int = 2
    _map_template_path = os.path.join(working_directory, "data", "fs25-map-template.zip")
    _texture_schema = os.path.join(working_directory, "data", "fs25-texture-schema.json")

    def dem_file_path(self, map_directory: str) -> str:
        """Returns the path to the DEM file.

        Arguments:
            map_directory (str): The path to the map directory.

        Returns:
            str: The path to the DEM file."""
        return os.path.join(map_directory, "maps", "map", "data", "dem.png")
