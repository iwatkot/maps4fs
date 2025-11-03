"""This module contains the Game class and its subclasses. Game class is used to define
different versions of the game for which the map is generated. Each game has its own map
template file and specific settings for map generation."""

from __future__ import annotations

import os
from typing import Callable

import maps4fs.generator.config as mfscfg
from maps4fs.generator.component.background import Background
from maps4fs.generator.component.building import Building
from maps4fs.generator.component.config import Config
from maps4fs.generator.component.grle import GRLE
from maps4fs.generator.component.i3d import I3d
from maps4fs.generator.component.road import Road
from maps4fs.generator.component.satellite import Satellite
from maps4fs.generator.component.texture import Texture


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
    dem_multipliyer: int = 2
    _additional_dem_name: str | None = None
    _map_template_file: str | None = None
    _texture_schema_file: str | None = None
    _grle_schema_file: str | None = None
    _tree_schema_file: str | None = None
    _buildings_schema_file: str | None = None
    _i3d_processing: bool = True
    _plants_processing: bool = True
    _environment_processing: bool = True
    _fog_processing: bool = True
    _dissolve: bool = True
    _mesh_processing: bool = True

    # Order matters! Some components depend on others.
    components = [Satellite, Texture, Background, GRLE, I3d, Config, Road, Building]

    def __init__(self, map_template_path: str | None = None):
        if map_template_path:
            self._map_template_path = map_template_path
        else:
            if not self._map_template_file:
                raise ValueError("Map template file not set.")
            self._map_template_path = os.path.join(
                mfscfg.MFS_TEMPLATES_DIR, self._map_template_file  # type: ignore
            )

        if not self._texture_schema_file:
            self._texture_schema = None
        else:
            self._texture_schema = os.path.join(mfscfg.MFS_TEMPLATES_DIR, self._texture_schema_file)  # type: ignore

        if not self._grle_schema_file:
            self._grle_schema = None
        else:
            self._grle_schema = os.path.join(mfscfg.MFS_TEMPLATES_DIR, self._grle_schema_file)  # type: ignore

        if not self._tree_schema_file:
            self._tree_schema = None
        else:
            self._tree_schema = os.path.join(mfscfg.MFS_TEMPLATES_DIR, self._tree_schema_file)  # type: ignore

        if not self._buildings_schema_file:
            self._buildings_schema_file = None
        else:
            self._buildings_schema_file = os.path.join(mfscfg.MFS_TEMPLATES_DIR, self._buildings_schema_file)  # type: ignore

    def set_components_by_names(self, component_names: list[str]) -> None:
        """Sets the components used for map generation by their names.

        Arguments:
            component_names (list[str]): List of component names to be used.
        """
        self.components = [comp for comp in self.components if comp.__name__ in component_names]

    def map_xml_path(self, map_directory: str) -> str:
        """Returns the path to the map.xml file.

        Arguments:
            map_directory (str): The path to the map directory.

        Returns:
            str: The path to the map.xml file.
        """
        return os.path.join(map_directory, "maps", "map", "map.xml")

    @classmethod
    def from_code(cls, code: str, map_template_path: str | None = None) -> Game:
        """Returns the game instance based on the game code.

        Arguments:
            code (str): The code of the game.
            map_template_path (str, optional): Path to the map template file. Defaults to None.

        Returns:
            Game: The game instance.
        """
        for game in cls.__subclasses__():
            if game.code and game.code.lower() == code.lower():
                return game(map_template_path)
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

    @property
    def grle_schema(self) -> str:
        """Returns the path to the GRLE layers schema file.

        Raises:
            ValueError: If the GRLE layers schema path is not set.

        Returns:
            str: The path to the GRLE layers schema file."""
        if not self._grle_schema:
            raise ValueError("GRLE layers schema path not set.")
        return self._grle_schema

    @property
    def tree_schema(self) -> str:
        """Returns the path to the tree layers schema file.

        Raises:
            ValueError: If the tree layers schema path is not set.

        Returns:
            str: The path to the tree layers schema file."""
        if not self._tree_schema:
            raise ValueError("Tree layers schema path not set.")
        return self._tree_schema

    @property
    def buildings_schema(self) -> str:
        """Returns the path to the buildings layers schema file.

        Raises:
            ValueError: If the buildings layers schema path is not set.

        Returns:
            str: The path to the buildings layers schema file."""
        if not self._buildings_schema_file:
            raise ValueError("Buildings layers schema path not set.")
        return self._buildings_schema_file

    def dem_file_path(self, map_directory: str) -> str:
        """Returns the path to the DEM file.

        Arguments:
            map_directory (str): The path to the map directory.

        Returns:
            str: The path to the DEM file."""
        raise NotImplementedError

    def weights_dir_path(self, map_directory: str) -> str:
        """Returns the path to the weights directory.

        Arguments:
            map_directory (str): The path to the map directory.

        Returns:
            str: The path to the weights directory."""
        raise NotImplementedError

    def license_plates_dir_path(self, map_directory: str) -> str:
        """Returns the path to the license plates directory.

        Arguments:
            map_directory (str): The path to the map directory.

        Returns:
            str: The path to the license plates directory."""
        raise NotImplementedError

    def get_density_map_fruits_path(self, map_directory: str) -> str:
        """Returns the path to the density map fruits file.

        Arguments:
            map_directory (str): The path to the map directory.

        Returns:
            str: The path to the density map fruits file."""
        weights_dir = self.weights_dir_path(map_directory)
        return os.path.join(weights_dir, "densityMap_fruits.png")

    def get_farmlands_path(self, map_directory: str) -> str:
        """Returns the path to the farmlands file.

        Arguments:
            map_directory (str): The path to the map directory.

        Returns:
            str: The path to the farmlands file."""
        weights_dir = self.weights_dir_path(map_directory)
        return os.path.join(weights_dir, "infoLayer_farmlands.png")

    def get_environment_path(self, map_directory: str) -> str:
        """Returns the path to the environment file.

        Arguments:
            map_directory (str): The path to the map directory.

        Returns:
            str: The path to the environment file."""
        weights_dir = self.weights_dir_path(map_directory)
        return os.path.join(weights_dir, "infoLayer_environment.png")

    def get_indoor_mask_path(self, map_directory: str) -> str:
        """Returns the path to the indoor mask file.

        Arguments:
            map_directory (str): The path to the map directory.

        Returns:
            str: The path to the indoor mask file."""
        weights_dir = self.weights_dir_path(map_directory)
        return os.path.join(weights_dir, "infoLayer_indoorMask.png")

    def get_farmlands_xml_path(self, map_directory: str) -> str:
        """Returns the path to the farmlands xml file.

        Arguments:
            map_directory (str): The path to the map directory.

        Returns:
            str: The path to the farmlands xml file."""
        raise NotImplementedError

    def get_environment_xml_path(self, map_directory: str) -> str:
        """Returns the path to the environment xml file.

        Arguments:
            map_directory (str): The path to the map directory.

        Returns:
            str: The path to the environment xml file."""
        raise NotImplementedError

    def i3d_file_path(self, map_directory: str) -> str:
        """Returns the path to the i3d file.

        Arguments:
            map_directory (str): The path to the map directory.

        Returns:
            str: The path to the i3d file."""
        raise NotImplementedError

    def overview_file_path(self, map_directory: str) -> str:
        """Returns the path to the overview image file.

        Arguments:
            map_directory (str): The path to the map directory.

        Returns:
            str: The path to the overview image file."""
        raise NotImplementedError

    @property
    def i3d_processing(self) -> bool:
        """Returns whether the i3d file should be processed.

        Returns:
            bool: True if the i3d file should be processed, False otherwise."""
        return self._i3d_processing

    @property
    def environment_processing(self) -> bool:
        """Returns whether the environment should be processed.

        Returns:
            bool: True if the environment should be processed, False otherwise."""
        return self._environment_processing

    @property
    def fog_processing(self) -> bool:
        """Returns whether the fog should be processed.

        Returns:
            bool: True if the fog should be processed, False otherwise."""
        return self._fog_processing

    @property
    def plants_processing(self) -> bool:
        """Returns whether the plants should be processed.

        Returns:
            bool: True if the plants should be processed, False otherwise."""
        return self._plants_processing

    @property
    def additional_dem_name(self) -> str | None:
        """Returns the name of the additional DEM file.

        Returns:
            str | None: The name of the additional DEM file."""
        return self._additional_dem_name

    def splines_file_path(self, map_directory: str) -> str:
        """Returns the path to the splines file.

        Arguments:
            map_directory (str): The path to the map directory.

        Returns:
            str: The path to the splines file."""
        i3d_base_directory = os.path.dirname(self.i3d_file_path(map_directory))
        return os.path.join(i3d_base_directory, "splines.i3d")

    @property
    def dissolve(self) -> bool:
        """Returns whether the dissolve should be applied.

        Returns:
            bool: True if the dissolve should be applied, False otherwise."""
        return self._dissolve

    @property
    def mesh_processing(self) -> bool:
        """Returns whether the mesh should be processed.

        Returns:
            bool: True if the mesh should be processed, False otherwise."""
        return self._mesh_processing

    def validate_template(self, map_directory: str) -> None:
        """Validates that all required files exist in the map template directory.

        Arguments:
            map_directory (str): The path to the map directory.

        Raises:
            FileNotFoundError: If any required files are missing from the template.
        """
        all_files = []
        for root, _, files in os.walk(map_directory):
            for file in files:
                all_files.append(os.path.join(root, file))

        missing_files = []
        for func in self.required_file_methods():
            try:
                required_filepath = func(map_directory)
            except NotImplementedError:
                continue
            if required_filepath not in all_files:
                missing_files.append(required_filepath)
        if missing_files:
            raise FileNotFoundError(f"The following files are not found: {missing_files}.")

    def required_file_methods(self) -> list[Callable[[str], str]]:
        """Returns a list of methods that return paths to required files for map generation.

        Returns:
            list[Callable[[str], str]]: List of methods that take a map directory path
                and return file paths that are required for the map template.
        """
        return [
            self.map_xml_path,
            self.i3d_file_path,
            self.get_environment_xml_path,
            self.get_farmlands_xml_path,
        ]


