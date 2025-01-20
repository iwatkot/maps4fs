"""This module contains the base WMS provider."""

import os
from abc import abstractmethod

from owslib.wms import WebMapService
from tqdm import tqdm

from maps4fs.generator.dtm import utils
from maps4fs.generator.dtm.dtm import DTMProvider


# pylint: disable=too-many-locals
class WMSProvider(DTMProvider):
    """Generic provider of WMS sources."""

    _is_base = True
    _wms_version = "1.3.0"
    _source_crs: str = "EPSG:4326"
    _tile_size: float = 0.02

    @abstractmethod
    def get_wms_parameters(self, tile: tuple[float, float, float, float]) -> dict:
        """Get the parameters for the WMS request.

        Arguments:
            tile (tuple): The tile to download.

        Returns:
            dict: The parameters for the WMS request.
        """

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
        """Download tiles from the WMS provider.

        Arguments:
            tiles (list): List of tiles to download.

        Returns:
            list: List of paths to the downloaded GeoTIFF files.
        """
        all_tif_files = []
        wms = WebMapService(
            self._url,
            version=self._wms_version,
            # auth=Authentication(verify=False),
            timeout=600,
        )
        for tile in tqdm(tiles, desc="Downloading tiles", unit="tile", disable=self.map.is_public):
            file_name = "_".join(map(str, tile)) + ".tif"
            file_path = os.path.join(self.shared_tiff_path, file_name)
            if not os.path.exists(file_path):
                output = wms.getmap(**self.get_wms_parameters(tile))
                with open(file_path, "wb") as f:
                    f.write(output.read())

            all_tif_files.append(file_path)
        return all_tif_files
