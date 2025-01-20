"""This module contains the base WCS provider."""

import os
from abc import abstractmethod

from owslib.wcs import WebCoverageService
from tqdm import tqdm

from maps4fs.generator.dtm import utils
from maps4fs.generator.dtm.dtm import DTMProvider


# pylint: disable=too-many-locals
class WCSProvider(DTMProvider):
    """Generic provider of WCS sources."""

    _is_base = True
    _wcs_version = "2.0.1"
    _source_crs: str = "EPSG:4326"
    _tile_size: float = 0.02

    @abstractmethod
    def get_wcs_parameters(self, tile: tuple[float, float, float, float]) -> dict:
        """Get the parameters for the WCS request.

        Arguments:
            tile (tuple): The tile to download.

        Returns:
            dict: The parameters for the WCS request.
        """

    def get_wcs_instance_parameters(self) -> dict:
        """Get the parameters for the WCS instance.

        Returns:
            dict: The parameters for the WCS instance.
        """
        return {
            "url": self._url,
            "version": self._wcs_version,
            "timeout": 120,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.shared_tiff_path = os.path.join(self._tile_directory, "shared")
        os.makedirs(self.shared_tiff_path, exist_ok=True)

    def download_tiles(self) -> list[str]:
        bbox = self.get_bbox()
        bbox = utils.transform_bbox(bbox, self._source_crs)
        tiles = utils.tile_bbox(bbox, self._tile_size)

        all_tif_files = self.download_all_tiles(tiles)
        return all_tif_files

    def download_all_tiles(self, tiles: list[tuple[float, float, float, float]]) -> list[str]:
        """Download tiles from the NI provider.

        Arguments:
            tiles (list): List of tiles to download.

        Returns:
            list: List of paths to the downloaded GeoTIFF files.
        """
        all_tif_files = []
        params = self.get_wcs_instance_parameters()
        wcs = WebCoverageService(**params)

        for tile in tqdm(tiles, desc="Downloading tiles", unit="tile", disable=self.map.is_public):
            file_name = "_".join(map(str, tile)) + ".tif"
            file_path = os.path.join(self.shared_tiff_path, file_name)
            if not os.path.exists(file_path):
                output = wcs.getCoverage(**self.get_wcs_parameters(tile))
                with open(file_path, "wb") as f:
                    f.write(output.read())

            all_tif_files.append(file_path)
        return all_tif_files
