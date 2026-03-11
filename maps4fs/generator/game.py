"""Game configuration and Game class for maps4fs map generation.

FS25 is the only supported game. Adding a new game (e.g. FS28) requires
only a new GameConfig instance and its associated schema JSON files — no
component code changes are needed.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Callable

from maps4fs.generator.component.background import Background
from maps4fs.generator.component.building import Building
from maps4fs.generator.component.config import Config
from maps4fs.generator.component.grle import GRLE
from maps4fs.generator.component.road import Road
from maps4fs.generator.component.satellite import Satellite
from maps4fs.generator.component.scene import Scene
from maps4fs.generator.component.texture import Texture
from maps4fs.generator.constants import MFS_TEMPLATES_DIR
from maps4fs.generator.settings import Parameters


@dataclass
class GameConfig:
    """Data-driven descriptor for a supported game version.

    All *path* fields are relative to the map directory so they can be joined
    with any concrete map_directory at runtime.  Schema file names are
    relative to the shared templates directory.
    """

    code: str
    dem_multiplier: int

    # --- relative paths inside the map directory ---
    dem_path: str
    weights_dir: str
    i3d_path: str
    splines_path: str
    map_xml_path: str
    farmlands_xml_path: str | None
    environment_xml_path: str | None
    overview_path: str | None
    license_plates_dir: str | None
    additional_dem_name: str | None

    # --- schema file names (relative to templates dir) ---
    texture_schema: str
    grle_schema: str | None
    tree_schema: str | None
    buildings_schema: str | None
    map_template: str

    # --- feature flags ---
    i3d_processing: bool = True
    plants_processing: bool = True
    environment_processing: bool = True
    fog_processing: bool = True
    dissolve: bool = True
    mesh_processing: bool = True


# ---------------------------------------------------------------------------
# FS25 — the only supported game configuration
# ---------------------------------------------------------------------------

FS25_CONFIG = GameConfig(
    code="FS25",
    dem_multiplier=2,
    dem_path=os.path.join("map", "data", "dem.png"),
    weights_dir=os.path.join("map", "data"),
    i3d_path=os.path.join("map", "map.i3d"),
    splines_path=os.path.join("map", "splines.i3d"),
    map_xml_path=os.path.join("map", "map.xml"),
    farmlands_xml_path=os.path.join("map", "config", "farmlands.xml"),
    environment_xml_path=os.path.join("map", "config", "environment.xml"),
    overview_path=os.path.join("map", "overview.dds"),
    license_plates_dir=os.path.join("map", "licensePlates"),
    additional_dem_name="unprocessedHeightMap.png",
    texture_schema="fs25-texture-schema.json",
    grle_schema="fs25-grle-schema.json",
    tree_schema="fs25-tree-schema.json",
    buildings_schema="fs25-buildings-schema.json",
    map_template="fs25-map-template.zip",
)

_CONFIGS: dict[str, GameConfig] = {FS25_CONFIG.code: FS25_CONFIG}


# ---------------------------------------------------------------------------
# Game class
# ---------------------------------------------------------------------------


class Game:
    """Runtime wrapper around a GameConfig that provides path helpers and
    resolved schema paths.

    Arguments:
        config (GameConfig): The game configuration to use.
        map_template_path (str, optional): Override for the map template zip.
    """

    # Order matters — some components depend on earlier ones.
    components = [Satellite, Texture, Background, GRLE, Config, Road, Scene, Building]

    def __init__(self, config: GameConfig, map_template_path: str | None = None) -> None:
        self.config = config
        templates_dir = MFS_TEMPLATES_DIR

        self._template_path = map_template_path or os.path.join(templates_dir, config.map_template)
        self._texture_schema = (
            os.path.join(templates_dir, config.texture_schema) if config.texture_schema else None
        )
        self._grle_schema = (
            os.path.join(templates_dir, config.grle_schema) if config.grle_schema else None
        )
        self._tree_schema = (
            os.path.join(templates_dir, config.tree_schema) if config.tree_schema else None
        )
        self._buildings_schema = (
            os.path.join(templates_dir, config.buildings_schema)
            if config.buildings_schema
            else None
        )

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------

    @classmethod
    def from_code(cls, code: str, map_template_path: str | None = None) -> Game:
        """Return a Game instance for the given game code.

        Arguments:
            code (str): The game code (e.g. "FS25").
            map_template_path (str, optional): Override for the map template.

        Raises:
            ValueError: If the code is not recognised.
        """
        config = _CONFIGS.get(code) or _CONFIGS.get(code.upper())
        if config is None:
            raise ValueError(f"Game with code {code!r} not found.")
        return cls(config, map_template_path)

    # ------------------------------------------------------------------
    # Simple properties
    # ------------------------------------------------------------------

    @property
    def code(self) -> str:
        return self.config.code

    @property
    def dem_multiplier(self) -> int:
        return self.config.dem_multiplier

    # Typo kept as alias so existing callers keep working
    @property
    def dem_multipliyer(self) -> int:
        return self.config.dem_multiplier

    @property
    def template_path(self) -> str:
        return self._template_path

    @property
    def texture_schema(self) -> str:
        if not self._texture_schema:
            raise ValueError("Texture schema path not set.")
        return self._texture_schema

    @property
    def grle_schema(self) -> str:
        if not self._grle_schema:
            raise ValueError("GRLE schema path not set.")
        return self._grle_schema

    @property
    def tree_schema(self) -> str:
        if not self._tree_schema:
            raise ValueError("Tree schema path not set.")
        return self._tree_schema

    @property
    def buildings_schema(self) -> str:
        if not self._buildings_schema:
            raise ValueError("Buildings schema path not set.")
        return self._buildings_schema

    @property
    def additional_dem_name(self) -> str | None:
        return self.config.additional_dem_name

    @property
    def i3d_processing(self) -> bool:
        return self.config.i3d_processing

    @property
    def environment_processing(self) -> bool:
        return self.config.environment_processing

    @property
    def fog_processing(self) -> bool:
        return self.config.fog_processing

    @property
    def plants_processing(self) -> bool:
        return self.config.plants_processing

    @property
    def dissolve(self) -> bool:
        return self.config.dissolve

    @property
    def mesh_processing(self) -> bool:
        return self.config.mesh_processing

    # ------------------------------------------------------------------
    # Path helpers
    # ------------------------------------------------------------------

    def dem_file_path(self, map_directory: str) -> str:
        return os.path.join(map_directory, self.config.dem_path)

    def weights_dir_path(self, map_directory: str) -> str:
        return os.path.join(map_directory, self.config.weights_dir)

    def i3d_file_path(self, map_directory: str) -> str:
        return os.path.join(map_directory, self.config.i3d_path)

    def splines_file_path(self, map_directory: str) -> str:
        return os.path.join(map_directory, self.config.splines_path)

    def map_xml_path(self, map_directory: str) -> str:
        return os.path.join(map_directory, self.config.map_xml_path)

    def license_plates_dir_path(self, map_directory: str) -> str:
        if self.config.license_plates_dir is None:
            raise NotImplementedError
        return os.path.join(map_directory, self.config.license_plates_dir)

    def get_farmlands_xml_path(self, map_directory: str) -> str:
        if self.config.farmlands_xml_path is None:
            raise NotImplementedError
        return os.path.join(map_directory, self.config.farmlands_xml_path)

    def get_environment_xml_path(self, map_directory: str) -> str:
        if self.config.environment_xml_path is None:
            raise NotImplementedError
        return os.path.join(map_directory, self.config.environment_xml_path)

    def overview_file_path(self, map_directory: str) -> str:
        if self.config.overview_path is None:
            raise NotImplementedError
        return os.path.join(map_directory, self.config.overview_path)

    def get_farmlands_path(self, map_directory: str) -> str:
        return os.path.join(self.weights_dir_path(map_directory), Parameters.INFO_LAYER_FARMLANDS)

    def get_environment_path(self, map_directory: str) -> str:
        return os.path.join(self.weights_dir_path(map_directory), Parameters.INFO_LAYER_ENVIRONMENT)

    def get_indoor_mask_path(self, map_directory: str) -> str:
        return os.path.join(self.weights_dir_path(map_directory), "infoLayer_indoorMask.png")

    def get_density_map_fruits_path(self, map_directory: str) -> str:
        return os.path.join(self.weights_dir_path(map_directory), Parameters.DENSITY_MAP_FRUITS)

    # ------------------------------------------------------------------
    # Component management
    # ------------------------------------------------------------------

    def set_components_by_names(self, component_names: list[str]) -> None:
        """Filter the component list to only those whose class names are given."""
        self.components = [c for c in self.components if c.__name__ in component_names]

    # ------------------------------------------------------------------
    # Template validation
    # ------------------------------------------------------------------

    def required_file_methods(self) -> list[Callable[[str], str]]:
        return [
            self.map_xml_path,
            self.i3d_file_path,
            self.get_environment_xml_path,
            self.get_farmlands_xml_path,
        ]

    def validate_template(self, map_directory: str) -> None:
        """Raise FileNotFoundError if any required file is missing."""
        all_files: list[str] = []
        for froot, _, files in os.walk(map_directory):
            for ffile in files:
                all_files.append(os.path.join(froot, ffile))

        missing = []
        for func in self.required_file_methods():
            try:
                path = func(map_directory)
            except NotImplementedError:
                continue
            if path not in all_files:
                missing.append(path)

        if missing:
            raise FileNotFoundError(f"The following files are not found: {missing}.")


# ---------------------------------------------------------------------------
# Backward-compat: FS25 name still resolves to a Game whose config is FS25.
# Code that does `Game.from_code("FS25")` continues to work unchanged.
# ---------------------------------------------------------------------------

FS25 = FS25_CONFIG  # module-level alias for anything that checked `isinstance(game, FS25)`
