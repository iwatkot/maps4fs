"""This module contains provider of Lithuania data."""

from typing import List
import requests
import numpy as np
from maps4fs.generator.dtm.dtm import DTMProvider

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
    _extents = (56.4501789128452, 53.8901567283941, 26.8198345671209, 20.9312456789123)
    _max_tile_size = 4096
    _url = "https://utility.arcgis.com/usrsvcs/servers/fef66dec83c14b0295180ecafa662aa0/rest/services/DTM_LT2020/ImageServer/exportImage"

    def download_tiles(self) -> List[str]:
        north, south, east, west = self.get_bbox()
        
        # Calculate grid size based on requested size
        grid_size = max(1, self.size // self._max_tile_size)
        tile_size = min(self._max_tile_size, self.size)
        
        lat_splits = np.linspace(south, north, grid_size + 1)
        lon_splits = np.linspace(west, east, grid_size + 1)
        download_urls = []

        for i in range(grid_size):
            for j in range(grid_size):
                tile_south, tile_north = lat_splits[i:i+2]
                tile_west, tile_east = lon_splits[j:j+2]
                
                params = {
                    'f': 'json',
                    'bbox': f"{tile_west},{tile_south},{tile_east},{tile_north}",
                    'bboxSR': '4326',
                    'imageSR': '3346',
                    'format': 'tiff',
                    'pixelType': 'F32',
                    'size': f"{tile_size},{tile_size}"
                }

                response = requests.get(self.url, params=params, verify=False, timeout=60)
                data = response.json()
                image_url = data.get('href')
                
                if not image_url:
                    self.logger.error(f"Failed response: {response.text}")
                    raise RuntimeError(f"No image URL in response for tile {i},{j}")

                download_urls.append(image_url)

        return self.download_tif_files(download_urls, self._tile_directory)