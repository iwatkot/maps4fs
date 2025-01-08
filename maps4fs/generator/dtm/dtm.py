"""This module contains the DTMProvider class and its subclasses. DTMProvider class is used to
define different providers of digital terrain models (DTM) data. Each provider has its own URL
and specific settings for downloading and processing the data."""

from __future__ import annotations

from abc import ABC, abstractmethod
import os
from typing import TYPE_CHECKING, Type

import numpy as np
import osmnx as ox  # type: ignore
import rasterio  # type: ignore
import requests
from pydantic import BaseModel

from maps4fs.logger import Logger

if TYPE_CHECKING:
    from maps4fs.generator.map import Map


class DTMProviderSettings(BaseModel):
    """Base class for DTM provider settings models."""


# pylint: disable=too-many-public-methods
class DTMProvider(ABC):
    """Base class for DTM providers."""

    _code: str | None = None
    _name: str | None = None
    _region: str | None = None
    _icon: str | None = None
    _resolution: float | str | None = None

    _url: str | None = None

    _author: str | None = None
    _contributors: str | None = None
    _is_community: bool = False
    _is_base: bool = False
    _settings: Type[DTMProviderSettings] | None = None

    _instructions: str | None = None

    # pylint: disable=R0913, R0917
    def __init__(
        self,
        coordinates: tuple[float, float],
        user_settings: DTMProviderSettings | None,
        size: int,
        directory: str,
        logger: Logger,
        map: Map | None = None,  # pylint: disable=W0622
    ):
        self._coordinates = coordinates
        self._user_settings = user_settings
        self._size = size

        if not self._code:
            raise ValueError("Provider code must be defined.")
        self._tile_directory = os.path.join(directory, self._code)
        os.makedirs(self._tile_directory, exist_ok=True)

        self.logger = logger
        self.map = map

        self._data_info: dict[str, int | str | float] | None = None

    @property
    def data_info(self) -> dict[str, int | str | float] | None:
        """Information about the DTM data.

        Returns:
            dict: Information about the DTM data.
        """
        return self._data_info

    @data_info.setter
    def data_info(self, value: dict[str, int | str | float] | None) -> None:
        """Set information about the DTM data.

        Arguments:
            value (dict): Information about the DTM data.
        """
        self._data_info = value

    @property
    def coordinates(self) -> tuple[float, float]:
        """Coordinates of the center point of the DTM data.

        Returns:
            tuple: Latitude and longitude of the center point.
        """
        return self._coordinates

    @property
    def size(self) -> int:
        """Size of the DTM data in meters.

        Returns:
            int: Size of the DTM data.
        """
        return self._size

    @property
    def url(self) -> str | None:
        """URL of the provider."""
        return self._url

    def formatted_url(self, **kwargs) -> str:
        """Formatted URL of the provider."""
        if not self.url:
            raise ValueError("URL must be defined.")
        return self.url.format(**kwargs)

    @classmethod
    def author(cls) -> str | None:
        """Author of the provider.

        Returns:
            str: Author of the provider.
        """
        return cls._author

    @classmethod
    def contributors(cls) -> str | None:
        """Contributors of the provider.

        Returns:
            str: Contributors of the provider.
        """
        return cls._contributors

    @classmethod
    def is_base(cls) -> bool:
        """Is the provider a base provider.

        Returns:
            bool: True if the provider is a base provider, False otherwise.
        """
        return cls._is_base

    @classmethod
    def is_community(cls) -> bool:
        """Is the provider a community-driven project.

        Returns:
            bool: True if the provider is a community-driven project, False otherwise.
        """
        return cls._is_community

    @classmethod
    def settings(cls) -> Type[DTMProviderSettings] | None:
        """Settings model of the provider.

        Returns:
            Type[DTMProviderSettings]: Settings model of the provider.
        """
        return cls._settings

    @classmethod
    def instructions(cls) -> str | None:
        """Instructions for using the provider.

        Returns:
            str: Instructions for using the provider.
        """
        return cls._instructions

    @property
    def user_settings(self) -> DTMProviderSettings | None:
        """User settings of the provider.

        Returns:
            DTMProviderSettings: User settings of the provider.
        """
        return self._user_settings

    @classmethod
    def description(cls) -> str:
        """Description of the provider.

        Returns:
            str: Provider description.
        """
        return f"{cls._icon} {cls._region} [{cls._resolution} m/px] {cls._name}"

    @classmethod
    def get_provider_by_code(cls, code: str) -> Type[DTMProvider] | None:
        """Get a provider by its code.

        Arguments:
            code (str): Provider code.

        Returns:
            DTMProvider: Provider class or None if not found.
        """
        for provider in cls.__subclasses__():
            if provider._code == code:  # pylint: disable=W0212
                return provider
        return None

    @classmethod
    def get_provider_descriptions(cls) -> dict[str, str]:
        """Get descriptions of all providers, where keys are provider codes and
        values are provider descriptions.

        Returns:
            dict: Provider descriptions.
        """
        providers = {}
        for provider in cls.__subclasses__():
            if not provider.is_base():
                providers[provider._code] = provider.description()  # pylint: disable=W0212
        return providers  # type: ignore

    def download_tile(self, output_path: str, **kwargs) -> bool:
        """Download a tile from the provider.

        Arguments:
            output_path (str): Path to save the downloaded tile.

        Returns:
            bool: True if the tile was downloaded successfully, False otherwise.
        """
        url = self.formatted_url(**kwargs)
        response = requests.get(url, stream=True, timeout=10)
        if response.status_code == 200:
            with open(output_path, "wb") as file:
                for chunk in response.iter_content(chunk_size=1024):
                    file.write(chunk)
            return True
        return False

    def get_or_download_tile(self, output_path: str, **kwargs) -> str | None:
        """Get or download a tile from the provider.

        Arguments:
            output_path (str): Path to save the downloaded tile.

        Returns:
            str: Path to the downloaded tile or None if the tile not exists and was
                not downloaded.
        """
        if not os.path.exists(output_path):
            if not self.download_tile(output_path, **kwargs):
                return None
        return output_path

    def get_tile_parameters(self, *args, **kwargs) -> dict:
        """Get parameters for the tile, that will be used to format the URL.
        Must be implemented in subclasses.

        Returns:
            dict: Tile parameters to format the URL.
        """
        raise NotImplementedError

    @abstractmethod
    def get_numpy(self) -> np.ndarray:
        """Get numpy array of the tile.
        Resulting array must be 16 bit (signed or unsigned) integer and it should be already
        windowed to the bounding box of ROI. It also must have only one channel.

        Returns:
            np.ndarray: Numpy array of the tile.
        """
        raise NotImplementedError

    def get_bbox(self) -> tuple[float, float, float, float]:
        """Get bounding box of the tile based on the center point and size.

        Returns:
            tuple: Bounding box of the tile (north, south, east, west).
        """
        west, south, east, north = ox.utils_geo.bbox_from_point(  # type: ignore
            self.coordinates, dist=self.size // 2, project_utm=False
        )
        bbox = north, south, east, west
        return bbox

    def extract_roi(self, tile_path: str) -> np.ndarray:
        """Extract region of interest (ROI) from the GeoTIFF file.

        Arguments:
            tile_path (str): Path to the GeoTIFF file.

        Raises:
            ValueError: If the tile does not contain any data.

        Returns:
            np.ndarray: Numpy array of the ROI.
        """
        north, south, east, west = self.get_bbox()
        with rasterio.open(tile_path) as src:
            self.logger.debug("Opened tile, shape: %s, dtype: %s.", src.shape, src.dtypes[0])
            window = rasterio.windows.from_bounds(west, south, east, north, src.transform)
            self.logger.debug(
                "Window parameters. Column offset: %s, row offset: %s, width: %s, height: %s.",
                window.col_off,
                window.row_off,
                window.width,
                window.height,
            )
            data = src.read(1, window=window)
        if not data.size > 0:
            raise ValueError("No data in the tile.")

        return data

    def info_sequence(self) -> dict[str, int | str | float] | None:
        """Returns the information sequence for the component. Must be implemented in the child
        class. If the component does not have an information sequence, an empty dictionary must be
        returned.

        Returns:
            dict[str, int | str | float] | None: Information sequence for the component.
        """
        return self.data_info
