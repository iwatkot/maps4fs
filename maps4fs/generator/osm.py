"""OSM file validation and repair utilities."""

from __future__ import annotations

import json
import os
import shutil
from xml.etree import ElementTree as ET

import osmnx as ox
from osmnx._errors import InsufficientResponseError


def check_osm_file(file_path: str) -> bool:
    """Try to parse the OSM file with OSMnx using all texture schema tag combinations.

    Arguments:
        file_path (str): Path to the OSM file.

    Returns:
        bool: True if the file is valid, False otherwise.
    """
    from maps4fs.generator.game import FS25

    with open(FS25().texture_schema, encoding="utf-8") as f:
        schema = json.load(f)

    tags = [element["tags"] for element in schema if element.get("tags")]

    for tag in tags:
        try:
            ox.features_from_xml(file_path, tags=tag)
        except InsufficientResponseError:
            continue
        except Exception:  # pylint: disable=W0718
            return False
    return True


def fix_osm_file(input_file_path: str, output_file_path: str | None = None) -> tuple[bool, int]:
    """Fix an OSM file by removing <relation> nodes and nodes with action='delete'.

    Arguments:
        input_file_path (str): Path to the input OSM file.
        output_file_path (str | None): Path to save the fixed file. Defaults to overwrite input.

    Returns:
        tuple[bool, int]: (file_is_valid_after_fix, number_of_removed_elements)
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
    """Validate and, if necessary, repair a custom OSM file.

    Arguments:
        custom_osm (str | None): Path to the custom OSM file. No-op if None.
        save_directory (str | None): Directory to copy the (fixed) file into.
        output_name (str): Filename for the copy saved to save_directory.

    Raises:
        FileNotFoundError: If the custom OSM file does not exist.
        ValueError: If the file is invalid and cannot be fixed.
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
