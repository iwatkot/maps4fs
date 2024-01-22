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
    "200": "For plains",
    "400": "For hills",
    "600": "For large hills",
    "800": "For mountains",
}
SRTM = "https://elevation-tiles-prod.s3.amazonaws.com/skadi/{latitude_band}/{tile_name}.hgt.gz"
# endregion

# region settings
DemSettings = namedtuple("DemSettings", ["blur_seed", "max_height"])
# endregion


class Map:
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
        self._prepare_dirs(name)
        self._set_map_size()
        self._prepare_weights()

        self.logger.log(f"Fetching map data for coordinates: {coordinates}...")
        self.bbox = ox.utils_geo.bbox_from_point(self.coordinates, dist=self.distance)
        self._read_parameters()
        self._locate_map()
        self.draw()
        self.save_dem()

    def _prepare_dirs(self, name: str | None) -> None:
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
        tree = ET.parse(self.map_xml_path)
        self.logger.log(f"Map XML file loaded from: {self.map_xml_path}.")
        root = tree.getroot()
        for map_elem in root.iter("map"):
            map_elem.set("width", str(self.distance * 2))
            map_elem.set("height", str(self.distance * 2))
        tree.write(self.map_xml_path)
        self.logger.log(f"Map XML file saved to: {self.map_xml_path}.")

    def _prepare_weights(self):
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
        def __init__(self, name: str, tags: dict[str, str | list[str]], width: int = None):
            self.name = name
            self.tags = tags
            self.width = width
            self._get_paths()
            self._check_shapes()

        def _get_paths(self):
            if self.name == "waterPuddle":
                self.paths = [os.path.join(weights_dir, "waterPuddle_weight.png")]
                return
            pattern = re.compile(rf"{self.name}\d{{2}}_weight")
            paths = [path for path in weight_files if pattern.search(path)]
            if not paths:
                raise FileNotFoundError(f"Texture not found: {self.name}")
            self.paths = paths

        def _check_shapes(self):
            unique_shapes = set()
            for path in self.paths:
                img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
                unique_shapes.add(img.shape)
            if len(unique_shapes) > 1:
                raise ValueError(f"Texture {self.name} has multiple shapes: {unique_shapes}")

        @property
        def path(self):
            return self.paths[0]

    @property
    def layers(self):
        asphalt = self.Layer("asphalt", {"highway": ["motorway", "trunk", "primary"]}, width=8)
        concrete = self.Layer("concrete", {"building": True})
        dirtDark = self.Layer(
            "dirtDark", {"highway": ["unclassified", "residential", "track"]}, width=2
        )
        grassDirt = self.Layer("grassDirt", {"natural": ["wood", "tree_row"]}, width=2)
        grass = self.Layer("grass", {"natural": "grassland"})
        forestGround = self.Layer("forestGround", {"landuse": "farmland"})
        gravel = self.Layer("gravel", {"highway": ["secondary", "tertiary", "road"]}, width=4)
        waterPuddle = self.Layer("waterPuddle", {"natural": "water", "waterway": True}, width=10)
        return [asphalt, concrete, dirtDark, forestGround, grass, grassDirt, gravel, waterPuddle]

    def _read_parameters(self):
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

    def _locate_map(self):
        self.easting = self.minimum_x < 500000
        self.northing = self.minimum_y < 10000000
        self.logger.log(f"Map is in {'east' if self.easting else 'west'} of central meridian.")
        self.logger.log(f"Map is in {'north' if self.northing else 'south'} hemisphere.")

    def get_relative_x(self, x: float) -> int:
        if self.easting:
            raw_x = x - self.minimum_x
        else:
            raw_x = self.minimum_x - x
        return int(raw_x * self.height_coef)

    def get_relative_y(self, y: float) -> int:
        if self.northing:
            raw_y = y - self.minimum_y
        else:
            raw_y = self.minimum_y - y
        return self.height - int(raw_y * self.width_coef)

    def _to_np(self, geometry: shapely.geometry.polygon.Polygon, *args) -> np.ndarray:
        xs, ys = geometry.exterior.coords.xy
        xs = [int(self.get_relative_x(x)) for x in xs.tolist()]
        ys = [int(self.get_relative_y(y)) for y in ys.tolist()]
        pairs = list(zip(xs, ys))
        return np.array(pairs, dtype=np.int32).reshape((-1, 1, 2))

    def _to_polygon(self, obj: pd.core.series.Series, width: int | None) -> np.ndarray | None:
        geometry = obj["geometry"]
        geometry_type = geometry.geom_type
        converter = self._converters(geometry_type)
        if not converter:
            self.logger.log(f"Geometry type {geometry_type} not supported.")
            return
        return converter(geometry, width)

    def _linestring(self, geometry: shapely.geometry.linestring.LineString, width: int | None):
        polygon = geometry.buffer(width)
        return self._to_np(polygon)

    def _converters(self, geom_type: str) -> Callable[[shapely.geometry, int | None], np.ndarray]:
        converters = {"Polygon": self._to_np, "LineString": self._linestring}
        return converters.get(geom_type)

    def polygons(
        self, tags: dict[str, str | list[str]], width: int | None
    ) -> Generator[np.ndarray, None, None]:
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
        for layer in self.layers:
            img = cv2.imread(layer.path, cv2.IMREAD_UNCHANGED)
            for polygon in self.polygons(layer.tags, layer.width):
                cv2.fillPoly(img, [polygon], color=255)
            cv2.imwrite(layer.path, img)
            self.logger.log(f"Texture {layer.path} saved.")

    # def pack_mod(self) -> None:
    #     shutil.make_archive(MOD_SAVE_PATH, "zip", OUTPUT_DIR)
    #     self.logger.log(f"Archive created: {MOD_SAVE_PATH}.")
    #     return MOD_SAVE_PATH

    def _tile_info(self, lat: float, lon: float) -> tuple[str, str]:
        latitude_band = f"N{int(lat):02d}"
        tile_name = f"N{int(lat):02d}E{int(lon):03d}"
        return latitude_band, tile_name

    def _download_tile(self) -> str:
        latitude_band, tile_name = self._tile_info(*self.coordinates)
        self.logger.log(f"Downloading tile {tile_name} from latitude band {latitude_band}...")

        compressed_save_path = os.path.join(self.gz_dir, f"{tile_name}.hgt.gz")
        if os.path.isfile(compressed_save_path):
            self.logger.log(
                f"Compressed tile already exists: {compressed_save_path}, skipping download."
            )
        else:
            self.logger.log(f"Compressed tile {tile_name} does not exist, downloading...")
            url = SRTM.format(latitude_band=latitude_band, tile_name=tile_name)
            self.logger.log(f"Trying to get response from {url}...")
            self.logger.log("Compressed tile does not exist, downloading...")
            response = requests.get(url, stream=True)

            if response.status_code == 200:
                self.logger.log(f"Response received. Saving to {compressed_save_path}...")
                with open(compressed_save_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                self.logger.log("Compressed tile successfully downloaded.")
            else:
                self.logger.log(f"Response was failed with status code {response.status_code}.")
                return

        decompressed_file_path = os.path.join(self.hgt_dir, f"{tile_name}.hgt")
        with gzip.open(compressed_save_path, "rb") as f_in:
            with open(decompressed_file_path, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)
        self.logger.log(f"Tile decompressed to {decompressed_file_path}.")
        return decompressed_file_path

    def save_dem(self):
        north, south, east, west = ox.utils_geo.bbox_from_point(
            self.coordinates, dist=self.distance
        )
        max_y, min_y = max(north, south), min(north, south)
        max_x, min_x = max(east, west), min(east, west)

        tile_path = self._download_tile()
        with rasterio.open(tile_path) as src:
            window = rasterio.windows.from_bounds(min_x, min_y, max_x, max_y, src.transform)
            data = src.read(1, window=window)
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
        dem_output_resolution = (self.distance + 1, self.distance + 1)
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
