"""This module contains functions for working with Digital Elevation Models (DEMs)."""

import os

import rasterio  # type: ignore
from pyproj import Transformer
from rasterio.io import DatasetReader  # type: ignore


def read_geo_tiff(file_path: str) -> DatasetReader:
    """Read a GeoTIFF file and return the DatasetReader object.

    Args:
        file_path (str): The path to the GeoTIFF file.

    Raises:
        FileNotFoundError: If the file is not found.
        RuntimeError: If there is an error reading the file.

    Returns:
        DatasetReader: The DatasetReader object for the GeoTIFF file.
    """
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    try:
        src = rasterio.open(file_path)
    except Exception as e:
        raise RuntimeError(f"Error reading file: {file_path}") from e

    if not src.bounds or not src.crs:
        raise RuntimeError(
            f"Can not read bounds or CRS from file: {file_path}. "
            f"Bounds: {src.bounds}, CRS: {src.crs}"
        )

    return src


def get_geo_tiff_bbox(
    src: DatasetReader, dst_crs: str | None = "EPSG:4326"
) -> tuple[float, float, float, float]:
    """Return the bounding box of a GeoTIFF file in the destination CRS.

    Args:
        src (DatasetReader): The DatasetReader object for the GeoTIFF file.
        dst_crs (str, optional): The destination CRS. Defaults to "EPSG:4326".

    Returns:
        tuple[float, float, float, float]: The bounding box in the destination CRS
            as (north, south, east, west).
    """
    left, bottom, right, top = src.bounds

    transformer = Transformer.from_crs(src.crs, dst_crs, always_xy=True)

    east, north = transformer.transform(left, top)
    west, south = transformer.transform(right, bottom)

    return north, south, east, west