class FS22(Game):
    """Class used to define the game version FS22."""

    code = "FS22"
    _map_template_file = "fs22-map-template.zip"
    _texture_schema_file = "fs22-texture-schema.json"
    _i3d_processing = False
    _environment_processing = False
    _fog_processing = False
    _plants_processing = False
    _dissolve = False
    _mesh_processing = False

    def dem_file_path(self, map_directory: str) -> str:
        """Returns the path to the DEM file.

        Arguments:
            map_directory (str): The path to the map directory.

        Returns:
            str: The path to the DEM file."""
        return os.path.join(map_directory, "maps", "map", "data", "map_dem.png")

    def weights_dir_path(self, map_directory: str) -> str:
        """Returns the path to the weights directory.

        Arguments:
            map_directory (str): The path to the map directory.

        Returns:
            str: The path to the weights directory."""
        return os.path.join(map_directory, "maps", "map", "data")

    def i3d_file_path(self, map_directory: str) -> str:
        """Returns the path to the i3d file.

        Arguments:
            map_directory (str): The path to the map directory.

        Returns:
            str: The path to the i3d file."""
        return os.path.join(map_directory, "maps", "map", "map.i3d")


class FS25(Game):
    """Class used to define the game version FS25."""

    code = "FS25"
    dem_multipliyer: int = 2
    _additional_dem_name = "unprocessedHeightMap.png"
    _map_template_file = "fs25-map-template.zip"
    _texture_schema_file = "fs25-texture-schema.json"
    _grle_schema_file = "fs25-grle-schema.json"
    _tree_schema_file = "fs25-tree-schema.json"
    _buildings_schema_file = "fs25-buildings-schema.json"

    def dem_file_path(self, map_directory: str) -> str:
        """Returns the path to the DEM file.

        Arguments:
            map_directory (str): The path to the map directory.

        Returns:
            str: The path to the DEM file."""
        return os.path.join(map_directory, "map", "data", "dem.png")

    def map_xml_path(self, map_directory: str) -> str:
        """Returns the path to the map.xml file.

        Arguments:
            map_directory (str): The path to the map directory.

        Returns:
            str: The path to the map.xml file.
        """
        return os.path.join(map_directory, "map", "map.xml")

    def weights_dir_path(self, map_directory: str) -> str:
        """Returns the path to the weights directory.

        Arguments:
            map_directory (str): The path to the map directory.

        Returns:
            str: The path to the weights directory."""
        return os.path.join(map_directory, "map", "data")

    def license_plates_dir_path(self, map_directory: str) -> str:
        """Returns the path to the license plates directory.

        Arguments:
            map_directory (str): The path to the map directory.

        Returns:
            str: The path to the license plates directory."""
        return os.path.join(map_directory, "map", "licensePlates")

    def i3d_file_path(self, map_directory: str) -> str:
        """Returns the path to the i3d file.

        Arguments:
            map_directory (str): The path to the map directory.

        Returns:
            str: The path to the i3d file."""
        return os.path.join(map_directory, "map", "map.i3d")

    def get_farmlands_xml_path(self, map_directory: str) -> str:
        """Returns the path to the farmlands xml file.

        Arguments:
            map_directory (str): The path to the map directory.

        Returns:
            str: The path to the farmlands xml file."""
        return os.path.join(map_directory, "map", "config", "farmlands.xml")

    def get_environment_xml_path(self, map_directory: str) -> str:
        """Returns the path to the environment xml file.

        Arguments:
            map_directory (str): The path to the map directory.

        Returns:
            str: The path to the environment xml file."""
        return os.path.join(map_directory, "map", "config", "environment.xml")

    def overview_file_path(self, map_directory: str) -> str:
        """Returns the path to the overview image file.

        Arguments:
            map_directory (str): The path to the map directory.

        Returns:
            str: The path to the overview image file."""
        return os.path.join(map_directory, "map", "overview.dds")
