import os
import re
import warnings
from typing import Any, Callable, Generator

import cv2
import numpy as np
import osmnx as ox
import pandas as pd
import shapely.geometry

import maps4fs.globals as g
from maps4fs.generator import Component


class Texture(Component):
    class Layer:
        """Class which represents a layer with textures and tags.
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
        """

        def __init__(
            self,
            weights_dir: str,
            name: str,
            tags: dict[str, str | list[str]],
            width: int = None,
            color: tuple[int, int, int] = None,
        ):
            self.weights_dir = weights_dir
            self.name = name
            self.tags = tags
            self.width = width
            self.color = color if color else (255, 255, 255)
            self._get_paths()

        def _get_paths(self):
            """Gets paths to textures of the layer.

            Raises:
                FileNotFoundError: If texture is not found.
            """
            if self.name == "waterPuddle":
                self.paths = [os.path.join(self.weights_dir, "waterPuddle_weight.png")]
                return
            weight_files = [
                os.path.join(self.weights_dir, f)
                for f in os.listdir(self.weights_dir)
                if f.endswith("_weight.png")
            ]
            pattern = re.compile(rf"{self.name}\d{{2}}_weight")
            paths = [path for path in weight_files if pattern.search(path)]
            if not paths:
                raise FileNotFoundError(f"Texture not found: {self.name}")
            self.paths = paths

        @property
        def path(self) -> str:
            """Returns path to the first texture of the layer.

            Returns:
                str: Path to the texture.
            """
            return self.paths[0]

    def __init__(
        self,
        coordinates: tuple[float, float],
        distance: int,
        map_directory: str,
        logger: Any = None,
        **kwargs,
    ):
        super().__init__(coordinates, distance, map_directory, logger)
        self._weights_dir = os.path.join(self.map_directory, "maps", "map", "data")
        self._bbox = ox.utils_geo.bbox_from_point(self.coordinates, dist=self.distance)

    def process(self):
        self._prepare_weights()
        self._read_parameters()
        self.draw()

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
        self.logger.debug(f"Map minimum coordinates (XxY): {self.minimum_x} x {self.minimum_y}.")
        self.logger.debug(f"Map maximum coordinates (XxY): {self.maximum_x} x {self.maximum_y}.")

        self.height = abs(north - south)
        self.width = abs(east - west)
        self.logger.info(f"Map dimensions (HxW): {self.height} x {self.width}.")

        self.height_coef = self.height / (self.distance * 2)
        self.width_coef = self.width / (self.distance * 2)
        self.logger.debug(f"Map coefficients (HxW): {self.height_coef} x {self.width_coef}.")

        self.easting = self.minimum_x < 500000
        self.northing = self.minimum_y < 10000000
        self.logger.debug(f"Map is in {'east' if self.easting else 'west'} of central meridian.")
        self.logger.debug(f"Map is in {'north' if self.northing else 'south'} hemisphere.")

    def _prepare_weights(self):
        self.logger.debug("Starting preparing weights...")
        for texture_name, layer_numbers in g.TEXTURES.items():
            self._generate_weights(texture_name, layer_numbers)
        self.logger.debug(f"Prepared weights for {len(g.TEXTURES)} textures.")

    def _generate_weights(self, texture_name: str, layer_numbers: int) -> None:
        """Generates weight files for textures. Each file is a numpy array of zeros and dtype uint8 (0-255).

        Args:
            texture_name (str): Name of the texture.
            layer_numbers (int): Number of layers in the texture.
        """
        size = self.distance * 2
        postfix = "_weight.png"
        if layer_numbers == 0:
            filepaths = [os.path.join(self._weights_dir, texture_name + postfix)]
        else:
            filepaths = [
                os.path.join(self._weights_dir, texture_name + str(i).zfill(2) + postfix)
                for i in range(1, layer_numbers + 1)
            ]

        for filepath in filepaths:
            img = np.zeros((size, size), dtype=np.uint8)
            cv2.imwrite(filepath, img)

    @property
    def layers(self) -> list[Layer]:
        """Returns list of layers with textures and tags from textures.json.

        Returns:
            list[Layer]: List of layers.
        """
        asphalt = self.Layer(
            self._weights_dir,
            "asphalt",
            {"highway": ["motorway", "trunk", "primary"]},
            width=8,
            color=(70, 70, 70),
        )
        concrete = self.Layer(
            self._weights_dir, "concrete", {"building": True}, width=8, color=(130, 130, 130)
        )
        dirtDark = self.Layer(
            self._weights_dir,
            "dirtDark",
            {"highway": ["unclassified", "residential", "track"]},
            width=2,
            color=(33, 67, 101),
        )
        grassDirt = self.Layer(
            self._weights_dir,
            "grassDirt",
            {"natural": ["wood", "tree_row"]},
            width=2,
            color=(0, 252, 124),
        )
        grass = self.Layer(
            self._weights_dir, "grass", {"natural": "grassland"}, color=(34, 255, 34)
        )
        forestGround = self.Layer(
            self._weights_dir, "forestGround", {"landuse": "farmland"}, color=(47, 107, 85)
        )
        gravel = self.Layer(
            self._weights_dir,
            "gravel",
            {"highway": ["secondary", "tertiary", "road"]},
            width=4,
            color=(140, 180, 210),
        )
        waterPuddle = self.Layer(
            self._weights_dir,
            "waterPuddle",
            {"natural": "water", "waterway": True},
            width=10,
            color=(255, 20, 20),
        )
        return [asphalt, concrete, dirtDark, forestGround, grass, grassDirt, gravel, waterPuddle]

    def draw(self) -> None:
        """Iterates over layers and fills them with polygons from OSM data."""
        for layer in self.layers:
            img = cv2.imread(layer.path, cv2.IMREAD_UNCHANGED)
            for polygon in self.polygons(layer.tags, layer.width):
                cv2.fillPoly(img, [polygon], color=255)
            cv2.imwrite(layer.path, img)
            self.logger.debug(f"Texture {layer.path} saved.")

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
            self.logger.warning(f"Geometry type {geometry_type} not supported.")
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
                objects = ox.features_from_bbox(*self._bbox, tags=tags)
        except Exception as e:
            self.logger.error(f"Error fetching objects for tags: {tags}.")
            self.logger.error(e)
            return
        objects_utm = ox.project_gdf(objects, to_latlong=False)
        self.logger.debug(f"Fetched {len(objects_utm)} elements for tags: {tags}.")

        for index, obj in objects_utm.iterrows():
            polygon = self._to_polygon(obj, width)
            if polygon is None:
                continue
            yield polygon
