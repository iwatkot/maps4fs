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
from dataclasses import dataclass, field
from typing import Any

from maps4fs.generator.component.background import Background
from maps4fs.generator.component.building import Building
from maps4fs.generator.component.config import Config
from maps4fs.generator.component.dem import DEM
from maps4fs.generator.component.electricity import Electricity
from maps4fs.generator.component.grle import GRLE
from maps4fs.generator.component.road import Road
from maps4fs.generator.component.satellite import Satellite
from maps4fs.generator.component.scene import Scene
from maps4fs.generator.component.soil import Soil
from maps4fs.generator.component.texture import Texture
from maps4fs.generator.component.water import Water
from maps4fs.generator.constants import Paths
from maps4fs.generator.settings import Parameters


@dataclass
class GameConfig:
    """Game-specific XML paths and tuning values.

    Components read these instead of embedding literals, so a new game requires
    only a new ``Game`` subclass that passes a customised ``GameConfig`` —
    no changes to component code.
    """

    # --- I3D XPaths ---
    i3d_terrain_xpath: str = ".//Scene/TerrainTransformGroup"
    i3d_sun_xpath: str = ".//Scene/Light[@name='sun']"
    i3d_displacement_layer_xpath: str = ".//Scene/TerrainTransformGroup/Layers/DisplacementLayer"
    i3d_layers_xpath: str = ".//Scene/TerrainTransformGroup/Layers"
    i3d_gameplay_xpath: str = ".//TransformGroup[@name='gameplay']"
    i3d_fields_xpath: str = ".//TransformGroup[@name='fields']"

    # --- I3D structural element XPaths ---
    i3d_scene_xpath: str = ".//Scene"
    i3d_shapes_xpath: str = ".//Shapes"
    i3d_files_xpath: str = ".//Files"
    i3d_user_attributes_xpath: str = ".//UserAttributes"
    i3d_shape_xpath: str = ".//Shape"
    i3d_material_xpath: str = ".//Material"

    # --- I3D named element XPaths ---
    i3d_bg_terrain_material_xpath: str = ".//Material[@name='background_terrain_material']"
    i3d_bg_terrain_shape_xpath: str = ".//Shape[@name='background_terrain_shape']"
    i3d_ocean_material_xpath: str = ".//Material[@name='OceanShader']"
    i3d_water_shader_file_xpath: str = "File[@fileId='3']"
    i3d_mapbounds_tg_xpath: str = ".//Scene/TransformGroup[@name='mapbounds']"
    i3d_foliage_multilayer_xpath: str = ".//FoliageMultiLayer"
    i3d_farmlands_info_layer_xpath: str = ".//InfoLayer[@name='farmlands']"
    i3d_soil_map_info_layer_xpath: str = ".//InfoLayer[@name='soilMap']"
    i3d_indoor_mask_info_layer_xpath: str = ".//InfoLayer[@name='indoorMask']"
    i3d_indoor_mask_group_xpath: str = ".//InfoLayer[@name='indoorMask']/Group"
    i3d_all_file_nodes_xpath: str = ".//File"
    i3d_file_by_id_xpath_template: str = ".//Files/File[@fileId='{file_id}']"
    i3d_file_by_filename_xpath_template: str = ".//Files/File[@filename='{filename}']"

    # --- Buildings I3D element and attribute names ---
    i3d_buildings_group_name: str = "buildings"
    i3d_transform_group_tag: str = "TransformGroup"
    i3d_files_section_tag: str = "Files"
    i3d_file_tag: str = "File"
    i3d_reference_node_tag: str = "ReferenceNode"
    i3d_attr_name: str = "name"
    i3d_attr_file_id: str = "fileId"
    i3d_attr_filename: str = "filename"
    i3d_attr_translation: str = "translation"
    i3d_attr_rotation: str = "rotation"
    i3d_attr_reference_id: str = "referenceId"
    i3d_attr_node_id: str = "nodeId"
    i3d_zero_translation: str = "0 0 0"

    # --- Scene XML tag/attribute names ---
    i3d_shape_tag: str = "Shape"
    i3d_nurbs_curve_tag: str = "NurbsCurve"
    i3d_cv_tag: str = "cv"
    i3d_note_tag: str = "Note"
    i3d_user_attributes_tag: str = "UserAttributes"
    i3d_user_attribute_tag: str = "UserAttribute"
    i3d_attribute_tag: str = "Attribute"
    i3d_custom_parameter_tag: str = "CustomParameter"
    i3d_normalmap_tag: str = "Normalmap"

    i3d_attr_shape_id: str = "shapeId"
    i3d_attr_degree: str = "degree"
    i3d_attr_form: str = "form"
    i3d_attr_point: str = "c"
    i3d_attr_text: str = "text"
    i3d_attr_color: str = "color"
    i3d_attr_fixed_size: str = "fixedSize"
    i3d_attr_type: str = "type"
    i3d_attr_value: str = "value"
    i3d_attr_last_shadow_min: str = "lastShadowMapSplitBboxMin"
    i3d_attr_last_shadow_max: str = "lastShadowMapSplitBboxMax"
    i3d_attr_size: str = "size"
    i3d_attr_max_height: str = "maxHeight"
    i3d_attr_receive_shadows: str = "receiveShadows"
    i3d_attr_specular_color: str = "specularColor"
    i3d_attr_custom_shader_id: str = "customShaderId"
    i3d_attr_custom_shader_variation: str = "customShaderVariation"
    i3d_attr_static: str = "static"
    i3d_attr_collision_filter_group: str = "collisionFilterGroup"
    i3d_attr_collision_filter_mask: str = "collisionFilterMask"
    i3d_attr_casts_shadows: str = "castsShadows"
    i3d_attr_scale: str = "scale"
    i3d_attr_num_type_index_channels: str = "numTypeIndexChannels"
    i3d_attr_num_channels: str = "numChannels"
    i3d_attr_runtime: str = "runtime"
    i3d_attr_first_channel: str = "firstChannel"

    # --- I3D tuning values ---
    sun_bbox_y_min: int = -128
    sun_bbox_y_max: int = 148
    displacement_size_multiplier: int = 8

    # --- Environment XML XPaths ---
    env_latitude_xpath: str = "./latitude"
    env_seasons_xpath: str = ".//weather/season"
    env_fog_max_height_xpath: str = "./fog/heightFog/maxHeight"

    # --- Map XML ---
    map_xml_license_plates_xpath: str = ".//licensePlates"
    map_xml_license_plates_filename: str = "map/licensePlates/licensePlatesPL.xml"
    map_xml_precision_farming_xpath: str = "./precisionFarming"
    map_xml_precision_farming_soil_map_xpath: str = "./precisionFarming/soilMap"

    # --- License plate XML structure ---
    lp_xml_license_plate_xpath: str = ".//licensePlate"
    lp_xml_variations_xpath: str = "variations"
    lp_xml_variation_xpath: str = "variation"
    lp_xml_value_xpath: str = "value"
    lp_xml_char_pos_x_values: list[str] = field(
        default_factory=lambda: ["-0.1712", "-0.1172", "-0.0632"]
    )

    # --- License plate I3D ---
    lp_i3d_file_elements_xpath: str = ".//File"
    lp_i3d_texture_file_id: str = "12"
    lp_i3d_eu_texture_filename: str = "licensePlates_diffuseEU.png"
    lp_i3d_default_texture_filename: str = "licensePlates_diffuse.png"


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
    components: list[type[Any]] = [
        Satellite,
        Texture,
        DEM,
        Water,
        Background,
        GRLE,
        Config,
        Soil,
        Road,
        Scene,
        Building,
        Electricity,
    ]

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
    _ELECTRICITY_SCHEMA: str = ""
    _BACKGROUND_SCHEMA: str = ""
    _MAP_TEMPLATE: str = ""

    # Game-specific XML paths and tuning values.
    # Subclasses may replace this with a customised GameConfig instance.
    config: GameConfig = GameConfig()

    def __init_subclass__(cls, **kwargs: object) -> None:
        """Register subclasses by game code for dynamic lookup.

        Arguments:
            cls (type[Game]): Newly created subclass.
            **kwargs (object): Additional subclass initialization arguments.
        """
        super().__init_subclass__(**kwargs)
        if cls.code:
            Game._registry[cls.code.upper()] = cls

    def __init__(self, map_template_path: str | None = None) -> None:
        """Initialize schema/template paths and map-relative placeholders.

        Arguments:
            map_template_path (str | None): Optional override for the map template archive path.
        """
        templates_dir = Paths.TEMPLATES_DIR
        self.template_path: str = map_template_path or os.path.join(
            templates_dir, self._MAP_TEMPLATE
        )
        self.texture_schema: str = os.path.join(templates_dir, self._TEXTURE_SCHEMA)
        self.grle_schema: str = os.path.join(templates_dir, self._GRLE_SCHEMA)
        self.tree_schema: str = os.path.join(templates_dir, self._TREE_SCHEMA)
        self.buildings_schema: str = os.path.join(templates_dir, self._BUILDINGS_SCHEMA)
        self.electricity_schema: str = os.path.join(templates_dir, self._ELECTRICITY_SCHEMA)
        self.background_schema: str = (
            os.path.join(templates_dir, self._BACKGROUND_SCHEMA) if self._BACKGROUND_SCHEMA else ""
        )

        # Map-relative paths — populated by set_map_directory()
        self.dem_file_path: str = ""
        self.weights_dir_path: str = ""
        self.i3d_file_path: str = ""
        self.splines_file_path: str = ""
        self.map_xml_path: str = ""
        self.farmlands_xml_path: str = ""
        self.environment_xml_path: str = ""
        self.overview_file_path: str = ""
        self.license_plates_dir_path: str = ""
        self.farmlands_path: str = ""
        self.environment_path: str = ""
        self.indoor_mask_path: str = ""
        self.density_map_fruits_path: str = ""

    @classmethod
    def from_code(cls, code: str, map_template_path: str | None = None) -> Game:
        """Return a Game instance for the given game code.

        Arguments:
            code (str): The game code, e.g. ``"FS25"``.
            map_template_path (str, optional): Override for the map template zip.

        Returns:
            Game: Instantiated game definition for the requested code.

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
    _ELECTRICITY_SCHEMA = "fs25-electricity-schema.json"
    _BACKGROUND_SCHEMA = "fs25-background-schema.json"
    _MAP_TEMPLATE = "fs25-map-template.zip"
