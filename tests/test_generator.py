import json
import os
import shutil
from random import choice
from time import time

import cv2

from maps4fs import Map
from maps4fs.generator.game import Game

working_directory = os.getcwd()

base_directory = os.path.join(working_directory, "tests/data")
if os.path.isdir(base_directory):
    shutil.rmtree(base_directory)

coordinates_cases = [
    (45.369648574398184, 19.801106980618925),
    (39.51147544442993, -115.96064194571787),
    (-13.038004302866275, -57.09179831840436),
    (-15.912277514425883, 25.9557832265989),
    (-35.95760563718185, 149.1495358824173),
    (58.52085065306593, 31.27771396353221),
    (35.25541295723034, 139.04857855524995),
]

game_code_cases = ["FS25"]


def get_random_size() -> tuple[int, int]:
    """Return random size.

    Returns:
        tuple[int, int]: Random size.
    """
    sizes_cases = [(1024, 1024), (2048, 2048), (4096, 4096), (8192, 8192)]
    return choice(sizes_cases[:2])  # Larger maps are too slow for automated tests.


def map_directory(game_code: str) -> str:
    """Creates a new map directory and returns its path.

    Arguments:
        game_code {str} -- Game code.

    Returns:
        str: Path to the new map directory.
    """
    timestamp = int(time())
    directory = os.path.join(base_directory, f"{game_code}_{timestamp}")
    os.makedirs(directory, exist_ok=True)
    return directory


def load_textures_schema(json_path: str) -> dict:
    """Load textures schema from JSON file.

    Arguments:
        json_path (str): Path to the JSON file.

    Returns:
        dict: Loaded JSON file.
    """
    with open(json_path, "r") as file:
        return json.load(file)


def test_map():
    """Test Map generation for different cases."""
    for game_code in game_code_cases:
        game = Game.from_code(game_code)
        for coordinates in coordinates_cases:
            height, width = get_random_size()
            directory = map_directory(game_code)

            map = Map(
                game=game,
                coordinates=coordinates,
                size=height,
                rotation=0,
                map_directory=directory,
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
                        height,
                        width,
                        3,
                    ), f"Texture shape mismatch: {img.shape} != {(height, width, 3)}"
                    assert img.dtype == "uint8", f"Texture dtype mismatch: {img.dtype} != uint8"

            dem_name = "map_dem.png" if game_code == "FS22" else "dem.png"

            dem_file = os.path.join(textures_directory, dem_name)
            assert os.path.isfile(dem_file), f"DEM file not found: {dem_file}"
            img = cv2.imread(dem_file, cv2.IMREAD_UNCHANGED)
            assert img is not None, f"DEM could not be read: {dem_file}"

            assert img.dtype == "uint16", f"DEM dtype mismatch: {img.dtype} != uint16"


def test_map_preview():
    """Test Map preview generation."""
    case = choice(coordinates_cases)

    game_code = choice(game_code_cases)
    game = Game.from_code(game_code)

    height, width = get_random_size()

    directory = map_directory(game_code)
    map = Map(
        game=game,
        coordinates=case,
        size=height,
        rotation=0,
        map_directory=directory,
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


def test_map_pack():
    """Test Map packing into zip archive."""
    case = choice(coordinates_cases)

    game_code = choice(game_code_cases)
    game = Game.from_code(game_code)

    height, width = get_random_size()

    directory = map_directory(game_code)
    map = Map(
        game=game,
        coordinates=case,
        size=height,
        rotation=30,
        map_directory=directory,
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
