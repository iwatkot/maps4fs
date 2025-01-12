"""This module contains provider of Bavaria data."""

import os

from xml.etree import ElementTree as ET
import numpy as np
import requests
from maps4fs.generator.dtm.dtm import DTMProvider, DTMProviderSettings

class BavariaProviderSettings(DTMProviderSettings):
    """Settings for the Bavaria provider."""


class BavariaProvider(DTMProvider):
    """Provider of Bavaria Digital terrain model (DTM) 1m data.
    Data is provided by the 'Bayerische Vermessungsverwaltung' and available
    at https://geodaten.bayern.de/opengeodata/OpenDataDetail.html?pn=dgm1 under CC BY 4.0 license.
    """

    _code = "bavaria"
    _name = "Bavaria DGM1"
    _region = "DE"
    _icon = "🇩🇪󠁥󠁢󠁹󠁿"
    _resolution = 1
    _data: np.ndarray | None = None
    _settings = BavariaProviderSettings
    _author = "[H4rdB4se](https://github.com/H4rdB4se)"
    _is_community = True
    _instructions = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tiff_path = os.path.join(self._tile_directory, "tiffs")
        os.makedirs(self.tiff_path, exist_ok=True)
        self.meta4_path = os.path.join(self._tile_directory, "meta4")
        os.makedirs(self.meta4_path, exist_ok=True)

    def download_tiles(self) -> list[str]:
        download_urls = self.get_download_urls()
        all_tif_files = self.download_tif_files(download_urls, self.tiff_path)
        return all_tif_files

    def get_download_urls(self) -> list[str]:
        """Download .meta4 (xml format) file and extract URLs of all required GeoTIFF files.

        Returns:
            list: List of download URLs.
        """
        urls: list[str] = []
        try:
            # Make the GET request
            (north, south, east, west) = self.get_bbox()
            response = requests.post(
                "https://geoservices.bayern.de/services/poly2metalink/metalink/dgm1",
                (f"SRID=4326;POLYGON(({west} {south},{east} {south},"
                 f"{east} {north},{west} {north},{west} {south}))"),
                stream=True,
                timeout=60
            )

            # Check if the request was successful (HTTP status code 200)
            if response.status_code == 200:
                file_path = os.path.join(self.meta4_path, "download.meta4")
                # Write the content of the response to the file
                with open(file_path, "wb") as meta_file:
                    for chunk in response.iter_content(chunk_size=8192):  # Download in chunks
                        meta_file.write(chunk)
                self.logger.info("File downloaded successfully: %s", file_path)

                # Parse the XML response
                root = ET.parse(file_path).getroot()
                namespace = {'ml': 'urn:ietf:params:xml:ns:metalink'}

                for file in root.findall('.//ml:file', namespace):
                    url = file.find('ml:url', namespace)
                    if url is not None:
                        urls.append(str(url.text))
            # pylint: disable=R0801
            else:
                self.logger.error("Failed to get data. HTTP Status Code: %s", response.status_code)
        except requests.exceptions.RequestException as e:
            self.logger.error("Failed to get data. Error: %s", e)
        self.logger.debug("Received %s urls", len(urls))
        return urls
        # pylint: enable=R0801
