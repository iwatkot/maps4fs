"""This module contains provider of Mecklenburg-Vorpommern data."""

from maps4fs.generator.dtm.base.wcs import WCSProvider
from maps4fs.generator.dtm.dtm import DTMProvider, DTMProviderSettings


class MecklenburgVorpommernProviderSettings(DTMProviderSettings):
    """Settings for the Mecklenburg-Vorpommern provider."""

    dataset: dict | str = {
        "mv_dgm": "Mecklenburg-Vorpommern DGM1",
        "mv_dgm5": "Mecklenburg-Vorpommern DGM5",
        "mv_dgm25": "Mecklenburg-Vorpommern DGM25",
    }


class MecklenburgVorpommernProvider(WCSProvider, DTMProvider):
    """Provider of Mecklenburg-Vorpommern data."""

    _code = "mv"
    _name = "Mecklenburg-Vorpommern"
    _region = "DE"
    _icon = "🇩🇪"
    _resolution = "1-25"
    _author = "[kbrandwijk](https://github.com/kbrandwijk)"
    _is_community = True
    _instructions = None
    _is_base = False
    _settings = MecklenburgVorpommernProviderSettings
    # _extents = (72.1016879476356962, 57.2738836442695103, 33.3365910058243742, -2.0075617181675725)

    _url = "https://www.geodaten-mv.de/dienste/dgm_wcs"
    _wcs_version = "2.0.1"
    _source_crs = "EPSG:25833"
    _tile_size = 1000

    def get_wcs_parameters(self, tile):
        return {
            "identifier": [self.user_settings.dataset],
            "subsets": [("x", str(tile[1]), str(tile[3])), ("y", str(tile[0]), str(tile[2]))],
            # "width": 1000,
            # "height": 1000,
            "format": "image/tiff",
        }
