"""This module contains functions to work with custom OSM files."""

import json
from xml.etree import ElementTree as ET

import osmnx as ox
from osmnx._errors import InsufficientResponseError

from maps4fs.generator.game import FS25


def check_osm_file(file_path: str) -> bool:
    """Tries to read the OSM file using OSMnx and returns True if the file is valid,
    False otherwise.

    Arguments:
        file_path (str): Path to the OSM file.

    Returns:
        bool: True if the file is valid, False otherwise.
    """
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


def fix_osm_file(input_file_path: str, output_file_path: str) -> tuple[bool, int]:
    """Fixes the OSM file by removing all the <relation> nodes and all the nodes with
    action='delete'.

    Arguments:
        input_file_path (str): Path to the input OSM file.
        output_file_path (str): Path to the output OSM file.

    Returns:
        tuple[bool, int]: A tuple containing the result of the check_osm_file function
            and the number of fixed errors.
    """
    broken_entries = ["relation", ".//*[@action='delete']"]

    tree = ET.parse(input_file_path)
    root = tree.getroot()

    fixed_errors = 0
    for entry in broken_entries:
        for element in root.findall(entry):
            root.remove(element)
            fixed_errors += 1

    tree.write(output_file_path)
    result = check_osm_file(output_file_path)

    return result, fixed_errors
