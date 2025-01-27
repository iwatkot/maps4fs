"""This module contains provider of Lithuania data."""

from typing import List

import requests

from maps4fs.generator.dtm.dtm import DTMProvider
from maps4fs.generator.dtm.utils import tile_bbox


class LithuaniaProvider(DTMProvider):
    """Provider of Lithuania data."""

    _code = "lithuania"
    _name = "Lithuania"
    _region = "LT"
    _icon = "🇱🇹"
    _resolution = 1.0
    _author = "[Tox3](https://github.com/Tox3)"
    _is_community = True
    _is_base = False
    _extents = [
        (
            56.4501789128452,
            53.8901567283941,
            26.8198345671209,
            20.9312456789123,
        )
    ]
    _max_tile_size = 4096
    _url = (
        "https://utility.arcgis.com/usrsvcs/servers/fef66dec83c14b0295180ecafa662aa0/"
        "rest/services/DTM_LT2020/ImageServer/exportImage"
    )

    def download_tiles(self) -> List[str]:
        """Download DTM tiles for Lithuania."""
        bbox = self.get_bbox()
        grid_size = max(1, self.size // self._max_tile_size)
        tile_size = (self.size / grid_size) / 111000  # Convert to degrees

        raw_tiles = tile_bbox(bbox, tile_size)
        # Fix coordinate swapping from utils.tile_bbox
        tiles = [(t[1], t[3], t[0], t[2]) for t in raw_tiles]  # Reorder N,S,E,W correctly

        download_urls = []
        for i, (north, south, east, west) in enumerate(tiles):
            params = {
                "f": "json",
                "bbox": f"{west},{south},{east},{north}",
                "bboxSR": "4326",
                "imageSR": "3346",
                "format": "tiff",
                "pixelType": "F32",
                "size": f"{self._max_tile_size},{self._max_tile_size}",
            }

            response = requests.get(
                self.url, params=params, verify=False, timeout=60  # type: ignore
            )
            data = response.json()
            if "href" not in data:
                raise RuntimeError(f"No image URL in response for tile {i}")
            download_urls.append(data["href"])

        return self.download_tif_files(download_urls, self._tile_directory)
