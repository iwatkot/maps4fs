"""This module contains the base class for all map generation components."""

from __future__ import annotations

import json
import os
from copy import deepcopy
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable

import cv2
import numpy as np
import osmnx as ox
from shapely.affinity import rotate, translate
from shapely.geometry import LineString, Polygon, box

from maps4fs.generator.settings import Parameters

if TYPE_CHECKING:
    from maps4fs.generator.game import Game
    from maps4fs.generator.map import Map


class AttrDict(dict):
    """A dictionary that allows attribute-style access to its keys.
    Allows safe access to non-existing keys, returning None instead of raising KeyError.
    """

    def __getattr__(self, name: str) -> Any | None:
        """Returns the value of the given key or None if the key does not exist.

        Arguments:
            name (str): The key to retrieve.

        Returns:
            Any | None: The value of the key or None if the key does not exist.
        """
        try:
            return self[name]
        except KeyError:
            return None

    def __setattr__(self, name: str, value: Any) -> None:
        """Sets the value of the given key.

        Arguments:
            name (str): The key to set.
            value (Any): The value to set.
        """
        self[name] = value


@dataclass(frozen=True)
class ComponentPaths:
    """Resolved filesystem paths used by all components."""

    map_directory: str

    @property
    def previews_directory(self) -> str:
        return os.path.join(self.map_directory, "previews")

    @property
    def satellite_directory(self) -> str:
        return os.path.join(self.map_directory, "satellite")

    @property
    def generation_info_path(self) -> str:
        return os.path.join(self.map_directory, "generation_info.json")


