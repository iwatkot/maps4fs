"""Integration and settings-focused tests for map generation."""

from __future__ import annotations

import itertools
import json
import os
import shutil
from time import time
from xml.etree import ElementTree as ET

import cv2
import numpy as np
import pytest

from maps4fs import DTMProvider, GenerationSettings, Map
from maps4fs.generator.constants import Parameters
from maps4fs.generator.game import Game
from maps4fs.generator.settings import (
    BackgroundSettings,
    DEMSettings,
    GRLESettings,
    I3DSettings,
    SatelliteSettings,
)

working_directory = os.getcwd()

base_directory = os.path.join(working_directory, "tests/data")
if os.path.isdir(base_directory):
    shutil.rmtree(base_directory)

# Representative coordinates with diverse terrain types.
# FS25 only — FS22 is deprecated.
COORDINATE_CASES = {
    "balkans": (45.369648574398184, 19.801106980618925),  # farmland, rivers
    "nevada": (39.51147544442993, -115.96064194571787),  # desert, significant elevation
    "brazil": (-13.038004302866275, -57.09179831840436),  # tropical, flat
    "zambia": (-15.912277514425883, 25.9557832265989),  # savanna
    "australia": (-35.95760563718185, 149.1495358824173),  # varied terrain
    "russia": (58.52085065306593, 31.27771396353221),  # northern forest, flat
    "japan": (35.25541295723034, 139.04857855524995),  # mountainous
}

# Number of coordinate cases used for each test group.
FS25_MAP_CASES = 1
FS25_PREVIEW_CASES = 1

SIZE_CASES = [512]
ROTATION_CASES = [0]

# Component keys expected in generation_info.json after a successful full run.
EXPECTED_INFO_KEYS = {"Texture", "Background", "GRLE", "Config", "Scene"}

dtm_provider_code = "srtm30"
dtm_provider = DTMProvider.get_provider_by_code(dtm_provider_code)

