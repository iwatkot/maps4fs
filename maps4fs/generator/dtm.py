"""This module contains the DTMProvider class and its subclasses. DTMProvider class is used to
define different providers of digital terrain models (DTM) data. Each provider has its own URL
and specific settings for downloading and processing the data."""

from __future__ import annotations

import gzip
import math
import os
import shutil
from typing import Type

from PIL import Image
import numpy as np
import osmnx as ox  # type: ignore
import rasterio  # type: ignore
import requests
from rasterio._warp import Resampling
from rasterio.merge import merge
from rasterio.warp import calculate_default_transform, reproject
from rasterio.windows import from_bounds
from rasterio.enums import Resampling as enumsResampling

from maps4fs.logger import Logger
from datetime import datetime


class DTMProvider:
    """Base class for DTM providers."""

    _code: str | None = None
    _name: str | None = None
    _region: str | None = None
    _icon: str | None = None
    _resolution: float | None = None

    _url: str | None = None

    def __init__(self, coordinates: tuple[float, float], size: int, directory: str, logger: Logger):
        self._coordinates = coordinates
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

class USGS1mProvider(DTMProvider):
    """Provider of USGS."""

    _code = "USGS1m"
    _name = "USGS 1m"
    _region = "USA"
    _icon = ""
    _resolution = 1
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_path = os.path.join("USGS_temp", f"timestamp_{timestamp}")

    url = f"https://tnmaccess.nationalmap.gov/api/v1/products?prodFormats=GeoTIFF,IMG&prodExtents=10000 x 10000 meter&datasets=Digital Elevation Model (DEM) 1 meter&polygon="

    def getDownloadUrls(self) -> list[str]:
        urls = []
        try:
            # Make the GET request
            (west, south, east, north) = self.get_bbox()
            response = requests.get(self.url + f"{west} {south},{east} {south},{east} {north},{west} {north},{west} {south}&=")

            # Check if the request was successful (HTTP status code 200)
            if response.status_code == 200:
                # Parse the JSON response
                json_data = response.json()
                items = json_data['items']
                for item in items:
                    urls.append(item['downloadURL'])
                self.downloadTifFiles(urls)
            else:
                print(f"Failed to get data. HTTP Status Code: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print("An error occurred:", e)
        return urls

    def downloadTifFiles(self, urls) -> list[str]:
        tif_files = []
        for url in urls:
            file_name = os.path.basename(url)
            file_path = os.path.join(self.output_path, file_name)
            if not os.path.exists(file_path):
                print(f"Downloading file: {file_name}")
                try:
                    # Send a GET request to the file URL
                    response = requests.get(url, stream=True)
                    response.raise_for_status()  # Raise an error for HTTP status codes 4xx/5xx

                    # Write the content of the response to the file
                    with open(file_path, "wb") as file:
                        for chunk in response.iter_content(chunk_size=8192):  # Download in chunks
                            file.write(chunk)
                    print(f"File downloaded successfully: {file_path}")
                except requests.exceptions.RequestException as e:
                    print(f"Failed to download file: {e}")
            else:
                print(f"File already exists: {file_name}")

            tif_files.append(file_path)
        return tif_files

    def merge_geotiff(self, input_files, output_file):
        # Open all input GeoTIFF files as datasets
        datasets = [rasterio.open(file) for file in input_files]

        # Merge datasets
        mosaic, out_transform = merge(datasets)

        # Get metadata from the first file and update it for the output
        out_meta = datasets[0].meta.copy()
        out_meta.update({
            "driver": "GTiff",
            "height": mosaic.shape[1],
            "width": mosaic.shape[2],
            "transform": out_transform,
            "count": mosaic.shape[0]  # Number of bands
        })

        # Write merged GeoTIFF to the output file
        with rasterio.open(output_file, "w", **out_meta) as dest:
            dest.write(mosaic)

        print(f"GeoTIFF images merged successfully into {output_file}")

    def reproject_geotiff(input_tiff, output_tiff, target_crs):
        # Open the source GeoTIFF
        with rasterio.open(input_tiff) as src:
            # Get the transform, width, and height of the target CRS
            transform, width, height = calculate_default_transform(
                src.crs,
                target_crs,
                src.width,
                src.height,
                *src.bounds
            )

            # Update the metadata for the target GeoTIFF
            kwargs = src.meta.copy()
            kwargs.update({
                'crs': target_crs,
                'transform': transform,
                'width': width,
                'height': height
            })

            # Open the destination GeoTIFF file and reproject
            with rasterio.open(output_tiff, 'w', **kwargs) as dst:
                for i in range(1, src.count + 1):  # Iterate over all raster bands
                    reproject(
                        source=rasterio.band(src, i),
                        destination=rasterio.band(dst, i),
                        src_transform=src.transform,
                        src_crs=src.crs,
                        dst_transform=transform,
                        dst_crs=target_crs,
                        resampling=Resampling.nearest  # Choose resampling method
                    )
        print(f"Reprojected GeoTIFF saved to {output_tiff}")

    def crop_geotiff(self, input_tiff, output_tiff, bounds, target_crs):
        """
        Crop a GeoTIFF based on given geographic bounding box and save to a new file.

        :param input_tiff: Path to the input GeoTIFF file.
        :param output_tiff: Path to save the cropped GeoTIFF file.
        :param bounds: Bounding box as (west, south, east, north) in the target CRS.
        :param target_crs: Target CRS (e.g. EPSG:4326).
        """
        # Open the input GeoTIFF
        with rasterio.open(self, input_tiff) as src:
            # Ensure the source CRS matches the target CRS
            if str(src.crs) != str(target_crs):
                raise ValueError(
                    f"The GeoTIFF CRS is {src.crs}, but the target CRS is {target_crs}. Reprojection may be required.")

            # Create a rasterio window from the bounding box
            (west, south, east, north) = self.get_bbox()
            window = from_bounds(west, south, east, north, transform=src.transform)

            # Update metadata for the cropped window
            out_meta = src.meta.copy()
            out_meta.update({
                "height": int(window.height),
                "width": int(window.width),
                "transform": src.window_transform(window)  # Update the transform for the cropped region
            })

            # Read the cropped window and write to the output file
            with rasterio.open(output_tiff, "w", **out_meta) as dst:
                for i in range(1, src.count + 1):  # Iterate through all the bands
                    dst.write(src.read(i, window=window), indexes=i)

        print(f"Cropped GeoTIFF saved to {output_tiff}")

    def convert_geotiff_to_png(self, input_tiff, output_png, min_height, max_height, target_crs, outsize):
        """
        Convert a GeoTIFF to a scaled PNG with UInt16 values using a specific coordinate system and output size.

        :param input_tiff: Path to the input GeoTIFF file.
        :param output_png: Path to save the output PNG file.
        :param min_height: Minimum terrain height (input range).
        :param max_height: Maximum terrain height (input range).
        :param target_crs: Target CRS (e.g., EPSG:4326 for CRS:84).
        :param outsize: Tuple for output image size (width, height).
        """
        # Open the input GeoTIFF file
        with rasterio.open(input_tiff) as src:
            # Ensure the input CRS is the desired one (or convert)
            if str(src.crs) != str(target_crs):
                raise ValueError(
                    f"The GeoTIFF CRS is {src.crs}, but the target CRS is {target_crs}. Reprojection may be required.")

            # Read the data resampled to the desired output size (mapSize + 1 x mapSize + 1)
            data = src.read(
                1,  # Read only the first band
                out_shape=(outsize[1], outsize[0]),  # Resize (height, width)
                resampling=enumsResampling.bilinear  # Use bilinear resampling for smoother resizing
            )

            # Scale the data to the 0–65535 range (UInt16)
            scaled_data = np.clip((data - min_height) * (65535 / (max_height - min_height)), 0, 65535).astype(np.uint16)

        # Save the scaled data as a PNG (UInt16)
        Image.fromarray(scaled_data).save(output_png, format="PNG")
        print(f"GeoTIFF successfully converted and saved to {output_png}")

    def get_numpy(self) -> np.ndarray:
        (west, south, east, north) = self.get_bbox()
        download_urls = self.getDownloadUrls()
        all_tif_files = self.downloadTifFiles(download_urls)
        self.merge_geotiff(all_tif_files, os.path.join(self.output_path, "merged.tif"))
        return self.extract_roi(os.path.join(self.output_path, "merged.tif"))
        #self.reproject_geotiff(os.path.join(self.output_path, "merged.tif"), os.path.join(self.output_path, "reprojected.tif"),
        #                  "EPSG:4326")
        #self.crop_geotiff(os.path.join(self.output_path, "reprojected.tif"), os.path.join(self.output_path, "cropped.tif"),
        #             (west, south, east, north), "EPSG:4326")
        #self.convert_geotiff_to_png(
        #    os.path.join(self.output_path, "cropped.tif"),
        #    os.path.join(self.output_path, "dem.png"),
        #    min_height=0,
        #    max_height=200,
        #    target_crs="EPSG:4326",
        #    outsize=(mapSize + 1, mapSize + 1)
        #)

