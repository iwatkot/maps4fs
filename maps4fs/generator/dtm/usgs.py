"""This module contains provider of USGS data."""

import os
from datetime import datetime
from zipfile import ZipFile

import numpy as np
import rasterio
import requests
from rasterio.enums import Resampling
from rasterio.merge import merge
from rasterio.warp import calculate_default_transform, reproject
from rasterio.windows import from_bounds

from maps4fs.generator.dtm.dtm import DTMProvider, DTMProviderSettings


class USGSProviderSettings(DTMProviderSettings):
    """Settings for the USGS provider."""

    max_local_elevation: int = 255
    dataset: tuple | str = (
        'Digital Elevation Model (DEM) 1 meter',
        'Alaska IFSAR 5 meter DEM',
        'National Elevation Dataset (NED) 1/9 arc-second',
        'National Elevation Dataset (NED) 1/3 arc-second',
        'National Elevation Dataset (NED) 1 arc-second',
        'National Elevation Dataset (NED) Alaska 2 arc-second',
        'Original Product Resolution (OPR) Digital Elevation Model (DEM)',
    )


class USGSProvider(DTMProvider):
    """Provider of USGS."""

    _code = "USGS"
    _name = "USGS"
    _region = "USA"
    _icon = "🇺🇸"
    _resolution = 'variable'
    _data: np.ndarray | None = None
    _settings = USGSProviderSettings
    _author = "[ZenJakey](https://github.com/ZenJakey)"
    _contributors = "[kbrandwijk](https://github.com/kbrandwijk)"
    _is_community = True
    _instructions = (
        "ℹ️ Set the max local elevation to approx the local max elevation for your area in"
        " meters. This will allow you to use heightScale 255 in GE with minimal tweaking."
        " Setting this value too low can cause a flat map!"
    )

    _url = (
        "https://tnmaccess.nationalmap.gov/api/v1/products?prodFormats=GeoTIFF,IMG"

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
                + f"&datasets={self.user_settings.dataset}"  # type: ignore
                + f"&bbox={west},{north},{east},{south}"
            )
            self.logger.debug("Getting file locations from USGS...")

            # Check if the request was successful (HTTP status code 200)
            if response.status_code == 200:
                # Parse the JSON response
                json_data = response.json()
                items = json_data["items"]
                for item in items:
                    urls.append(item["downloadURL"])
                # self.download_tif_files(urls)
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
                    if file_name.endswith('.zip'):
                        with ZipFile(file_path, "r") as f_in:
                            f_in.extract(file_name.replace('.zip', '.img'), self.shared_tiff_path)
                        tif_files.append(file_path.replace('.zip', '.img'))
                    else:
                        tif_files.append(file_path)
                except requests.exceptions.RequestException as e:
                    self.logger.error("Failed to download file: %s", e)
            else:
                self.logger.debug("File already exists: %s", file_name)
                if file_name.endswith('.zip'):
                    if not os.path.exists(file_path.replace('.zip', '.img')):
                        with ZipFile(file_path, "r") as f_in:
                            f_in.extract(file_name.replace('.zip', '.img'), self.shared_tiff_path)
                    tif_files.append(file_path.replace('.zip', '.img'))
                else:
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
