"""This module contains provider of Italy data."""

from owslib.util import Authentication

from maps4fs.generator.dtm.base.wcs import WCSProvider
from maps4fs.generator.dtm.dtm import DTMProvider


class ItalyProvider(WCSProvider, DTMProvider):
    """Provider of Italy data."""

    _code = "italy"
    _name = "Italy Tinitaly/1.1"
    _region = "IT"
    _icon = "🇮🇹"
    _resolution = 10
    _author = "[kbrandwijk](https://github.com/kbrandwijk)"
    _is_community = True
    _instructions = None
    _is_base = False
    _extents = (47.15570815704503, 35.177652867276855, 19.720144130809693, 6.527697471770745)

    _url = "http://tinitaly.pi.ingv.it/TINItaly_1_1/wcs"
    _wcs_version = "2.0.1"
    _source_crs = "EPSG:32632"
    _tile_size = 10000

    def get_wcs_instance_parameters(self):
        settings = super().get_wcs_instance_parameters()
        settings["auth"] = Authentication(
            verify=False,
        )
        return settings

    def get_wcs_parameters(self, tile):
        return {
            "identifier": ["TINItaly_1_1__tinitaly_dem"],
            "subsets": [("E", str(tile[1]), str(tile[3])), ("N", str(tile[0]), str(tile[2]))],
            "format": "image/tiff",
        }
