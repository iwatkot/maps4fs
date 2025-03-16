"""This module contains provider of Thuringia data."""

import os
from pyproj import Transformer, CRS
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
        self.tiff_path = os.path.join(self._tile_directory, f"tiffs")
        os.makedirs(self.tiff_path, exist_ok=True)

    def download_tiles(self) -> list[str]:
        (north, south, east, west) = self.get_converted_bbox()
        download_urls = self.get_download_urls(north, south, east, west)
        all_tif_files = self.download_tif_files(download_urls, self.tiff_path)
        return all_tif_files
    
    @staticmethod
    def get_first_n_digits(value: int, digits: int) -> int:
        return int(str(value)[:digits])
    
    def get_converted_bbox(self) -> dict[float, float, float, float]:
        """Returns bounding box in the format of (north, south, east, west) in EPSG:25832."""

        (north, south, east, west) = self.get_bbox()

        transformer = Transformer.from_crs("epsg:4326", "epsg:25832")
        north_utm, east_utm = transformer.transform(north, east)
        south_utm, west_utm = transformer.transform(south, west)
    
        self.logger.debug("Converted bounding box: %s", (north_utm, south_utm, east_utm, west_utm))

        return (north_utm, south_utm, east_utm, west_utm)
    
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
        lat = self.get_first_n_digits(south, 3)
        while lat <= self.get_first_n_digits(north, 3):
            lon = self.get_first_n_digits(west, 4)
            while lon <= self.get_first_n_digits(east, 4):
                tile_url = f"https://geoportal.geoportal-th.de/hoehendaten/DGM/dgm_2020-2025/dgm1_32_{lat}_{lon}_1_th_2020-2025.zip"
                urls.append(tile_url)
                lon += 1
            lat += 1
        return urls