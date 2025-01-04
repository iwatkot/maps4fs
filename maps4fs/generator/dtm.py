"""This module contains the DTMProvider class and its subclasses. DTMProvider class is used to
define different providers of digital terrain models (DTM) data. Each provider has its own URL
and specific settings for downloading and processing the data."""

from __future__ import annotations

import gzip
import math
import os
import shutil
from datetime import datetime
from typing import Type

import numpy as np
import osmnx as ox  # type: ignore
import rasterio  # type: ignore
import requests
from numpy import ndarray
from pydantic import BaseModel
from rasterio._warp import Resampling  # type: ignore # pylint: disable=E0611
from rasterio.merge import merge  # type: ignore
from rasterio.warp import calculate_default_transform, reproject  # type: ignore
from rasterio.windows import from_bounds  # type: ignore

from maps4fs.logger import Logger


class DTMProviderSettings(BaseModel):
    """Base class for DTM provider settings models."""


class DTMProvider:
    """Base class for DTM providers."""

    _code: str | None = None
    _name: str | None = None
    _region: str | None = None
    _icon: str | None = None
    _resolution: float | None = None

    _url: str | None = None

    _author: str | None = None
    _is_community: bool = False
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
    ):
        self._coordinates = coordinates
        self._user_settings = user_settings
        self._size = size

        if not self._code:
            raise ValueError("Provider code must be defined.")
        self._tile_directory = os.path.join(directory, self._code)
        os.makedirs(self._tile_directory, exist_ok=True)

        self.logger = logger

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


class SRTM30Provider(DTMProvider):
    """Provider of Shuttle Radar Topography Mission (SRTM) 30m data."""

    _code = "srtm30"
    _name = "SRTM 30 m"
    _region = "Global"
    _icon = "🌎"
    _resolution = 30.0

    _url = "https://elevation-tiles-prod.s3.amazonaws.com/skadi/{latitude_band}/{tile_name}.hgt.gz"

    _author = "[iwatkot](https://github.com/iwatkot)"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hgt_directory = os.path.join(self._tile_directory, "hgt")
        self.gz_directory = os.path.join(self._tile_directory, "gz")
        os.makedirs(self.hgt_directory, exist_ok=True)
        os.makedirs(self.gz_directory, exist_ok=True)

    def get_tile_parameters(self, *args, **kwargs) -> dict[str, str]:
        """Returns latitude band and tile name for SRTM tile from coordinates.

        Arguments:
            lat (float): Latitude.
            lon (float): Longitude.

        Returns:
            dict: Tile parameters.
        """
        lat, lon = args

        tile_latitude = math.floor(lat)
        tile_longitude = math.floor(lon)

        latitude_band = f"N{abs(tile_latitude):02d}" if lat >= 0 else f"S{abs(tile_latitude):02d}"
        if lon < 0:
            tile_name = f"{latitude_band}W{abs(tile_longitude):03d}"
        else:
            tile_name = f"{latitude_band}E{abs(tile_longitude):03d}"

        self.logger.debug(
            "Detected tile name: %s for coordinates: lat %s, lon %s.", tile_name, lat, lon
        )
        return {"latitude_band": latitude_band, "tile_name": tile_name}

    def get_numpy(self) -> np.ndarray:
        """Get numpy array of the tile.

        Returns:
            np.ndarray: Numpy array of the tile.
        """
        tile_parameters = self.get_tile_parameters(*self.coordinates)
        tile_name = tile_parameters["tile_name"]
        decompressed_tile_path = os.path.join(self.hgt_directory, f"{tile_name}.hgt")

        if not os.path.isfile(decompressed_tile_path):
            compressed_tile_path = os.path.join(self.gz_directory, f"{tile_name}.hgt.gz")
            if not self.get_or_download_tile(compressed_tile_path, **tile_parameters):
                raise FileNotFoundError(f"Tile {tile_name} not found.")

            with gzip.open(compressed_tile_path, "rb") as f_in:
                with open(decompressed_tile_path, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)

        return self.extract_roi(decompressed_tile_path)


class USGS1mProviderSettings(DTMProviderSettings):
    """Settings for the USGS 1m provider."""

    max_local_elevation: int = 255


