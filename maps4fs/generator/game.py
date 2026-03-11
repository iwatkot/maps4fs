"""Game definitions for maps4fs map generation.

``Game`` is the base class. Each supported game is a subclass that sets its
own path constants and schema file names. ``Game.from_code("FS25")`` looks up
the subclass registry and returns the right instance.

Adding a new game requires only a new subclass — no changes to ``Game``.

Call ``set_map_directory()`` once the map directory is known; this populates
all map-relative path attributes so callers can access them as plain strings
without passing a directory argument.
"""

from __future__ import annotations

import os

from maps4fs.generator.component.background import Background
from maps4fs.generator.component.building import Building
from maps4fs.generator.component.config import Config
from maps4fs.generator.component.grle import GRLE
from maps4fs.generator.component.road import Road
from maps4fs.generator.component.satellite import Satellite
from maps4fs.generator.component.scene import Scene
from maps4fs.generator.component.texture import Texture
from maps4fs.generator.constants import Paths
from maps4fs.generator.settings import Parameters


class Game:
    """Base class for game definitions.

    Subclass this to add a new game. Set ``code`` and override all ``_*``
    path/schema constants. The subclass is automatically registered and
    discoverable via ``Game.from_code()``.

    Call ``set_map_directory()`` once the concrete map directory is known.
    After that all ``*_path`` / ``*_dir`` attributes are ready plain strings.
    """

    _registry: dict[str, type[Game]] = {}

    # Order matters — some components depend on earlier ones.
    # Subclasses may override to use a different component list.
    components = [Satellite, Texture, Background, GRLE, Config, Road, Scene, Building]

    # Subclasses must set a non-empty code.
    code: str = ""

    # Relative paths inside the map directory — subclasses must override.
    _DEM_PATH: str = ""
    _WEIGHTS_DIR: str = ""
    _I3D_PATH: str = ""
    _SPLINES_PATH: str = ""
    _MAP_XML: str = ""
    _FARMLANDS_XML: str = ""
    _ENVIRONMENT_XML: str = ""
    _OVERVIEW_PATH: str = ""
    _LICENSE_PLATES_DIR: str = ""
    additional_dem_name: str = ""

    # Schema file names relative to the templates directory — subclasses must override.
    _TEXTURE_SCHEMA: str = ""
    _GRLE_SCHEMA: str = ""
    _TREE_SCHEMA: str = ""
    _BUILDINGS_SCHEMA: str = ""
    _MAP_TEMPLATE: str = ""

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls.code:
            Game._registry[cls.code.upper()] = cls

    def __init__(self, map_template_path: str | None = None) -> None:
        templates_dir = Paths.TEMPLATES_DIR
        self.template_path: str = map_template_path or os.path.join(
            templates_dir, self._MAP_TEMPLATE
        )
        self.texture_schema: str = os.path.join(templates_dir, self._TEXTURE_SCHEMA)
        self.grle_schema: str = os.path.join(templates_dir, self._GRLE_SCHEMA)
        self.tree_schema: str = os.path.join(templates_dir, self._TREE_SCHEMA)
        self.buildings_schema: str = os.path.join(templates_dir, self._BUILDINGS_SCHEMA)

        # Map-relative paths — populated by set_map_directory()
        self.dem_file_path: str | None = None
        self.weights_dir_path: str | None = None
        self.i3d_file_path: str | None = None
        self.splines_file_path: str | None = None
        self.map_xml_path: str | None = None
        self.farmlands_xml_path: str | None = None
        self.environment_xml_path: str | None = None
        self.overview_file_path: str | None = None
        self.license_plates_dir_path: str | None = None
        self.farmlands_path: str | None = None
        self.environment_path: str | None = None
        self.indoor_mask_path: str | None = None
        self.density_map_fruits_path: str | None = None

    @classmethod
    def from_code(cls, code: str, map_template_path: str | None = None) -> "Game":
        """Return a Game instance for the given game code.

        Arguments:
            code (str): The game code, e.g. ``"FS25"``.
            map_template_path (str, optional): Override for the map template zip.

        Raises:
            ValueError: If the code is not recognised.
        """
        game_cls = Game._registry.get(code.upper())
        if game_cls is None:
            raise ValueError(f"Game with code {code!r} not found.")
        return game_cls(map_template_path)

    def set_map_directory(self, map_directory: str) -> None:
        """Resolve and store all map-relative paths for the given directory.

        Call once per generation session, right after the map directory is known.

        Arguments:
            map_directory (str): Absolute path to the map working directory.
        """
        weights_dir = os.path.join(map_directory, self._WEIGHTS_DIR)
        self.dem_file_path = os.path.join(map_directory, self._DEM_PATH)
        self.weights_dir_path = weights_dir
        self.i3d_file_path = os.path.join(map_directory, self._I3D_PATH)
        self.splines_file_path = os.path.join(map_directory, self._SPLINES_PATH)
        self.map_xml_path = os.path.join(map_directory, self._MAP_XML)
        self.farmlands_xml_path = os.path.join(map_directory, self._FARMLANDS_XML)
        self.environment_xml_path = os.path.join(map_directory, self._ENVIRONMENT_XML)
        self.overview_file_path = os.path.join(map_directory, self._OVERVIEW_PATH)
        self.license_plates_dir_path = os.path.join(map_directory, self._LICENSE_PLATES_DIR)
        self.farmlands_path = os.path.join(weights_dir, Parameters.INFO_LAYER_FARMLANDS)
        self.environment_path = os.path.join(weights_dir, Parameters.INFO_LAYER_ENVIRONMENT)
        self.indoor_mask_path = os.path.join(weights_dir, "infoLayer_indoorMask.png")
        self.density_map_fruits_path = os.path.join(weights_dir, Parameters.DENSITY_MAP_FRUITS)

    def set_components_by_names(self, component_names: list[str]) -> None:
        """Filter the component list to only those whose class names are given."""
        self.components = [c for c in self.components if c.__name__ in component_names]


class FS25(Game):
    """Farming Simulator 25 game definition."""

    code = "FS25"

    # Relative paths inside the map directory
    _DEM_PATH = os.path.join("map", "data", "dem.png")
    _WEIGHTS_DIR = os.path.join("map", "data")
    _I3D_PATH = os.path.join("map", "map.i3d")
    _SPLINES_PATH = os.path.join("map", "splines.i3d")
    _MAP_XML = os.path.join("map", "map.xml")
    _FARMLANDS_XML = os.path.join("map", "config", "farmlands.xml")
    _ENVIRONMENT_XML = os.path.join("map", "config", "environment.xml")
    _OVERVIEW_PATH = os.path.join("map", "overview.dds")
    _LICENSE_PLATES_DIR = os.path.join("map", "licensePlates")
    additional_dem_name = "unprocessedHeightMap.png"

    # Schema file names relative to the templates directory
    _TEXTURE_SCHEMA = "fs25-texture-schema.json"
    _GRLE_SCHEMA = "fs25-grle-schema.json"
    _TREE_SCHEMA = "fs25-tree-schema.json"
    _BUILDINGS_SCHEMA = "fs25-buildings-schema.json"
    _MAP_TEMPLATE = "fs25-map-template.zip"
