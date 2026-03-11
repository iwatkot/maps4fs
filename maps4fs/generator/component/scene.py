"""This module contains the Scene class for FS25 map I3D scene editing."""

from __future__ import annotations

import json
import os
import shutil
from random import choice, randint, uniform
from typing import Any, Generator
from xml.etree import ElementTree as ET

import cv2
import numpy as np
from tqdm import tqdm

from maps4fs.generator.component.base.component_image import ImageComponent
from maps4fs.generator.component.base.component_xml import XMLComponent, XmlDocument
from maps4fs.generator.constants import Paths
from maps4fs.generator.monitor import monitor_performance
from maps4fs.generator.settings import Parameters

NODE_ID_STARTING_VALUE = 2000
SPLINES_NODE_ID_STARTING_VALUE = 5000
TREE_NODE_ID_STARTING_VALUE = 30000
FILE_ID_STARTING_VALUE = 120000
BINARY_MESHES_NODE_ID_STARTING_VALUE = 150000
BOUNDS_FILE_ID = 160000
BOUNDS_NODE_ID = 200000

FIELDS_ATTRIBUTES = [
    ("angle", "integer", "0"),
    ("missionAllowed", "boolean", "true"),
    ("missionOnlyGrass", "boolean", "false"),
    ("nameIndicatorIndex", "string", "1"),
    ("polygonIndex", "string", "0"),
    ("teleportIndicatorIndex", "string", "2"),
]


