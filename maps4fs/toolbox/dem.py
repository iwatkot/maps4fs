"""This module contains functions for working with Digital Elevation Models (DEMs)."""

import os

import rasterio  # type: ignore
from pyproj import Transformer
from rasterio.io import DatasetReader  # type: ignore
from rasterio.windows import from_bounds  # type: ignore


def read_geo_tiff(file_path: str) -> DatasetReader:
    """Read a GeoTIFF file and return the DatasetReader object.

    Arguments:
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

    Arguments:
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


# pylint: disable=R0914
def extract_roi(file_path: str, bbox: tuple[float, float, float, float]) -> str:
    """Extract a region of interest (ROI) from a GeoTIFF file and save it as a new file.

    Arguments:
        file_path (str): The path to the GeoTIFF file.
        bbox (tuple[float, float, float, float]): The bounding box of the region of interest
            as (north, south, east, west).

    Raises:
        RuntimeError: If there is no data in the selected region.

    Returns:
        str: The path to the new GeoTIFF file containing the extracted ROI.
    """
    with rasterio.open(file_path) as src:
        transformer = Transformer.from_crs("EPSG:4326", src.crs, always_xy=True)
        north, south, east, west = bbox

        left, bottom = transformer.transform(west, south)
        right, top = transformer.transform(east, north)

        window = from_bounds(left, bottom, right, top, src.transform)
        data = src.read(window=window)

    if not data.size > 0:
        raise RuntimeError("No data in the selected region.")

    base_name = os.path.basename(file_path).split(".")[0]
    dir_name = os.path.dirname(file_path)

    output_name = f"{base_name}_{north}_{south}_{east}_{west}.tif"

    output_path = os.path.join(dir_name, output_name)

    with rasterio.open(
        output_path,
        "w",
        driver="GTiff",
        height=data.shape[1],
        width=data.shape[2],
        count=data.shape[0],
        dtype=data.dtype,
        crs=src.crs,
        transform=src.window_transform(window),
    ) as dst:
        dst.write(data)

    return output_path
