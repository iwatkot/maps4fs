"""This module contains provider of Thuringia data."""

import os
from maps4fs.generator.dtm import utils
from maps4fs.generator.dtm.dtm import DTMProvider

class ThuringiaProvider(DTMProvider):
    """Provider of Thuringia data.
    Data is provided by the Kompetenzzentrum Geodateninfrastruktur Thüringen (© GDI-Th) and available
    at https://geoportal.thueringen.de/gdi-th/download-offene-geodaten/download-hoehendaten under BY 2.0 license.
    """
    _code = "thuringia"
    _name = "Thüringen DGM1"
    _region = "DE"
    _icon = "🇩🇪󠁥󠁢󠁹󠁿"
    _resolution = 1
    _author = "[H4rdB4se](https://github.com/H4rdB4se)"
    _is_community = True
    _instructions = None
    _extents = [(51.5997, 50.2070, 12.69674, 9.8548)]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tiff_path = os.path.join(self._tile_directory, "tiffs")
        os.makedirs(self.tiff_path, exist_ok=True)

    def download_tiles(self) -> list[str]:
        bbox = self.get_bbox()
        west, east, north, south = utils.transform_bbox(bbox, "EPSG:25832")
        download_urls = self.get_download_urls(north, south, east, west)
        all_tif_files = self.download_tif_files(download_urls, self.tiff_path)
        return all_tif_files

    @staticmethod
    def get_first_n_digits(value: float, digits: int) -> int:
        """Get the first n digits of a number."""
        return int(str(value)[:digits])

    def get_download_urls(self, north: float, south: float, east: float, west: float) -> list[str]:
        """Calculate all possible tiles within the bounding box.

        Args:
            north (float): Northern boundary.
            south (float): Southern boundary.
            east (float): Eastern boundary.
            west (float): Western boundary.

        Returns:
            list: List of tile names.
        """
        urls = []
        lat = self.get_first_n_digits(south, 4)
        while lat <= self.get_first_n_digits(north, 4):
            lon = self.get_first_n_digits(west, 3)
            while lon <= self.get_first_n_digits(east, 3):
                tile_url = f"https://geoportal.geoportal-th.de/hoehendaten/DGM/dgm_2020-2025/dgm1_32_{lon}_{lat}_1_th_2020-2025.zip"
                urls.append(tile_url)
                lon += 1
            lat += 1
        return urls