class Component:
    """Base class for all map generation components.

    Arguments:
        game (Game): The game instance for which the map is generated.
        map (Map): The map instance for which the component is generated.
        map_size (int, optional): Override the map canvas size (default: map.size).
        map_rotated_size (int, optional): Override the rotated canvas size
            (default: map.rotated_size). Used by Background to pass a larger canvas.
    """

    def __init__(
        self,
        game: Game,
        map: Map,
        *,
        map_size: int | None = None,
        map_rotated_size: int | None = None,
        **kwargs: Any,
    ):
        self.game = game
        self.map = map
        self.map_size = map_size if map_size is not None else map.size
        self.map_rotated_size = (
            map_rotated_size if map_rotated_size is not None else map.rotated_size
        )
        self.coordinates = map.coordinates
        self.rotation = map.rotation
        self.map_directory = map.map_directory
        self.paths = ComponentPaths(self.map_directory)
        self.logger = map.logger
        self.kwargs = kwargs

        self.logger.debug(
            "Component %s initialized. Map size: %s, map rotated size: %s",
            self.__class__.__name__,
            self.map_size,
            self.map_rotated_size,
        )

        self._prepare_directories()

        self.save_bbox()
        self.preprocess()

        self.assets = AttrDict()

    def _prepare_directories(self) -> None:
        """Ensure all shared component output directories exist."""
        os.makedirs(self.paths.previews_directory, exist_ok=True)
        os.makedirs(self.paths.satellite_directory, exist_ok=True)

    def preprocess(self) -> None:
        """Prepares the component for processing. Must be implemented in the child class."""
        return

    def process(self) -> None:
        """Launches the component processing. Must be implemented in the child class.

        Raises:
            NotImplementedError: If the method is not implemented in the child class.
        """
        raise NotImplementedError

    def previews(self) -> list[str]:
        """Returns a list of paths to the preview images. If the component does not generate any
        previews, the method may not be re-implemented in the child class.

        Returns:
            list[str]: A list of paths to the preview images.
        """
        return []

    @property
    def previews_directory(self) -> str:
        """The directory where the preview images are stored.

        Returns:
            str: The directory where the preview images are stored.
        """
        return self.paths.previews_directory

    @property
    def satellite_directory(self) -> str:
        """The directory where the satellite images are stored.

        Returns:
            str: The directory where the satellite images are stored.
        """
        return self.paths.satellite_directory

    @property
    def generation_info_path(self) -> str:
        """The path to the generation info JSON file.

        Returns:
            str: The path to the generation info JSON file.
        """
        return self.paths.generation_info_path

    def info_sequence(self) -> dict[Any, Any]:
        """Returns the information sequence for the component. Must be implemented in the child
        class. If the component does not have an information sequence, an empty dictionary must be
        returned.

        Returns:
            dict[Any, Any]: The information sequence for the component.
        """
        return {}

    def commit_generation_info(self) -> None:
        """Commits the generation info to the generation info JSON file."""
        self.update_generation_info(self.info_sequence())

    def update_generation_info(self, data: dict[Any, Any]) -> None:
        """Updates the generation info with the provided data.
        If the generation info file does not exist, it will be created.

        Arguments:
            data (dict[Any, Any]): The data to update the generation info with.
        """
        if os.path.isfile(self.generation_info_path):
            with open(self.generation_info_path, "r", encoding="utf-8") as file:
                generation_info = json.load(file)
                self.logger.debug("Loaded generation info from %s", self.generation_info_path)
        else:
            self.logger.debug(
                "Generation info file does not exist, creating a new one in %s",
                self.generation_info_path,
            )
            generation_info = {}

        updated_generation_info = deepcopy(generation_info)
        updated_generation_info[self.__class__.__name__] = data

        self.logger.debug("Updated generation info, now contains %s fields", len(data))

        with open(self.generation_info_path, "w", encoding="utf-8") as file:
            try:
                json.dump(updated_generation_info, file, indent=4)
            except Exception as e:
                self.logger.warning("Could not save updated generation info: %s", e)

        self.logger.debug("Saved updated generation info to %s", self.generation_info_path)

    def get_bbox(
        self,
        coordinates: tuple[float, float] | None = None,
        distance: int | None = None,
    ) -> tuple[float, float, float, float]:
        """Calculates the bounding box of the map from the coordinates and the height and
        width of the map.
        If coordinates and distance are not provided, the instance variables are used.

        Arguments:
            coordinates (tuple[float, float], optional): The latitude and longitude of the center
                of the map. Defaults to None.
            distance (int, optional): The distance from the center of the map to the edge of the
                map in all directions. Defaults to None.

        Returns:
            tuple[float, float, float, float]: The bounding box of the map.
        """
        coordinates = coordinates or self.coordinates
        distance = distance or int(self.map_rotated_size / 2)

        west, south, east, north = ox.utils_geo.bbox_from_point(
            coordinates,
            dist=distance,
        )

        bbox = north, south, east, west
        self.logger.debug(
            "Calculated bounding box for component: %s: %s, distance: %s",
            self.__class__.__name__,
            bbox,
            distance,
        )
        return bbox

    def save_bbox(self) -> None:
        """Saves the bounding box of the map to the component instance from the coordinates and the
        height and width of the map.
        """
        self.bbox = self.get_bbox()
        self.logger.debug("Saved bounding box: %s", self.bbox)

    @property
    def new_bbox(self) -> tuple[float, float, float, float]:
        """This property is used for a new version of osmnx library, where the order of coordinates
        has been changed to (left, bottom, right, top).

        Returns:
            tuple[float, float, float, float]: The bounding box of the map in the new order:
                (left, bottom, right, top).
        """
        # FutureWarning: The expected order of coordinates in `bbox`
        # will change in the v2.0.0 release to `(left, bottom, right, top)`.
        north, south, east, west = self.bbox
        return west, south, east, north

    def get_polygon_center(self, polygon_points: list[tuple[int, int]]) -> tuple[int, int]:
        """Calculates the center of a polygon defined by a list of points.

        Arguments:
            polygon_points (list[tuple[int, int]]): The points of the polygon.

        Returns:
            tuple[int, int]: The center of the polygon.
        """
        polygon = Polygon(polygon_points)
        center = polygon.centroid
        return int(center.x), int(center.y)

    @staticmethod
    def polygon_points_to_np(
        polygon_points: list[tuple[int, int]], divide: int | None = None
    ) -> np.ndarray:
        """Convert polygon points to Nx1x2 int32 array optionally divided by factor."""
        array = np.array(polygon_points, dtype=np.int32).reshape((-1, 1, 2))
        if divide:
            return array // divide
        return array

    @staticmethod
    def polygon_dimensions_and_rotation(polygon_points: np.ndarray) -> tuple[float, float, float]:
        """Return width, depth and normalized rotation angle using min-area rectangle."""
        points = polygon_points.astype(np.float32)
        (_, _), (width, height), angle = cv2.minAreaRect(points)

        if width < height:
            width, height = height, width
            angle = angle + 90.0

        rotation_angle = (-angle) % 360.0
        return width, height, rotation_angle

    def absolute_to_relative(
        self, point: tuple[int, int], center: tuple[int, int]
    ) -> tuple[int, int]:
        """Converts a pair of absolute coordinates to relative coordinates.

        Arguments:
            point (tuple[int, int]): The absolute coordinates.
            center (tuple[int, int]): The center coordinates.

        Returns:
            tuple[int, int]: The relative coordinates.
        """
        cx, cy = center
        x, y = point
        return x - cx, y - cy

    def top_left_coordinates_to_center(self, top_left: tuple[int, int]) -> tuple[int, int]:
        """Converts a pair of coordinates from the top-left system to the center system.
        In top-left system, the origin (0, 0) is in the top-left corner of the map, while in the
        center system, the origin is in the center of the map.

        Arguments:
            top_left (tuple[int, int]): The coordinates in the top-left system.

        Returns:
            tuple[int, int]: The coordinates in the center system.
        """
        x, y = top_left
        cs_x = x - self.scaled_size // 2
        cs_y = y - self.scaled_size // 2

        return cs_x, cs_y

    def fit_object_into_bounds(
        self,
        polygon_points: list[tuple[int, int]] | None = None,
        linestring_points: list[tuple[int, int]] | None = None,
        margin: int = 0,
        angle: int = 0,
        border: int = 0,
        canvas_size: int | None = None,
        xshift: int = 0,
        yshift: int = 0,
        rotated_canvas_size: int | None = None,
    ) -> list[tuple[int, int]]:
        """Fits a polygon into the bounds of the map.

        Arguments:
            polygon_points (list[tuple[int, int]]): The points of the polygon.
            linestring_points (list[tuple[int, int]]): The points of the linestring.
            margin (int, optional): The margin to add to the polygon. Defaults to 0.
            angle (int, optional): The angle to rotate the polygon by. Defaults to 0.
            border (int, optional): The border to add to the bounds. Defaults to 0.
            canvas_size (int, optional): The size of the canvas. Defaults to None.
            xshift (int, optional): The x-axis shift to apply. Will be added to calculated offset.
            yshift (int, optional): The y-axis shift to apply. Will be added to calculated offset.

        Returns:
            list[tuple[int, int]]: The points of the polygon fitted into the map bounds.
        """
        if polygon_points is None and linestring_points is None:
            raise ValueError("Either polygon or linestring points must be provided.")

        limit = canvas_size or self.scaled_size

        min_x = min_y = 0 + border
        max_x = max_y = limit - border

        object_type = Polygon if polygon_points else LineString

        osm_object = object_type(polygon_points or linestring_points)

        if angle:
            if rotated_canvas_size is not None:
                # Caller supplied the size of the rotated input pixel space explicitly.
                # Use its centre as the rotation origin and derive the translation to
                # map that centre onto the output canvas centre.
                center_x = center_y = rotated_canvas_size // 2
                offset = limit // 2 - rotated_canvas_size // 2
            else:
                center_x = center_y = self.map_rotated_size * self.map.size_scale // 2  # type: ignore
                offset = (
                    int((self.map_size / 2) - (self.map_rotated_size / 2)) * self.map.size_scale  # type: ignore
                )
            self.logger.debug(
                "Rotating the osm_object by %s degrees with center at %sx%s",
                angle,
                center_x,
                center_y,
            )
            osm_object = rotate(osm_object, -angle, origin=(center_x, center_y))
            xoff = yoff = offset
            xoff += xshift
            yoff += yshift
            self.logger.debug("Translating the osm_object by X: %s, Y: %s", xoff, yoff)
            osm_object = translate(osm_object, xoff=xoff, yoff=yoff)
            self.logger.debug("Rotated and translated the osm_object.")

        if margin and object_type is Polygon:
            osm_object = osm_object.buffer(margin, join_style="mitre")
            if osm_object.is_empty:
                raise ValueError("The osm_object is empty after adding the margin.")

        # Create a bounding box for the map bounds
        bounds = box(min_x, min_y, max_x, max_y)

        # Intersect the osm_object with the bounds to fit it within the map
        try:
            fitted_osm_object = osm_object.intersection(bounds)
            self.logger.debug("Fitted the osm_object into the bounds: %s", bounds)
        except Exception as e:
            raise ValueError(f"Could not fit the osm_object into the bounds: {e}") from e

        if not isinstance(fitted_osm_object, object_type):
            raise ValueError("The fitted osm_object is not valid (probably splitted into parts).")

        # Return the fitted polygon points
        if object_type is Polygon:
            as_list = list(fitted_osm_object.exterior.coords)
        elif object_type is LineString:
            as_list = list(fitted_osm_object.coords)
        else:
            raise ValueError("The object type is not supported.")

        if not as_list:
            raise ValueError("The fitted osm_object has no points.")
        return as_list

    # Maps (layer_name, layer_key) pairs to their map.context attribute names.
    # Used by get_infolayer_data for direct in-memory lookups.
    _INFO_LAYER_CONTEXT_MAP: dict[tuple[str, str], str] = {
        ("textures", "fields"): "fields",
        ("textures", "buildings"): "buildings",
        ("textures", "roads_polylines"): "roads_polylines",
        ("textures", "water_polylines"): "water_polylines",
        ("textures", "farmyards"): "farmyards",
        ("textures", "forest"): "forest",
        ("textures", "water"): "water",
        ("background", "water"): "background_water",
        ("background", "water_polylines"): "background_water_polylines",
    }

    def get_infolayer_data(self, layer_name: str, layer_key: str) -> Any | None:
        """Return data from a named info layer by key.

        Reads map.context only. Legacy info_layers/*.json channel is removed.

        Arguments:
            layer_name (str): Name of the info layer (e.g. "textures", "background").
            layer_key (str): Key within the layer (e.g. "fields", "buildings").

        Returns:
            Any | None: The value or None if not found.
        """
        ctx_attr = self._INFO_LAYER_CONTEXT_MAP.get((layer_name, layer_key))
        if ctx_attr is not None:
            return getattr(self.map.context, ctx_attr, None)
        return None

    @staticmethod
    def interpolate_points(
        polyline: list[tuple[int, int]], num_points: int = 4
    ) -> list[tuple[int, int]]:
        """Receives a list of tuples, which represents a polyline. Add additional points
        between the existing points to make the polyline smoother.

        Arguments:
            polyline (list[tuple[int, int]]): The list of points to interpolate.
            num_points (int): The number of additional points to add between each pair of points.

        Returns:
            list[tuple[int, int]]: The list of points with additional points.
        """
        if not polyline or num_points < 1:
            return polyline

        interpolated_polyline = []
        for i in range(len(polyline) - 1):
            p1 = polyline[i]
            p2 = polyline[i + 1]
            interpolated_polyline.append(p1)
            for j in range(1, num_points + 1):
                new_point = (
                    p1[0] + (p2[0] - p1[0]) * j / (num_points + 1),
                    p1[1] + (p2[1] - p1[1]) * j / (num_points + 1),
                )
                interpolated_polyline.append((int(new_point[0]), int(new_point[1])))
        interpolated_polyline.append(polyline[-1])

        return interpolated_polyline

    def get_z_scaling_factor(self, ignore_height_scale_multiplier: bool = False) -> float:
        """Calculates the scaling factor for the Z axis based on the map settings.

        Returns:
            float -- The scaling factor for the Z axis.
        """

        scaling_factor = 1 / self.map.dem_settings.multiplier

        if self.map.context.height_scale_multiplier and not ignore_height_scale_multiplier:
            scaling_factor *= self.map.context.height_scale_multiplier
        if self.map.context.mesh_z_scaling_factor:
            scaling_factor *= 1 / self.map.context.mesh_z_scaling_factor

        return scaling_factor

    @property
    def scaled_size(self) -> int:
        """Returns the output size of the map if it was set, otherwise returns the map size.

        Returns:
            int: The output size of the map or the map size.
        """
        return self.map_size if self.map.output_size is None else self.map.output_size

    def get_z_coordinate_from_dem(self, not_resized_dem: np.ndarray, x: int, y: int) -> float:
        """Gets the Z coordinate from the DEM image for the given coordinates.

        Arguments:
            not_resized_dem (np.ndarray): The not resized DEM image.
            x (int): The x coordinate.
            y (int): The y coordinate.

        Returns:
            float: The Z coordinate.
        """
        dem_x_size, dem_y_size = not_resized_dem.shape

        x = int(max(0, min(x, dem_x_size - 1)))
        y = int(max(0, min(y, dem_y_size - 1)))

        z = not_resized_dem[y, x]
        z *= self.get_z_scaling_factor(ignore_height_scale_multiplier=True)

        return z

    @staticmethod
    def get_item_with_fallback(
        items: list[Any], check_function: Callable, start_at: int = 0, end_on: int | None = None
    ) -> Any | None:
        """Slices the list from start_at to end_on and returns the result of the check_function
        of the first item that returns a non-None value. If no item passes the check_function,
        None is returned.

        Arguments:
            items (list[Any]): The list of items to check.
            check_function (Callable): The function to check each item.
            start_at (int): The index to start checking from. Defaults to 0 (start of the list).
            end_on (int | None): The index to stop checking at. Defaults to None (end of the
                list, including the last item).

        Returns:
            Any | None: The first item that passes the check_function or None if no item passes
                the check_function.
        """
        sliced_items = items[start_at:end_on]
        for item in sliced_items:
            result = check_function(item)
            if result is not None:
                return result
        return None

    @staticmethod
    def get_image_safely(image_path: str) -> np.ndarray | None:
        """Safely gets an image from the provided path.

        Arguments:
            image_path (str): The path to the image.

        Returns:
            np.ndarray | None: The image or None if not found or failed to load.
        """
        if not os.path.isfile(image_path):
            return None

        try:
            image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
            return image
        except Exception:
            return None

    def get_dem_image_with_fallback(
        self, start_at: int = 0, end_on: int | None = None
    ) -> np.ndarray | None:
        """Gets the DEM image using fallback mechanism.

        Arguments:
            start_at (int, optional): The index to start checking from. Defaults to 0.
            end_on (int | None, optional): The index to end checking on. Defaults to None (end of
                the list, including the last item).

        Returns:
            np.ndarray | None: The DEM image or None if not found.
        """
        background_directory = os.path.join(self.map_directory, "background")
        items = [
            os.path.join(background_directory, dem_type)
            for dem_type in Parameters.SUPPORTED_DEM_TYPES
        ]
        return self.get_item_with_fallback(items, self.get_image_safely, start_at, end_on)

    def get_non_zero_bounds(self, image: np.ndarray) -> tuple[int, int, int, int] | None:
        """Gets the distance from each edge of the image to the nearest non-zero pixel.

        Arguments:
            image (np.ndarray): The image to get the non-zero bounds of.

        Returns:
            tuple[int, int, int, int] | None: Distances (left, top, right, bottom) from each
                edge to the nearest non-zero pixel, or None if the image is empty.
        """
        coords = cv2.findNonZero(image)
        if coords is None:
            return None
        x, y, w, h = cv2.boundingRect(coords)
        image_height, image_width = image.shape[:2]
        return x, y, image_width - (x + w), image_height - (y + h)

    @staticmethod
    def get_dem_extremes_by_mask(
        dem: np.ndarray, mask: np.ndarray
    ) -> tuple[tuple[int, int, float], tuple[int, int, float]] | None:
        """Finds the minimum and maximum DEM values within the non-zero area of a mask,
        along with their pixel coordinates.

        Arguments:
            dem (np.ndarray): The DEM image.
            mask (np.ndarray): The mask image (non-zero pixels define the region of interest).

        Returns:
            tuple | None: ((min_x, min_y, min_val), (max_x, max_y, max_val)) or None if the
                mask is empty.
        """
        binary_mask = (mask > 0).astype(np.uint8)
        if not np.any(binary_mask):
            return None

        masked_dem = np.where(binary_mask, dem.astype(np.float64), np.nan)

        min_idx = np.nanargmin(masked_dem)
        max_idx = np.nanargmax(masked_dem)

        min_y, min_x = np.unravel_index(min_idx, masked_dem.shape)
        max_y, max_x = np.unravel_index(max_idx, masked_dem.shape)

        min_val = float(dem[min_y, min_x])
        max_val = float(dem[max_y, max_x])

        return (int(min_x), int(min_y), min_val), (int(max_x), int(max_y), max_val)
