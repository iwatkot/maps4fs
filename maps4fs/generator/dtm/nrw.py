"""This module contains provider of NRW data."""

import os

import numpy as np
from owslib.wcs import WebCoverageService
from owslib.util import Authentication
from pyproj import Transformer

from maps4fs.generator.dtm.dtm import DTMProvider, DTMProviderSettings


class NRWProviderSettings(DTMProviderSettings):
    """Settings for the NRW provider."""


# pylint: disable=too-many-locals
class NRWProvider(DTMProvider):
    """Generic provider of WCS sources."""

    _code = "NRW"
    _name = "North Rhine-Westphalia DGM1"
    _region = "DE"
    _icon = "🇩🇪󠁥󠁢󠁹󠁿"
    _resolution = 1
    _data: np.ndarray | None = None
    _settings = NRWProviderSettings
    _author = "[kbrandwijk](https://github.com/kbrandwijk)"
    _is_community = True
    _instructions = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.shared_tiff_path = os.path.join(self._tile_directory, "shared")
        os.makedirs(self.shared_tiff_path, exist_ok=True)

    def download_tiles(self) -> list[str]:
        bbox = self.get_bbox()
        bbox = self.transform_bbox(bbox, "EPSG:25832")

        tiles = self.tile_bbox(bbox, 1000)

        all_tif_files = self.download_all_tiles(tiles)
        return all_tif_files

    def tile_bbox(
            self,
            bbox: tuple[float, float, float, float],
            tile_size: int) -> list[tuple[float, float, float, float]]:
        """Tile the bounding box into smaller bounding boxes of a specified size.

        Arguments:
            bbox (tuple): Bounding box to tile (north, south, east, west).
            tile_size (int): Size of the tiles in meters.

        Returns:
            list: List of smaller bounding boxes (north, south, east, west).
        """
        north, south, east, west = bbox
        x_coords = np.arange(west, east, tile_size)
        y_coords = np.arange(south, north, tile_size)
        x_coords = np.append(x_coords, east).astype(x_coords.dtype)
        y_coords = np.append(y_coords, north).astype(y_coords.dtype)

        x_min, y_min = np.meshgrid(x_coords[:-1], y_coords[:-1], indexing="ij")
        x_max, y_max = np.meshgrid(x_coords[1:], y_coords[1:], indexing="ij")

        tiles = np.stack([x_min.ravel(), y_min.ravel(), x_max.ravel(), y_max.ravel()], axis=1)

        return tiles

    def download_all_tiles(self, tiles: list[tuple[float, float, float, float]]) -> list[str]:
        """Download tiles from the NRW provider.

        Arguments:
            tiles (list): List of tiles to download.

        Returns:
            list: List of paths to the downloaded GeoTIFF files.
        """
        all_tif_files = []
        wcs = WebCoverageService(
            'https://www.wcs.nrw.de/geobasis/wcs_nw_dgm',
            auth=Authentication(verify=False),
            timeout=600)
        for tile in tiles:
            file_name = '_'.join(map(str, tile)) + '.tif'
            file_path = os.path.join(self.shared_tiff_path, file_name)

            if not os.path.exists(file_path):
                output = wcs.getCoverage(
                    identifier=['nw_dgm'],
                    subsets=[('y', str(tile[0]), str(tile[2])), ('x', str(tile[1]), str(tile[3]))],
                    format='image/tiff'
                )
                with open(file_path, 'wb') as f:
                    f.write(output.read())

            all_tif_files.append(file_path)
        return all_tif_files

    def transform_bbox(
            self,
            bbox: tuple[float, float, float, float],
            to_crs: str) -> tuple[float, float, float, float]:
        """Transform the bounding box to a different coordinate reference system (CRS).

        Arguments:
            bbox (tuple): Bounding box to transform (north, south, east, west).
            to_crs (str): Target CRS (e.g., EPSG:4326 for CRS:84).

        Returns:
            tuple: Transformed bounding box (north, south, east, west).
        """
        transformer = Transformer.from_crs("epsg:4326", to_crs)
        north, south, east, west = bbox
        bottom_left_x, bottom_left_y = transformer.transform(xx=south, yy=west)
        top_left_x, top_left_y = transformer.transform(xx=north, yy=west)
        top_right_x, top_right_y = transformer.transform(xx=north, yy=east)
        bottom_right_x, bottom_right_y = transformer.transform(xx=south, yy=east)

        west = min(bottom_left_y, bottom_right_y)
        east = max(top_left_y, top_right_y)
        south = min(bottom_left_x, top_left_x)
        north = max(bottom_right_x, top_right_x)

        return north, south, east, west
