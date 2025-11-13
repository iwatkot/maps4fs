"""This module contains the base class for all map generation components."""

from __future__ import annotations

import json
import os
from copy import deepcopy
from typing import TYPE_CHECKING, Any, Callable

import cv2
import numpy as np
import osmnx as ox
from pyproj import Transformer
from shapely.affinity import rotate, translate
from shapely.geometry import LineString, Polygon, box

from maps4fs.generator.qgis import save_scripts

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


class Component:
    """Base class for all map generation components.

    Arguments:
        game (Game): The game instance for which the map is generated.
        map (Map): The map instance for which the component is generated.
        coordinates (tuple[float, float]): The latitude and longitude of the center of the map.
        map_size (int): The size of the map in pixels.
        map_rotated_size (int): The size of the map in pixels after rotation.
        rotation (int): The rotation angle of the map.
        map_directory (str): The directory where the map files are stored.
        logger (Any, optional): The logger to use. Must have at least three basic methods: debug,
            info, warning. If not provided, default logging will be used.
    """

    def __init__(
        self,
        game: Game,
        map: Map,
        coordinates: tuple[float, float],
        map_size: int,
        map_rotated_size: int,
        rotation: int,
        map_directory: str,
        logger: Any = None,
        **kwargs: dict[str, Any],
    ):
        self.game = game
        self.map = map
        self.coordinates = coordinates
        self.map_size = map_size
        self.map_rotated_size = map_rotated_size
        self.rotation = rotation
        self.map_directory = map_directory
        self.logger = logger
        self.kwargs = kwargs

        self.logger.debug(
            "Component %s initialized. Map size: %s, map rotated size: %s",
            self.__class__.__name__,
            self.map_size,
            self.map_rotated_size,
        )

        os.makedirs(self.previews_directory, exist_ok=True)
        os.makedirs(self.scripts_directory, exist_ok=True)
        os.makedirs(self.info_layers_directory, exist_ok=True)
        os.makedirs(self.satellite_directory, exist_ok=True)

        self.save_bbox()
        self.preprocess()

        self.assets = AttrDict()

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
        return os.path.join(self.map_directory, "previews")

    @property
    def info_layers_directory(self) -> str:
        """The directory where the info layers are stored.

        Returns:
            str: The directory where the info layers are stored.
        """
        return os.path.join(self.map_directory, "info_layers")

    @property
    def scripts_directory(self) -> str:
        """The directory where the scripts are stored.

        Returns:
            str: The directory where the scripts are stored.
        """
        return os.path.join(self.map_directory, "scripts")

    @property
    def satellite_directory(self) -> str:
        """The directory where the satellite images are stored.

        Returns:
            str: The directory where the satellite images are stored.
        """
        return os.path.join(self.map_directory, "satellite")

    @property
    def generation_info_path(self) -> str:
        """The path to the generation info JSON file.

        Returns:
            str: The path to the generation info JSON file.
        """
        return os.path.join(self.map_directory, "generation_info.json")

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

    def get_espg3857_bbox(
        self, bbox: tuple[float, float, float, float] | None = None, add_margin: bool = False
    ) -> tuple[float, float, float, float]:
        """Converts the bounding box to EPSG:3857.
        If the bounding box is not provided, the instance variable is used.

        Arguments:
            bbox (tuple[float, float, float, float], optional): The bounding box to convert.
            add_margin (bool, optional): Whether to add a margin to the bounding box.

        Returns:
            tuple[float, float, float, float]: The bounding box in EPSG:3857.
        """
        bbox = bbox or self.bbox
        north, south, east, west = bbox
        transformer = Transformer.from_crs("epsg:4326", "epsg:3857")
        epsg3857_north, epsg3857_west = transformer.transform(north, west)
        epsg3857_south, epsg3857_east = transformer.transform(south, east)

        if add_margin:
            margin = 500
            epsg3857_north = int(epsg3857_north - margin)
            epsg3857_south = int(epsg3857_south + margin)
            epsg3857_east = int(epsg3857_east - margin)
            epsg3857_west = int(epsg3857_west + margin)

        return epsg3857_north, epsg3857_south, epsg3857_east, epsg3857_west

    def get_epsg3857_string(
        self, bbox: tuple[float, float, float, float] | None = None, add_margin: bool = False
    ) -> str:
        """Converts the bounding box to EPSG:3857 string.
        If the bounding box is not provided, the instance variable is used.

        Arguments:
            bbox (tuple[float, float, float, float], optional): The bounding box to convert.
            add_margin (bool, optional): Whether to add a margin to the bounding box.

        Returns:
            str: The bounding box in EPSG:3857 string.
        """
        north, south, east, west = self.get_espg3857_bbox(bbox, add_margin=add_margin)
        return f"{north},{south},{east},{west} [EPSG:3857]"

    def create_qgis_scripts(
        self, qgis_layers: list[tuple[str, float, float, float, float]]
    ) -> None:
        """Creates QGIS scripts from the given layers.
        Each layer is a tuple where the first element is a name of the layer and the rest are the
        bounding box coordinates in EPSG:3857.
        For filenames, the class name is used as a prefix.

        Arguments:
            qgis_layers (list[tuple[str, float, float, float, float]]): The list of layers to
                create scripts for.
        """
        class_name = self.__class__.__name__.lower()
        save_scripts(qgis_layers, class_name, self.scripts_directory)

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
            center_x = center_y = self.map_rotated_size * self.map.size_scale // 2
            self.logger.debug(
                "Rotating the osm_object by %s degrees with center at %sx%s",
                angle,
                center_x,
                center_y,
            )
            osm_object = rotate(osm_object, -angle, origin=(center_x, center_y))
            offset = int((self.map_size / 2) - (self.map_rotated_size / 2)) * self.map.size_scale
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

    def get_infolayer_path(self, layer_name: str) -> str | None:
        """Returns the path to the info layer file.

        Arguments:
            layer_name (str): The name of the layer.

        Returns:
            str | None: The path to the info layer file or None if the layer does not exist.
        """
        info_layer_path = os.path.join(self.info_layers_directory, f"{layer_name}.json")
        if not os.path.isfile(info_layer_path):
            self.logger.warning("Info layer %s does not exist", info_layer_path)
            return None
        return info_layer_path

    def get_infolayer_data(self, layer_name: str, layer_key: str) -> Any | None:
        """Reads the JSON file of the requested info layer and returns the value of the requested
        key. If the layer or the key does not exist, None is returned.

        Arguments:
            layer_name (str): The name of the layer.
            layer_key (str): The key to get the value of.

        Returns:
            Any | None: The value of the requested key or None if the layer or the key does not
                exist.
        """
        infolayer_path = self.get_infolayer_path(layer_name)
        if not infolayer_path:
            return None

        with open(infolayer_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        return data.get(layer_key)

    def rotate_image(
        self,
        image_path: str,
        angle: int,
        output_height: int,
        output_width: int,
        output_path: str | None = None,
    ) -> None:
        """Rotates an image by a given angle around its center and cuts out the center to match
        the output size.

        Arguments:
            image_path (str): The path to the image to rotate.
            angle (int): The angle to rotate the image by.
            output_height (int): The height of the output image.
            output_width (int): The width of the output image.
        """
        if not os.path.isfile(image_path):
            self.logger.warning("Image %s does not exist", image_path)
            return

        image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
        if image is None:
            self.logger.warning("Image %s could not be read", image_path)
            return

        self.logger.debug("Read image from %s with shape: %s", image_path, image.shape)

        if not output_path:
            output_path = image_path

        height, width = image.shape[:2]
        center = (width // 2, height // 2)

        self.logger.debug(
            "Rotating the image... Angle: %s, center: %s, height: %s, width: %s",
            angle,
            center,
            height,
            width,
        )

        rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(image, rotation_matrix, (width, height))

        start_x = center[0] - output_width // 2
        start_y = center[1] - output_height // 2
        end_x = start_x + output_width
        end_y = start_y + output_height

        self.logger.debug(
            "Cropping the rotated image: start_x: %s, start_y: %s, end_x: %s, end_y: %s",
            start_x,
            start_y,
            end_x,
            end_y,
        )

        cropped = rotated[start_y:end_y, start_x:end_x]

        self.logger.debug("Shape of the cropped image: %s", cropped.shape)

        cv2.imwrite(output_path, cropped)

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

        if self.map.shared_settings.height_scale_multiplier and not ignore_height_scale_multiplier:
            scaling_factor *= self.map.shared_settings.height_scale_multiplier
        if self.map.shared_settings.mesh_z_scaling_factor:
            scaling_factor *= 1 / self.map.shared_settings.mesh_z_scaling_factor

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
