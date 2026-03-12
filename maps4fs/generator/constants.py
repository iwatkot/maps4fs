"""Pure path/name constants for the maps4fs generator.

Zero side effects — safe to import without triggering network requests or
filesystem mutations. All download/setup logic lives in bootstrap.py.
"""

from __future__ import annotations

import os


class Paths:
    """All static paths and names used by the generator.

    Every attribute is resolved once at class-definition time, so there are
    no repeated ``os.path.join`` calls scattered through the code base.
    Access via ``Paths.TEMPLATES_DIR``, etc.
    """

    # ---- Directory roots ------------------------------------------------
    TEMPLATES_DIR = os.path.join(os.getcwd(), "templates")
    EXECUTABLES_DIR = os.path.join(os.getcwd(), "executables")
    DEFAULTS_DIR = os.path.join(os.getcwd(), "defaults")
    LOCALE_DIR = os.path.join(os.getcwd(), "locale")

    DEM_DEFAULTS_DIR = os.path.join(DEFAULTS_DIR, "dem")
    OSM_DEFAULTS_DIR = os.path.join(DEFAULTS_DIR, "osm")
    MSETTINGS_DEFAULTS_DIR = os.path.join(DEFAULTS_DIR, "main_settings")
    GSETTINGS_DEFAULTS_DIR = os.path.join(DEFAULTS_DIR, "generation_settings")

    ROOT_DIR = os.getenv("MFS_ROOT_DIRECTORY", os.path.join(os.getcwd(), "mfsrootdir"))
    CACHE_DIR = os.path.join(ROOT_DIR, "cache")
    DATA_DIR = os.path.join(ROOT_DIR, "maps")

    DTM_CACHE_DIR = os.path.join(CACHE_DIR, "dtm")
    SAT_CACHE_DIR = os.path.join(CACHE_DIR, "sat")
    OSMNX_CACHE_DIR = os.path.join(CACHE_DIR, "osmnx")
    OSMNX_DATA_DIR = os.path.join(CACHE_DIR, "odata")

    CACHE_DIRS = [DTM_CACHE_DIR, SAT_CACHE_DIR, OSMNX_CACHE_DIR, OSMNX_DATA_DIR]

    # ---- Executable names and remote URLs --------------------------------
    I3D_CONVERTER_NAME = "i3dConverter.exe"
    I3D_CONVERTER_REMOTE_URL = "http://storage.atlasfs.xyz/mfsmedia/i3dConverter.exe"
    TEXCONV_NAME = "texconv.exe"
    TEXCONV_REMOTE_URL = (
        "https://github.com/microsoft/DirectXTex/releases/download/oct2025/texconv.exe"
    )

    # ---- Map template structure -----------------------------------------
    MAP_BOUNDS_FILENAME = "map_bounds"
    TEMPLATES_STRUCTURE = {
        "fs25": ["texture_schemas", "tree_schemas", "buildings_schemas", "map_templates"],
        "fs22": ["texture_schemas", "map_templates"],
    }

    TQDM_DISABLE = os.getenv("TQDM_DISABLE", "0") == "1"

    # ---- Path helpers ---------------------------------------------------

    @staticmethod
    def get_map_bounds_file_paths() -> tuple[str, str] | None:
        """Return paths to map_bounds.i3d and map_bounds.i3d.shapes, or None if missing."""
        i3d_path = os.path.join(Paths.TEMPLATES_DIR, f"{Paths.MAP_BOUNDS_FILENAME}.i3d")
        shapes_path = os.path.join(Paths.TEMPLATES_DIR, f"{Paths.MAP_BOUNDS_FILENAME}.i3d.shapes")
        if all(os.path.isfile(p) for p in (i3d_path, shapes_path)):
            return i3d_path, shapes_path
        return None

    @staticmethod
    def get_windows_executable_path(executable_name: str) -> str | None:
        """Return path to a Windows executable in EXECUTABLES_DIR, or None."""
        if os.name != "nt":
            return None
        expected = os.path.join(Paths.EXECUTABLES_DIR, executable_name)
        return expected if os.path.isfile(expected) else None

    @staticmethod
    def get_i3d_executable_path() -> str | None:
        """Return path to i3dConverter.exe, or None."""
        return Paths.get_windows_executable_path(Paths.I3D_CONVERTER_NAME)

    @staticmethod
    def get_texconv_executable_path() -> str | None:
        """Return path to texconv.exe, or None."""
        return Paths.get_windows_executable_path(Paths.TEXCONV_NAME)


