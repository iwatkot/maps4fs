"""Utility functions for the DTM generator."""

import numpy as np
from pyproj import Transformer


def tile_bbox(
    bbox: tuple[float, float, float, float], tile_size: float
) -> list[tuple[float, float, float, float]]:
    """Tile the bounding box into smaller bounding boxes of a specified size.

    Arguments:
        bbox (tuple): Bounding box to tile (north, south, east, west).
        tile_size (int): Size of the tiles in meters.

    Returns:
        list: List of smaller bounding boxes (north, south, east, west).
    """
    north, south, east, west = bbox
    x_coords = np.arange(west, east, tile_size if east > west else -tile_size)
    y_coords = np.arange(north, south, tile_size if south > north else -tile_size)
    x_coords = np.append(x_coords, east).astype(x_coords.dtype)
    y_coords = np.append(y_coords, south).astype(y_coords.dtype)

    x_min, y_min = np.meshgrid(x_coords[:-1], y_coords[:-1], indexing="ij")
    x_max, y_max = np.meshgrid(x_coords[1:], y_coords[1:], indexing="ij")

    tiles = np.stack(
        [x_min.ravel(), y_min.ravel(), x_max.ravel(), y_max.ravel()], axis=1, dtype=float
    )

    return [tuple(tile[i].item() for i in range(4)) for tile in tiles]


def transform_bbox(
    bbox: tuple[float, float, float, float], to_crs: str
) -> tuple[float, float, float, float]:
    """Transform the bounding box to a different coordinate reference system (CRS).

    Arguments:
        bbox (tuple): Bounding box to transform (north, south, east, west).
        to_crs (str): Target CRS (e.g., EPSG:4326 for CRS:84).

    Returns:
        tuple: Transformed bounding box (north, south, east, west).
    """
    transformer = Transformer.from_crs("epsg:4326", to_crs)
    north, south, east, west = bbox

    # EPSG:4326 is lat, lon, so xx is lat and yy is lon
    bottom_left_x, bottom_left_y = transformer.transform(xx=south, yy=west)
    top_left_x, top_left_y = transformer.transform(xx=north, yy=west)
    top_right_x, top_right_y = transformer.transform(xx=north, yy=east)
    bottom_right_x, bottom_right_y = transformer.transform(xx=south, yy=east)

    west = min(bottom_left_y, bottom_right_y)
    east = max(top_left_y, top_right_y)
    north = min(bottom_left_x, top_left_x)
    south = max(bottom_right_x, top_right_x)

    return north, south, east, west
