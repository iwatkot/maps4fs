import os
import re
import shutil
from typing import Callable, Generator

import cv2
import numpy as np
import osmnx as ox
import pandas as pd
import shapely
from rich.console import Console

console = Console()
WORKING_DIR = os.getcwd()
console.log(f"Working directory: {WORKING_DIR}")
MOD_SAVE_PATH = os.path.join(WORKING_DIR, "FS22_MapTemplate")

DATA_DIR = os.path.join(WORKING_DIR, "data")
TEMPLATE_ARCHIVE = os.path.join(DATA_DIR, "map-template.zip")

if not os.path.isfile(TEMPLATE_ARCHIVE):
    raise FileNotFoundError(
        f"Template archive not found: {TEMPLATE_ARCHIVE}. Please clone the repository again."
    )

OUTPUT_DIR = os.path.join(WORKING_DIR, "output")
WEIGHTS_DIR = os.path.join(OUTPUT_DIR, "maps", "map", "data")
WEIGHTS_FILES = [
    os.path.join(WEIGHTS_DIR, f) for f in os.listdir(WEIGHTS_DIR) if f.endswith("_weight.png")
]
console.log(f"Fetched {len(WEIGHTS_FILES)} weight files.")


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Map(metaclass=Singleton):
    def __init__(self, coordinates: tuple[float, float], distance: int):
        self._load_data()
        console.log(f"Fetching map data for coordinates: {coordinates}...")
        self.coordinates = coordinates
        self.distance = distance
        self.bbox = ox.utils_geo.bbox_from_point(self.coordinates, dist=self.distance)
        self._get_parameters()
        self.draw()
        self._prepare_mod()

    class Layer:
        def __init__(self, name: str, tags: dict[str, str | list[str]], width: int = None):
            self.name = name
            self.tags = tags
            self.width = width
            self._get_paths()
            self._check_shapes()
            console.log(f"Weights file for texture {self.name} loaded and checked.")

        def _get_paths(self):
            if self.name == "waterPuddle":
                self.paths = [os.path.join(WEIGHTS_DIR, "waterPuddle_weight.png")]
                return
            pattern = re.compile(rf"{self.name}\d{{2}}_weight")
            paths = [path for path in WEIGHTS_FILES if pattern.search(path)]
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
        dirt = self.Layer("dirt", {"highway": ["unclassified", "residential"]}, width=2)
        forestGround = self.Layer("forestGround", {"natural": "wood"})
        grass = self.Layer("grass", {"natural": "grassland"})
        gravel = self.Layer("gravel", {"highway": ["secondary", "tertiary"]}, width=4)
        waterPuddle = self.Layer("waterPuddle", {"natural": "water"})
        return [asphalt, concrete, dirt, forestGround, grass, gravel, waterPuddle]

    def _load_data(self):
        if not os.path.isdir(OUTPUT_DIR):
            os.mkdir(OUTPUT_DIR)
            console.log("Output directory created.")
        else:
            console.log("Output directory already exists and will be deleted.")
            shutil.rmtree(OUTPUT_DIR)
            os.mkdir(OUTPUT_DIR)

        shutil.unpack_archive(TEMPLATE_ARCHIVE, OUTPUT_DIR)
        console.log("Template archive unpacked.")

    def _get_parameters(self):
        north, south, east, west = ox.utils_geo.bbox_from_point(
            self.coordinates, dist=self.distance, project_utm=True
        )
        self.minimum_x = west
        self.minimum_y = south
        console.log(f"Map minimum coordinates (XxY): {self.minimum_x} x {self.minimum_y}.")
        console.log(f"Map maximum coordinates (XxY): {east} x {north}.")

        self.easting = self.minimum_x < 500000
        self.northing = self.minimum_y < 10000000
        console.log(f"Map is in {'east' if self.easting else 'west'} of central meridian.")
        console.log(f"Map is in {'north' if self.northing else 'south'} hemisphere.")

        self.height = abs(north - south)
        self.width = abs(east - west)
        console.log(f"Map dimensions (HxW): {self.height} x {self.width}.")

        self.height_coef = self.height / (self.distance * 2)
        self.width_coef = self.width / (self.distance * 2)
        console.log(f"Map coefficients (HxW): {self.height_coef} x {self.width_coef}.")

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
            console.log(f"Geometry type {geometry_type} not supported.")
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
        objects = ox.features_from_bbox(*self.bbox, tags=tags)
        objects_utm = ox.project_gdf(objects, to_latlong=False)
        console.log(f"Fetched {len(objects_utm)} elements for tags: {tags}.")

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
            console.log(f"Texture {layer.path} saved.")

    def _prepare_mod(self) -> None:
        shutil.make_archive(MOD_SAVE_PATH, "zip", OUTPUT_DIR)
        console.log(f"Archive created: {MOD_SAVE_PATH}.")