class Parameters:
    """All named constants used across generator components.

    Domain-agnostic string keys, numeric thresholds, node ID ranges, pixel
    values, and file-name fragments.  Having everything in one place makes it
    easy to grep or change a value without hunting across many modules.
    """

    # ---- OSM / texture layer tags ---------------------------------------
    FIELD = "field"
    FIELDS = "fields"
    BUILDINGS = "buildings"
    TEXTURES = "textures"
    BACKGROUND = "background"
    FOREST = "forest"
    ROADS = "roads"
    ROADS_POLYLINES = "roads_polylines"
    WATER_POLYLINES = "water_polylines"
    WATER = "water"
    FARMYARDS = "farmyards"

    POINTS = "points"
    TAGS = "tags"
    WIDTH = "width"
    ROAD_TEXTURE = "road_texture"
    DRAIN = "drain"

    # ---- Texture channels / runtime keys -------------------------------
    TEXTURE_CHANNEL_TEXTURES = "textures"
    TEXTURE_CHANNEL_BACKGROUND = "background"
    OSM_REQUESTS_TIMEOUT = 10
    OSM_PREFETCH_WORKERS = 3

    # ---- Texture file/path fragments -----------------------------------
    MASKS_DIRECTORY = "masks"
    ROADS_DIRECTORY = "roads"
    BLOCKMASK_FILENAME = "BLOCKMASK.png"
    TEXTURES_OSM_PREVIEW_FILENAME = "textures_osm.png"
    PNG_EXTENSION = ".png"
    WEIGHT_FILE_POSTFIX = "_weight.png"

    # ---- Image / texture sizes ------------------------------------------
    MAXIMUM_BACKGROUND_TEXTURE_SIZE = 4096
    PREVIEW_MAXIMUM_SIZE = 2048
    OVERVIEW_IMAGE_SIZE = 4096
    OVERVIEW_IMAGE_FILENAME = "overview"
    FULL = "FULL"
    PREVIEW = "PREVIEW"

    # ---- Map geometry ---------------------------------------------------
    BACKGROUND_DISTANCE = 2048
    RESIZE_FACTOR = 8

    # ---- Terrain layer names --------------------------------------------
    DECIMATED_BACKGROUND = "decimated_background"
    BACKGROUND_TERRAIN = "background_terrain"
    POLYGON_WATER = "polygon_water"
    POLYLINE_WATER = "polyline_water"
    HEIGHT_SCALE = "heightScale"

    # ---- DEM file names -------------------------------------------------
    NOT_RESIZED_DEM = "not_resized.png"
    NOT_RESIZED_DEM_FOUNDATIONS = "not_resized_with_foundations.png"
    NOT_RESIZED_DEM_ROADS = "not_resized_with_flattened_roads.png"

    # Priority-ordered list of DEM variants (most to least detailed)
    SUPPORTED_DEM_TYPES = [NOT_RESIZED_DEM_ROADS, NOT_RESIZED_DEM_FOUNDATIONS, NOT_RESIZED_DEM]

    # ---- Info-layer / density map file names ----------------------------
    INFO_LAYER_FARMLANDS = "infoLayer_farmlands.png"
    DENSITY_MAP_FRUITS = "densityMap_fruits.png"
    INFO_LAYER_ENVIRONMENT = "infoLayer_environment.png"

    # ---- Plants / farmland limits ---------------------------------------
    FARMLAND_ID_LIMIT = 254
    PLANTS_ISLAND_PERCENT = 100
    PLANTS_ISLAND_MINIMUM_SIZE = 10
    PLANTS_ISLAND_MAXIMUM_SIZE = 200
    PLANTS_ISLAND_VERTEX_COUNT = 30
    PLANTS_ISLAND_ROUNDING_RADIUS = 15
    WATER_ADD_WIDTH = 2

    # ---- Background mesh segment geometry -------------------------------
    SEGMENT_LENGTH = 2
    POLYLINE_WATER_WIDTH_EXTENSION = 2

    # ---- GRLE pixel values ----------------------------------------------
    WATER_AREA_PIXEL_VALUE = 8

    # ---- Environment area type pixel values -----------------------------
    ENVIRONMENT_AREA_TYPES: dict[str, int] = {
        "open_land": 0,
        "city": 1,
        "village": 2,
        "harbor": 3,
        "industrial": 4,
        "open_water": 5,
    }

    # ---- Plant / grass pixel values -------------------------------------
    PLANT_PIXEL_VALUES: dict[str, int] = {
        "smallDenseMix": 33,
        "meadow": 131,
    }
    DEFAULT_GRASS_PIXEL_VALUE = 131

    # ---- Road Z-offset --------------------------------------------------
    PATCH_Z_OFFSET = -0.001
    ROAD_INTERSECTION_TOLERANCE = 1.0
    ROAD_PATCH_SEGMENT_PADDING = 2
    ROAD_TEXTURE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".dds")
    ROAD_MESH_FILENAME_PREFIX = "roads_"
    ASSETS_DIRECTORY = "assets"

    # ---- Road processing info keys --------------------------------------
    ROAD_INFO_TEXTURES = "road_textures"
    ROAD_INFO_TOTAL_OSM = "total_OSM_roads"
    ROAD_INFO_TOTAL_FITTED = "total_fitted_roads"
    ROAD_INFO_TOTAL_PATCHES = "total_patches_created"

    # ---- Mesh component constants --------------------------------------
    OBJ_INDEX_OFFSET = 1
    ROAD_MATERIAL_NAME = "RoadMaterial"
    TERRAIN_MATERIAL_NAME = "TerrainMaterial_XZ"
    TEXTURE_TILE_SIZE_METERS = 10.0
    UV_LIMIT = 32.0
    UV_SPLIT_SAFETY_MARGIN = 30.0
    INTERPOLATION_TARGET_SEGMENT_LENGTH = 5.0
    INTERPOLATION_MAX_ANGLE_CHANGE = 30.0

    I3D_ENCODING = "iso-8859-1"
    I3D_VERSION = "1.6"
    I3D_SCHEMA = "http://i3d.giants.ch/schema/i3d-1.6.xsd"
    I3D_XSI_NAMESPACE = "http://www.w3.org/2001/XMLSchema-instance"
    I3D_EXPORT_PROGRAM = "maps4fs"
    I3D_EXPORT_VERSION = "1.0"
    I3D_WATER_SHADER_PATH = "$data/shaders/oceanShader.xml"
    I3D_WATER_SHADER_PATH_BINARY_BROKEN = 'filename="data/shaders/oceanShader.xml"'
    I3D_WATER_SHADER_PATH_BINARY_FIXED = 'filename="$data/shaders/oceanShader.xml"'

    # ---- Background/Water file names ------------------------------------
    BACKGROUND_DIRECTORY = "background"
    WATER_DIRECTORY = "water"
    TEXTURED_MESH_DIRECTORY = "textured_mesh"
    WATER_MASK_FILENAME = "polygon_water_mask.png"
    POLYGON_WATER_MESH_FILENAME = "polygon_water.obj"
    POLYLINE_WATER_MESH_FILENAME = "polyline_water.obj"

    # ---- Scene component runtime constants ------------------------------
    SCENE_INFO_FORESTS = "Forests"
    SCENE_INFO_FIELDS = "Fields"
    SPLINE_TAG_FIELD = "field"
    SPLINE_DIRECTION_ORIGINAL = "original"
    SPLINE_DIRECTION_REVERSED = "reversed"
    SPLINE_NAME_PREFIX = "spline"
    NURBS_DEGREE = "3"
    NURBS_FORM_OPEN = "open"
    DEFAULT_TRANSLATION = "0 0 0"

    FIELD_NAME_PREFIX = "field"
    FIELD_POLYGON_POINTS_NAME = "polygonPoints"
    FIELD_POINT_PREFIX = "point"
    FIELD_NAME_INDICATOR = "nameIndicator"
    FIELD_TELEPORT_INDICATOR = "teleportIndicator"
    FIELD_NOTE_NAME = "Note"
    FIELD_NOTE_TEXT_TEMPLATE = "{name}&#xA;0.00 ha"
    FIELD_NOTE_COLOR = "4278190080"
    FIELD_NOTE_FIXED_SIZE = "true"

    SPLINE_USER_ATTRIBUTES = [
        ("maxSpeedScale", "integer", "1"),
        ("speedLimit", "integer", "100"),
    ]
    WATER_ONCREATE_ATTRIBUTE = [("onCreate", "scriptCallback", "Environment.onCreateWater")]
    TREE_GROUP_NAME = "trees"

    MESH_CENTROID_X = "mesh_centroid_x"
    MESH_CENTROID_Y = "mesh_centroid_y"
    MESH_CENTROID_Z = "mesh_centroid_z"

    BINARY_I3D_SUFFIX = "_binary.i3d"
    BACKGROUND_ASSET_DIRNAME = "background"
    WATER_ASSET_DIRNAME = "water"
    MAP_BOUNDS_DIRNAME = "map_bounds"
    MAP_BOUNDS_I3D_FILENAME = "map_bounds.i3d"
    MAP_BOUNDS_SHAPES_FILENAME = "map_bounds.i3d.shapes"
    MAP_BOUNDS_REFERENCE_NAME = "mapbounds"
    MAP_BOUNDS_REFERENCE_HEIGHT = 1024

    # ---- I3D postprocess constants --------------------------------------
    I3D_TRUE = "true"
    I3D_FALSE = "false"
    I3D_WATER_SHADER_FILE_ID = "4"
    I3D_NORMALMAP_FILE_ID = "2"
    I3D_NORMALMAP_FILENAME = "$data/maps/textures/shared/water_normal.dds"
    I3D_WATER_SPECULAR = "1 1 1"
    I3D_WATER_SHADER_VARIATION = "simple"
    I3D_WATER_PARAM_FOG_COLOR_NAME = "underwaterFogColor"
    I3D_WATER_PARAM_FOG_DEPTH_NAME = "underwaterFogDepth"
    I3D_WATER_UNDERWATER_FOG_COLOR = "0.12 0.14 0.11 1"
    I3D_WATER_UNDERWATER_FOG_DEPTH = "1.4 1.2 1 1"
    I3D_ROAD_COLLISION_FILTER_GROUP = "0x601c"
    I3D_ROAD_COLLISION_FILTER_MASK = "0xfffffbff"
    I3D_WATER_COLLISION_FILTER_GROUP = "0x80000000"
    I3D_WATER_COLLISION_FILTER_MASK = "0x1"

    # ---- License-plate image crop coordinates ---------------------------
    COUNTRY_CODE_TOP = 169
    COUNTRY_CODE_BOTTOM = 252
    COUNTRY_CODE_LEFT = 74
    COUNTRY_CODE_RIGHT = 140

    LICENSE_PLATES_XML_FILENAME = "licensePlatesPL.xml"
    LICENSE_PLATES_I3D_FILENAME = "licensePlatesPL.i3d"

    # ---- Building constants ---------------------------------------------
    BUILDINGS_STARTING_NODE_ID = 10000
    DEFAULT_HEIGHT = 200
    AUTO_REGION = "auto"
    ALL_REGIONS = "all"
    BUILDINGS_DIRECTORY = "buildings"
    BUILDING_CATEGORIES_FILENAME = "building_categories.png"
    DEFAULT_BUILDING_CATEGORY = "residential"

    AREA_TYPES = {
        "residential": 10,
        "commercial": 20,
        "industrial": 30,
        "retail": 40,
        "farmyard": 50,
        "religious": 60,
        "recreation": 70,
    }
    PIXEL_TYPES = {v: k for k, v in AREA_TYPES.items()}

    # ---- Scene / I3D node ID ranges -------------------------------------
    NODE_ID_STARTING_VALUE = 2000
    SPLINES_NODE_ID_STARTING_VALUE = 5000
    TREE_NODE_ID_STARTING_VALUE = 30000
    FILE_ID_STARTING_VALUE = 120000
    BINARY_MESHES_NODE_ID_STARTING_VALUE = 150000
    BOUNDS_FILE_ID = 160000
    BOUNDS_NODE_ID = 200000

    FIELDS_ATTRIBUTES = [
        ("angle", "integer", "0"),
        ("missionAllowed", "boolean", "true"),
        ("missionOnlyGrass", "boolean", "false"),
        ("nameIndicatorIndex", "string", "1"),
        ("polygonIndex", "string", "0"),
        ("teleportIndicatorIndex", "string", "2"),
    ]
