"""This module contains utility functions for working with maps4fs."""

import json
import os
import shutil
from datetime import datetime
from typing import Any
from xml.etree import ElementTree as ET

import osmnx as ox
from geopy.geocoders import Nominatim
from osmnx._errors import InsufficientResponseError


def check_osm_file(file_path: str) -> bool:
    """Tries to read the OSM file using OSMnx and returns True if the file is valid,
    False otherwise.

    Arguments:
        file_path (str): Path to the OSM file.

    Returns:
        bool: True if the file is valid, False otherwise.
    """
    from maps4fs.generator.game import FS25

    with open(FS25().texture_schema, encoding="utf-8") as f:
        schema = json.load(f)

    tags = []
    for element in schema:
        element_tags = element.get("tags")
        if element_tags:
            tags.append(element_tags)

    for tag in tags:
        try:
            ox.features_from_xml(file_path, tags=tag)
        except InsufficientResponseError:
            continue
        except Exception:  # pylint: disable=W0718
            return False
    return True


def fix_osm_file(input_file_path: str, output_file_path: str | None = None) -> tuple[bool, int]:
    """Fixes the OSM file by removing all the <relation> nodes and all the nodes with
    action='delete'.

    Arguments:
        input_file_path (str): Path to the input OSM file.
        output_file_path (str | None): Path to the output OSM file. If None, the input file
            will be overwritten.

    Returns:
        tuple[bool, int]: A tuple containing the result of the check_osm_file function
            and the number of fixed errors.
    """
    broken_entries = ["relation", ".//*[@action='delete']"]
    output_file_path = output_file_path or input_file_path

    tree = ET.parse(input_file_path)
    root = tree.getroot()

    fixed_errors = 0
    for entry in broken_entries:
        for element in root.findall(entry):
            root.remove(element)
            fixed_errors += 1

    tree.write(output_file_path)  # type: ignore
    result = check_osm_file(output_file_path)  # type: ignore

    return result, fixed_errors


def check_and_fix_osm(
    custom_osm: str | None, save_directory: str | None = None, output_name: str = "custom_osm.osm"
) -> None:
    """Check and fix custom OSM file if necessary.

    Arguments:
        custom_osm (str | None): Path to the custom OSM file.
        save_directory (str | None): Directory to save the fixed OSM file.
        output_name (str): Name of the output OSM file.

    Raises:
        FileNotFoundError: If the custom OSM file does not exist.
        ValueError: If the custom OSM file is not valid and cannot be fixed.
    """
    if not custom_osm:
        return None
    if not os.path.isfile(custom_osm):
        raise FileNotFoundError(f"Custom OSM file {custom_osm} does not exist.")

    osm_is_valid = check_osm_file(custom_osm)
    if not osm_is_valid:
        fixed, _ = fix_osm_file(custom_osm)
        if not fixed:
            raise ValueError(f"Custom OSM file {custom_osm} is not valid and cannot be fixed.")

    if save_directory:
        output_path = os.path.join(save_directory, output_name)
        shutil.copyfile(custom_osm, output_path)

    return None


def get_country_by_coordinates(coordinates: tuple[float, float]) -> str:
    """Get country name by coordinates.

    Returns:
        str: Country name.
    """
    try:
        geolocator = Nominatim(user_agent="maps4fs")
        location = geolocator.reverse(coordinates, language="en")
        if location and "country" in location.raw["address"]:
            return location.raw["address"]["country"]
    except Exception:
        return "Unknown"
    return "Unknown"


def get_timestamp() -> str:
    """Get current underscore-separated timestamp.

    Returns:
        str: Current timestamp.
    """
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def coordinate_to_string(coordinate: float) -> str:
    """Convert coordinate to string with 3 decimal places.

    Arguments:
        coordinate (float): Coordinate value.

    Returns:
        str: Coordinate as string.
    """
    return f"{coordinate:.3f}".replace(".", "_")


def dump_json(filename: str, directory: str, data: dict[Any, Any] | Any | None) -> None:
    """Dump data to a JSON file.

    Arguments:
        filename (str): Name of the JSON file.
        directory (str): Directory to save the JSON file.
        data (dict[Any, Any] | Any | None): Data to dump.
    """
    if not data:
        return
    if not isinstance(data, (dict, list)):
        raise TypeError("Data must be a dictionary or a list.")
    save_path = os.path.join(directory, filename)
    with open(save_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)
