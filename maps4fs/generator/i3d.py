"""This module contains the Config class for map settings and configuration."""

from __future__ import annotations

import json
import os
from xml.etree import ElementTree as ET

from shapely.geometry import Polygon

from maps4fs.generator.component import Component

DEFAULT_HEIGHT_SCALE = 2000
DEFAULT_MAX_LOD_DISTANCE = 10000
DEFAULT_MAX_LOD_OCCLUDER_DISTANCE = 10000
NODE_ID_STARTING_VALUE = 500


# pylint: disable=R0903
class I3d(Component):
    """Component for map i3d file settings and configuration.

    Arguments:
        coordinates (tuple[float, float]): The latitude and longitude of the center of the map.
        map_height (int): The height of the map in pixels.
        map_width (int): The width of the map in pixels.
        map_directory (str): The directory where the map files are stored.
        logger (Any, optional): The logger to use. Must have at least three basic methods: debug,
            info, warning. If not provided, default logging will be used.
    """

    _map_i3d_path: str | None = None

    def preprocess(self) -> None:
        """Gets the path to the map I3D file from the game instance and saves it to the instance
        attribute. If the game does not support I3D files, the attribute is set to None."""
        try:
            self._map_i3d_path = self.game.i3d_file_path(self.map_directory)
            self.logger.debug("Map I3D path: %s.", self._map_i3d_path)
        except NotImplementedError:
            self.logger.info("I3D file processing is not implemented for this game.")
            self._map_i3d_path = None

    def process(self) -> None:
        """Updates the map I3D file with the default settings."""
        self._update_i3d_file()
        self._add_fields()

    def _get_tree(self) -> ET.ElementTree | None:
        """Returns the ElementTree instance of the map I3D file."""
        if not self._map_i3d_path:
            self.logger.info("I3D is not obtained, skipping the update.")
            return None
        if not os.path.isfile(self._map_i3d_path):
            self.logger.warning("I3D file not found: %s.", self._map_i3d_path)
            return None

        return ET.parse(self._map_i3d_path)

    def _update_i3d_file(self) -> None:
        # """Updates the map I3D file with the default settings."""
        # if not self._map_i3d_path:
        #     self.logger.info("I3D is not obtained, skipping the update.")
        #     return
        # if not os.path.isfile(self._map_i3d_path):
        #     self.logger.warning("I3D file not found: %s.", self._map_i3d_path)
        #     return

        # tree = ET.parse(self._map_i3d_path)

        tree = self._get_tree()
        if tree is None:
            return

        self.logger.debug("Map I3D file loaded from: %s.", self._map_i3d_path)

        root = tree.getroot()
        for map_elem in root.iter("Scene"):
            for terrain_elem in map_elem.iter("TerrainTransformGroup"):
                terrain_elem.set("heightScale", str(DEFAULT_HEIGHT_SCALE))
                self.logger.debug(
                    "heightScale attribute set to %s in TerrainTransformGroup element.",
                    DEFAULT_HEIGHT_SCALE,
                )
                terrain_elem.set("maxLODDistance", str(DEFAULT_MAX_LOD_DISTANCE))
                self.logger.debug(
                    "maxLODDistance attribute set to %s in TerrainTransformGroup element.",
                    DEFAULT_MAX_LOD_DISTANCE,
                )

                terrain_elem.set("occMaxLODDistance", str(DEFAULT_MAX_LOD_OCCLUDER_DISTANCE))
                self.logger.debug(
                    "occMaxLODDistance attribute set to %s in TerrainTransformGroup element.",
                    DEFAULT_MAX_LOD_OCCLUDER_DISTANCE,
                )

                self.logger.debug("TerrainTransformGroup element updated in I3D file.")

        tree.write(self._map_i3d_path)
        self.logger.debug("Map I3D file saved to: %s.", self._map_i3d_path)

    def previews(self) -> list[str]:
        """Returns a list of paths to the preview images (empty list).
        The component does not generate any preview images so it returns an empty list.

        Returns:
            list[str]: An empty list.
        """
        return []

    def _add_fields(self) -> None:
        tree = self._get_tree()
        if tree is None:
            return

        textures_info_layer_path = os.path.join(self.info_layers_directory, "textures.json")
        if not os.path.isfile(textures_info_layer_path):
            self.logger.warning("Textures info layer not found: %s.", textures_info_layer_path)
            return

        with open(textures_info_layer_path, "r") as textures_info_layer_file:
            textures_info_layer = json.load(textures_info_layer_file)

        fields: list[tuple[int, int]] | None = textures_info_layer.get("fields")
        if not fields:
            self.logger.warning("Fields data not found in textures info layer.")
            return

        self.logger.debug("Found %s fields in textures info layer.", len(fields))

        # Get the "gameplay" node
        # Get the "fields" node
        # For each field in the fields list:
        # Create an XML section

        root = tree.getroot()
        gameplay_node = root.find(".//TransformGroup[@name='gameplay']")
        if gameplay_node is not None:
            self.logger.debug("Found the gameplay node.")

            fields_node = gameplay_node.find(".//TransformGroup[@name='fields']")

            if fields_node is not None:
                self.logger.debug("Found the fields node.")

                node_id = NODE_ID_STARTING_VALUE

                for field_id, field in enumerate(fields, start=1):
                    #     <TransformGroup name="field1" translation="-1992.99 0 -1967.57" nodeId="745">
                    #       <TransformGroup name="polygonPoints" nodeId="746">
                    #         <TransformGroup name="point1" translation="-50.782 0 177.125" nodeId="747"/>
                    #         <TransformGroup name="point2" translation="-49.1483 0 -75.8821" nodeId="748"/>
                    #         <TransformGroup name="point3" translation="154.956 0 -76.8693" nodeId="749"/>
                    #       </TransformGroup>
                    #       <TransformGroup name="nameIndicator" nodeId="750">
                    #         <Note name="Note" nodeId="751" text="field1&amp;#xA;2.58 ha" color="4278190080" fixedSize="true"/>
                    #       </TransformGroup>
                    #       <TransformGroup name="teleportIndicator" nodeId="752"/>
                    #     </TransformGroup>
                    field_node = ET.Element("TransformGroup")
                    field_node.set("name", f"field{field_id}")
                    cx, cy = self.get_polygon_center(field)
                    field_node.set("translation", f"{cx} 0 {cy}")
                    field_node.set("nodeId", str(node_id))
                    node_id += 1

                    polygon_points_node = ET.Element("TransformGroup")
                    polygon_points_node.set("name", "polygonPoints")
                    polygon_points_node.set("nodeId", str(node_id))
                    node_id += 1

                    for point_id, point in enumerate(field, start=1):
                        rx, ry = self.absolute_to_relative(point, (cx, cy))

                        point_node = ET.Element("TransformGroup")
                        point_node.set("name", f"point{point_id}")
                        point_node.set("translation", f"{rx} 0 {ry}")
                        point_node.set("nodeId", str(node_id))
                        node_id += 1

                        polygon_points_node.append(point_node)

                    field_node.append(polygon_points_node)

                    name_indicator_node = ET.Element("TransformGroup")
                    name_indicator_node.set("name", "nameIndicator")
                    name_indicator_node.set("nodeId", str(node_id))

                    note_node = ET.Element("Note")
                    note_node.set("name", "Note")
                    note_node.set("nodeId", str(node_id))
                    note_node.set("text", f"field{field_id}&#xA;2.58 ha")
                    note_node.set("color", "4278190080")
                    note_node.set("fixedSize", "true")

                    name_indicator_node.append(note_node)

                    field_node.append(name_indicator_node)

                    teleport_indicator_node = ET.Element("TransformGroup")
                    teleport_indicator_node.set("name", "teleportIndicator")
                    teleport_indicator_node.set("nodeId", str(node_id))

                    field_node.append(teleport_indicator_node)

                    fields_node.append(field_node)

                    self.logger.debug("Field %s added to the I3D file.", field_id)

            tree.write(self._map_i3d_path)
            self.logger.debug("Map I3D file saved to: %s.", self._map_i3d_path)

    def get_polygon_center(self, polygon_points: list[tuple[int, int]]) -> tuple[int, int]:
        polygon = Polygon(polygon_points)
        center = polygon.centroid
        return int(center.x), int(center.y)

    def absolute_to_relative(
        self, point: tuple[int, int], center: tuple[int, int]
    ) -> tuple[int, int]:
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
        # using self.map_width and self.map_height
        # ensure that the new value in in bounds
        # e.g. for map width 4000, the center x value range is -2000 to 2000
        # if it's out of bounds, set it to the closest bound, e.g. for -2100 set it to -2000

        # cs_x_max = self.map_width // 2
        # cs_x_min = -cs_x_max
        # cs_y_max = self.map_height // 2
        # cs_y_min = -cs_y_max

        x, y = top_left
        cs_x = x - self.map_width // 2
        cs_y = self.map_height // 2 - y

        def to_bounds(value: int) -> int:
            half_width = self.map_width // 2
            return max(-half_width, min(half_width, value))

        return to_bounds(cs_x), to_bounds(cs_y)

    # e.g. x= 2000, map_width = 5000, it means that new x should be 2000 - 5000 // 2 = 2000 - 2500 = -500


# <TransformGroup name="gameplay" nodeId="743">
#   <TransformGroup name="fields" translation="0 91.5 0" nodeId="744">
#     <TransformGroup name="field1" translation="-1992.99 0 -1967.57" nodeId="745">
#       <TransformGroup name="polygonPoints" nodeId="746">
#         <TransformGroup name="point1" translation="-50.782 0 177.125" nodeId="747"/>
#         <TransformGroup name="point2" translation="-49.1483 0 -75.8821" nodeId="748"/>
#         <TransformGroup name="point3" translation="154.956 0 -76.8693" nodeId="749"/>
#       </TransformGroup>
#       <TransformGroup name="nameIndicator" nodeId="750">
#         <Note name="Note" nodeId="751" text="field1&amp;#xA;2.58 ha" color="4278190080" fixedSize="true"/>
#       </TransformGroup>
#       <TransformGroup name="teleportIndicator" nodeId="752"/>
#     </TransformGroup>
