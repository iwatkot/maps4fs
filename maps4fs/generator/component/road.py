"""Component for map roads processing and generation."""

import os
import shutil
from collections import defaultdict
from typing import Any

import numpy as np
import shapely
import trimesh
from shapely.geometry import Point

import maps4fs.generator.config as mfscfg
from maps4fs.generator.component.base.component_mesh import (
    LineSurfaceEntry,
    MeshComponent,
)
from maps4fs.generator.component.i3d import I3d
from maps4fs.generator.settings import Parameters

PATCH_Z_OFFSET = -0.001


class Road(I3d, MeshComponent):
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

    def process(self):
        """Process and generate roads for the map."""
        try:
            self.generate_roads()
        except Exception as e:
            self.logger.error("Error during road generation: %s", e)

    def generate_roads(self) -> None:
        """Generate roads for the map based on the info layer data."""
        road_infos = self.get_infolayer_data(Parameters.TEXTURES, Parameters.ROADS_POLYLINES)
        if not road_infos:
            self.logger.warning("Roads polylines data not found in textures info layer.")
            return

        roads_by_texture = defaultdict(list)
        for road_info in road_infos:  # type: ignore
            road_texture = road_info.get("road_texture")
            if road_texture:
                roads_by_texture[road_texture].append(road_info)

        self.info["road_textures"] = list(roads_by_texture.keys())
        self.info["total_OSM_roads"] = len(road_infos)

        fitted_roads_count = 0
        patches_created_count = 0
        for texture, roads_polylines in roads_by_texture.items():
            self.logger.debug("Processing roads with texture: %s", texture)

            # The texture name is represents the name of texture file without extension
            # for easy reference if the texture uses various extensions.
            # E.g. 'asphalt', 'gravel' -> 'asphalt.png', 'gravel.jpg', etc.

            road_entries: list[LineSurfaceEntry] = []
            for road_id, road_info in enumerate(roads_polylines, start=1):  # type: ignore
                if isinstance(road_info, dict):
                    points: list[int | float] = road_info.get("points")  # type: ignore
                    width: int = road_info.get("width")  # type: ignore
                else:
                    continue

                if not points or len(points) < 2 or not width:
                    self.logger.debug("Invalid road data for road ID %s: %s", road_id, road_info)
                    continue

                try:
                    fitted_road = self.fit_object_into_bounds(
                        linestring_points=points, angle=self.rotation  # type: ignore
                    )
                except ValueError as e:
                    self.logger.debug(
                        "Road %s could not be fitted into the map bounds with error: %s",
                        road_id,
                        e,
                    )
                    continue

                try:
                    linestring = shapely.LineString(fitted_road)
                except ValueError as e:
                    self.logger.debug(
                        "Road %s could not be converted to a LineString with error: %s",
                        road_id,
                        e,
                    )
                    continue

                road_entries.append(LineSurfaceEntry(linestring=linestring, width=width))

            self.logger.debug("Total found for mesh generation: %d", len(road_entries))

            if road_entries:
                fitted_roads_count += len(road_entries)
                # 1. Apply smart interpolation to make linestrings smoother,
                # but carefully, ensuring that points are not too close to each other.
                # Otherwise it may lead to artifacts in the mesh.
                interpolated_road_entries: list[LineSurfaceEntry] = self.smart_interpolation(
                    road_entries
                )

                # 2. Split line surfaces that exceed Giants Engine's UV coordinate limits
                # Giants Engine requires UV coordinates in [-32, 32] range
                split_line_surface_entries: list[LineSurfaceEntry] = self.split_long_line_surfaces(
                    interpolated_road_entries
                )

                patches_line_surface_entries: list[LineSurfaceEntry] = self.get_patches_linestrings(
                    split_line_surface_entries
                )
                patches_created_count += len(patches_line_surface_entries)
                split_line_surface_entries.extend(patches_line_surface_entries)
                self.generate_line_surface_mesh(split_line_surface_entries, texture)

        self.info["total_fitted_roads"] = fitted_roads_count
        self.info["total_patches_created"] = patches_created_count

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
        patches = []
        tolerance = 1.0  # Distance tolerance for endpoint intersection detection
        cumulative_offset = PATCH_Z_OFFSET

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
                    # Check if endpoint is near the other road (but not at its endpoints)
                    distance = endpoint.distance(other_road)

                    if distance < tolerance:
                        # This is a potential T-junction
                        # Make sure it's not connecting at the other road's endpoints
                        other_start = Point(other_road.coords[0])
                        other_end = Point(other_road.coords[-1])

                        # Skip if connecting at endpoints (this is a proper intersection, not T)
                        if (
                            endpoint.distance(other_start) < tolerance
                            or endpoint.distance(other_end) < tolerance
                        ):
                            continue

                        # Find the closest point on the other road
                        intersection_point = other_road.interpolate(other_road.project(endpoint))

                        # Find which segment of other_road contains this intersection
                        coords = list(other_road.coords)
                        segment_idx = None

                        for i in range(len(coords) - 1):
                            segment = shapely.LineString([coords[i], coords[i + 1]])
                            if segment.distance(intersection_point) < tolerance:
                                segment_idx = i
                                break

                        if segment_idx is None:
                            continue

                        # Create patch: take 2 points before and 2 points after the intersection
                        # Ensure we don't go out of bounds
                        start_idx = max(0, segment_idx - 2)
                        end_idx = min(len(coords) - 1, segment_idx + 3)

                        # Need at least 2 points for a valid linestring
                        if end_idx - start_idx < 1:
                            continue

                        # Extract the patch segment
                        patch_coords = coords[start_idx : end_idx + 1]

                        try:
                            patch_linestring = shapely.LineString(patch_coords)
                            patch_z_offset = other_z_offset + cumulative_offset
                            cumulative_offset += PATCH_Z_OFFSET
                            path_road_entry = LineSurfaceEntry(
                                linestring=patch_linestring,
                                width=other_width,
                                z_offset=patch_z_offset,
                            )
                            patches.append(path_road_entry)
                            self.logger.debug(
                                "Created patch for T-junction: road %d intersects road %d",
                                idx,
                                other_idx,
                            )
                        except Exception as e:
                            self.logger.debug("Failed to create patch linestring: %s", e)
                            continue

        self.logger.debug("Generated %d patch segments for T-junctions", len(patches))
        return patches

    def find_texture_file(self, templates_directory: str, texture_base_name: str) -> str:
        """Finds the texture file with supported extensions in the templates directory.

        Arguments:
            templates_directory (str): The directory where texture files are stored.
            texture_base_name (str): The base name of the texture file without extension.

        Returns:
            (str): The full path to the found texture file.
        """
        for ext in [".png", ".jpg", ".jpeg", ".dds"]:
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
        road_mesh_directory = os.path.join(self.map_directory, "roads", texture)
        os.makedirs(road_mesh_directory, exist_ok=True)

        try:
            texture_path = self.find_texture_file(mfscfg.MFS_TEMPLATES_DIR, texture)
        except FileNotFoundError as e:
            self.logger.warning("Texture file not found: %s", e)
            return

        dst_texture_path = os.path.join(
            road_mesh_directory,
            os.path.basename(texture_path),  # From templates/asphalt.png -> asphalt.png.
        )

        shutil.copyfile(texture_path, dst_texture_path)
        self.logger.debug("Texture copied to %s", dst_texture_path)

        obj_output_path = os.path.join(road_mesh_directory, f"roads_{texture}.obj")
        mtl_output_path = os.path.join(road_mesh_directory, f"roads_{texture}.mtl")

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

        output_directory = os.path.join(self.map_directory, "assets", "roads", texture)
        os.makedirs(output_directory, exist_ok=True)

        self.mesh_to_i3d(mesh, output_directory, f"roads_{texture}", texture_path=dst_texture_path)

    def info_sequence(self) -> dict[str, Any]:
        """Returns information about the road processing as a dictionary.

        Returns:
            dict[str, Any]: Information about road processing.
        """
        return self.info
