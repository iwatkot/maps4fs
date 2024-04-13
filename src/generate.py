import gzip
import json
import os
import re
import shutil
import warnings
import xml.etree.ElementTree as ET
from collections import namedtuple
from typing import Any, Callable, Generator

import cv2
import numpy as np
import osmnx as ox
import pandas as pd
import rasterio
import requests
import shapely

# region constants
MAP_SIZES = ["2048", "4096", "8192", "16384"]
MAX_HEIGHTS = {
    "100": "🍀 For flatlands",
    "200": "🍀 For plains",
    "400": "🗻 For hills",
    "600": "⛰️ For large hills",
    "800": "🏔️ For mountains",
}
SRTM = "https://elevation-tiles-prod.s3.amazonaws.com/skadi/{latitude_band}/{tile_name}.hgt.gz"
# endregion

# region settings
DemSettings = namedtuple("DemSettings", ["blur_seed", "max_height"])
# endregion


class Map:
    """Class which represents a map instance. It's using to generate map from coordinates.
    It's using OSM data to generate textures and SRTM data to generate DEM.

    Args:
        working_directory (str): Path to working directory.
        coordinates (tuple[float, float]): Coordinates of the map center.
        distance (int): Distance from the map center to the map edge.
        dem_settings (DemSettings): Settings for DEM generation.
        logger (Any): Logger instance.
        name (str, optional): Name of the map instance. Defaults to None. Used for multiple instances.

    Attributes:
        working_directory (str): Path to working directory.
        coordinates (tuple[float, float]): Coordinates of the map center.
        distance (int): Distance from the map center to the map edge.
        dem_settings (DemSettings): Settings for DEM generation.
        logger (Any): Logger instance.
        bbox (tuple[float, float, float, float]): Bounding box of the map.
        minimum_x (float): Minimum X coordinate of the map in UTM format.
        minimum_y (float): Minimum Y coordinate of the map in UTM format.
        maximum_x (float): Maximum X coordinate of the map in UTM format.
        maximum_y (float): Maximum Y coordinate of the map in UTM format.
        height (float): Height of the map in meters.
        width (float): Width of the map in meters.
        height_coef (float): Height coefficient (meters per pixel).
        width_coef (float): Width coefficient (meters per pixel).
        easting (bool): True if map is in east hemisphere, False otherwise.
        northing (bool): True if map is in north hemisphere, False otherwise.
        output_dir (str): Path to output directory.
        gz_dir (str): Path to gz directory.
        hgt_dir (str): Path to hgt directory.
        data_dir (str): Path to data directory.
        weights_dir (str): Path to weights directory.
        map_xml_path (str): Path to map.xml file.
        map_dem_path (str): Path to map_dem.png file.
        layers (list[Layer]): List of layers with textures and tags from textures.json.
    """

    def __init__(
        self,
        working_directory: str,
        coordinates: tuple[float, float],
        distance: int,
        dem_settings: DemSettings,
        logger: Any,
        name: str = None,
    ):
        self.working_directory = working_directory
        self.coordinates = coordinates
        self.distance = distance
        self.dem_settings = dem_settings
        self.logger = logger
        self.name = name
        self._prepare_dirs(name)
        self._set_map_size()
        self._prepare_weights()

        self.logger.log(f"Fetching map data for coordinates: {coordinates}...")
        self.bbox = ox.utils_geo.bbox_from_point(self.coordinates, dist=self.distance)
        self._read_parameters()
        self._locate_map()
        self.draw()
        self.dem()

    def _prepare_dirs(self, name: str | None) -> None:
        """Defines directories for map generation and creates some of them.
        Unpacks template archive to output directory.
        Following directories are used by the instance:
            - output (where template will be unpacked and weights edited)
            - output/{name} (if name is provided for multiple instances)
            - temp (contains gz and hgt directories)
            - temp/gz (where SRTM files will be downloaded)
            - temp/hgt (where SRTM files will be extracted)
            - data (contains map-template.zip)
        """
        self.working_directory = os.getcwd()
        self.logger.log(f"Working directory: {self.working_directory}")

        self.output_dir = os.path.join(self.working_directory, "output")
        if name:
            self.output_dir = os.path.join(self.output_dir, name)
        os.makedirs(self.output_dir, exist_ok=True)
        self.logger.log(f"Output directory created: {self.output_dir}")

        tmp_dir = os.path.join(self.working_directory, "temp")
        self.gz_dir = os.path.join(tmp_dir, "gz")
        self.hgt_dir = os.path.join(tmp_dir, "hgt")
        os.makedirs(self.gz_dir, exist_ok=True)
        os.makedirs(self.hgt_dir, exist_ok=True)
        self.logger.log(f"Temporary directories created: {self.gz_dir}, {self.hgt_dir}")

        self.data_dir = os.path.join(self.working_directory, "data")
        template_archive = os.path.join(self.data_dir, "map-template.zip")
        shutil.unpack_archive(template_archive, self.output_dir)
        self.logger.log(f"Template archive unpacked to {self.output_dir}")

        global weights_dir
        weights_dir = os.path.join(self.output_dir, "maps", "map", "data")
        self.weights_dir = weights_dir
        self.logger.log(f"Weights directory: {self.weights_dir}")
        self.map_xml_path = os.path.join(self.output_dir, "maps", "map", "map.xml")
        self.map_dem_path = os.path.join(self.weights_dir, "map_dem.png")
        self.logger.log(f"Map XML file: {self.map_xml_path}, DEM file: {self.map_dem_path}")

    def _set_map_size(self):
        """Edits map.xml file to set correct map size."""
        tree = ET.parse(self.map_xml_path)
        self.logger.log(f"Map XML file loaded from: {self.map_xml_path}.")
        root = tree.getroot()
        for map_elem in root.iter("map"):
            map_elem.set("width", str(self.distance * 2))
            map_elem.set("height", str(self.distance * 2))
        tree.write(self.map_xml_path)
        self.logger.log(f"Map XML file saved to: {self.map_xml_path}.")

    def _prepare_weights(self):
        """Prepares weights for textures from textures.json."""
        textures_path = os.path.join(self.working_directory, "textures.json")
        textures = json.load(open(textures_path, "r"))
        self.logger.log(f"Loaded {len(textures)} textures from {textures_path}.")
        for texture_name, layer_numbers in textures.items():
            self._generate_weights(texture_name, layer_numbers)
        self.logger.log(f"Generated weights for {len(textures)} textures.")

        global weight_files
        weight_files = [
            os.path.join(self.weights_dir, f)
            for f in os.listdir(self.weights_dir)
            if f.endswith("_weight.png")
        ]
        self.logger.log(f"Fetched {len(weight_files)} weight files.")

    def _generate_weights(self, texture_name: str, layer_numbers: int) -> None:
        """Generates weight files for textures. Each file is a numpy array of zeros and dtype uint8 (0-255).

        Args:
            texture_name (str): Name of the texture.
            layer_numbers (int): Number of layers in the texture.
        """
        size = self.distance * 2
        postfix = "_weight.png"
        if layer_numbers == 0:
            filepaths = [os.path.join(self.weights_dir, texture_name + postfix)]
        else:
            filepaths = [
                os.path.join(self.weights_dir, texture_name + str(i).zfill(2) + postfix)
                for i in range(1, layer_numbers + 1)
            ]

        for filepath in filepaths:
            img = np.zeros((size, size), dtype=np.uint8)
            cv2.imwrite(filepath, img)

    class Layer:
        """Class which represents a layer with textures and tags from textures.json.
        It's using to obtain data from OSM using tags and make changes into corresponding textures.

        Args:
            name (str): Name of the layer.
            tags (dict[str, str | list[str]]): Dictionary of tags to search for.
            width (int | None): Width of the polygon in meters (only for LineString).
            color (tuple[int, int, int]): Color of the layer in BGR format.

        Attributes:
            name (str): Name of the layer.
            tags (dict[str, str | list[str]]): Dictionary of tags to search for.
            width (int | None): Width of the polygon in meters (only for LineString).
            paths (list[str]): List of paths to textures of the layer.
            path (str): Path to the first texture of the layer.
        """

        def __init__(
            self,
            name: str,
            tags: dict[str, str | list[str]],
            width: int = None,
            color: tuple[int, int, int] = None,
        ):
            self.name = name
            self.tags = tags
            self.width = width
            self.color = color if color else (255, 255, 255)
            self._get_paths()
            self._check_shapes()

        def _get_paths(self):
            """Gets paths to textures of the layer.

            Raises:
                FileNotFoundError: If texture is not found.
            """
            if self.name == "waterPuddle":
                self.paths = [os.path.join(weights_dir, "waterPuddle_weight.png")]
                return
            pattern = re.compile(rf"{self.name}\d{{2}}_weight")
            paths = [path for path in weight_files if pattern.search(path)]
            if not paths:
                raise FileNotFoundError(f"Texture not found: {self.name}")
            self.paths = paths

        def _check_shapes(self) -> None:
            """Checks if all textures of the layer have the same shape.

            Raises:
                ValueError: If textures have different shapes.
            """
            unique_shapes = set()
            for path in self.paths:
                img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
                unique_shapes.add(img.shape)
            if len(unique_shapes) > 1:
                raise ValueError(f"Texture {self.name} has multiple shapes: {unique_shapes}")

        @property
        def path(self) -> str:
            """Returns path to the first texture of the layer.

            Returns:
                str: Path to the texture.
            """
            return self.paths[0]

    @property
    def layers(self) -> list[Layer]:
        """Returns list of layers with textures and tags from textures.json.

        Returns:
            list[Layer]: List of layers.
        """
        asphalt = self.Layer(
            "asphalt", {"highway": ["motorway", "trunk", "primary"]}, width=8, color=(70, 70, 70)
        )
        concrete = self.Layer("concrete", {"building": True}, width=8, color=(130, 130, 130))
        dirtDark = self.Layer(
            "dirtDark",
            {"highway": ["unclassified", "residential", "track"]},
            width=2,
            color=(33, 67, 101),
        )
        grassDirt = self.Layer(
            "grassDirt", {"natural": ["wood", "tree_row"]}, width=2, color=(0, 252, 124)
        )
        grass = self.Layer("grass", {"natural": "grassland"}, color=(34, 255, 34))
        forestGround = self.Layer("forestGround", {"landuse": "farmland"}, color=(47, 107, 85))
        gravel = self.Layer(
            "gravel", {"highway": ["secondary", "tertiary", "road"]}, width=4, color=(140, 180, 210)
        )
        waterPuddle = self.Layer(
            "waterPuddle", {"natural": "water", "waterway": True}, width=10, color=(255, 20, 20)
        )
        return [asphalt, concrete, dirtDark, forestGround, grass, grassDirt, gravel, waterPuddle]

    def _read_parameters(self) -> None:
        """Reads map parameters from OSM data, such as:
        - minimum and maximum coordinates in UTM format
        - map dimensions in meters
        - map coefficients (meters per pixel)
        """
        north, south, east, west = ox.utils_geo.bbox_from_point(
            self.coordinates, dist=self.distance, project_utm=True
        )
        # Parameters of the map in UTM format (meters).
        self.minimum_x = min(west, east)
        self.minimum_y = min(south, north)
        self.maximum_x = max(west, east)
        self.maximum_y = max(south, north)
        self.logger.log(f"Map minimum coordinates (XxY): {self.minimum_x} x {self.minimum_y}.")
        self.logger.log(f"Map maximum coordinates (XxY): {self.maximum_x} x {self.maximum_y}.")

        self.height = abs(north - south)
        self.width = abs(east - west)
        self.logger.log(f"Map dimensions (HxW): {self.height} x {self.width}.")

        self.height_coef = self.height / (self.distance * 2)
        self.width_coef = self.width / (self.distance * 2)
        self.logger.log(f"Map coefficients (HxW): {self.height_coef} x {self.width_coef}.")

    def _locate_map(self) -> None:
        """Checks if map is in east or west hemisphere and in north or south hemisphere."""
        self.easting = self.minimum_x < 500000
        self.northing = self.minimum_y < 10000000
        self.logger.log(f"Map is in {'east' if self.easting else 'west'} of central meridian.")
        self.logger.log(f"Map is in {'north' if self.northing else 'south'} hemisphere.")

    def get_relative_x(self, x: float) -> int:
        """Converts UTM X coordinate to relative X coordinate in map image.

        Args:
            x (float): UTM X coordinate.

        Returns:
            int: Relative X coordinate in map image.
        """
        if self.easting:
            raw_x = x - self.minimum_x
        else:
            raw_x = self.minimum_x - x
        return int(raw_x * self.height_coef)

    def get_relative_y(self, y: float) -> int:
        """Converts UTM Y coordinate to relative Y coordinate in map image.

        Args:
            y (float): UTM Y coordinate.

        Returns:
            int: Relative Y coordinate in map image.
        """
        if self.northing:
            raw_y = y - self.minimum_y
        else:
            raw_y = self.minimum_y - y
        return self.height - int(raw_y * self.width_coef)

    def _to_np(self, geometry: shapely.geometry.polygon.Polygon, *args) -> np.ndarray:
        """Converts Polygon geometry to numpy array of polygon points.

        Args:
            geometry (shapely.geometry.polygon.Polygon): Polygon geometry.
            *args: Additional arguments:
                - width (int | None): Width of the polygon in meters.

        Returns:
            np.ndarray: Numpy array of polygon points.
        """
        xs, ys = geometry.exterior.coords.xy
        xs = [int(self.get_relative_x(x)) for x in xs.tolist()]
        ys = [int(self.get_relative_y(y)) for y in ys.tolist()]
        pairs = list(zip(xs, ys))
        return np.array(pairs, dtype=np.int32).reshape((-1, 1, 2))

    def _to_polygon(self, obj: pd.core.series.Series, width: int | None) -> np.ndarray | None:
        """Converts OSM object to numpy array of polygon points.

        Args:
            obj (pd.core.series.Series): OSM object.
            width (int | None): Width of the polygon in meters.

        Returns:
            np.ndarray | None: Numpy array of polygon points.
        """
        geometry = obj["geometry"]
        geometry_type = geometry.geom_type
        converter = self._converters(geometry_type)
        if not converter:
            self.logger.log(f"Geometry type {geometry_type} not supported.")
            return
        return converter(geometry, width)

    def _sequence(
        self,
        geometry: shapely.geometry.linestring.LineString | shapely.geometry.point.Point,
        width: int | None,
    ) -> np.ndarray:
        """Converts LineString or Point geometry to numpy array of polygon points.

        Args:
            geometry (shapely.geometry.linestring.LineString | shapely.geometry.point.Point):
                LineString or Point geometry.
            width (int | None): Width of the polygon in meters.

        Returns:
            np.ndarray: Numpy array of polygon points.
        """
        polygon = geometry.buffer(width)
        return self._to_np(polygon)

    def _converters(self, geom_type: str) -> Callable[[shapely.geometry, int | None], np.ndarray]:
        """Returns a converter function for a given geometry type.

        Args:
            geom_type (str): Geometry type.

        Returns:
            Callable[[shapely.geometry, int | None], np.ndarray]: Converter function.
        """
        converters = {"Polygon": self._to_np, "LineString": self._sequence, "Point": self._sequence}
        return converters.get(geom_type)

    def polygons(
        self, tags: dict[str, str | list[str]], width: int | None
    ) -> Generator[np.ndarray, None, None]:
        """Generator which yields numpy arrays of polygons from OSM data.

        Args:
            tags (dict[str, str | list[str]]): Dictionary of tags to search for.
            width (int | None): Width of the polygon in meters (only for LineString).

        Yields:
            Generator[np.ndarray, None, None]: Numpy array of polygon points.
        """
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", DeprecationWarning)
                objects = ox.features_from_bbox(*self.bbox, tags=tags)
        except Exception as e:
            self.logger.log(f"Error fetching objects for tags: {tags}.")
            self.logger.log(e)
            return
        objects_utm = ox.project_gdf(objects, to_latlong=False)
        self.logger.log(f"Fetched {len(objects_utm)} elements for tags: {tags}.")

        for index, obj in objects_utm.iterrows():
            polygon = self._to_polygon(obj, width)
            if polygon is None:
                continue
            yield polygon

    def draw(self) -> None:
        """Iterates over layers and fills them with polygons from OSM data."""
        for layer in self.layers:
            img = cv2.imread(layer.path, cv2.IMREAD_UNCHANGED)
            for polygon in self.polygons(layer.tags, layer.width):
                cv2.fillPoly(img, [polygon], color=255)
            cv2.imwrite(layer.path, img)
            self.logger.log(f"Texture {layer.path} saved.")

    def _tile_info(self, lat: float, lon: float) -> tuple[str, str]:
        """Returns latitude band and tile name for SRTM tile from coordinates.

        Args:
            lat (float): Latitude.
            lon (float): Longitude.

        Returns:
            tuple[str, str]: Latitude band and tile name.
        """
        latitude_band = f"N{int(lat):02d}"
        if lon < 0:
            tile_name = f"N{int(lat):02d}W{int(abs(lon)):03d}"
        else:
            tile_name = f"N{int(lat):02d}E{int(lon):03d}"
        return latitude_band, tile_name

    def _download_tile(self) -> str | None:
        """Downloads SRTM tile from Amazon S3 using coordinates.

        Returns:
            str: Path to compressed tile or None if download failed.
        """
        latitude_band, tile_name = self._tile_info(*self.coordinates)
        compressed_file_path = os.path.join(self.gz_dir, f"{tile_name}.hgt.gz")
        url = SRTM.format(latitude_band=latitude_band, tile_name=tile_name)
        self.logger.log(f"Trying to get response from {url}...")
        response = requests.get(url, stream=True)

        if response.status_code == 200:
            self.logger.log(f"Response received. Saving to {compressed_file_path}...")
            with open(compressed_file_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            self.logger.log("Compressed tile successfully downloaded.")
        else:
            self.logger.log(f"Response was failed with status code {response.status_code}.")
            return

        return compressed_file_path

    def _srtm_tile(self) -> str | None:
        """Determines SRTM tile name from coordinates downloads it if necessary, and decompresses it.

        Returns:
            str: Path to decompressed tile or None if download failed.
        """
        latitude_band, tile_name = self._tile_info(*self.coordinates)
        self.logger.log(f"SRTM tile name {tile_name} from latitude band {latitude_band}.")

        decompressed_file_path = os.path.join(self.hgt_dir, f"{tile_name}.hgt")
        if os.path.isfile(decompressed_file_path):
            self.logger.log(
                f"Decompressed tile already exists: {decompressed_file_path}, skipping download."
            )
            return decompressed_file_path

        compressed_file_path = self._download_tile()
        if not compressed_file_path:
            self.logger.log("Download from SRTM failed, DEM file will be filled with zeros.")
            return
        with gzip.open(compressed_file_path, "rb") as f_in:
            with open(decompressed_file_path, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)
        self.logger.log(f"Tile decompressed to {decompressed_file_path}.")
        return decompressed_file_path

    def dem(self) -> None:
        """Reads SRTM file, crops it to map size, normalizes and blurs it, saves to map directory."""
        north, south, east, west = ox.utils_geo.bbox_from_point(
            self.coordinates, dist=self.distance
        )
        max_y, min_y = max(north, south), min(north, south)
        max_x, min_x = max(east, west), min(east, west)

        dem_output_resolution = (self.distance + 1, self.distance + 1)

        tile_path = self._srtm_tile()
        if not tile_path:
            self.logger.log("Tile was not downloaded, DEM file will be filled with zeros.")
            self._save_empty_dem(dem_output_resolution)
            return

        with rasterio.open(tile_path) as src:
            self.logger.log(f"Opened tile, shape: {src.shape}, dtype: {src.dtypes[0]}.")
            window = rasterio.windows.from_bounds(min_x, min_y, max_x, max_y, src.transform)
            self.logger.log(
                f"Window parameters. Column offset: {window.col_off}, row offset: {window.row_off}, "
                f"width: {window.width}, height: {window.height}."
            )
            data = src.read(1, window=window)

        if not data.size > 0:
            self.logger.log("DEM data is empty, DEM file will be filled with zeros.")
            self._save_empty_dem(dem_output_resolution)
            return

        self.logger.log(
            f"DEM data was read from SRTM file. Shape: {data.shape}, dtype: {data.dtype}. "
            f"Min: {data.min()}, max: {data.max()}."
        )

        normalized_data = self._normalize_dem(data)

        resampled_data = cv2.resize(
            normalized_data, dem_output_resolution, interpolation=cv2.INTER_LINEAR
        )
        self.logger.log(
            f"DEM data was resampled. Shape: {resampled_data.shape}, dtype: {resampled_data.dtype}. "
            f"Min: {resampled_data.min()}, max: {resampled_data.max()}."
        )

        blur_seed = self.dem_settings.blur_seed
        blurred_data = cv2.GaussianBlur(resampled_data, (blur_seed, blur_seed), 0)
        cv2.imwrite(self.map_dem_path, blurred_data)
        self.logger.log(f"DEM data was blurred and saved to {self.map_dem_path}.")

    def _save_empty_dem(self, dem_output_resolution: tuple[int, int]) -> None:
        """Saves empty DEM file filled with zeros."""
        dem_data = np.zeros(dem_output_resolution, dtype="uint16")
        cv2.imwrite(self.map_dem_path, dem_data)
        self.logger.log(f"DEM data filled with zeros and saved to {self.map_dem_path}.")

    def _normalize_dem(self, data: np.ndarray) -> np.ndarray:
        """Normalize DEM data to 16-bit unsigned integer using max height from settings.

        Args:
            data (np.ndarray): DEM data from SRTM file after cropping.

        Returns:
            np.ndarray: Normalized DEM data.
        """
        max_dev = data.max() - data.min()
        max_height = self.dem_settings.max_height
        scaling_factor = max_dev / max_height if max_dev < max_height else 1
        adjusted_max_height = int(65535 * scaling_factor)
        self.logger.log(
            f"Maximum deviation: {max_dev}. Scaling factor: {scaling_factor}. "
            f"Adjusted max height: {adjusted_max_height}."
        )
        normalized_data = (
            (data - data.min()) / (data.max() - data.min()) * adjusted_max_height
        ).astype("uint16")
        self.logger.log(
            f"DEM data was normalized to {normalized_data.min()} - {normalized_data.max()}."
        )
        return normalized_data

    def pack(self) -> str:
        """Packs map directory to zip archive.

        Returns:
            str: Path to the archive.
        """
        archives_dir = os.path.join(self.working_directory, "archives")
        os.makedirs(archives_dir, exist_ok=True)
        archive_name = self.name if self.name else "map"
        archive_name += ".zip"
        archive_path = os.path.join(archives_dir, archive_name)
        self.logger.log(f"Packing map to {archive_path}...")
        shutil.make_archive(archive_path[:-4], "zip", self.output_dir)
        self.logger.log(f"Map packed to {archive_path}.")
        return archive_path

    def preview(self) -> str:
        """Merges layers into one image and saves it to previews directory.

        Returns:
            str: Path to the preview.
        """
        preview_size = (2048, 2048)
        images = [
            cv2.resize(cv2.imread(layer.path, cv2.IMREAD_UNCHANGED), preview_size)
            for layer in self.layers
        ]
        colors = [layer.color for layer in self.layers]
        color_images = []
        for img, color in zip(images, colors):
            color_img = np.zeros((img.shape[0], img.shape[1], 3), dtype=np.uint8)
            color_img[img > 0] = color
            color_images.append(color_img)
        merged = np.sum(color_images, axis=0, dtype=np.uint8)
        self.logger.log(
            f"Merged layers into one image. Shape: {merged.shape}, dtype: {merged.dtype}."
        )
        previews_dir = os.path.join(self.working_directory, "previews")
        os.makedirs(previews_dir, exist_ok=True)
        preview_name = self.name if self.name else "preview"
        preview_name += ".png"
        preview_path = os.path.join(previews_dir, preview_name)
        cv2.imwrite(preview_path, merged)
        self.logger.log(f"Preview saved to {preview_path}.")
        return preview_path
