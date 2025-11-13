"""Component for map roads processing and generation."""

import os
import shutil
from collections import defaultdict
from typing import Any, NamedTuple

import numpy as np
import shapely
import trimesh
from shapely.geometry import Point

import maps4fs.generator.config as mfscfg
from maps4fs.generator.component.base.component_mesh import MeshComponent
from maps4fs.generator.component.i3d import I3d
from maps4fs.generator.settings import Parameters

PATCH_Z_OFFSET = -0.001


class RoadEntry(NamedTuple):
    """Data structure representing a road entry with its linestring, width, and optional z-offset."""

    linestring: shapely.LineString
    width: int
    z_offset: float = 0.0


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

            road_entries: list[RoadEntry] = []
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

                road_entries.append(RoadEntry(linestring=linestring, width=width))

            self.logger.debug("Total found for mesh generation: %d", len(road_entries))

            if road_entries:
                fitted_roads_count += len(road_entries)
                # 1. Apply smart interpolation to make linestrings smoother,
                # but carefully, ensuring that points are not too close to each other.
                # Otherwise it may lead to artifacts in the mesh.
                interpolated_road_entries: list[RoadEntry] = self.smart_interpolation(road_entries)

                # 2. Split roads that exceed Giants Engine's UV coordinate limits
                # Giants Engine requires UV coordinates in [-32, 32] range
                split_road_entries: list[RoadEntry] = self.split_long_roads(
                    interpolated_road_entries
                )

                patches_road_entries: list[RoadEntry] = self.get_patches_linestrings(
                    split_road_entries
                )
                patches_created_count += len(patches_road_entries)
                split_road_entries.extend(patches_road_entries)
                self.generate_road_mesh(split_road_entries, texture)

        self.info["total_fitted_roads"] = fitted_roads_count
        self.info["total_patches_created"] = patches_created_count

    def smart_interpolation(self, road_entries: list[RoadEntry]) -> list[RoadEntry]:
        """Apply smart interpolation to road linestrings.
        Making sure that result polylines do not have points too close to each other.

        Arguments:
            road_entries (list[RoadEntry]): List of RoadEntry objects

        Returns:
            (list[RoadEntry]): List of RoadEntry objects with interpolated linestrings.
        """
        interpolated_entries = []
        target_segment_length = 5  # Target distance between points in meters (denser)
        max_angle_change = 30.0  # Maximum angle change in degrees to allow interpolation

        for linestring, width, z_offset in road_entries:
            coords = list(linestring.coords)
            if len(coords) < 2:
                interpolated_entries.append(RoadEntry(linestring, width, z_offset))
                continue

            # Check if road has sharp curves - if so, skip interpolation
            has_sharp_curves = False
            if len(coords) >= 3:
                for i in range(1, len(coords) - 1):
                    # Calculate angle change at this point
                    v1_x = coords[i][0] - coords[i - 1][0]
                    v1_y = coords[i][1] - coords[i - 1][1]
                    v2_x = coords[i + 1][0] - coords[i][0]
                    v2_y = coords[i + 1][1] - coords[i][1]

                    # Calculate angle between vectors
                    dot = v1_x * v2_x + v1_y * v2_y
                    len1 = np.sqrt(v1_x**2 + v1_y**2)
                    len2 = np.sqrt(v2_x**2 + v2_y**2)

                    if len1 > 0 and len2 > 0:
                        cos_angle = np.clip(dot / (len1 * len2), -1.0, 1.0)
                        angle_deg = np.degrees(np.arccos(cos_angle))

                        if angle_deg > max_angle_change:
                            has_sharp_curves = True
                            break

            if has_sharp_curves:
                # Skip interpolation for curved roads
                interpolated_entries.append(RoadEntry(linestring, width, z_offset))
                continue

            # Check if interpolation is needed
            needs_interpolation = False
            for i in range(len(coords) - 1):
                segment_length = np.sqrt(
                    (coords[i + 1][0] - coords[i][0]) ** 2 + (coords[i + 1][1] - coords[i][1]) ** 2
                )
                if segment_length > target_segment_length * 1.5:
                    needs_interpolation = True
                    break

            if not needs_interpolation:
                # Road is already dense enough
                interpolated_entries.append(RoadEntry(linestring, width, z_offset))
                continue

            # Perform interpolation using shapely's interpolate (follows curves)
            road_length = linestring.length
            num_points = int(np.ceil(road_length / target_segment_length)) + 1

            new_coords = []
            for i in range(num_points):
                distance = min(i * target_segment_length, road_length)
                point = linestring.interpolate(distance)
                new_coords.append((point.x, point.y))

            # Ensure last point is exact
            if new_coords[-1] != coords[-1]:
                new_coords.append(coords[-1])

            # Create new linestring with interpolated coordinates
            # No cleanup needed - interpolation already creates evenly spaced points
            try:
                interpolated_linestring = shapely.LineString(new_coords)
                interpolated_entries.append(RoadEntry(interpolated_linestring, width, z_offset))
            except Exception as e:
                self.logger.warning(
                    "Failed to create interpolated linestring: %s. Using original.", e
                )
                interpolated_entries.append(RoadEntry(linestring, width, z_offset))

        self.logger.debug(
            "Smart interpolation complete. Processed %d roads.", len(interpolated_entries)
        )
        return interpolated_entries

    def split_long_roads(
        self, road_entries: list[RoadEntry], texture_tile_size: float = 10.0
    ) -> list[RoadEntry]:
        """Split roads that exceed Giants Engine's UV coordinate limits.

        Giants Engine requires UV coordinates to be in [-32, 32] range.
        Roads longer than 32 * texture_tile_size meters need to be split.

        Arguments:
            road_entries (list[RoadEntry]): List of RoadEntry objects
            texture_tile_size (float): Size of texture tile in meters

        Returns:
            (list[RoadEntry]): List of RoadEntry objects with long roads split.
        """
        max_road_length = 30.0 * texture_tile_size  # Use 30 instead of 32 for safety margin
        split_entries = []

        for linestring, width, z_offset in road_entries:
            road_length = linestring.length

            if road_length <= max_road_length:
                # Road is short enough, keep as is
                split_entries.append(RoadEntry(linestring, width, z_offset))
                continue

            # Road is too long, split it into segments
            num_segments = int(np.ceil(road_length / max_road_length))
            segment_length = road_length / num_segments

            self.logger.debug(
                "Splitting road (%.2fm) into %d segments of ~%.2fm each",
                road_length,
                num_segments,
                segment_length,
            )

            for i in range(num_segments):
                start_distance = i * segment_length
                end_distance = min((i + 1) * segment_length, road_length)

                # Extract segment using shapely's substring
                try:
                    segment_linestring = shapely.ops.substring(
                        linestring, start_distance, end_distance, normalized=False
                    )
                    split_entries.append(RoadEntry(segment_linestring, width, z_offset))
                    self.logger.debug(
                        "  Segment %d: %.2fm to %.2fm (length: %.2fm)",
                        i,
                        start_distance,
                        end_distance,
                        segment_linestring.length,
                    )
                except Exception as e:
                    self.logger.warning("Failed to split road segment %d: %s", i, e)

        self.logger.debug(
            "Road splitting complete: %d roads -> %d segments",
            len(road_entries),
            len(split_entries),
        )
        return split_entries

    def get_patches_linestrings(self, road_entries: list[RoadEntry]) -> list[RoadEntry]:
        """Generate patch segments for T-junction intersections.

        This method identifies T-junctions where one road ends at another road,
        and creates patch segments from the continuous (main) road to overlay
        the intersection and prevent z-fighting.

        Arguments:
            road_entries (list[RoadEntry]): List of RoadEntry objects

        Returns:
            (list[RoadEntry]): List of patch RoadEntry objects to be added.
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
                            path_road_entry = RoadEntry(
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

    def generate_road_mesh(self, road_entries: list[RoadEntry], texture: str) -> None:
        """Generates the road mesh from linestrings and saves it as an I3D asset.

        Arguments:
            road_entries (list[RoadEntry]): List of RoadEntry objects to generate the mesh from.
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
            texture_path=dst_texture_path,
            obj_output_path=obj_output_path,
            mtl_output_path=mtl_output_path,
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

    def create_textured_linestrings_mesh(
        self,
        road_entries: list[RoadEntry],
        texture_path: str,
        obj_output_path: str,
        mtl_output_path: str,
    ) -> None:
        """Creates a textured mesh from linestrings with varying widths.

        This method generates a 3D mesh for roads by:
        1. Creating rectangular strips along each linestring based on its width
        2. Applying proper UV mapping for tiled texture along the road length
        3. Exporting the mesh to OBJ format with corresponding MTL material file

        Arguments:
            linestrings: List of tuples containing (shapely.LineString, width in meters)
            texture_path: Path to the texture image file to apply
            obj_output_path: Output path for the OBJ mesh file
            mtl_output_path: Output path for the MTL material file
        """
        # Use the not resized DEM with flattened roads to get accurate Z values
        # for the road mesh vertices.
        not_resized_dem = self.get_dem_image_with_fallback()
        if not_resized_dem is None:
            self.logger.warning(
                "Not resized DEM with flattened roads is not available. "
                "Cannot generate road mesh."
            )
            return

        vertices = []
        faces = []
        uvs = []
        vertex_offset = 0

        texture_tile_size = 10.0  # meters - how many meters before texture repeats

        patches_count = sum(1 for entry in road_entries if entry.z_offset > 0)
        self.logger.debug(
            "Creating mesh for %d roads (%d patches with z-offset)",
            len(road_entries),
            patches_count,
        )

        for _, (linestring, width, z_offset) in enumerate(road_entries):
            coords = list(linestring.coords)
            if len(coords) < 2:
                continue

            # Generate road strip vertices
            segment_vertices = []
            segment_uvs = []
            accumulated_distance = 0.0
            prev_center_3d: tuple[float, float, float] | None = (
                None  # Track previous center point in 3D
            )

            for i in range(len(coords)):  # pylint: disable=consider-using-enumerate
                x, y = coords[i]

                # Calculate direction vector for perpendicular offset
                if i == 0:
                    # First point: use direction to next point
                    dx = coords[i + 1][0] - coords[i][0]
                    dy = coords[i + 1][1] - coords[i][1]
                elif i == len(coords) - 1:
                    # Last point: use direction from previous point
                    dx = coords[i][0] - coords[i - 1][0]
                    dy = coords[i][1] - coords[i - 1][1]
                else:
                    # Middle points: average direction
                    dx1 = coords[i][0] - coords[i - 1][0]
                    dy1 = coords[i][1] - coords[i - 1][1]
                    dx2 = coords[i + 1][0] - coords[i][0]
                    dy2 = coords[i + 1][1] - coords[i][1]
                    dx = (dx1 + dx2) / 2.0
                    dy = (dy1 + dy2) / 2.0

                # Normalize direction and get perpendicular
                length = np.sqrt(dx * dx + dy * dy)
                if length > 0:
                    dx /= length
                    dy /= length

                # Perpendicular vector (rotated 90 degrees)
                perp_x = -dy
                perp_y = dx

                exact_z_value = self.get_z_coordinate_from_dem(not_resized_dem, x, y)
                offsetted_z = -exact_z_value + z_offset

                # Create left and right vertices with z-offset
                left_vertex = (x + perp_x * width, y + perp_y * width, offsetted_z)
                right_vertex = (x - perp_x * width, y - perp_y * width, offsetted_z)

                segment_vertices.append(left_vertex)
                segment_vertices.append(right_vertex)

                # Calculate UV coordinates based on 3D distance (including Z changes)
                # U coordinate: 0 for left edge, 1 for right edge
                # V coordinate: based on accumulated 3D distance along the road
                segment_distance_3d = 0.0
                current_center_3d = (x, y, offsetted_z)

                # pylint: disable=unsubscriptable-object
                if i > 0 and prev_center_3d is not None:
                    # Calculate both 2D and 3D distances for comparison
                    segment_distance_3d = np.sqrt(
                        (current_center_3d[0] - prev_center_3d[0]) ** 2
                        + (current_center_3d[1] - prev_center_3d[1]) ** 2
                        + (current_center_3d[2] - prev_center_3d[2]) ** 2
                    )
                    accumulated_distance += segment_distance_3d

                prev_center_3d = current_center_3d

                # Calculate V coordinate - divide by texture tile size
                v_coord_raw = accumulated_distance / texture_tile_size

                # Store raw V coordinate for now - we'll apply modulo to the entire road later
                segment_uvs.append((0.0, v_coord_raw))  # Left edge
                segment_uvs.append((1.0, v_coord_raw))  # Right edge

            # Add vertices and UVs to global lists
            vertices.extend(segment_vertices)
            uvs.extend(segment_uvs)

            # Create faces (triangles) for the road strip
            num_segments = len(coords) - 1
            for i in range(num_segments):
                # Each segment creates 2 triangles (a quad)
                # Vertex indices for this segment
                v0 = vertex_offset + i * 2  # Left vertex of current segment
                v1 = vertex_offset + i * 2 + 1  # Right vertex of current segment
                v2 = vertex_offset + (i + 1) * 2  # Left vertex of next segment
                v3 = vertex_offset + (i + 1) * 2 + 1  # Right vertex of next segment

                # First triangle (counter-clockwise winding)
                faces.append((v0, v2, v1))
                # Second triangle
                faces.append((v1, v2, v3))

            vertex_offset += len(segment_vertices)

        if not vertices:
            self.logger.warning("No vertices generated for road mesh.")
            return

        # Write MTL file
        mtl_filename = os.path.basename(mtl_output_path)
        texture_filename = os.path.basename(texture_path)

        with open(mtl_output_path, "w", encoding="utf-8") as mtl_file:
            mtl_file.write("# Road material\n")
            mtl_file.write("newmtl RoadMaterial\n")
            mtl_file.write("Ka 1.0 1.0 1.0\n")  # Ambient color
            mtl_file.write("Kd 1.0 1.0 1.0\n")  # Diffuse color
            mtl_file.write("Ks 0.3 0.3 0.3\n")  # Specular color
            mtl_file.write("Ns 10.0\n")  # Specular exponent
            mtl_file.write("illum 2\n")  # Illumination model
            mtl_file.write(f"map_Kd {texture_filename}\n")  # Diffuse texture map

        self.logger.debug("MTL file written to %s", mtl_output_path)

        # Write OBJ file
        with open(obj_output_path, "w", encoding="utf-8") as obj_file:
            obj_file.write("# Road mesh generated by maps4fs\n")
            obj_file.write(f"mtllib {mtl_filename}\n\n")

            # Write vertices
            obj_file.write(f"# {len(vertices)} vertices\n")
            for v in vertices:
                obj_file.write(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n")

            # Write UV coordinates
            obj_file.write(f"\n# {len(uvs)} texture coordinates\n")
            for uv in uvs:
                obj_file.write(f"vt {uv[0]:.6f} {uv[1]:.6f}\n")

            # Write faces with material
            obj_file.write(f"\n# {len(faces)} faces\n")
            obj_file.write("usemtl RoadMaterial\n")
            for face in faces:
                # OBJ format uses 1-based indexing
                # Format: f v1/vt1 v2/vt2 v3/vt3
                obj_file.write(
                    f"f {face[0] + 1}/{face[0] + 1} "
                    f"{face[1] + 1}/{face[1] + 1} "
                    f"{face[2] + 1}/{face[2] + 1}\n"
                )

        self.logger.debug(
            "OBJ file written to %s with %d vertices and %d faces",
            obj_output_path,
            len(vertices),
            len(faces),
        )

    def info_sequence(self) -> dict[str, Any]:
        """Returns information about the road processing as a dictionary.

        Returns:
            dict[str, Any]: Information about road processing.
        """
        return self.info
