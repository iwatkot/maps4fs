"""Component for map roads processing and generation."""

from __future__ import annotations

import os
import shutil
from collections import defaultdict
from typing import Any

import numpy as np
import shapely
import trimesh
from shapely.geometry import GeometryCollection, MultiPolygon, Point, Polygon

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
        self.generate_line_surface_mesh(split_entries, texture)
        return len(road_entries), 0

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

        mesh_created = self.create_connected_road_network_mesh(
            road_entries=road_entries,
            obj_output_path=obj_output_path,
            mtl_output_path=mtl_output_path,
            texture_path=dst_texture_path,
        )

        if not mesh_created or not os.path.isfile(obj_output_path):
            self.logger.warning("Connected road mesh was not created for texture: %s", texture)
            return

        # Load the mesh but preserve_order to maintain UV mapping
        mesh = trimesh.load_mesh(obj_output_path, force="mesh", process=False)
        rotation_matrix = trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0])
        mesh.apply_transform(rotation_matrix)

        # Keep road normals facing upward in engine space.
        if len(mesh.face_normals) > 0 and float(np.mean(mesh.face_normals[:, 1])) < 0.0:
            mesh.invert()

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

    def create_connected_road_network_mesh(
        self,
        road_entries: list[LineSurfaceEntry],
        obj_output_path: str,
        mtl_output_path: str | None = None,
        texture_path: str | None = None,
    ) -> bool:
        """Create one connected road-network mesh for all line entries.

        The generated mesh shares intersection geometry and adapts to terrain
        by triangulating a single unioned road surface.
        """
        dem_image = self.get_dem_image_with_fallback()
        if dem_image is None:
            self.logger.warning("DEM is not available. Cannot generate connected road mesh.")
            return False

        road_surface = self._build_connected_road_surface(road_entries)
        if road_surface is None or road_surface.is_empty:
            self.logger.warning("Connected road surface is empty.")
            return False

        vertices, faces, uvs = self._triangulate_road_surface(
            road_surface=road_surface,
            dem_image=dem_image,
            road_entries=road_entries,
        )
        if not vertices or not faces:
            self.logger.warning("No triangles produced for connected road mesh.")
            return False

        if mtl_output_path and texture_path:
            self._write_road_mtl(mtl_output_path, texture_path)

        mtl_filename = os.path.basename(mtl_output_path) if mtl_output_path else None
        with open(obj_output_path, "w", encoding="utf-8") as obj_file:
            obj_file.write("# Connected road mesh generated by maps4fs\n")
            if mtl_filename:
                obj_file.write(f"mtllib {mtl_filename}\n\n")

            for vertex in vertices:
                obj_file.write(f"v {vertex[0]:.6f} {vertex[1]:.6f} {vertex[2]:.6f}\n")
            for uv in uvs:
                obj_file.write(f"vt {uv[0]:.6f} {uv[1]:.6f}\n")

            if mtl_filename:
                obj_file.write(f"usemtl {Parameters.ROAD_MATERIAL_NAME}\n")

            for face in faces:
                v1, v2, v3 = [idx + Parameters.OBJ_INDEX_OFFSET for idx in face]
                obj_file.write(f"f {v1}/{v1} {v2}/{v2} {v3}/{v3}\n")

        self.logger.debug(
            "Connected road mesh written to %s with %d vertices and %d faces",
            obj_output_path,
            len(vertices),
            len(faces),
        )
        return True

    def _build_connected_road_surface(
        self,
        road_entries: list[LineSurfaceEntry],
    ) -> Polygon | MultiPolygon | None:
        """Build a unioned polygonal road surface from centerline entries."""
        buffered_geometries: list[Polygon] = []

        for linestring, width, _ in road_entries:
            if linestring.is_empty or linestring.length <= 0:
                continue

            dense_coords = self._densify_linestring_coords(
                linestring,
                target_segment_length=Parameters.INTERPOLATION_TARGET_SEGMENT_LENGTH,
            )
            if len(dense_coords) < 2:
                continue

            dense_line = shapely.LineString(dense_coords)
            safe_width = max(float(width), 0.5)
            try:
                buffered = dense_line.buffer(
                    safe_width,
                    cap_style=2,
                    join_style=1,
                )
            except Exception as e:
                self.logger.debug("Failed to buffer road line: %s", e)
                continue

            if buffered.is_empty:
                continue
            buffered_geometries.extend(self._extract_polygons(buffered))

        if not buffered_geometries:
            return None

        try:
            unioned = shapely.unary_union(buffered_geometries)
        except Exception as e:
            self.logger.warning("Failed to union buffered roads: %s", e)
            return None

        if not unioned.is_valid:
            try:
                unioned = shapely.make_valid(unioned)
            except Exception:
                pass

        polygons = self._extract_polygons(unioned)
        if not polygons:
            return None

        merged = shapely.unary_union(polygons)
        if merged.is_empty:
            return None

        if isinstance(merged, (Polygon, MultiPolygon)):
            return merged

        merged_polygons = self._extract_polygons(merged)
        if not merged_polygons:
            return None

        if len(merged_polygons) == 1:
            return merged_polygons[0]
        return shapely.MultiPolygon(merged_polygons)

    def _triangulate_road_surface(
        self,
        road_surface: Polygon | MultiPolygon,
        dem_image: np.ndarray,
        road_entries: list[LineSurfaceEntry],
    ) -> tuple[
        list[tuple[float, float, float]],
        list[tuple[int, int, int]],
        list[tuple[float, float]],
    ]:
        """Triangulate the connected road surface and sample DEM height per vertex."""
        polygons = self._extract_polygons(road_surface)
        if not polygons:
            return [], [], []

        sampling_step = self._get_network_sampling_step(road_entries)

        xy_points: dict[tuple[int, int], tuple[float, float]] = {}
        for polygon in polygons:
            self._add_ring_points(xy_points, polygon.exterior.coords)
            for interior in polygon.interiors:
                self._add_ring_points(xy_points, interior.coords)
            representative = polygon.representative_point()
            self._add_point(xy_points, float(representative.x), float(representative.y))

        self._add_centerline_points(
            points=xy_points,
            road_entries=road_entries,
            road_surface=road_surface,
            sampling_step=sampling_step,
        )

        if len(xy_points) < 3:
            return [], [], []

        point_cloud = shapely.MultiPoint(list(xy_points.values()))
        raw_triangles = shapely.ops.triangulate(point_cloud)
        if not raw_triangles:
            return [], [], []

        vertices: list[tuple[float, float, float]] = []
        faces: list[tuple[int, int, int]] = []
        uvs: list[tuple[float, float]] = []
        vertex_index: dict[tuple[int, int], int] = {}
        tile_size = max(Parameters.TEXTURE_TILE_SIZE_METERS, 1.0)
        uv_sources = [
            (entry.linestring, max(float(entry.width), 1.0))
            for entry in road_entries
            if not entry.linestring.is_empty and entry.linestring.length > 0
        ]

        for triangle in raw_triangles:
            if triangle.is_empty or triangle.area <= 0.0:
                continue

            representative = triangle.representative_point()
            if not road_surface.covers(representative):
                continue

            coords = [(float(x), float(y)) for x, y in list(triangle.exterior.coords)[:3]]
            # Keep triangles clockwise in XY so after +90deg X-rotation normals face +Y.
            if self._signed_triangle_area(coords) > 0.0:
                coords[1], coords[2] = coords[2], coords[1]

            face_indices: list[int] = []
            for x, y in coords:
                key = self._point_key(x, y)
                idx = vertex_index.get(key)
                if idx is None:
                    z = -float(self.get_z_coordinate_from_dem(dem_image, x, y))
                    idx = len(vertices)
                    vertex_index[key] = idx
                    vertices.append((x, y, z))
                    uvs.append(self._compute_vertex_uv(x, y, uv_sources, tile_size))
                face_indices.append(idx)

            if len(set(face_indices)) != 3:
                continue
            faces.append((face_indices[0], face_indices[1], face_indices[2]))

        return vertices, faces, uvs

    def _compute_vertex_uv(
        self,
        x: float,
        y: float,
        uv_sources: list[tuple[shapely.LineString, float]],
        tile_size: float,
    ) -> tuple[float, float]:
        """Map UVs using the nearest road centerline like strip-based generation."""
        if not uv_sources:
            return (x / tile_size, y / tile_size)

        point = Point(x, y)
        best_line: shapely.LineString | None = None
        best_width = 1.0
        best_distance = float("inf")

        for linestring, width in uv_sources:
            distance = float(linestring.distance(point))
            if distance < best_distance:
                best_distance = distance
                best_line = linestring
                best_width = width

        if best_line is None:
            return (x / tile_size, y / tile_size)

        along = float(best_line.project(point))
        signed_lateral = self._signed_lateral_distance(best_line, point, along, best_distance)

        u = float(np.clip(0.5 + (signed_lateral / max(best_width, 1.0)), 0.0, 1.0))
        v = along / tile_size
        return (u, v)

    @staticmethod
    def _signed_lateral_distance(
        linestring: shapely.LineString,
        point: Point,
        along: float,
        absolute_distance: float,
    ) -> float:
        """Return signed lateral distance of a point relative to local line tangent."""
        line_length = float(linestring.length)
        if line_length <= 0.0:
            return 0.0

        epsilon = min(1.0, max(line_length * 0.01, 0.01))
        start_d = max(0.0, along - epsilon)
        end_d = min(line_length, along + epsilon)

        p0 = linestring.interpolate(start_d)
        p1 = linestring.interpolate(end_d)

        dx = float(p1.x - p0.x)
        dy = float(p1.y - p0.y)
        tangent_len = float(np.hypot(dx, dy))
        if tangent_len <= 1e-9:
            return 0.0

        nearest = linestring.interpolate(along)
        vx = float(point.x - nearest.x)
        vy = float(point.y - nearest.y)
        cross_z = dx * vy - dy * vx
        sign = 1.0 if cross_z >= 0.0 else -1.0
        return sign * absolute_distance

    def _get_network_sampling_step(self, road_entries: list[LineSurfaceEntry]) -> float:
        """Choose interior triangulation sampling step from source road widths."""
        widths = [max(float(entry.width), 1.0) for entry in road_entries]
        if not widths:
            return Parameters.INTERPOLATION_TARGET_SEGMENT_LENGTH

        median_width = float(np.median(widths))
        return float(np.clip(median_width, 2.0, 8.0))

    def _add_centerline_points(
        self,
        points: dict[tuple[int, int], tuple[float, float]],
        road_entries: list[LineSurfaceEntry],
        road_surface: Polygon | MultiPolygon,
        sampling_step: float,
    ) -> None:
        """Add interior samples along original centerlines to improve terrain fitting."""
        for linestring, _, _ in road_entries:
            if linestring.is_empty or linestring.length <= 0:
                continue

            dense_coords = self._densify_linestring_coords(
                linestring,
                target_segment_length=sampling_step,
            )
            for x, y in dense_coords:
                point = Point(float(x), float(y))
                if road_surface.covers(point):
                    self._add_point(points, float(x), float(y))

    def _add_ring_points(
        self,
        points: dict[tuple[int, int], tuple[float, float]],
        ring_coords: Any,
    ) -> None:
        """Add ring coordinates to a unique XY point map."""
        for x, y in ring_coords:
            self._add_point(points, float(x), float(y))

    def _add_point(
        self,
        points: dict[tuple[int, int], tuple[float, float]],
        x: float,
        y: float,
    ) -> None:
        """Store a point by quantized key to avoid near-duplicate vertices."""
        points[self._point_key(x, y)] = (x, y)

    @staticmethod
    def _point_key(x: float, y: float) -> tuple[int, int]:
        """Return quantized key for robust float deduplication."""
        precision = 1000
        return (int(round(x * precision)), int(round(y * precision)))

    @staticmethod
    def _signed_triangle_area(coords: list[tuple[float, float]]) -> float:
        """Signed 2D area; positive for counter-clockwise vertex order."""
        return 0.5 * (
            coords[0][0] * (coords[1][1] - coords[2][1])
            + coords[1][0] * (coords[2][1] - coords[0][1])
            + coords[2][0] * (coords[0][1] - coords[1][1])
        )

    def _extract_polygons(self, geometry: Any) -> list[Polygon]:
        """Extract polygon parts from any Shapely geometry container."""
        if geometry is None or geometry.is_empty:
            return []

        if isinstance(geometry, Polygon):
            return [geometry]

        if isinstance(geometry, MultiPolygon):
            return [poly for poly in geometry.geoms if not poly.is_empty]

        if isinstance(geometry, GeometryCollection):
            polygons: list[Polygon] = []
            for geom in geometry.geoms:
                polygons.extend(self._extract_polygons(geom))
            return polygons

        return []

    def info_sequence(self) -> dict[str, Any]:
        """Returns information about the road processing as a dictionary.

        Returns:
            dict[str, Any]: Information about road processing.
        """
        return self.info
