"""Generic utility functions and helpers for maps4fs.

Domain-specific utilities live in dedicated modules:
  - maps4fs.generator.osm  — OSM file validation and repair
  - maps4fs.generator.geo  — geocoding / region lookup
"""

import json
import os
from datetime import datetime
from typing import Any

# Re-export for backward compatibility
from maps4fs.generator.geo import get_country_by_coordinates, get_region_by_coordinates  # noqa: F401
from maps4fs.generator.osm import check_and_fix_osm, check_osm_file, fix_osm_file  # noqa: F401


def get_timestamp() -> str:
    """Return current underscore-separated timestamp (YYYYMMDD_HHMMSS)."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def coordinate_to_string(coordinate: float) -> str:
    """Convert a coordinate float to a 3-decimal string with dots replaced by underscores.

    Arguments:
        coordinate (float): Coordinate value.

    Returns:
        str: E.g. 45.369 → "45_369".
    """
    return f"{coordinate:.3f}".replace(".", "_")


def dump_json(filename: str, directory: str, data: dict[Any, Any] | Any | None) -> None:
    """Write data to a JSON file, silently skipping falsy or empty data.

    Arguments:
        filename (str): File name (not path).
        directory (str): Directory to write into.
        data: Dict or list to serialise. Raises TypeError for other non-None values.
    """
    if not data:
        return
    if not isinstance(data, (dict, list)):
        raise TypeError("Data must be a dictionary or a list.")
    save_path = os.path.join(directory, filename)
    with open(save_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)


class Singleton(type):
    """Metaclass that enforces at-most-one instance per class."""

    _instances: dict[Any, Any] = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]
