"""Module with Texture class for generating textures for the map using OSM data."""

from __future__ import annotations

import json
import os
import warnings
from typing import Callable, Generator, Optional

import cv2
import numpy as np
import osmnx as ox  # type: ignore
import pandas as pd
import shapely.geometry  # type: ignore
from shapely.geometry.base import BaseGeometry  # type: ignore

from maps4fs.generator.component import Component

PREVIEW_MAXIMUM_SIZE = 2048


# pylint: disable=R0902
class Texture(Component):
    """Class which generates textures for the map using OSM data.

    Attributes:
        weights_dir (str): Path to the directory with weights.
        name (str): Name of the texture.
        tags (dict[str, str | list[str] | bool]): Dictionary of tags to search for.
        width (int | None): Width of the polygon in meters (only for LineString).
        color (tuple[int, int, int]): Color of the layer in BGR format.
    """

    # pylint: disable=R0903
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

        # pylint: disable=R0913
        def __init__(  # pylint: disable=R0917
            self,
            name: str,
            count: int,
            tags: dict[str, str | list[str] | bool] | None = None,
            width: int | None = None,
            color: tuple[int, int, int] | list[int] | None = None,
        ):
            self.name = name
            self.count = count
            self.tags = tags
            self.width = width
            self.color = color if color else (255, 255, 255)

        def to_json(self) -> dict[str, str | list[str] | bool]:  # type: ignore
            """Returns dictionary with layer data.

            Returns:
                dict: Dictionary with layer data."""
            data = {
                "name": self.name,
                "count": self.count,
                "tags": self.tags,
                "width": self.width,
                "color": list(self.color),
            }

            data = {k: v for k, v in data.items() if v is not None}
            return data  # type: ignore

        @classmethod
        def from_json(cls, data: dict[str, str | list[str] | bool]) -> Texture.Layer:
            """Creates a new instance of the class from dictionary.

            Args:
                data (dict[str, str | list[str] | bool]): Dictionary with layer data.

            Returns:
                Layer: New instance of the class.
            """
            return cls(**data)  # type: ignore

        def path(self, weights_directory: str) -> str:
            """Returns path to the first texture of the layer.

            Arguments:
                weights_directory (str): Path to the directory with weights.

            Returns:
                str: Path to the texture.
            """
            if self.name == "waterPuddle":
                return os.path.join(weights_directory, "waterPuddle_weight.png")
            return os.path.join(weights_directory, f"{self.name}01_weight.png")

    def preprocess(self) -> None:
        if not os.path.isfile(self.game.texture_schema):
            raise FileNotFoundError(f"Texture layers schema not found: {self.game.texture_schema}")

        try:
            with open(self.game.texture_schema, "r", encoding="utf-8") as f:
                layers_schema = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Error loading texture layers schema: {e}") from e

        self.layers = [self.Layer.from_json(layer) for layer in layers_schema]
        self.logger.info("Loaded %s layers.", len(self.layers))

        self._weights_dir = os.path.join(self.map_directory, "maps", "map", "data")
        self.info_save_path = os.path.join(self.map_directory, "generation_info.json")

    def process(self):
        self._prepare_weights()
        self._read_parameters()
        self.draw()
        self.info_sequence()

    # pylint: disable=W0201
    def _read_parameters(self) -> None:
        """Reads map parameters from OSM data, such as:
        - minimum and maximum coordinates in UTM format
        - map dimensions in meters
        - map coefficients (meters per pixel)
        """
        north, south, east, west = self.get_bbox(project_utm=True)

        # Parameters of the map in UTM format (meters).
        self.minimum_x = min(west, east)
        self.minimum_y = min(south, north)
        self.maximum_x = max(west, east)
        self.maximum_y = max(south, north)
        self.logger.debug("Map minimum coordinates (XxY): %s x %s.", self.minimum_x, self.minimum_y)
        self.logger.debug("Map maximum coordinates (XxY): %s x %s.", self.maximum_x, self.maximum_y)

        self.height = abs(north - south)
        self.width = abs(east - west)
        self.logger.info("Map dimensions (HxW): %s x %s.", self.height, self.width)

        self.height_coef = self.height / self.map_height
        self.width_coef = self.width / self.map_width
        self.logger.debug("Map coefficients (HxW): %s x %s.", self.height_coef, self.width_coef)

    def info_sequence(self) -> None:
        """Saves generation info to JSON file "generation_info.json".

        Info sequence contains following attributes:
            - coordinates
            - bbox
            - map_height
            - map_width
            - minimum_x
            - minimum_y
            - maximum_x
            - maximum_y
            - height
            - width
            - height_coef
            - width_coef
        """
        useful_attributes = [
            "coordinates",
            "bbox",
            "map_height",
            "map_width",
            "minimum_x",
            "minimum_y",
            "maximum_x",
            "maximum_y",
            "height",
            "width",
            "height_coef",
            "width_coef",
        ]
        info_sequence = {attr: getattr(self, attr, None) for attr in useful_attributes}

        with open(self.info_save_path, "w") as f:  # pylint: disable=W1514
            json.dump(info_sequence, f, indent=4)
        self.logger.info("Generation info saved to %s.", self.info_save_path)

    def _prepare_weights(self):
        self.logger.debug("Starting preparing weights from %s layers.", len(self.layers))

        for layer in self.layers:
            self._generate_weights(layer.name, layer.count)
        self.logger.debug("Prepared weights for %s layers.", len(self.layers))

    def _generate_weights(self, texture_name: str, layer_numbers: int) -> None:
        """Generates weight files for textures. Each file is a numpy array of zeros and
            dtype uint8 (0-255).

        Args:
            texture_name (str): Name of the texture.
            layer_numbers (int): Number of layers in the texture.
        """
        size = (self.map_height, self.map_width)
        postfix = "_weight.png"
        if layer_numbers == 0:
            filepaths = [os.path.join(self._weights_dir, texture_name + postfix)]
        else:
            filepaths = [
                os.path.join(self._weights_dir, texture_name + str(i).zfill(2) + postfix)
                for i in range(1, layer_numbers + 1)
            ]

        for filepath in filepaths:
            img = np.zeros(size, dtype=np.uint8)
            cv2.imwrite(filepath, img)  # pylint: disable=no-member

    @property
    def layers(self) -> list[Layer]:
        """Returns list of layers with textures and tags from textures.json.

        Returns:
            list[Layer]: List of layers.
        """
        return self._layers

    @layers.setter
    def layers(self, layers: list[Layer]) -> None:
        """Sets list of layers with textures and tags.

        Args:
            layers (list[Layer]): List of layers.
        """
        self._layers = layers

    # pylint: disable=no-member
    def draw(self) -> None:
        """Iterates over layers and fills them with polygons from OSM data."""
        for layer in self.layers:
            if not layer.tags:
                self.logger.debug("Layer %s has no tags, there's nothing to draw.", layer.name)
                continue
            layer_path = layer.path(self._weights_dir)
            self.logger.debug("Drawing layer %s.", layer_path)

            img = cv2.imread(layer_path, cv2.IMREAD_UNCHANGED)
            for polygon in self.polygons(layer.tags, layer.width):  # type: ignore
                cv2.fillPoly(img, [polygon], color=255)  # type: ignore
            cv2.imwrite(layer_path, img)
            self.logger.debug("Texture %s saved.", layer_path)

    def get_relative_x(self, x: float) -> int:
        """Converts UTM X coordinate to relative X coordinate in map image.

        Args:
            x (float): UTM X coordinate.

        Returns:
            int: Relative X coordinate in map image.
        """
        raw_x = x - self.minimum_x
        return int(raw_x * self.height_coef)

    def get_relative_y(self, y: float) -> int:
        """Converts UTM Y coordinate to relative Y coordinate in map image.

        Args:
            y (float): UTM Y coordinate.

        Returns:
            int: Relative Y coordinate in map image.
        """
        raw_y = y - self.minimum_y
        return self.height - int(raw_y * self.width_coef)

    # pylint: disable=W0613
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
            self.logger.warning("Geometry type %s not supported.", geometry_type)
            return None
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

    def _converters(
        self, geom_type: str
    ) -> Optional[Callable[[BaseGeometry, Optional[int]], np.ndarray]]:
        """Returns a converter function for a given geometry type.

        Args:
            geom_type (str): Geometry type.

        Returns:
            Callable[[shapely.geometry, int | None], np.ndarray]: Converter function.
        """
        converters = {"Polygon": self._to_np, "LineString": self._sequence, "Point": self._sequence}
        return converters.get(geom_type)  # type: ignore

    def polygons(
        self, tags: dict[str, str | list[str] | bool], width: int | None
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
                objects = ox.features_from_bbox(bbox=self.bbox, tags=tags)
        except Exception as e:  # pylint: disable=W0718
            self.logger.warning("Error fetching objects for tags: %s.", tags)
            self.logger.warning(e)
            return
        objects_utm = ox.project_gdf(objects, to_latlong=False)
        self.logger.debug("Fetched %s elements for tags: %s.", len(objects_utm), tags)

        for _, obj in objects_utm.iterrows():
            polygon = self._to_polygon(obj, width)
            if polygon is None:
                continue
            yield polygon

    def previews(self) -> list[str]:
        """Invokes methods to generate previews. Returns list of paths to previews.

        Returns:
            list[str]: List of paths to previews.
        """
        preview_paths = []
        preview_paths.append(self._osm_preview())
        return preview_paths

    # pylint: disable=no-member
    def _osm_preview(self) -> str:
        """Merges layers into one image and saves it into the png file.

        Returns:
            str: Path to the preview.
        """
        scaling_factor = min(
            PREVIEW_MAXIMUM_SIZE / self.map_width, PREVIEW_MAXIMUM_SIZE / self.map_height
        )

        preview_size = (
            int(self.map_width * scaling_factor),
            int(self.map_height * scaling_factor),
        )
        self.logger.debug(
            "Scaling factor: %s. Preview size: %s.",
            scaling_factor,
            preview_size,
        )

        images = [
            cv2.resize(
                cv2.imread(layer.path(self._weights_dir), cv2.IMREAD_UNCHANGED), preview_size
            )
            for layer in self.layers
        ]
        colors = [layer.color for layer in self.layers]
        color_images = []
        for img, color in zip(images, colors):
            color_img = np.zeros((img.shape[0], img.shape[1], 3), dtype=np.uint8)
            color_img[img > 0] = color
            color_images.append(color_img)
        merged = np.sum(color_images, axis=0, dtype=np.uint8)
        self.logger.debug(
            "Merged layers into one image. Shape: %s, dtype: %s.",
            merged.shape,
            merged.dtype,
        )
        preview_path = os.path.join(self.map_directory, "preview_osm.png")
        cv2.imwrite(preview_path, merged)  # pylint: disable=no-member
        self.logger.info("Preview saved to %s.", preview_path)
        return preview_path
