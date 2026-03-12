"""Component for map roads processing and generation."""

from __future__ import annotations

import os
import shutil
from collections import defaultdict
from typing import Any

import numpy as np
import shapely
import trimesh
from shapely.geometry import Point

from maps4fs.generator.component.base.component_mesh import (
    LineSurfaceEntry,
    MeshComponent,
)
from maps4fs.generator.constants import Paths
from maps4fs.generator.settings import Parameters


class Road(MeshComponent):
    """Component for map roads processing and generation.

    Arguments:
        game (Game): The game instance for which the map is generated.
        coordinates (tuple[float, float]): The latitude and longitude of the center of the map.
        map_size (int): The size of the map in pixels.
        map_rotated_size (int): The size of the map in pixels after rotation.
        rotation (int): The rotation angle of the map.
        map_directoryPara (str): The directory where the map files are stored.
        logger (Any, optional): The logger to use. Must have at least three basic methods: debug,
            info, warning. If not provided, default logging will be used.
    """

    def preprocess(self) -> None:
        """Preprocess the road data before generation."""
        self.info: dict[str, Any] = {}

    def process(self) -> None:
        """Process and generate roads for the map."""
        try:
            self.generate_roads()
        except Exception as e:
            self.logger.error("Error during road generation: %s", e)

    def generate_roads(self) -> None:
        """Generate roads for the map based on the info layer data."""
        road_infos = self._load_road_infos()
        if road_infos is None:
            self.logger.warning("Roads polylines data not found in textures info layer.")
            return

        roads_by_texture = self._group_roads_by_texture(road_infos)
        self.info[Parameters.ROAD_INFO_TEXTURES] = list(roads_by_texture.keys())
        self.info[Parameters.ROAD_INFO_TOTAL_OSM] = len(road_infos)

        fitted_roads_count = 0
        patches_created_count = 0
        for texture, roads_polylines in roads_by_texture.items():
            texture_fitted, texture_patches = self._process_texture_roads(texture, roads_polylines)
            fitted_roads_count += texture_fitted
            patches_created_count += texture_patches

        self.info[Parameters.ROAD_INFO_TOTAL_FITTED] = fitted_roads_count
        self.info[Parameters.ROAD_INFO_TOTAL_PATCHES] = patches_created_count

    def _load_road_infos(self) -> list[dict[str, Any]] | None:
        """Load road polyline info records from context."""
        road_infos = self.get_infolayer_data(Parameters.TEXTURES, Parameters.ROADS_POLYLINES)
        if not road_infos:
            return None
        return [info for info in road_infos if isinstance(info, dict)]

    def _group_roads_by_texture(
        self,
        road_infos: list[dict[str, Any]],
    ) -> dict[str, list[dict[str, Any]]]:
        """Group road records by texture key."""
        roads_by_texture: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for road_info in road_infos:
            road_texture = road_info.get(Parameters.ROAD_TEXTURE)
            if isinstance(road_texture, str) and road_texture:
                roads_by_texture[road_texture].append(road_info)
        return roads_by_texture

    def _process_texture_roads(
        self,
        texture: str,
        roads_polylines: list[dict[str, Any]],
    ) -> tuple[int, int]:
        """Process roads for one texture and return (fitted_roads, created_patches)."""
        self.logger.debug("Processing roads with texture: %s", texture)
        road_entries = self._build_road_entries(roads_polylines)
        self.logger.debug("Total found for mesh generation: %d", len(road_entries))
        if not road_entries:
            return 0, 0

        interpolated_entries = self.smart_interpolation(road_entries)
        split_entries = self.split_long_line_surfaces(interpolated_entries)
        patch_entries = self.get_patches_linestrings(split_entries)
        split_entries.extend(patch_entries)
        self.generate_line_surface_mesh(split_entries, texture)
        return len(road_entries), len(patch_entries)

    def _build_road_entries(self, roads_polylines: list[dict[str, Any]]) -> list[LineSurfaceEntry]:
        """Convert raw road records to fitted linestring entries."""
        road_entries: list[LineSurfaceEntry] = []
        for road_id, road_info in enumerate(roads_polylines, start=1):
            road_entry = self._build_road_entry(road_info, road_id)
            if road_entry is not None:
                road_entries.append(road_entry)
        return road_entries

    def _build_road_entry(self, road_info: dict[str, Any], road_id: int) -> LineSurfaceEntry | None:
        """Build one fitted road entry from source info record."""
        points = road_info.get(Parameters.POINTS)
        width = road_info.get(Parameters.WIDTH)

        if not points or not isinstance(points, list) or len(points) < 2 or not width:
            self.logger.debug("Invalid road data for road ID %s: %s", road_id, road_info)
            return None

        try:
            fitted_road = self.fit_object_into_bounds(linestring_points=points, angle=self.rotation)
        except ValueError as e:
            self.logger.debug(
                "Road %s could not be fitted into the map bounds with error: %s",
                road_id,
                e,
            )
            return None

        try:
            linestring = shapely.LineString(fitted_road)
        except ValueError as e:
            self.logger.debug(
                "Road %s could not be converted to a LineString with error: %s",
                road_id,
                e,
            )
            return None

        return LineSurfaceEntry(linestring=linestring, width=int(width))

    def get_patches_linestrings(
        self, road_entries: list[LineSurfaceEntry]
    ) -> list[LineSurfaceEntry]:
        """Generate patch segments for T-junction intersections.

        This method identifies T-junctions where one road ends at another road,
        and creates patch segments from the continuous (main) road to overlay
        the intersection and prevent z-fighting.

        Arguments:
            road_entries (list[LineSurfaceEntry]): List of LineSurfaceEntry objects

        Returns:
            (list[LineSurfaceEntry]): List of patch LineSurfaceEntry objects to be added.
        """
        patches: list[LineSurfaceEntry] = []
        tolerance = Parameters.ROAD_INTERSECTION_TOLERANCE
        cumulative_offset = Parameters.PATCH_Z_OFFSET

        # Process each road to find T-junctions
        for idx, (road, _, _) in enumerate(road_entries):
            # Get the endpoints of this road
            start_point = Point(road.coords[0])
            end_point = Point(road.coords[-1])

            # Check if either endpoint intersects with another road's middle
            for other_idx, (other_road, other_width, other_z_offset) in enumerate(road_entries):
                if idx == other_idx:
                    continue

                # Check both endpoints
                for endpoint in [start_point, end_point]:
                    patch_entry, cumulative_offset = self._build_t_junction_patch(
                        endpoint,
                        other_road,
                        other_width,
                        other_z_offset,
                        cumulative_offset,
                        tolerance,
                    )
                    if patch_entry is None:
                        continue

                    patches.append(patch_entry)
                    self.logger.debug(
                        "Created patch for T-junction: road %d intersects road %d",
                        idx,
                        other_idx,
                    )

        self.logger.debug("Generated %d patch segments for T-junctions", len(patches))
        return patches

    def _build_t_junction_patch(
        self,
        endpoint: Point,
        other_road: shapely.LineString,
        other_width: int,
        other_z_offset: float,
        cumulative_offset: float,
        tolerance: float,
    ) -> tuple[LineSurfaceEntry | None, float]:
        """Build one patch entry for a T-junction endpoint, returning updated offset."""
        if endpoint.distance(other_road) >= tolerance:
            return None, cumulative_offset
        if self._is_other_road_endpoint(endpoint, other_road, tolerance):
            return None, cumulative_offset

        intersection_point = other_road.interpolate(other_road.project(endpoint))
        coords = list(other_road.coords)
        segment_idx = self._find_segment_index(coords, intersection_point, tolerance)
        if segment_idx is None:
            return None, cumulative_offset

        patch_coords = self._extract_patch_coords(coords, segment_idx)
        if patch_coords is None:
            return None, cumulative_offset

        try:
            patch_linestring = shapely.LineString(patch_coords)
        except Exception as e:
            self.logger.debug("Failed to create patch linestring: %s", e)
            return None, cumulative_offset

        patch_z_offset = other_z_offset + cumulative_offset
        next_offset = cumulative_offset + Parameters.PATCH_Z_OFFSET
        return (
            LineSurfaceEntry(
                linestring=patch_linestring,
                width=other_width,
                z_offset=patch_z_offset,
            ),
            next_offset,
        )

    @staticmethod
    def _is_other_road_endpoint(
        endpoint: Point, other_road: shapely.LineString, tolerance: float
    ) -> bool:
        """Return True when endpoint intersects near either end of the other road."""
        other_start = Point(other_road.coords[0])
        other_end = Point(other_road.coords[-1])
        return (
            endpoint.distance(other_start) < tolerance or endpoint.distance(other_end) < tolerance
        )

    @staticmethod
    def _find_segment_index(
        coords: list[tuple[float, float]],
        intersection_point: Point,
        tolerance: float,
    ) -> int | None:
        """Return index of segment that contains intersection point within tolerance."""
        for idx in range(len(coords) - 1):
            segment = shapely.LineString([coords[idx], coords[idx + 1]])
            if segment.distance(intersection_point) < tolerance:
                return idx
        return None

    @staticmethod
    def _extract_patch_coords(
        coords: list[tuple[float, float]],
        segment_idx: int,
    ) -> list[tuple[float, float]] | None:
        """Extract bounded patch coordinates around segment index."""
        padding = Parameters.ROAD_PATCH_SEGMENT_PADDING
        start_idx = max(0, segment_idx - padding)
        end_idx = min(len(coords) - 1, segment_idx + padding + 1)
        if end_idx - start_idx < 1:
            return None
        return coords[start_idx : end_idx + 1]

    def find_texture_file(self, templates_directory: str, texture_base_name: str) -> str:
        """Finds the texture file with supported extensions in the templates directory.

        Arguments:
            templates_directory (str): The directory where texture files are stored.
            texture_base_name (str): The base name of the texture file without extension.

        Returns:
            (str): The full path to the found texture file.
        """
        for ext in Parameters.ROAD_TEXTURE_EXTENSIONS:
            texture_path = os.path.join(templates_directory, texture_base_name + ext).lower()
            if os.path.isfile(texture_path):
                return texture_path
        raise FileNotFoundError(
            f"Texture file for base name {texture_base_name} not found in {templates_directory}."
        )

    def generate_line_surface_mesh(
        self, road_entries: list[LineSurfaceEntry], texture: str
    ) -> None:
        """Generates the road mesh from linestrings and saves it as an I3D asset.

        Arguments:
            road_entries (list[LineSurfaceEntry]): List of LineSurfaceEntry objects to generate the mesh from.
            texture (str): The base name of the texture file to use for the roads.
        """
        road_mesh_directory = os.path.join(self.map_directory, Parameters.ROADS_DIRECTORY, texture)
        os.makedirs(road_mesh_directory, exist_ok=True)

        try:
            texture_path = self.find_texture_file(Paths.TEMPLATES_DIR, texture)
        except FileNotFoundError as e:
            self.logger.warning("Texture file not found: %s", e)
            return

        dst_texture_path = os.path.join(
            road_mesh_directory,
            os.path.basename(texture_path),  # From templates/asphalt.png -> asphalt.png.
        )

        shutil.copyfile(texture_path, dst_texture_path)
        self.logger.debug("Texture copied to %s", dst_texture_path)

        obj_output_path = os.path.join(
            road_mesh_directory,
            f"{Parameters.ROAD_MESH_FILENAME_PREFIX}{texture}.obj",
        )
        mtl_output_path = os.path.join(
            road_mesh_directory,
            f"{Parameters.ROAD_MESH_FILENAME_PREFIX}{texture}.mtl",
        )

        self.create_textured_linestrings_mesh(
            road_entries=road_entries,
            obj_output_path=obj_output_path,
            mtl_output_path=mtl_output_path,
            texture_path=dst_texture_path,
        )

        # Load the mesh but preserve_order to maintain UV mapping
        mesh = trimesh.load_mesh(obj_output_path, force="mesh", process=False)
        rotation_matrix = trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0])
        mesh.apply_transform(rotation_matrix)

        vertices = mesh.vertices
        center = vertices.mean(axis=0)
        mesh.vertices = vertices - center

        # Save exact vertex centroid (post-rotation, pre-centering) for GE positioning.
        # center[0] = mean pixel X (east-west), center[2] = mean pixel Y (north-south)
        # after the 90° X-rotation that maps pixel Y -> mesh Z.
        self.map.context.set_mesh_position(
            texture,
            mesh_centroid_x=float(center[0]),
            mesh_centroid_y=float(center[1]),
            mesh_centroid_z=float(center[2]),
        )

        output_directory = os.path.join(
            self.map_directory,
            Parameters.ASSETS_DIRECTORY,
            Parameters.ROADS_DIRECTORY,
            texture,
        )
        os.makedirs(output_directory, exist_ok=True)

        self.mesh_to_i3d(
            mesh,
            output_directory,
            f"{Parameters.ROAD_MESH_FILENAME_PREFIX}{texture}",
            texture_path=dst_texture_path,
            # center_mesh=True,
        )

    def info_sequence(self) -> dict[str, Any]:
        """Returns information about the road processing as a dictionary.

        Returns:
            dict[str, Any]: Information about road processing.
        """
        return self.info
