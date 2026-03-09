import json
import os
import shutil
from time import time

import cv2
import pytest

from maps4fs import DTMProvider, GenerationSettings, Map
from maps4fs.generator.game import Game
from maps4fs.generator.settings import (
    BackgroundSettings,
    DEMSettings,
    SatelliteSettings,
)

working_directory = os.getcwd()

base_directory = os.path.join(working_directory, "tests/data")
if os.path.isdir(base_directory):
    shutil.rmtree(base_directory)

COORDINATE_CASES = {
    "balkans": (45.369648574398184, 19.801106980618925),
    "nevada": (39.51147544442993, -115.96064194571787),
    "brazil": (-13.038004302866275, -57.09179831840436),
    "zambia": (-15.912277514425883, 25.9557832265989),
    "australia": (-35.95760563718185, 149.1495358824173),
    "russia": (58.52085065306593, 31.27771396353221),
    "japan": (35.25541295723034, 139.04857855524995),
}

GAME_CODE_CASES = {"FS25": 3, "FS22": 1}

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


def map_directory(game_code: str) -> str:
    timestamp = int(time())
    directory = os.path.join(base_directory, f"{game_code}_{timestamp}")
    os.makedirs(directory, exist_ok=True)
    return directory


def load_textures_schema(json_path: str) -> dict:
    with open(json_path, "r") as file:
        return json.load(file)


def _build_map_test_cases() -> tuple[list[tuple], list[str]]:
    cases, ids = [], []
    for game_code, n_cases in GAME_CODE_CASES.items():
        coord_names = list(COORDINATE_CASES.keys())[:n_cases]
        for name in coord_names:
            cases.append((game_code, COORDINATE_CASES[name], 1024))
            ids.append(f"{game_code}-{name}-1024")
    return cases, ids


def _build_preview_test_cases() -> tuple[list[tuple], list[str]]:
    cases, ids = [], []
    for game_code, n_cases in GAME_CODE_CASES.items():
        coord_names = list(COORDINATE_CASES.keys())[: min(n_cases, 2)]
        for name in coord_names:
            cases.append((game_code, COORDINATE_CASES[name], 1024))
            ids.append(f"{game_code}-{name}-1024")
    return cases, ids


def _build_pack_test_cases() -> tuple[list[tuple], list[str]]:
    cases, ids = [], []
    for game_code in GAME_CODE_CASES:
        name = list(COORDINATE_CASES.keys())[0]
        cases.append((game_code, COORDINATE_CASES[name], 1024))
        ids.append(f"{game_code}-{name}-1024")
    return cases, ids


_MAP_CASES, _MAP_IDS = _build_map_test_cases()
_PREVIEW_CASES, _PREVIEW_IDS = _build_preview_test_cases()
_PACK_CASES, _PACK_IDS = _build_pack_test_cases()


@pytest.mark.parametrize("game_code,coordinates,size", _MAP_CASES, ids=_MAP_IDS)
def test_map(game_code: str, coordinates: tuple[float, float], size: int):
    """Test Map generation for different coordinate cases."""
    game = Game.from_code(game_code)
    directory = map_directory(game_code)

    print(f"Generating map for {game_code} at {coordinates} with size {size}x{size}...")

    map = Map(
        game=game,
        dtm_provider=dtm_provider,
        dtm_provider_settings=None,
        coordinates=coordinates,
        size=size,
        rotation=0,
        map_directory=directory,
        generation_settings=generation_settings,
    )

    for _ in map.generate():
        pass

    layers_schema = load_textures_schema(game.texture_schema)

    texture_subdir = "maps/map/data" if game_code == "FS22" else "map/data"

    textures_directory = os.path.join(directory, texture_subdir)
    for texture in layers_schema:
        texture_name = texture["name"]
        numer_of_layers = texture["count"]

        exclude_weight = texture.get("exclude_weight", False)
        if exclude_weight:
            continue

        if numer_of_layers == 0:
            continue
        for idx in range(1, numer_of_layers + 1):
            texture_path = os.path.join(
                textures_directory, f"{texture_name}{str(idx).zfill(2)}_weight.png"
            )
            assert os.path.isfile(texture_path), f"Texture not found: {texture_path}"
            img = cv2.imread(texture_path)
            assert img is not None, f"Texture could not be read: {texture_path}"
            assert img.shape == (
                size,
                size,
                3,
            ), f"Texture shape mismatch: {img.shape} != {(size, size, 3)}"
            assert img.dtype == "uint8", f"Texture dtype mismatch: {img.dtype} != uint8"

    dem_name = "map_dem.png" if game_code == "FS22" else "dem.png"

    dem_file = os.path.join(textures_directory, dem_name)
    assert os.path.isfile(dem_file), f"DEM file not found: {dem_file}"
    img = cv2.imread(dem_file, cv2.IMREAD_UNCHANGED)
    assert img is not None, f"DEM could not be read: {dem_file}"

    assert img.dtype == "uint16", f"DEM dtype mismatch: {img.dtype} != uint16"


@pytest.mark.parametrize("game_code,coordinates,size", _PREVIEW_CASES, ids=_PREVIEW_IDS)
def test_map_preview(game_code: str, coordinates: tuple[float, float], size: int):
    """Test Map preview generation."""
    game = Game.from_code(game_code)
    directory = map_directory(game_code)
    map = Map(
        game=game,
        dtm_provider=dtm_provider,
        dtm_provider_settings=None,
        coordinates=coordinates,
        size=size,
        rotation=0,
        map_directory=directory,
        generation_settings=generation_settings,
    )
    for _ in map.generate():
        pass
    previews_paths = map.previews()
    for preview_path in previews_paths:
        if not preview_path.endswith(".png"):
            continue
        assert os.path.isfile(preview_path), f"Preview not found: {preview_path}"
        img = cv2.imread(preview_path)
        assert img is not None, f"Preview could not be read: {preview_path}"


@pytest.mark.parametrize("game_code,coordinates,size", _PACK_CASES, ids=_PACK_IDS)
def test_map_pack(game_code: str, coordinates: tuple[float, float], size: int):
    """Test Map packing into zip archive."""
    game = Game.from_code(game_code)

    dem_settings = DEMSettings(multiplier=2, blur_radius=15, plateau=1000, water_depth=500)

    satellite_settings = SatelliteSettings(download_images=True, zoom_level=14)

    pack_generation_settings = GenerationSettings(
        dem_settings=dem_settings,
        background_settings=background_settings,
        satellite_settings=satellite_settings,
    )

    directory = map_directory(game_code)
    map = Map(
        game=game,
        dtm_provider=dtm_provider,
        dtm_provider_settings=None,
        coordinates=coordinates,
        size=size,
        rotation=30,
        map_directory=directory,
        generation_settings=pack_generation_settings,
    )
    for _ in map.generate():
        pass
    archive_name = os.path.join(base_directory, "archive")
    archive_path = map.pack(archive_name)
    assert os.path.isfile(archive_path), f"Archive not found: {archive_path}"
    unpacked_directory = os.path.join(base_directory, "unpacked")
    os.makedirs(unpacked_directory, exist_ok=True)
    try:
        shutil.unpack_archive(archive_path, unpacked_directory)
    except Exception as e:
        assert False, f"Archive could not be unpacked: {e}"
    assert os.path.isdir(unpacked_directory), f"Unpacked directory not found: {unpacked_directory}"
