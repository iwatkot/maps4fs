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
    _map_template_path: str | None = None

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


class FS22(Game):
    """Class used to define the game version FS22."""

    code = "FS22"
    _map_template_path = os.path.join(working_directory, "data", "map-template-fs22.zip")


class FS25(Game):
    """Class used to define the game version FS25."""

    code = "FS25"
    _map_template_path = os.path.join(working_directory, "data", "map-template-fs25.zip")