background_settings = BackgroundSettings(
    generate_background=True,
    generate_water=True,
    remove_center=False,
)
generation_settings = GenerationSettings(
    background_settings=background_settings,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_map_directory(label: str) -> str:
    timestamp = int(time())
    directory = os.path.join(base_directory, f"{label}_{timestamp}")
    os.makedirs(directory, exist_ok=True)
    return directory


def load_texture_schema(json_path: str) -> list[dict]:
    with open(json_path, "r") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Parametrize builders
# ---------------------------------------------------------------------------


def _build_map_test_cases() -> tuple[list[tuple], list[str]]:
    cases, ids = [], []
    coord_names = list(COORDINATE_CASES.keys())[:FS25_MAP_CASES]
    size_cycle = itertools.cycle(SIZE_CASES)
    rotation_cycle = itertools.cycle(ROTATION_CASES)
    for name in coord_names:
        size = next(size_cycle)
        rotation = next(rotation_cycle)
        cases.append((COORDINATE_CASES[name], size, None, rotation))
        ids.append(f"FS25-{name}-{size}-rot{rotation}")
    return cases, ids


def _build_preview_test_cases() -> tuple[list[tuple], list[str]]:
    cases, ids = [], []
    coord_names = list(COORDINATE_CASES.keys())[:FS25_PREVIEW_CASES]
    size_cycle = itertools.cycle(SIZE_CASES)
    rotation_cycle = itertools.cycle(ROTATION_CASES)
    for name in coord_names:
        size = next(size_cycle)
        rotation = next(rotation_cycle)
        cases.append((COORDINATE_CASES[name], size, rotation))
        ids.append(f"FS25-{name}-{size}-rot{rotation}")
    return cases, ids


def _build_pack_test_cases() -> tuple[list[tuple], list[str]]:
    name = list(COORDINATE_CASES.keys())[0]
    return [(COORDINATE_CASES[name], 512, -90)], [f"FS25-{name}-512-rot-90"]


_MAP_CASES, _MAP_IDS = _build_map_test_cases()
_PREVIEW_CASES, _PREVIEW_IDS = _build_preview_test_cases()
_PACK_CASES, _PACK_IDS = _build_pack_test_cases()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("coordinates,size,output_size,rotation", _MAP_CASES, ids=_MAP_IDS)
def test_map(
    coordinates: tuple[float, float],
    size: int,
    output_size: int | None,
    rotation: int,
):
    """Full generation test. Verifies textures, DEM, I3D structure, GRLE files,
    generation_info.json completeness, and overview.dds presence."""
    game = Game.from_code("FS25")
    directory = make_map_directory(f"FS25_{size}")

    extra_kwargs: dict = {}
    if output_size:
        extra_kwargs["output_size"] = output_size

    mp = Map(
        game=game,
        dtm_provider=dtm_provider,
        dtm_provider_settings=None,
        coordinates=coordinates,
        size=size,
        rotation=rotation,
        map_directory=directory,
        generation_settings=generation_settings,
        **extra_kwargs,
    )
    for _ in mp.generate():
        pass

    expected_size = output_size if output_size else size

    # --- Texture weight files ---
    schema = load_texture_schema(game.texture_schema)
    weights_dir = game.weights_dir_path
    for layer in schema:
        if layer.get("exclude_weight") or not layer.get("count"):
            continue
        for idx in range(1, layer["count"] + 1):
            path = os.path.join(weights_dir, f"{layer['name']}{str(idx).zfill(2)}_weight.png")
            assert os.path.isfile(path), f"Texture not found: {path}"
            img = cv2.imread(path)
            assert img is not None, f"Texture unreadable: {path}"
            assert img.shape == (
                expected_size,
                expected_size,
                3,
            ), f"Texture shape mismatch: {img.shape} != ({expected_size}, {expected_size}, 3)"
            assert img.dtype == np.uint8, f"Texture dtype mismatch: {img.dtype}"

    # --- DEM: exists, 16-bit grayscale, square, non-trivial ---
    dem_path = game.dem_file_path
    assert os.path.isfile(dem_path), f"DEM not found: {dem_path}"
    dem = cv2.imread(dem_path, cv2.IMREAD_UNCHANGED)
    assert dem is not None, f"DEM unreadable: {dem_path}"
    assert dem.dtype == np.uint16, f"DEM dtype mismatch: {dem.dtype} (expected uint16)"
    assert dem.ndim == 2, f"DEM should be single-channel, got shape {dem.shape}"
    assert dem.shape[0] == dem.shape[1], f"DEM should be square, got {dem.shape}"
    assert dem.max() > 0, "DEM is all zeros — elevation data was not written"

    # --- I3D: parseable, TerrainTransformGroup present, heightScale > 0 ---
    i3d_path = game.i3d_file_path
    assert os.path.isfile(i3d_path), f"map.i3d not found: {i3d_path}"
    i3d_tree = ET.parse(i3d_path)
    terrain = i3d_tree.getroot().find(".//Scene/TerrainTransformGroup")
    assert terrain is not None, "TerrainTransformGroup missing from map.i3d"
    height_scale_str = terrain.get("heightScale")
    assert height_scale_str is not None, "heightScale attribute missing from TerrainTransformGroup"
    assert int(float(height_scale_str)) > 0, f"heightScale not positive: {height_scale_str}"

    # --- GRLE info layer files ---
    grle_paths = [
        game.farmlands_path,
        game.density_map_fruits_path,
        game.environment_path,
    ]
    for grle_path in grle_paths:
        assert os.path.isfile(grle_path), f"GRLE file not found: {grle_path}"
        grle_img = cv2.imread(grle_path, cv2.IMREAD_UNCHANGED)
        assert grle_img is not None, f"GRLE file unreadable: {grle_path}"

    # --- Precision farming soil map and references ---
    soil_map_png_path = os.path.join(game.weights_dir_path, Parameters.INFO_LAYER_SOIL_MAP)
    assert os.path.isfile(soil_map_png_path), f"Soil map not found: {soil_map_png_path}"
    soil_map_png = cv2.imread(soil_map_png_path, cv2.IMREAD_UNCHANGED)
    assert soil_map_png is not None, f"Soil map unreadable: {soil_map_png_path}"
    assert soil_map_png.ndim == 3 and soil_map_png.shape[2] == 3, (
        "Soil map must be RGB (3 channels), got shape " f"{soil_map_png.shape}"
    )
    expected_soil_size = Parameters.SOIL_MAP_FIXED_SIZE
    assert soil_map_png.shape[:2] == (
        expected_soil_size,
        expected_soil_size,
    ), f"Soil map shape mismatch: {soil_map_png.shape[:2]} != {(expected_soil_size, expected_soil_size)}"

    soil_i3d_filename = f"data/{Parameters.INFO_LAYER_SOIL_MAP}"
    files_nodes = i3d_tree.getroot().findall(".//Files/File")
    soil_file_node = next(
        (node for node in files_nodes if node.get("filename") == soil_i3d_filename),
        None,
    )
    assert soil_file_node is not None, "Soil map File entry missing in map.i3d"
    soil_file_id = soil_file_node.get("fileId")
    assert soil_file_id is not None, "Soil map File entry has no fileId"

    soil_info_layer_node = i3d_tree.getroot().find(
        f".//InfoLayer[@name='{Parameters.SOIL_MAP_I3D_LAYER_NAME}']"
    )
    assert soil_info_layer_node is not None, "soilMap InfoLayer missing in map.i3d"
    assert (
        soil_info_layer_node.get("fileId") == soil_file_id
    ), "soilMap InfoLayer fileId does not match soil map File entry"
    assert (
        soil_info_layer_node.get("numChannels") == Parameters.SOIL_MAP_I3D_NUM_CHANNELS
    ), "soilMap InfoLayer numChannels must be 3"

    map_xml_root = ET.parse(game.map_xml_path).getroot()
    precision_farming_node = map_xml_root.find(f"./{Parameters.PRECISION_FARMING_TAG}")
    assert precision_farming_node is not None, "precisionFarming node missing in map.xml"
    soil_map_node = precision_farming_node.find(Parameters.SOIL_MAP_TAG)
    assert soil_map_node is not None, "precisionFarming/soilMap node missing in map.xml"
    assert soil_map_node.get("filename") == (
        f"data/{os.path.splitext(Parameters.INFO_LAYER_SOIL_MAP)[0]}"
        f"{Parameters.SOIL_MAP_GRLE_EXTENSION}"
    ), "precisionFarming soilMap filename is incorrect"

    # --- generation_info.json: present and contains all expected component keys ---
    info_path = os.path.join(directory, "generation_info.json")
    assert os.path.isfile(info_path), "generation_info.json not found"
    with open(info_path, "r") as f:
        info = json.load(f)
    missing = EXPECTED_INFO_KEYS - set(info.keys())
    assert not missing, f"generation_info.json missing component keys: {missing}"

    # --- overview.dds: required for FS25 in-game minimap ---
    overview_path = game.overview_file_path
    assert os.path.isfile(overview_path), f"overview.dds not found: {overview_path}"


@pytest.mark.parametrize("coordinates,size,rotation", _PREVIEW_CASES, ids=_PREVIEW_IDS)
def test_map_preview(coordinates: tuple[float, float], size: int, rotation: int) -> None:
    """Test that preview PNG files are generated and readable."""
    game = Game.from_code("FS25")
    directory = make_map_directory(f"FS25_preview_{size}")
    mp = Map(
        game=game,
        dtm_provider=dtm_provider,
        dtm_provider_settings=None,
        coordinates=coordinates,
        size=size,
        rotation=rotation,
        map_directory=directory,
        generation_settings=generation_settings,
    )
    for _ in mp.generate():
        pass
    for preview_path in mp.previews():
        if not preview_path.endswith(".png"):
            continue
        assert os.path.isfile(preview_path), f"Preview not found: {preview_path}"
        img = cv2.imread(preview_path)
        assert img is not None, f"Preview unreadable: {preview_path}"


@pytest.mark.parametrize("coordinates,size,rotation", _PACK_CASES, ids=_PACK_IDS)
def test_map_pack(coordinates: tuple[float, float], size: int, rotation: int) -> None:
    """Test map packing into a zip archive; verifies non-default DEM settings are accepted."""
    game = Game.from_code("FS25")
    pack_settings = GenerationSettings(
        dem_settings=DEMSettings(multiplier=2, blur_radius=15, plateau=1000, water_depth=500),
        background_settings=background_settings,
        satellite_settings=SatelliteSettings(download_images=True, zoom_level=14),
    )
    directory = make_map_directory(f"FS25_pack_{size}")
    mp = Map(
        game=game,
        dtm_provider=dtm_provider,
        dtm_provider_settings=None,
        coordinates=coordinates,
        size=size,
        rotation=rotation,
        map_directory=directory,
        generation_settings=pack_settings,
    )
    for _ in mp.generate():
        pass
    archive_path = mp.pack(os.path.join(base_directory, "archive"))
    assert os.path.isfile(archive_path), f"Archive not found: {archive_path}"
    unpacked_directory = os.path.join(base_directory, "unpacked")
    os.makedirs(unpacked_directory, exist_ok=True)
    shutil.unpack_archive(archive_path, unpacked_directory)
    assert os.path.isdir(unpacked_directory)


# ---------------------------------------------------------------------------
# Focused settings tests — each verifies that a specific GenerationSettings
# field is actually applied to the generation output.
# All use a single 512-size balkans run to keep CI time short.
# ---------------------------------------------------------------------------

_NO_BG = BackgroundSettings(generate_background=False, generate_water=False, remove_center=False)
_SETTINGS_COORDS = COORDINATE_CASES["balkans"]
_SETTINGS_SIZE = 512


def test_dem_plateau_lifts_floor() -> None:
    """DEMSettings.plateau shifts the minimum DEM value above zero.

    plateau=500 + default water_depth=40 pushes the minimum raw elevation to 540 m.
    After uint16 normalisation that value becomes > 0.
    """
    game = Game.from_code("FS25")
    directory = make_map_directory("FS25_dem_plateau")
    settings = GenerationSettings(
        dem_settings=DEMSettings(plateau=500),
        background_settings=_NO_BG,
    )
    mp = Map(
        game=game,
        dtm_provider=dtm_provider,
        dtm_provider_settings=None,
        coordinates=_SETTINGS_COORDS,
        size=_SETTINGS_SIZE,
        rotation=0,
        map_directory=directory,
        generation_settings=settings,
    )
    for _ in mp.generate():
        pass

    dem = cv2.imread(game.dem_file_path, cv2.IMREAD_UNCHANGED)
    assert dem is not None
    assert dem.min() > 0, f"DEM min={dem.min()}: plateau did not lift the terrain floor"


def test_dem_minimum_height_scale_respected() -> None:
    """DEMSettings.minimum_height_scale is enforced as a floor for heightScale in map.i3d."""
    game = Game.from_code("FS25")
    directory = make_map_directory("FS25_dem_mhs")
    settings = GenerationSettings(
        dem_settings=DEMSettings(minimum_height_scale=2000),
        background_settings=_NO_BG,
    )
    mp = Map(
        game=game,
        dtm_provider=dtm_provider,
        dtm_provider_settings=None,
        coordinates=_SETTINGS_COORDS,
        size=_SETTINGS_SIZE,
        rotation=0,
        map_directory=directory,
        generation_settings=settings,
    )
    for _ in mp.generate():
        pass

    i3d_tree = ET.parse(game.i3d_file_path)
    terrain = i3d_tree.getroot().find(".//Scene/TerrainTransformGroup")
    assert terrain is not None
    height_scale = int(float(terrain.get("heightScale", "0")))
    assert height_scale >= 2000, f"heightScale={height_scale} is below minimum_height_scale=2000"


def test_background_terrain_i3d_generated() -> None:
    """BackgroundSettings.generate_background=True produces background_terrain.i3d.

    Satellite images are required to texture the background mesh before it can be
    converted to i3d, so download_images=True is used here.
    polygon_water.i3d is omitted: its generation depends on OSM water polygon
    availability at the test coordinates and is therefore unreliable in CI.
    """
    game = Game.from_code("FS25")
    directory = make_map_directory("FS25_bg_terrain")
    settings = GenerationSettings(
        background_settings=BackgroundSettings(
            generate_background=True,
            generate_water=True,
            remove_center=False,
        ),
        satellite_settings=SatelliteSettings(download_images=True, zoom_level=14),
    )
    mp = Map(
        game=game,
        dtm_provider=dtm_provider,
        dtm_provider_settings=None,
        coordinates=_SETTINGS_COORDS,
        size=_SETTINGS_SIZE,
        rotation=0,
        map_directory=directory,
        generation_settings=settings,
    )
    for _ in mp.generate():
        pass

    bg_i3d = os.path.join(directory, "assets", "background", "background_terrain.i3d")
    assert os.path.isfile(bg_i3d), f"background_terrain.i3d not found: {bg_i3d}"


def test_grle_base_price_written_to_farmlands_xml() -> None:
    """GRLESettings.base_price is written as the pricePerHa attribute in farmlands.xml."""
    game = Game.from_code("FS25")
    directory = make_map_directory("FS25_grle_price")
    custom_price = 75000
    settings = GenerationSettings(
        grle_settings=GRLESettings(base_price=custom_price),
        background_settings=_NO_BG,
    )
    mp = Map(
        game=game,
        dtm_provider=dtm_provider,
        dtm_provider_settings=None,
        coordinates=_SETTINGS_COORDS,
        size=_SETTINGS_SIZE,
        rotation=0,
        map_directory=directory,
        generation_settings=settings,
    )
    for _ in mp.generate():
        pass

    farmlands_xml = game.farmlands_xml_path
    assert os.path.isfile(farmlands_xml), f"farmlands.xml not found: {farmlands_xml}"
    root = ET.parse(farmlands_xml).getroot()
    farmlands_node = root.find("farmlands")
    assert farmlands_node is not None, "<farmlands> element missing from farmlands.xml"
    assert farmlands_node.get("pricePerHa") == str(
        custom_price
    ), f"pricePerHa={farmlands_node.get('pricePerHa')!r}, expected {custom_price!r}"


def test_i3d_no_forest_info_when_trees_disabled() -> None:
    """I3DSettings.add_trees=False leaves Forests info empty in generation_info.json."""
    game = Game.from_code("FS25")
    directory = make_map_directory("FS25_no_trees")
    settings = GenerationSettings(
        i3d_settings=I3DSettings(add_trees=False),
        background_settings=_NO_BG,
    )
    mp = Map(
        game=game,
        dtm_provider=dtm_provider,
        dtm_provider_settings=None,
        coordinates=_SETTINGS_COORDS,
        size=_SETTINGS_SIZE,
        rotation=0,
        map_directory=directory,
        generation_settings=settings,
    )
    for _ in mp.generate():
        pass

    with open(os.path.join(directory, "generation_info.json")) as f:
        info = json.load(f)
    forest_info = info.get("Scene", {}).get("Forests", {})
    assert (
        forest_info == {}
    ), f"Forests info should be empty when add_trees=False, got: {forest_info}"


def test_config_license_plate_prefix_recorded() -> None:
    """I3DSettings.license_plate_prefix is stored in generation_info.json under Config."""
    game = Game.from_code("FS25")
    directory = make_map_directory("FS25_lp_prefix")
    prefix = "TST"
    settings = GenerationSettings(
        i3d_settings=I3DSettings(license_plate_prefix=prefix),
        background_settings=_NO_BG,
    )
    mp = Map(
        game=game,
        dtm_provider=dtm_provider,
        dtm_provider_settings=None,
        coordinates=_SETTINGS_COORDS,
        size=_SETTINGS_SIZE,
        rotation=0,
        map_directory=directory,
        generation_settings=settings,
    )
    for _ in mp.generate():
        pass

    with open(os.path.join(directory, "generation_info.json")) as f:
        info = json.load(f)
    # The prefix is padded to exactly 3 chars with spaces; strip before comparing.
    stored = info.get("Config", {}).get("license_plate_prefix", "")
    assert (
        stored.strip() == prefix
    ), f"license_plate_prefix={stored!r}, expected {prefix!r} (stripped)"
