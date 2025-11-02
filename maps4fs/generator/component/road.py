"""Component for map roads processing and generation."""

import os
import shutil
from collections import defaultdict
from typing import NamedTuple

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
        pass

    def process(self) -> None:
        road_infos = self.get_infolayer_data(Parameters.TEXTURES, Parameters.ROADS_POLYLINES)
        if not road_infos:
            self.logger.warning("Roads polylines data not found in textures info layer.")
            return

        roads_by_texture = defaultdict(list)
        for road_info in road_infos:  # type: ignore
            road_texture = road_info.get("road_texture")
            if road_texture:
                roads_by_texture[road_texture].append(road_info)

        for texture, roads_polylines in roads_by_texture.items():
            self.logger.info("Processing roads with texture: %s", texture)

            # The texture name is represents the name of texture file without extension
            # for easy reference if the texture uses various extensions.
            # E.g. 'asphalt', 'gravel' -> 'asphalt.png', 'gravel.jpg', etc.
            texture: str = texture.lower()

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

            self.logger.info("Total found for mesh generation: %d", len(road_entries))

            if road_entries:
                patches_road_entries: list[RoadEntry] = self.get_patches_linestrings(road_entries)
                road_entries.extend(patches_road_entries)
                self.generate_road_mesh(road_entries, texture)

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

        self.logger.info("Generated %d patch segments for T-junctions", len(patches))
        return patches

    def find_texture_file(self, templates_directory: str, texture_base_name: str) -> str:
        for ext in [".png", ".jpg", ".jpeg"]:
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
        self.logger.info("Texture copied to %s", dst_texture_path)

        obj_output_path = os.path.join(road_mesh_directory, f"roads_{texture}.obj")
        mtl_output_path = os.path.join(road_mesh_directory, f"roads_{texture}.mtl")

        self.create_textured_linestrings_mesh(
            road_entries=road_entries,
            texture_path=dst_texture_path,
            obj_output_path=obj_output_path,
            mtl_output_path=mtl_output_path,
        )

        mesh = trimesh.load_mesh(obj_output_path, force="mesh")
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
        not_resized_dem = self.get_not_resized_dem_with_flattened_roads()
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
        self.logger.info(
            "Creating mesh for %d roads (%d patches with z-offset)",
            len(road_entries),
            patches_count,
        )

        for linestring, width, z_offset in road_entries:
            coords = list(linestring.coords)
            if len(coords) < 2:
                continue

            # Generate road strip vertices
            segment_vertices = []
            segment_uvs = []
            accumulated_distance = 0.0

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

                # Calculate UV coordinates
                # U coordinate: 0 for left edge, 1 for right edge
                # V coordinate: based on accumulated distance along the road
                if i > 0:
                    segment_distance = np.sqrt(
                        (coords[i][0] - coords[i - 1][0]) ** 2
                        + (coords[i][1] - coords[i - 1][1]) ** 2
                    )
                    accumulated_distance += segment_distance

                v_coord = accumulated_distance / texture_tile_size

                # Add UVs for left and right vertices
                segment_uvs.append((0.0, v_coord))  # Left edge
                segment_uvs.append((1.0, v_coord))  # Right edge

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

        self.logger.info("MTL file written to %s", mtl_output_path)

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

        self.logger.info(
            "OBJ file written to %s with %d vertices and %d faces",
            obj_output_path,
            len(vertices),
            len(faces),
        )

    def info_sequence(self):
        return {}