# pylint: disable=W0223
class USGS1mProvider(DTMProvider):
    """Provider of USGS."""

    _code = "USGS1m"
    _name = "USGS 1m"
    _region = "USA"
    _icon = "🇺🇸"
    _resolution = 1
    _data: ndarray | None = None
    _settings = USGS1mProviderSettings
    _author = "[ZenJakey](https://github.com/ZenJakey)"

    _url = (
        "https://tnmaccess.nationalmap.gov/api/v1/products?prodFormats=GeoTIFF,IMG&prodExtents="
        "10000 x 10000 meter&datasets=Digital Elevation Model (DEM) 1 meter&polygon="
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.shared_tiff_path = os.path.join(self._tile_directory, "shared")
        os.makedirs(self.shared_tiff_path, exist_ok=True)
        self.output_path = os.path.join(self._tile_directory, f"timestamp_{timestamp}")
        os.makedirs(self.output_path, exist_ok=True)

    def get_download_urls(self) -> list[str]:
        """Get download URLs of the GeoTIFF files from the USGS API.

        Returns:
            list: List of download URLs.
        """
        urls = []
        try:
            # Make the GET request
            (north, south, east, west) = self.get_bbox()
            response = requests.get(  # pylint: disable=W3101
                self.url  # type: ignore
                + f"{west} {south},{east} {south},{east} {north},{west} {north},{west} {south}&="
            )
            self.logger.debug("Getting file locations from USGS...")

            # Check if the request was successful (HTTP status code 200)
            if response.status_code == 200:
                # Parse the JSON response
                json_data = response.json()
                items = json_data["items"]
                for item in items:
                    urls.append(item["downloadURL"])
                self.download_tif_files(urls)
            else:
                self.logger.error("Failed to get data. HTTP Status Code: %s", response.status_code)
        except requests.exceptions.RequestException as e:
            self.logger.error("Failed to get data. Error: %s", e)
        self.logger.debug("Received %s urls", len(urls))
        return urls

    def download_tif_files(self, urls: list[str]) -> list[str]:
        """Download GeoTIFF files from the given URLs.

        Arguments:
            urls (list): List of URLs to download GeoTIFF files from.

        Returns:
            list: List of paths to the downloaded GeoTIFF files.
        """
        tif_files = []
        for url in urls:
            file_name = os.path.basename(url)
            self.logger.debug("Retrieving TIFF: %s", file_name)
            file_path = os.path.join(self.shared_tiff_path, file_name)
            if not os.path.exists(file_path):
                try:
                    # Send a GET request to the file URL
                    response = requests.get(url, stream=True)  # pylint: disable=W3101
                    response.raise_for_status()  # Raise an error for HTTP status codes 4xx/5xx

                    # Write the content of the response to the file
                    with open(file_path, "wb") as file:
                        for chunk in response.iter_content(chunk_size=8192):  # Download in chunks
                            file.write(chunk)
                    self.logger.info("File downloaded successfully: %s", file_path)
                except requests.exceptions.RequestException as e:
                    self.logger.error("Failed to download file: %s", e)
            else:
                self.logger.debug("File already exists: %s", file_name)

            tif_files.append(file_path)
        return tif_files

    def merge_geotiff(self, input_files: list[str], output_file: str) -> None:
        """Merge multiple GeoTIFF files into a single GeoTIFF file.

        Arguments:
            input_files (list): List of input GeoTIFF files to merge.
            output_file (str): Path to save the merged GeoTIFF file.
        """
        # Open all input GeoTIFF files as datasets
        self.logger.debug("Merging tiff files...")
        datasets = [rasterio.open(file) for file in input_files]

        # Merge datasets
        mosaic, out_transform = merge(datasets)

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

    def reproject_geotiff(self, input_tiff: str, output_tiff: str, target_crs: str) -> None:
        """Reproject a GeoTIFF file to a new coordinate reference system (CRS).

        Arguments:
            input_tiff (str): Path to the input GeoTIFF file.
            output_tiff (str): Path to save the reprojected GeoTIFF file.
            target_crs (str): Target CRS (e.g., EPSG:4326 for CRS:84).
        """
        # Open the source GeoTIFF
        self.logger.debug("Reprojecting GeoTIFF to %s CRS...", target_crs)
        with rasterio.open(input_tiff) as src:
            # Get the transform, width, and height of the target CRS
            transform, width, height = calculate_default_transform(
                src.crs, target_crs, src.width, src.height, *src.bounds
            )

            # Update the metadata for the target GeoTIFF
            kwargs = src.meta.copy()
            kwargs.update(
                {"crs": target_crs, "transform": transform, "width": width, "height": height}
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
                        dst_crs=target_crs,
                        resampling=Resampling.nearest,  # Choose resampling method
                    )
        self.logger.debug("Reprojected GeoTIFF saved to %s", output_tiff)

    def extract_roi(self, input_tiff: str) -> np.ndarray:  # pylint: disable=W0237
        """
        Crop a GeoTIFF based on given geographic bounding box and save to a new file.

        Arguments:
            input_tiff (str): Path to the input GeoTIFF file.

        Returns:
            np.ndarray: Numpy array of the cropped GeoTIFF.
        """
        self.logger.debug("Extracting ROI...")
        # Open the input GeoTIFF
        with rasterio.open(input_tiff) as src:

            # Create a rasterio window from the bounding box
            (north, south, east, west) = self.get_bbox()
            window = from_bounds(west, south, east, north, transform=src.transform)

            data = src.read(1, window=window)
            self.logger.debug("Extracted ROI")
            return data

    # pylint: disable=R0914, R0917, R0913
    def convert_geotiff_to_geotiff(
        self,
        input_tiff: str,
        output_tiff: str,
        min_height: float,
        max_height: float,
        target_crs: str,
    ) -> None:
        """
        Convert a GeoTIFF to a scaled GeoTIFF with UInt16 values using a specific coordinate
        system and output size.

        Arguments:
            input_tiff (str): Path to the input GeoTIFF file.
            output_tiff (str): Path to save the output GeoTIFF file.
            min_height (float): Minimum terrain height (input range).
            max_height (float): Maximum terrain height (input range).
            target_crs (str): Target CRS (e.g., EPSG:4326 for CRS:84).
        """
        # Open the input GeoTIFF file
        self.logger.debug("Converting to uint16")
        with rasterio.open(input_tiff) as src:
            # Ensure the input CRS matches the target CRS (reprojection may be required)
            if str(src.crs) != str(target_crs):
                raise ValueError(
                    f"The GeoTIFF CRS is {src.crs}, but the target CRS is {target_crs}. "
                    "Reprojection may be required."
                )

            # Read the data from the first band
            data = src.read(1)  # Assuming the input GeoTIFF has only a single band

            # Identify the input file's NoData value
            input_nodata = src.nodata
            if input_nodata is None:
                input_nodata = -999999.0  # Default fallback if no NoData value is defined
            nodata_value = 0
            # Replace NoData values (e.g., -999999.0) with the new NoData value
            # (e.g., 65535 for UInt16)
            data[data == input_nodata] = nodata_value

            # Scale the data to the 0–65535 range (UInt16), avoiding NoData areas
            scaled_data = np.clip(
                (data - min_height) * (65535 / (max_height - min_height)), 0, 65535
            ).astype(np.uint16)
            scaled_data[data == nodata_value] = (
                nodata_value  # Preserve NoData value in the scaled array
            )

            # Compute the proper transform to ensure consistency
            # Get the original transform, width, and height
            transform = src.transform
            width = src.width
            height = src.height
            left, bottom, right, top = src.bounds

            # Adjust the transform matrix to make sure bounds and transform align correctly
            transform = rasterio.transform.from_bounds(left, bottom, right, top, width, height)

            # Prepare metadata for the output GeoTIFF
            metadata = src.meta.copy()
            metadata.update(
                {
                    "dtype": rasterio.uint16,  # Update dtype for uint16
                    "crs": target_crs,  # Update CRS if needed
                    "nodata": nodata_value,  # Set the new NoData value
                    "transform": transform,  # Use the updated, consistent transform
                }
            )

        # Write the scaled data to the output GeoTIFF
        with rasterio.open(output_tiff, "w", **metadata) as dst:
            dst.write(scaled_data, 1)  # Write the first band

        self.logger.debug(
            "GeoTIFF successfully converted and saved to %s, with nodata value: %s.",
            output_tiff,
            nodata_value,
        )

    def generate_data(self) -> np.ndarray:
        """Generate data from the USGS 1m provider.

        Returns:
            np.ndarray: Numpy array of the data.
        """
        download_urls = self.get_download_urls()
        all_tif_files = self.download_tif_files(download_urls)
        self.merge_geotiff(all_tif_files, os.path.join(self.output_path, "merged.tif"))
        self.reproject_geotiff(
            os.path.join(self.output_path, "merged.tif"),
            os.path.join(self.output_path, "reprojected.tif"),
            "EPSG:4326",
        )
        self.convert_geotiff_to_geotiff(
            os.path.join(self.output_path, "reprojected.tif"),
            os.path.join(self.output_path, "translated.tif"),
            min_height=0,
            max_height=self.user_settings.max_local_elevation,  # type: ignore
            target_crs="EPSG:4326",
        )
        return self.extract_roi(os.path.join(self.output_path, "translated.tif"))

    def get_numpy(self) -> np.ndarray:
        """Get numpy array of the tile.

        Returns:
            np.ndarray: Numpy array of the tile.
        """
        if not self.user_settings:
            raise ValueError("user_settings is 'none'")
        if self.user_settings.max_local_elevation <= 0:  # type: ignore
            raise ValueError(
                "Entered 'max_local_elevation' value is unable to be used. "
                "Use a value greater than 0."
            )
        if not self._data:
            self._data = self.generate_data()
        return self._data
