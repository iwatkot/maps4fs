"""OSM file validation and repair utilities."""

from __future__ import annotations

import os
import shutil
from xml.etree import ElementTree as ET

import osmnx as ox
from osmnx._errors import InsufficientResponseError

# Representative tags — if the file is fundamentally broken it will fail on any of these.
_CHECK_TAGS = [
    {"highway": True},
    {"building": True},
    {"landuse": True},
    {"natural": True},
    {"waterway": True},
]


def check_osm_file(file_path: str) -> bool:
    """Try to parse the OSM file with OSMnx using representative tag queries.

    Arguments:
        file_path (str): Path to the OSM file.

    Returns:
        bool: True if the file is valid, False otherwise.
    """
    for tag in _CHECK_TAGS:
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

    tree.write(output_file_path)
    result = check_osm_file(output_file_path)

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
