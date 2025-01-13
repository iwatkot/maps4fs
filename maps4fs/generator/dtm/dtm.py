"""This module contains the DTMProvider class and its subclasses. DTMProvider class is used to
define different providers of digital terrain models (DTM) data. Each provider has its own URL
and specific settings for downloading and processing the data."""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Type
from zipfile import ZipFile

import numpy as np
import osmnx as ox  # type: ignore
import rasterio  # type: ignore
import requests
from pydantic import BaseModel
from rasterio.enums import Resampling
from rasterio.merge import merge
from rasterio.warp import calculate_default_transform, reproject

from maps4fs.logger import Logger

if TYPE_CHECKING:
    from maps4fs.generator.map import Map


class DTMProviderSettings(BaseModel):
    """Base class for DTM provider settings models."""

    easy_mode: bool = True
    power_factor: int = 0


# pylint: disable=too-many-public-methods, too-many-instance-attributes
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

    _base_instructions = (
        "ℹ️ Using **Easy mode** is recommended, as it automatically adjusts the values in the "
        "image, so the terrain elevation in Giants Editor will match real world "
        "elevation in meters.  \n"
        "ℹ️ If the terrain height difference in the real world is bigger than 255 meters, "
        "the [Height scale](https://github.com/iwatkot/maps4fs/blob/main/docs/dem.md#height-scale)"
        " parameter in the **map.i3d** file will be automatically adjusted.  \n"
        "⚡ If the **Easy mode** option is disabled, you will probably get completely flat "
        "terrain, unless you adjust the DEM Multiplier Setting or the Height scale parameter in "
        "the Giants Editor.  \n"
        "💡 You can use the **Power factor** setting to make the difference between heights "
        "bigger. Be extremely careful with this setting, and use only low values, otherwise your "
        "terrain may be completely broken.  \n"
    )

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

    @classmethod
    def base_instructions(cls) -> str | None:
        """Instructions for using any provider.

        Returns:
            str: Instructions for using any provider.
        """
        return cls._base_instructions

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
            providers[provider._code] = provider.description()  # pylint: disable=W0212
        return providers  # type: ignore

    @abstractmethod
    def download_tiles(self) -> list[str]:
        """Download tiles from the provider.

        Returns:
            list: List of paths to the downloaded tiles.
        """
        raise NotImplementedError

    def get_numpy(self) -> np.ndarray:
        """Get numpy array of the tile.
        Resulting array must be 16 bit (signed or unsigned) integer and it should be already
        windowed to the bounding box of ROI. It also must have only one channel.

        Returns:
            np.ndarray: Numpy array of the tile.
        """
        # download tiles using DTM provider implementation
        tiles = self.download_tiles()
        self.logger.debug(f"Downloaded {len(tiles)} DEM tiles")

        # merge tiles if necessary
        if len(tiles) > 1:
            self.logger.debug("Multiple tiles downloaded. Merging tiles")
            tile, _ = self.merge_geotiff(tiles)
        else:
            tile = tiles[0]

        # determine CRS of the resulting tile and reproject if necessary
        with rasterio.open(tile) as src:
            crs = src.crs
        if crs != "EPSG:4326":
            self.logger.debug(f"Reprojecting GeoTIFF from {crs} to EPSG:4326...")
            tile = self.reproject_geotiff(tile)

        # extract region of interest from the tile
        data = self.extract_roi(tile)

        # process elevation data to be compatible with the game
        data = self.process_elevation(data)

        return data

    def process_elevation(self, data: np.ndarray) -> np.ndarray:
        """Process elevation data.

        Arguments:
            data (np.ndarray): Elevation data.

        Returns:
            np.ndarray: Processed elevation data.
        """
        self.data_info = {}
        self.add_numpy_params(data, "original")

        data = self.ground_height_data(data)
        self.add_numpy_params(data, "grounded")

        original_deviation = int(self.data_info["original_deviation"])
        in_game_maximum_height = 65535 // 255
        if original_deviation > in_game_maximum_height:
            suggested_height_scale_multiplier = (
                original_deviation / in_game_maximum_height  # type: ignore
            )
            suggested_height_scale_value = int(255 * suggested_height_scale_multiplier)
        else:
            suggested_height_scale_multiplier = 1
            suggested_height_scale_value = 255

        self.data_info["suggested_height_scale_multiplier"] = suggested_height_scale_multiplier
        self.data_info["suggested_height_scale_value"] = suggested_height_scale_value

        self.map.shared_settings.height_scale_multiplier = (  # type: ignore
            suggested_height_scale_multiplier
        )
        self.map.shared_settings.height_scale_value = suggested_height_scale_value  # type: ignore

        if self.user_settings.easy_mode:  # type: ignore
            try:
                data = self.normalize_dem(data)
                self.add_numpy_params(data, "normalized")

                normalized_deviation = self.data_info["normalized_deviation"]
                z_scaling_factor = normalized_deviation / original_deviation  # type: ignore
                self.data_info["z_scaling_factor"] = z_scaling_factor

                self.map.shared_settings.mesh_z_scaling_factor = z_scaling_factor  # type: ignore
                self.map.shared_settings.change_height_scale = True  # type: ignore

            except Exception as e:  # pylint: disable=W0718
                self.logger.error(
                    "Failed to normalize DEM data. Error: %s. Using original data.", e
                )

        return data.astype(np.uint16)

    def info_sequence(self) -> dict[str, int | str | float] | None:
        """Returns the information sequence for the component. Must be implemented in the child
        class. If the component does not have an information sequence, an empty dictionary must be
        returned.

        Returns:
            dict[str, int | str | float] | None: Information sequence for the component.
        """
        return self.data_info

    # region helpers
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

    def download_tif_files(self, urls: list[str], output_path: str) -> list[str]:
        """Download GeoTIFF files from the given URLs.

        Arguments:
            urls (list): List of URLs to download GeoTIFF files from.
            output_path (str): Path to save the downloaded GeoTIFF files.

        Returns:
            list: List of paths to the downloaded GeoTIFF files.
        """
        tif_files: list[str] = []
        for url in urls:
            file_name = os.path.basename(url)
            self.logger.debug("Retrieving TIFF: %s", file_name)
            file_path = os.path.join(output_path, file_name)
            if not os.path.exists(file_path):
                try:
                    # Send a GET request to the file URL
                    response = requests.get(url, stream=True, timeout=60)
                    response.raise_for_status()  # Raise an error for HTTP status codes 4xx/5xx

                    # Write the content of the response to the file
                    with open(file_path, "wb") as file:
                        for chunk in response.iter_content(chunk_size=8192):  # Download in chunks
                            file.write(chunk)
                    self.logger.debug("File downloaded successfully: %s", file_path)
                except requests.exceptions.RequestException as e:
                    self.logger.error("Failed to download file: %s", e)
            else:
                self.logger.debug("File already exists: %s", file_name)
            if file_name.endswith(".zip"):
                file_path = self.unzip_img_from_tif(file_name, output_path)
            tif_files.append(file_path)
        return tif_files

    def unzip_img_from_tif(self, file_name: str, output_path: str) -> str:
        """Unpacks the .img file from the zip file.

        Arguments:
            file_name (str): Name of the file to unzip.
            output_path (str): Path to the output directory.

        Returns:
            str: Path to the unzipped file.
        """
        file_path = os.path.join(output_path, file_name)
        img_file_name = file_name.replace(".zip", ".img")
        img_file_path = os.path.join(output_path, img_file_name)
        if not os.path.exists(img_file_path):
            with ZipFile(file_path, "r") as f_in:
                f_in.extract(img_file_name, output_path)
            self.logger.debug("Unzipped file %s to %s", file_name, img_file_name)
        else:
            self.logger.debug("File already exists: %s", img_file_name)
        return img_file_path

    def reproject_geotiff(self, input_tiff: str) -> str:
        """Reproject a GeoTIFF file to a new coordinate reference system (CRS).

        Arguments:
            input_tiff (str): Path to the input GeoTIFF file.

        Returns:
            str: Path to the reprojected GeoTIFF file.
        """
        output_tiff = os.path.join(self._tile_directory, "reprojected.tif")

        # Open the source GeoTIFF
        self.logger.debug("Reprojecting GeoTIFF to EPSG:4326 CRS...")
        with rasterio.open(input_tiff) as src:
            # Get the transform, width, and height of the target CRS
            transform, width, height = calculate_default_transform(
                src.crs, "EPSG:4326", src.width, src.height, *src.bounds
            )

            # Update the metadata for the target GeoTIFF
            kwargs = src.meta.copy()
            kwargs.update(
                {"crs": "EPSG:4326", "transform": transform, "width": width, "height": height}
            )

            # Open the destination GeoTIFF file and reproject
            with rasterio.open(output_tiff, "w", **kwargs) as dst:
                for i in range(1, src.count + 1):  # Iterate over all raster bands
                    reproject(
                        source=rasterio.band(src, i),
                        destination=rasterio.band(dst, i),
                        src_transform=src.transform,
                        src_crs=src.crs,
                        dst_transform=transform,
                        dst_crs="EPSG:4326",
                        resampling=Resampling.nearest,  # Choose resampling method
                    )

        self.logger.debug("Reprojected GeoTIFF saved to %s", output_tiff)
        return output_tiff

    def merge_geotiff(self, input_files: list[str]) -> tuple[str, str]:
        """Merge multiple GeoTIFF files into a single GeoTIFF file.

        Arguments:
            input_files (list): List of input GeoTIFF files to merge.
        """
        output_file = os.path.join(self._tile_directory, "merged.tif")
        # Open all input GeoTIFF files as datasets
        self.logger.debug("Merging tiff files...")
        datasets = [rasterio.open(file) for file in input_files]

        # Merge datasets
        crs = datasets[0].crs
        mosaic, out_transform = merge(datasets, nodata=0)

        # Get metadata from the first file and update it for the output
        out_meta = datasets[0].meta.copy()
        out_meta.update(
            {
                "driver": "GTiff",
                "height": mosaic.shape[1],
                "width": mosaic.shape[2],
                "transform": out_transform,
                "count": mosaic.shape[0],  # Number of bands
            }
        )

        # Write merged GeoTIFF to the output file
        with rasterio.open(output_file, "w", **out_meta) as dest:
            dest.write(mosaic)

        self.logger.debug("GeoTIFF images merged successfully into %s", output_file)
        return output_file, crs

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
            data = src.read(1, window=window, masked=True)
        if not data.size > 0:
            raise ValueError("No data in the tile.")

        return data

    def normalize_dem(self, data: np.ndarray) -> np.ndarray:
        """Normalize DEM data to 16-bit unsigned integer using max height from settings.

        Arguments:
            data (np.ndarray): DEM data from SRTM file after cropping.

        Returns:
            np.ndarray: Normalized DEM data.
        """
        maximum_height = int(data.max())
        minimum_height = int(data.min())
        deviation = maximum_height - minimum_height
        self.logger.debug(
            "Maximum height: %s. Minimum height: %s. Deviation: %s.",
            maximum_height,
            minimum_height,
            deviation,
        )
        self.logger.debug("Number of unique values in original DEM data: %s.", np.unique(data).size)

        adjusted_maximum_height = maximum_height * 255
        adjusted_maximum_height = min(adjusted_maximum_height, 65535)
        scaling_factor = adjusted_maximum_height / maximum_height
        self.logger.debug(
            "Adjusted maximum height: %s. Scaling factor: %s.",
            adjusted_maximum_height,
            scaling_factor,
        )

        if self.user_settings.power_factor:  # type: ignore
            power_factor = 1 + self.user_settings.power_factor / 10  # type: ignore
            self.logger.debug(
                "Applying power factor: %s to the DEM data.",
                power_factor,
            )
            data = np.power(data, power_factor).astype(np.uint16)

        normalized_data = np.round(data * scaling_factor).astype(np.uint16)
        self.logger.debug(
            "Normalized data maximum height: %s. Minimum height: %s. Number of unique values: %s.",
            normalized_data.max(),
            normalized_data.min(),
            np.unique(normalized_data).size,
        )
        return normalized_data

    @staticmethod
    def ground_height_data(data: np.ndarray, add_one: bool = True) -> np.ndarray:
        """Shift the data to ground level (0 meter).
        Optionally add one meter to the data to leave some room
        for the water level and pit modifications.

        Arguments:
            data (np.ndarray): DEM data after cropping.
            add_one (bool): Add one meter to the data

        Returns:
            np.ndarray: Unsigned DEM data.
        """
        data = data - data.min()
        if add_one:
            data = data + 1
        return data

    def add_numpy_params(
        self,
        data: np.ndarray,
        prefix: str,
    ) -> None:
        """Add numpy array parameters to the data_info dictionary.

        Arguments:
            data (np.ndarray): Numpy array of the tile.
            prefix (str): Prefix for the parameters.
        """
        self.data_info[f"{prefix}_minimum_height"] = int(data.min())  # type: ignore
        self.data_info[f"{prefix}_maximum_height"] = int(data.max())  # type: ignore
        self.data_info[f"{prefix}_deviation"] = int(data.max() - data.min())  # type: ignore
        self.data_info[f"{prefix}_unique_values"] = int(np.unique(data).size)  # type: ignore

    # endregion