class Scene(XMLComponent, ImageComponent):
    """Component for FS25 map I3D scene editing: height scale, sun bbox,
    displacement layer, splines, fields, forests, mesh insertion.

    Arguments:
        game (Game): The game instance for which the map is generated.
        coordinates (tuple[float, float]): The latitude and longitude of the center of the map.
        map_size (int): The size of the map in pixels.
        map_rotated_size (int): The size of the map in pixels after rotation.
        rotation (int): The rotation angle of the map.
        map_directory (str): The directory where the map files are stored.
        logger (Any, optional): The logger to use.
    """

    def preprocess(self) -> None:
        """Gets the path to the map I3D file from the game instance and saves it to the instance
        attribute. If the game does not support I3D files, the attribute is set to None."""
        self.xml_path = self.game.i3d_file_path

        self.forest_info: dict[str, Any] = {}
        self.field_info: dict[str, Any] = {}

    def process(self) -> None:
        """Updates the map I3D file and creates splines in a separate I3D file."""
        self.update_height_scale()

        self._update_parameters()

        self._add_fields()

        if self.map.i3d_settings.add_trees:
            self._add_forests()
        self._add_splines()

        self.insert_meshes()
        self.insert_map_bounds()

    def update_height_scale(self, value: int | None = None) -> None:
        """Updates the height scale value in the map I3D file.
        If the value is not provided, the method checks if the shared settings are set to change
        the height scale and if the height scale value is set. If not, the method returns without
        updating the height scale.

        Arguments:
            value (int, optional): The height scale value.
        """
        if not value:
            if (
                self.map.shared_settings.change_height_scale
                and self.map.shared_settings.height_scale_value
            ):
                value = int(self.map.shared_settings.height_scale_value)
            else:
                return

        with XmlDocument(self.xml_path) as doc:  # type: ignore
            doc.set_attrs(
                ".//Scene/TerrainTransformGroup",
                **{Parameters.HEIGHT_SCALE: str(value)},
            )

    def _update_parameters(self) -> None:
        """Updates the map I3D file with the sun bounding box and displacement layer size."""
        distance = self.map_size // 2
        with XmlDocument(self.xml_path) as doc:  # type: ignore
            doc.set_attrs(
                ".//Scene/Light[@name='sun']",
                lastShadowMapSplitBboxMin=f"-{distance},-128,-{distance}",
                lastShadowMapSplitBboxMax=f"{distance},148,{distance}",
            )
            doc.set_attrs(
                ".//Scene/TerrainTransformGroup/Layers/DisplacementLayer",
                size=str(int(self.map_size * 8)),
            )

    @monitor_performance
    def _add_splines(self) -> None:
        """Adds splines to the map I3D file."""
        splines_i3d_path = self.game.splines_file_path
        if not os.path.isfile(splines_i3d_path):
            self.logger.warning("Splines I3D file not found: %s.", splines_i3d_path)
            return

        splines_doc = XmlDocument(splines_i3d_path)

        roads_polylines = (
            self.get_infolayer_data(Parameters.TEXTURES, Parameters.ROADS_POLYLINES) or []
        )

        water_polylines = (
            self.get_infolayer_data(Parameters.TEXTURES, Parameters.WATER_POLYLINES) or []
        )
        roads_polylines.extend(water_polylines)

        if self.map.i3d_settings.field_splines:
            fields_polygons = self.get_infolayer_data(Parameters.TEXTURES, Parameters.FIELDS)
            if isinstance(roads_polylines, list) and isinstance(fields_polygons, list):
                roads_polylines.extend(fields_polygons)

        if not roads_polylines:
            self.logger.warning("Roads polylines data not found in textures info layer.")
            return

        root = splines_doc.root
        # Find <Shapes> element in the I3D file.
        shapes_node = root.find(".//Shapes")  # type: ignore
        # Find <Scene> element in the I3D file.
        scene_node = root.find(".//Scene")  # type: ignore

        if shapes_node is None or scene_node is None:
            self.logger.warning("Shapes or Scene node not found in I3D file.")
            return

        not_resized_dem = self.get_dem_image_with_fallback()
        if not_resized_dem is None:
            self.logger.warning("Not resized DEM not found.")
            return

        if self.map.output_size is not None:
            not_resized_dem = cv2.resize(
                not_resized_dem,
                (self.map.output_size, self.map.output_size),
                interpolation=cv2.INTER_NEAREST,
            )

        user_attributes_node = root.find(".//UserAttributes")  # type: ignore
        if user_attributes_node is None:
            self.logger.warning("UserAttributes node not found in I3D file.")
            return

        node_id = SPLINES_NODE_ID_STARTING_VALUE
        for road_id, road_info in enumerate(roads_polylines, start=1):
            if isinstance(road_info, dict):
                points = road_info.get("points")
                tags = road_info.get("tags")
                is_field = False
            else:
                points = road_info
                tags = "field"
                is_field = True

            try:
                fitted_road = self.fit_object_into_bounds(
                    linestring_points=points, angle=self.rotation
                )
            except ValueError as e:
                self.logger.debug(
                    "Road %s could not be fitted into the map bounds with error: %s",
                    road_id,
                    e,
                )
                continue

            fitted_road = self.interpolate_points(
                fitted_road, num_points=self.map.i3d_settings.spline_density
            )
            fitted_roads = [(fitted_road, "original")]

            if self.map.i3d_settings.add_reversed_splines:
                reversed_fitted_road = fitted_road[::-1]
                fitted_roads.append((reversed_fitted_road, "reversed"))

            for fitted_road, direction in fitted_roads:
                spline_name = f"spline_{road_id}_{direction}_{tags}"

                data = {
                    "name": spline_name,
                    "translation": "0 0 0",
                    "nodeId": str(node_id),
                    "shapeId": str(node_id),
                }

                scene_node.append(self.create_element("Shape", data))

                road_ccs = [self.top_left_coordinates_to_center(point) for point in fitted_road]

                data = {
                    "name": spline_name,
                    "shapeId": str(node_id),
                    "degree": "3",
                    "form": "open",
                }
                nurbs_curve_node = self.create_element("NurbsCurve", data)

                for point_ccs, point in zip(road_ccs, fitted_road):
                    cx, cy = point_ccs
                    x, y = point

                    z = self.get_z_coordinate_from_dem(not_resized_dem, x, y)

                    nurbs_curve_node.append(self.create_element("cv", {"c": f"{cx}, {z}, {cy}"}))

                shapes_node.append(nurbs_curve_node)

                if not is_field:
                    user_attribute_node = self.get_user_attribute_node(
                        node_id,
                        attributes=[
                            ("maxSpeedScale", "integer", "1"),
                            ("speedLimit", "integer", "100"),
                        ],
                    )

                    user_attributes_node.append(user_attribute_node)
                node_id += 1

        splines_doc.save()
        self.logger.debug("Splines I3D file saved to: %s.", splines_i3d_path)

        self.assets.splines = splines_i3d_path

    @monitor_performance
    def _add_fields(self) -> None:
        """Adds fields to the map I3D file."""
        fields_doc = XmlDocument(self.xml_path)  # type: ignore

        border = 0
        fields_layer = self.map.get_texture_layer(by_usage=Parameters.FIELD)
        if fields_layer and fields_layer.border:
            border = fields_layer.border

        fields = self.get_infolayer_data(Parameters.TEXTURES, Parameters.FIELDS)
        if not fields:
            self.logger.warning("Fields data not found in textures info layer.")
            return

        self.logger.debug("Found %s fields in textures info layer.", len(fields))
        self.logger.debug("Starging to add fields to the I3D file.")

        root = fields_doc.root
        gameplay_node = root.find(".//TransformGroup[@name='gameplay']")  # type: ignore

        if gameplay_node is None:
            return
        fields_node = gameplay_node.find(".//TransformGroup[@name='fields']")
        user_attributes_node = root.find(".//UserAttributes")  # type: ignore

        if fields_node is None or user_attributes_node is None:
            return

        node_id = NODE_ID_STARTING_VALUE
        field_id = 1
        added_fields = skipped_fields = 0
        skipped_field_ids: list[int] = []

        for field in tqdm(fields, desc="Adding fields", unit="field"):
            try:
                fitted_field = self.fit_object_into_bounds(
                    polygon_points=field, angle=self.rotation, border=border
                )
            except ValueError as e:
                self.logger.debug(
                    "Field %s could not be fitted into the map bounds with error: %s",
                    field_id,
                    e,
                )
                skipped_fields += 1
                continue

            field_ccs = [self.top_left_coordinates_to_center(point) for point in fitted_field]

            field_node, updated_node_id = self._get_field_xml_entry(field_id, field_ccs, node_id)
            if field_node is None:
                continue
            user_attributes_node.append(
                self.get_user_attribute_node(node_id, attributes=FIELDS_ATTRIBUTES)
            )
            node_id = updated_node_id

            # Adding the field node to the fields node.
            fields_node.append(field_node)
            self.logger.debug("Field %s added to the I3D file.", field_id)

            node_id += 1
            field_id += 1
            added_fields += 1

        self.field_info["added_fields"] = added_fields
        self.field_info["skipped_fields"] = skipped_fields
        self.field_info["skipped_field_ids"] = skipped_field_ids

        fields_doc.save()

        self.assets.fields = self.xml_path

    def _get_field_xml_entry(
        self, field_id: int, field_ccs: list[tuple[int, int]], node_id: int
    ) -> tuple[ET.Element, int] | tuple[None, int]:
        """Creates an XML entry for the field with given field ID and field coordinates.

        Arguments:
            field_id (int): The ID of the field.
            field_ccs (list[tuple[int, int]]): The coordinates of the field polygon points
                in the center coordinate system.
            node_id (int): The node ID of the field node.

        Returns:
            tuple[ET.Element, int] | tuple[None, int]: The field node and the updated node ID or
                None and the node ID.
        """
        try:
            cx, cy = self.get_polygon_center(field_ccs)
        except Exception as e:
            self.logger.debug("Field %s could not be fitted into the map bounds.", field_id)
            self.logger.debug("Error: %s", e)
            return None, node_id

        # Creating the main field node.
        data = {
            "name": f"field{field_id}",
            "translation": f"{cx} 0 {cy}",
            "nodeId": str(node_id),
        }
        field_node = self.create_element("TransformGroup", data)
        node_id += 1

        # Creating the polygon points node, which contains the points of the field.
        polygon_points_node = self.create_element(
            "TransformGroup", {"name": "polygonPoints", "nodeId": str(node_id)}
        )
        node_id += 1

        for point_id, point in enumerate(field_ccs, start=1):
            rx, ry = self.absolute_to_relative(point, (cx, cy))

            node_id += 1
            point_node = self.create_element(
                "TransformGroup",
                {
                    "name": f"point{point_id}",
                    "translation": f"{rx} 0 {ry}",
                    "nodeId": str(node_id),
                },
            )

            polygon_points_node.append(point_node)

        field_node.append(polygon_points_node)

        # Adding the name indicator node to the field node.
        name_indicator_node, node_id = self._get_name_indicator_node(node_id, field_id)
        field_node.append(name_indicator_node)

        node_id += 1
        field_node.append(
            self.create_element(
                "TransformGroup", {"name": "teleportIndicator", "nodeId": str(node_id)}
            )
        )

        return field_node, node_id

    def _get_name_indicator_node(self, node_id: int, field_id: int) -> tuple[ET.Element, int]:
        """Creates a name indicator node with given node ID and field ID.

        Arguments:
            node_id (int): The node ID of the name indicator node.
            field_id (int): The ID of the field.

        Returns:
            tuple[ET.Element, int]: The name indicator node and the updated node ID.
        """
        node_id += 1
        name_indicator_node = self.create_element(
            "TransformGroup", {"name": "nameIndicator", "nodeId": str(node_id)}
        )

        node_id += 1
        data = {
            "name": "Note",
            "nodeId": str(node_id),
            "text": f"field{field_id}&#xA;0.00 ha",
            "color": "4278190080",
            "fixedSize": "true",
        }
        note_node = self.create_element("Note", data)
        name_indicator_node.append(note_node)

        return name_indicator_node, node_id

    def get_user_attribute_node(
        self, node_id: int, attributes: list[tuple[str, str, str]]
    ) -> ET.Element:
        """Creates an XML user attribute node with given node ID.

        Arguments:
            node_id (int): The node ID of the user attribute node.
            attributes (list[tuple[str, str, str]]): The list of attributes to add to the node.

        Returns:
            ET.Element: The created user attribute node.
        """
        user_attribute_node = ET.Element("UserAttribute")
        user_attribute_node.set("nodeId", str(node_id))

        for name, attr_type, value in attributes:
            data = {
                "name": name,
                "type": attr_type,
                "value": value,
            }
            user_attribute_node.append(self.create_element("Attribute", data))

        return user_attribute_node

    def _read_tree_schema(self) -> list[dict[str, str]] | None:
        """Reads the tree schema from the game instance or from the custom schema.

        Returns:
            list[dict[str, int | str]] | None: The tree schema or None if the schema could not be
                read.
        """
        custom_schema = self.kwargs.get("tree_custom_schema")
        if custom_schema:
            tree_schema = custom_schema
        else:
            try:
                tree_schema_path = self.game.tree_schema
            except ValueError:
                self.logger.warning("Tree schema path not set for the Game %s.", self.game.code)
                return None

            if not os.path.isfile(tree_schema_path):
                self.logger.warning("Tree schema file was not found: %s.", tree_schema_path)
                return None

            try:
                with open(tree_schema_path, "r", encoding="utf-8") as tree_schema_file:
                    tree_schema = json.load(tree_schema_file)  # type: ignore
            except json.JSONDecodeError as e:
                self.logger.warning(
                    "Could not load tree schema from %s with error: %s", tree_schema_path, e
                )
                return None

        return tree_schema  # type: ignore

    def _get_random_tree(
        self, tree_schema: list[dict[str, str]], leaf_type: str | None = None
    ) -> dict[str, str]:
        """Gets a random tree from the tree schema.
        If the leaf type is provided, the method tries to get a tree with the same leaf type.

        Arguments:
            tree_schema (list[dict[str, str]]): The tree schema.
            leaf_type (str, optional): The leaf type of the tree. Defaults to None.

        Returns:
            dict[str, str]: The random tree from the schema
        """
        if not leaf_type:
            return choice(tree_schema)

        try:
            leaf_type = leaf_type.split("_")[0]
        except IndexError:
            return choice(tree_schema)

        if leaf_type == "mixed":
            trees_with_leaf_type = [tree for tree in tree_schema if tree.get("leaf_type")]
            if not trees_with_leaf_type:
                return choice(tree_schema)
            return choice(trees_with_leaf_type)

        trees_by_leaf_type = [tree for tree in tree_schema if tree.get("leaf_type") == leaf_type]
        if not trees_by_leaf_type:
            return choice(tree_schema)

        return choice(trees_by_leaf_type)

    @monitor_performance
    def _add_forests(self) -> None:
        """Adds forests to the map I3D file."""
        tree_schema = self._read_tree_schema()
        if not tree_schema:
            return

        if self.map.texture_settings.use_precise_tags:
            forest_layers = self.map.get_texture_layers(by_usage=Parameters.FOREST)
        else:
            layer = self.map.get_texture_layer(by_usage=Parameters.FOREST)
            forest_layers = [layer] if layer else []
        if not forest_layers:
            self.logger.warning("Forest layer not found.")
            return

        node_id = TREE_NODE_ID_STARTING_VALUE
        tree_count = 0
        forests_doc = XmlDocument(self.xml_path)  # type: ignore
        forests_root = forests_doc.root
        scene_node = forests_root.find(".//Scene")  # type: ignore
        if scene_node is None:
            self.logger.warning("Scene element not found in I3D file.")
            return

        for forest_layer in forest_layers:
            weights_directory = self.game.weights_dir_path
            forest_image_path = forest_layer.get_preview_or_path(weights_directory)

            if not forest_image_path or not os.path.isfile(forest_image_path):
                self.logger.warning("Forest image not found.")
                continue

            trees_node = self.create_element(
                "TransformGroup",
                {
                    "name": "trees",
                    "translation": "0 0 0",
                    "nodeId": str(node_id),
                },
            )
            node_id += 1

            not_resized_dem = self.get_dem_image_with_fallback()
            if not_resized_dem is None:
                self.logger.warning("Not resized DEM not found.")
                return

            if self.map.output_size is not None:
                not_resized_dem = cv2.resize(
                    not_resized_dem,
                    (self.map.output_size, self.map.output_size),
                    interpolation=cv2.INTER_NEAREST,
                )

            forest_image = cv2.imread(forest_image_path, cv2.IMREAD_UNCHANGED)

            step = self.get_step_by_limit(
                forest_image,  # type: ignore
                self.map.i3d_settings.tree_limit,
                self.map.i3d_settings.forest_density,
            )

            shift = (
                self.map.i3d_settings.forest_density
                * self.map.i3d_settings.trees_relative_shift
                / 100
            )

            for x, y in self.non_empty_pixels(forest_image, step=step):  # type: ignore
                shifted_x, shifted_y = self.randomize_coordinates((x, y), shift)

                shifted_x, shifted_y = int(shifted_x), int(shifted_y)

                z = self.get_z_coordinate_from_dem(not_resized_dem, shifted_x, shifted_y)

                xcs, ycs = self.top_left_coordinates_to_center((shifted_x, shifted_y))
                node_id += 1

                rotation = randint(-180, 180)

                random_tree = self._get_random_tree(tree_schema, forest_layer.precise_usage)
                tree_name = random_tree["name"]
                tree_id = random_tree["reference_id"]

                data = {
                    "name": tree_name,
                    "translation": f"{xcs} {z} {ycs}",
                    "rotation": f"0 {rotation} 0",
                    "referenceId": str(tree_id),
                    "nodeId": str(node_id),
                }
                trees_node.append(self.create_element("ReferenceNode", data))

                tree_count += 1

            scene_node.append(trees_node)

        forests_doc.save()

        self.forest_info["tree_count"] = tree_count
        self.forest_info["tree_limit"] = self.map.i3d_settings.tree_limit
        self.forest_info["initial_step"] = self.map.i3d_settings.forest_density
        self.forest_info["actual_step"] = step
        self.forest_info["shift"] = shift

        self.assets.forests = self.xml_path

    @staticmethod
    def randomize_coordinates(
        coordinates: tuple[int, int], shift_range: float
    ) -> tuple[float, float]:
        """Randomizes the coordinates of the point with the given density.

        Arguments:
            coordinates (tuple[int, int]): The coordinates of the point.
            shift_range (float): Maximum absolute shift in pixels.

        Returns:
            tuple[float, float]: The randomized coordinates of the point.
        """
        x_shift = uniform(-shift_range, shift_range)
        y_shift = uniform(-shift_range, shift_range)

        x, y = coordinates

        return x + x_shift, y + y_shift

    @staticmethod
    def non_empty_pixels(
        image: np.ndarray, step: int = 1
    ) -> Generator[tuple[int, int], None, None]:
        """Receives numpy array, which represents single-channeled image of uint8 type.
        Yield coordinates of non-empty pixels (pixels with value greater than 0), sampling about 1/step of them.

        Arguments:
            image (np.ndarray): The image to get non-empty pixels from.
            step (int, optional): The step to sample non-empty pixels. Defaults to 1.

        Yields:
            tuple[int, int]: The coordinates of non-empty pixels.
        """
        count = 0
        for y, row in enumerate(image):
            for x, value in enumerate(row):
                if value > 0:
                    if count % step == 0:
                        yield x, y
                    count += 1

    @staticmethod
    def non_empty_pixels_count(image: np.ndarray) -> int:
        """Counts the number of non-empty pixels in the image.

        Arguments:
            image (np.ndarray): The image to count non-empty pixels in.

        Returns:
            int: The number of non-empty pixels in the image.
        """
        return int(np.count_nonzero(image > 0))

    def get_step_by_limit(
        self, image: np.ndarray, limit: int, current_step: int | None = None
    ) -> int:
        """Calculates the step size for iterating through the image based on the limit based
        on the number of non-empty pixels in the image.

        Arguments:
            image (np.ndarray): The image to calculate the step size for.
            limit (int): The maximum number of non-empty pixels to process.
            current_step (int | None, optional): The current step size. If provided, the method
                will return the maximum of the recommended step and the current step.

        Returns:
            int: The recommended step size for iterating through the image.
        """
        available_tree_count = self.non_empty_pixels_count(image)
        self.forest_info["available_tree_count"] = available_tree_count
        if limit <= 0 or available_tree_count <= limit:
            recommended_step = 1
        else:
            recommended_step = int(available_tree_count / limit)

        self.forest_info["step_by_limit"] = recommended_step

        return recommended_step if not current_step else max(recommended_step, current_step)

    def info_sequence(self) -> dict[str, dict[str, str | float | int]]:
        """Returns information about the component.

        Returns:
            dict[str, dict[str, str | float | int]]: Information about the component.
        """
        data = {
            "Forests": self.forest_info,
            "Fields": self.field_info,
        }

        return data

    def _find_binary_i3d_in_directory(self, directory: str) -> str | None:
        """Finds the binary I3D file in the given directory.

        Arguments:
            directory (str): The directory to search for the binary I3D file.

        Returns:
            str | None: The path to the binary I3D file if found, otherwise None.
        """
        for file in os.listdir(directory):
            if file.endswith("_binary.i3d"):
                return os.path.join(directory, file)
        return None

    def _find_flat_binary_i3d_in_directory(self, directory: str) -> dict[str, str]:
        """Finds all binary I3D files directly in the given directory (non-recursive).

        Arguments:
            directory (str): The flat directory to scan.

        Returns:
            dict[str, str]: Mapping of asset name (filename stem, without '_binary.i3d') to path.
        """
        result: dict[str, str] = {}
        for file in os.listdir(directory):
            if file.endswith("_binary.i3d"):
                name = file[: -len("_binary.i3d")]
                result[name] = os.path.join(directory, file)
        return result

    def _find_nested_binary_i3d_in_directory(self, directory: str) -> dict[str, str]:
        """Finds binary I3D files in immediate subdirectories of the given directory.

        Arguments:
            directory (str): The directory containing subdirectories with binary I3D files.
                Expected structure: directory/type_name/something_binary.i3d

        Returns:
            dict[str, str]: Mapping of subdirectory name to binary I3D file path.
        """
        result: dict[str, str] = {}
        for entry in os.scandir(directory):
            if not entry.is_dir():
                continue
            binary_path = self._find_binary_i3d_in_directory(entry.path)
            if binary_path:
                result[entry.name] = binary_path
        return result

    def insert_meshes(self) -> None:
        """Inserts meshes into the I3D file."""
        assets_directory = self.map.assets_directory
        self.logger.debug(
            "Inserting meshes into the I3D file using assets from: %s.", assets_directory
        )

        background_assets_directory = os.path.join(assets_directory, "background")
        roads_assets_directory = os.path.join(assets_directory, "roads")
        water_assets_directory = os.path.join(assets_directory, "water")

        assets_directories: dict[str, str] = {
            Parameters.BACKGROUND_TERRAIN: background_assets_directory
        }
        if os.path.isdir(water_assets_directory):
            assets_directories.update(
                self._find_flat_binary_i3d_in_directory(water_assets_directory)
            )
        if os.path.isdir(roads_assets_directory):
            assets_directories.update(
                self._find_nested_binary_i3d_in_directory(roads_assets_directory)
            )

        file_id = FILE_ID_STARTING_VALUE
        node_id = BINARY_MESHES_NODE_ID_STARTING_VALUE

        # Load the main I3D document once; add all mesh references, then save once.
        main_doc = XmlDocument(self.xml_path)  # type: ignore
        main_root = main_doc.root
        files_node = main_root.find(".//Files")
        scene_node = main_root.find(".//Scene")
        if files_node is None or scene_node is None:
            self.logger.warning("Required nodes (Files, Scene) not found in I3D file.")
            return
        i3d_dir = os.path.dirname(self.xml_path)  # type: ignore

        for asset_name, asset_path in assets_directories.items():
            if os.path.isfile(asset_path):
                binary_i3d_path: str | None = asset_path
            elif os.path.isdir(asset_path):
                binary_i3d_path = self._find_binary_i3d_in_directory(asset_path)
            else:
                self.logger.warning("Asset path not found: %s.", asset_path)
                continue

            if not binary_i3d_path:
                self.logger.warning(
                    "Binary I3D file not found for asset: %s.",
                    asset_name,
                )
                continue

            self.logger.debug("Inserting mesh %s from file %s.", asset_name, binary_i3d_path)
            binary_rel_path = os.path.relpath(binary_i3d_path, i3d_dir).replace("\\", "/")
            self.logger.debug("Relative path for the binary I3D file: %s.", binary_rel_path)

            files_node.append(
                self.create_element("File", {"fileId": str(file_id), "filename": binary_rel_path})
            )
            scene_node.append(
                self.create_element(
                    "ReferenceNode",
                    {"name": asset_name, "referenceId": str(file_id), "nodeId": str(node_id)},
                )
            )

            self.logger.debug("Mesh %s inserted into the I3D file.", asset_name)

            file_id += 1
            node_id += 1

            self._postprocess_i3d(binary_i3d_path, asset_name)

        main_doc.save()

    def _postprocess_i3d(self, binary_i3d_path: str, asset_name: str) -> None:
        """Post-processes the I3D file after all modifications are done.

        Arguments:
            binary_i3d_path (str): The path to the binary I3D file that was inserted.
            asset_name (str): The name of the asset corresponding to the binary I3D file.
        """
        if asset_name == Parameters.BACKGROUND_TERRAIN:
            self.logger.debug("Post-processing background terrain mesh.")
            self._postprocess_background_terrain(binary_i3d_path)
        elif asset_name in (
            Parameters.WATER_RESOURCES,
            Parameters.WATER_RESOURCES_LINE_SURFACE,
        ):
            self.logger.debug("Post-processing water mesh for asset: %s.", asset_name)
            self._postprocess_water_resources(binary_i3d_path)
        else:
            self.logger.debug("Post-processing road mesh for asset: %s.", asset_name)
            self._postprocess_roads(binary_i3d_path)

        self.position_inserted_mesh(binary_i3d_path, asset_name)

    def position_inserted_mesh(self, binary_i3d_path: str, asset_name: str) -> None:
        """Reads the saved position data for the given asset and sets its translation in the
        binary I3D file.

        Arguments:
            binary_i3d_path (str): Path to the binary I3D file to position.
            asset_name (str): Name of the asset to position.
        """
        # We only need to lift it by its mean elevation so it aligns with the GE terrain.
        if asset_name == Parameters.BACKGROUND_TERRAIN:
            positions_directory = os.path.join(self.map_directory, "positions")
            position_file_path = os.path.join(
                positions_directory, f"{Parameters.BACKGROUND_TERRAIN}.json"
            )
            elevation = 0.0
            if os.path.isfile(position_file_path):
                try:
                    with open(position_file_path, "r", encoding="utf-8") as pf:
                        pos_data = json.load(pf)
                    elevation = float(pos_data.get("mesh_centroid_y", 0.0))
                except Exception as e:
                    self.logger.warning(
                        "Could not read background terrain elevation: %s. Using 0.", e
                    )
            self._set_mesh_translation(binary_i3d_path, f"0 {elevation} 0", asset_name)
            return

        positions_directory = os.path.join(self.map_directory, "positions")
        position_file_path = os.path.join(positions_directory, f"{asset_name}.json")
        if not os.path.isfile(position_file_path):
            self.logger.warning(
                "Position file not found for asset %s at path: %s. Skipping positioning.",
                asset_name,
                position_file_path,
            )
            return

        try:
            with open(position_file_path, "r", encoding="utf-8") as position_file:
                position_data = json.load(position_file)  # type: ignore
        except json.JSONDecodeError as e:
            self.logger.warning(
                "Could not load position data for asset %s from file %s with error: %s. Skipping positioning.",
                asset_name,
                position_file_path,
                e,
            )
            return

        min_z = position_data.get("min_z", 0.0)
        max_z = position_data.get("max_z", 0.0)

        # Prefer the exact mesh vertex centroid saved by road.py (post-rotation, pre-centering).
        # This matches vertices -= center exactly, unlike mask pixel centroid.
        mesh_centroid_x = position_data.get("mesh_centroid_x")
        mesh_centroid_z = position_data.get("mesh_centroid_z")

        if mesh_centroid_x is not None and mesh_centroid_z is not None:
            # Water meshes are generated over the full background canvas
            # (map_size + 2 * BACKGROUND_DISTANCE), so their pixel coordinates must be
            # offset by half the background canvas size, not half the map size.
            water_assets = {Parameters.WATER_RESOURCES, Parameters.WATER_RESOURCES_LINE_SURFACE}
            if asset_name in water_assets:
                canvas_half = (self.scaled_size + Parameters.BACKGROUND_DISTANCE * 2) // 2
            else:
                canvas_half = self.scaled_size // 2

            ge_x = float(mesh_centroid_x) - canvas_half
            ge_y = float(mesh_centroid_z) - canvas_half
            mesh_centroid_y = position_data.get("mesh_centroid_y")
            ge_elevation = (
                float(mesh_centroid_y) if mesh_centroid_y is not None else (min_z + max_z) / 2
            )
        else:
            centroid_x = position_data.get("centroid_x")
            centroid_y = position_data.get("centroid_y")
            if centroid_x is not None and centroid_y is not None:
                ge_x, ge_y = self.top_left_coordinates_to_center((centroid_x, centroid_y))
            else:
                left = position_data.get("left", 0)
                top = position_data.get("top", 0)
                right = position_data.get("right", 0)
                bottom = position_data.get("bottom", 0)
                center_pixel_x = int(left + (self.scaled_size - left - right) / 2)
                center_pixel_y = int(top + (self.scaled_size - top - bottom) / 2)
                ge_x, ge_y = self.top_left_coordinates_to_center((center_pixel_x, center_pixel_y))
            ge_elevation = (min_z + max_z) / 2

        # GE translation string order: X (east-west), Y (elevation), Z (north-south).
        translation = f"{ge_x} {ge_elevation} {ge_y}"
        self._set_mesh_translation(binary_i3d_path, translation, asset_name)

    def _set_mesh_translation(
        self, binary_i3d_path: str, translation: str, asset_name: str
    ) -> None:
        self.logger.debug("Positioning mesh %s at translation: %s.", asset_name, translation)

        doc = XmlDocument(binary_i3d_path)
        shape_node = doc.root.find(".//Shape")
        if shape_node is None:
            self.logger.warning("Shape node not found in binary I3D for asset %s.", asset_name)
            return

        shape_node.set("translation", translation)
        doc.save()

    def _postprocess_background_terrain(self, binary_i3d_path: str) -> None:
        """Post-processes the background terrain mesh in the I3D file."""
        doc = XmlDocument(binary_i3d_path)
        root = doc.root

        material_node = root.find(".//Material[@name='background_terrain_material']")
        shape_node = root.find(".//Shape[@name='background_terrain_shape']")

        if material_node is not None:
            if "specularColor" in material_node.attrib:
                del material_node.attrib["specularColor"]

        if shape_node is not None:
            shape_node.set("receiveShadows", "true")

        doc.save()

    def _postprocess_water_resources(self, binary_i3d_path: str) -> None:
        """Post-processes the water resources mesh in the I3D file.

        Arguments:
            binary_i3d_path (str): The path to the binary I3D file to post-process.
        """
        doc = XmlDocument(binary_i3d_path)
        root = doc.root

        # --- Files: bump shader fileId 3 → 4, insert normalmap as fileId 2 ---
        files_node = root.find(".//Files")
        if files_node is not None:
            shader_file = files_node.find("File[@fileId='3']")
            if shader_file is not None:
                shader_file.set("fileId", "4")
            normalmap_file = self.create_element(
                "File",
                {"fileId": "2", "filename": "$data/maps/textures/shared/water_normal.dds"},
            )
            files_node.insert(0, normalmap_file)

        # --- Material: update attributes and add children ---
        material_node = root.find(".//Material[@name='OceanShader']")
        if material_node is not None:
            material_node.set("specularColor", "1 1 1")
            material_node.set("customShaderId", "4")
            material_node.set("customShaderVariation", "simple")

            normalmap_elem = self.create_element("Normalmap", {"fileId": "2"})
            material_node.insert(0, normalmap_elem)

            material_node.append(
                self.create_element(
                    "CustomParameter",
                    {"name": "underwaterFogColor", "value": "0.12 0.14 0.11 1"},
                )
            )
            material_node.append(
                self.create_element(
                    "CustomParameter",
                    {"name": "underwaterFogDepth", "value": "1.4 1.2 1 1"},
                )
            )

        # --- Shape: add static/collision attrs, fix castsShadows ---
        shape_node = root.find(".//Shape")
        if shape_node is not None:
            shape_node.set("static", "true")
            shape_node.set("collisionFilterGroup", "0x80000000")
            shape_node.set("collisionFilterMask", "0x1")
            shape_node.set("castsShadows", "false")

        # --- Wrap bare Shape (direct Scene child) in a TransformGroup so GE respects translation ---
        scene_node = root.find(".//Scene")
        if scene_node is not None and shape_node is not None:
            if shape_node in list(scene_node):
                shape_nodeid = int(shape_node.get("nodeId", "4"))
                tg = self.create_element(
                    "TransformGroup",
                    {"name": shape_node.get("name", "water"), "nodeId": str(shape_nodeid - 1)},
                )
                scene_node.remove(shape_node)
                tg.append(shape_node)
                scene_node.append(tg)

        # --- UserAttributes: add onCreate callback ---
        user_attrs_node = root.find(".//UserAttributes")
        if user_attrs_node is None:
            user_attrs_node = ET.SubElement(root, "UserAttributes")

        shape_node_id = shape_node.get("nodeId") if shape_node is not None else None
        if shape_node_id is not None:
            ua = self.get_user_attribute_node(
                int(shape_node_id),
                [("onCreate", "scriptCallback", "Environment.onCreateWater")],
            )
            user_attrs_node.append(ua)

        doc.save()

    def _postprocess_roads(self, binary_i3d_path: str) -> None:
        """Post-processes a road mesh in the I3D file.

        Arguments:
            binary_i3d_path (str): The path to the binary I3D file to post-process.
        """
        doc = XmlDocument(binary_i3d_path)
        root = doc.root

        material_node = root.find(".//Material")
        if material_node is not None:
            material_node.attrib.pop("specularColor", None)

        shape_node = root.find(".//Shape")
        if shape_node is not None:
            shape_node.set("collisionFilterGroup", "0x601c")
            shape_node.set("collisionFilterMask", "0xfffffbff")
            shape_node.set("receiveShadows", "true")

        doc.save()

    def insert_map_bounds(self) -> None:
        """Inserts the map bounds into the I3D file by copying the template map bounds files,
        updating their positions, and adding a reference to the main I3D file."""
        filepaths = Paths.get_map_bounds_file_paths()
        if not filepaths:
            self.logger.warning(
                "Map bounds file paths could not be found. Skipping map bounds insertion."
            )
            return

        i3d_path, shapes_path = filepaths

        # Copy both files to map_directory/assets/map_bounds/
        # e.g. result: map_directory/assets/map_bounds/map_bounds.i3d
        # and map_directory/assets/map_bounds/map_bounds.i3d.shapes
        dest_dir = os.path.join(self.map_directory, "assets", "map_bounds")
        os.makedirs(dest_dir, exist_ok=True)
        dest_i3d_path = os.path.join(dest_dir, "map_bounds.i3d")
        dest_shapes_path = os.path.join(dest_dir, "map_bounds.i3d.shapes")
        try:
            shutil.copy(i3d_path, dest_i3d_path)
            shutil.copy(shapes_path, dest_shapes_path)
            self.logger.debug(
                "Map bounds files copied to %s and %s.", dest_i3d_path, dest_shapes_path
            )
        except IOError as e:
            self.logger.warning("Failed to copy map bounds files: %s.", e)
            return

        half = self.map_size // 2
        quarter = self.map_size // 4

        # 1. Update positions of the map bounds in the map_bounds.i3d file.
        # Translations use half the map size (GE center-origin coordinate system).
        # Scale span (Z) = half, scale height (X after rotation) = quarter (template ratio).
        bounds_doc = XmlDocument(dest_i3d_path)
        bounds_root = bounds_doc.root

        tg_node = bounds_root.find(".//Scene/TransformGroup[@name='mapbounds']")
        if tg_node is not None:
            shape_configs = {
                "mapbound_W": (f"-{half} 0 0", f"{quarter} 1 {half}"),
                "mapbound_E": (f"{half} 0 0", f"{quarter} 1 {half}"),
                "mapbound_N": (f"0 0 -{half}", f"{quarter} 1 {half}"),
                "mapbound_S": (f"0 0 {half}", f"{quarter} 1 {half}"),
            }
            for shape_name, (translation, scale) in shape_configs.items():
                shape_node = tg_node.find(f"Shape[@name='{shape_name}']")
                if shape_node is not None:
                    shape_node.set("translation", translation)
                    shape_node.set("scale", scale)

        bounds_doc.save()
        self.logger.debug("Map bounds positions updated in %s.", dest_i3d_path)

        # 2. Insert file reference into main I3D Files section and a ReferenceNode into Scene.
        main_doc = XmlDocument(self.xml_path)  # type: ignore
        root = main_doc.root
        files_node = root.find(".//Files")
        scene_node = root.find(".//Scene")

        if files_node is None or scene_node is None:
            self.logger.warning(
                "Files or Scene node not found in main I3D file. Skipping map bounds insertion."
            )
            return

        i3d_dir = os.path.dirname(self.xml_path)  # type: ignore
        bounds_rel_path = os.path.relpath(dest_i3d_path, i3d_dir).replace("\\", "/")

        files_node.append(
            self.create_element(
                "File", {"fileId": str(BOUNDS_FILE_ID), "filename": bounds_rel_path}
            )
        )
        # Y=1024 is the fixed height above ground in GE's X Z Y coordinate system.
        scene_node.append(
            self.create_element(
                "ReferenceNode",
                {
                    "name": "mapbounds",
                    "translation": "0 1024 0",
                    "referenceId": str(BOUNDS_FILE_ID),
                    "nodeId": str(BOUNDS_NODE_ID),
                },
            )
        )

        main_doc.save()
        self.logger.debug("Map bounds reference inserted into main I3D file.")
