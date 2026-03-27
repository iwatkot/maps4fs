"""Component for map roads processing and generation."""

from __future__ import annotations

import os
import shutil
from collections import defaultdict
from typing import Any, NamedTuple

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


class TextureSource(NamedTuple):
    """Road texture source and its allowed UV influence region.

    Arguments:
        linestring (shapely.LineString): Centerline used for UV projection.
        width (float): Effective road half-width used for UV mapping.
        influence (Polygon | MultiPolygon): Region where this source owns UVs.
    """

    linestring: shapely.LineString
    width: float
    influence: Polygon | MultiPolygon


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
        """Initialize road component state before generation."""
        self.info: dict[str, Any] = {}

    def process(self) -> None:
        """Process and generate roads for the map."""
        try:
            self.generate_roads()
        except Exception as e:
            self.logger.error("Error during road generation: %s", e)

    def generate_roads(self) -> None:
        """Generate all road meshes grouped by texture.

        Returns:
            None: This method updates component info and writes mesh assets.
        """
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
        """Load road polyline info records from context.

        Returns:
            list[dict[str, Any]] | None: Raw road records or None when unavailable.
        """
        road_infos = self.get_infolayer_data(Parameters.TEXTURES, Parameters.ROADS_POLYLINES)
        if not road_infos:
            return None
        return [info for info in road_infos if isinstance(info, dict)]

    def _group_roads_by_texture(
        self,
        road_infos: list[dict[str, Any]],
    ) -> dict[str, list[dict[str, Any]]]:
        """Group road records by texture key.

        Arguments:
            road_infos (list[dict[str, Any]]): Raw road records.

        Returns:
            dict[str, list[dict[str, Any]]]: Road records grouped by texture name.
        """
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
        """Process roads for one texture.

        Arguments:
            texture (str): Base texture name for the current road group.
            roads_polylines (list[dict[str, Any]]): Raw road records for the texture.

        Returns:
            tuple[int, int]: Number of fitted roads and created patches.
        """
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
        """Convert raw road records to fitted linestring entries.

        Arguments:
            roads_polylines (list[dict[str, Any]]): Raw road records.

        Returns:
            list[LineSurfaceEntry]: Validated and fitted road entries.
        """
        road_entries: list[LineSurfaceEntry] = []
        for road_id, road_info in enumerate(roads_polylines, start=1):
            road_entry = self._build_road_entry(road_info, road_id)
            if road_entry is not None:
                road_entries.append(road_entry)
        return road_entries

    def _build_road_entry(self, road_info: dict[str, Any], road_id: int) -> LineSurfaceEntry | None:
        """Build one fitted road entry from source info record.

        Arguments:
            road_info (dict[str, Any]): Raw road record.
            road_id (int): Sequential road identifier for logging.

        Returns:
            LineSurfaceEntry | None: Fitted road entry or None when invalid.
        """
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
        """Build one patch entry for a T-junction endpoint.

        Arguments:
            endpoint (Point): Candidate side-road endpoint.
            other_road (shapely.LineString): Potential dominant road.
            other_width (int): Dominant road width.
            other_z_offset (float): Dominant road Z offset.
            cumulative_offset (float): Current cumulative patch offset.
            tolerance (float): Intersection tolerance.

        Returns:
            tuple[LineSurfaceEntry | None, float]: Patch entry and updated cumulative offset.
        """
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
        """Return whether an endpoint is near either end of another road.

        Arguments:
            endpoint (Point): Endpoint to test.
            other_road (shapely.LineString): Road against which to test.
            tolerance (float): Endpoint proximity threshold.

        Returns:
            bool: True when the endpoint is near either end of the other road.
        """
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
        """Return index of the segment containing an intersection point.

        Arguments:
            coords (list[tuple[float, float]]): Polyline coordinates.
            intersection_point (Point): Intersection point to locate.
            tolerance (float): Segment distance tolerance.

        Returns:
            int | None: Segment index or None when not found.
        """
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
        """Extract bounded patch coordinates around a segment index.

        Arguments:
            coords (list[tuple[float, float]]): Source road coordinates.
            segment_idx (int): Segment index around the intersection.

        Returns:
            list[tuple[float, float]] | None: Patch coordinates or None when too short.
        """
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

        dst_texture_path = self._copy_texture_to_mesh_directory(texture_path, road_mesh_directory)
        shutil.copyfile(texture_path, dst_texture_path)
        self.logger.debug("Texture copied to %s", dst_texture_path)

        obj_output_path, mtl_output_path = self._build_mesh_output_paths(
            road_mesh_directory,
            texture,
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

        mesh, center = self._load_transform_and_center_mesh(obj_output_path)

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

    @staticmethod
    def _copy_texture_to_mesh_directory(texture_path: str, road_mesh_directory: str) -> str:
        """Return destination path for a copied road texture.

        Arguments:
            texture_path (str): Source texture path.
            road_mesh_directory (str): Output directory for road mesh assets.

        Returns:
            str: Destination texture path.
        """
        return os.path.join(road_mesh_directory, os.path.basename(texture_path))

    @staticmethod
    def _build_mesh_output_paths(road_mesh_directory: str, texture: str) -> tuple[str, str]:
        """Build OBJ and MTL output paths for one road texture.

        Arguments:
            road_mesh_directory (str): Directory for generated road files.
            texture (str): Road texture name.

        Returns:
            tuple[str, str]: OBJ path and MTL path.
        """
        return (
            os.path.join(
                road_mesh_directory,
                f"{Parameters.ROAD_MESH_FILENAME_PREFIX}{texture}.obj",
            ),
            os.path.join(
                road_mesh_directory,
                f"{Parameters.ROAD_MESH_FILENAME_PREFIX}{texture}.mtl",
            ),
        )

    def _load_transform_and_center_mesh(
        self,
        obj_output_path: str,
    ) -> tuple[trimesh.Trimesh, np.ndarray]:
        """Load generated mesh, rotate it, and center it around its centroid.

        Arguments:
            obj_output_path (str): Path to the generated OBJ mesh.

        Returns:
            tuple[trimesh.Trimesh, np.ndarray]: Centered mesh and original centroid.
        """
        mesh = trimesh.load_mesh(obj_output_path, force="mesh", process=False)
        rotation_matrix = trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0])
        mesh.apply_transform(rotation_matrix)

        has_face_normals = mesh.face_normals.size > 0
        mean_normal_y = float(np.mean(mesh.face_normals[:, 1])) if has_face_normals else 0.0
        if has_face_normals and mean_normal_y < 0.0:
            mesh.invert()

        vertices = mesh.vertices
        center = vertices.mean(axis=0)
        mesh.vertices = vertices - center
        return mesh, center

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

        Arguments:
            road_entries (list[LineSurfaceEntry]): Source road entries.
            obj_output_path (str): Output OBJ path.
            mtl_output_path (str | None): Output MTL path.
            texture_path (str | None): Texture path referenced by the MTL.

        Returns:
            bool: True when the mesh was created successfully.
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
                v1, v2, v3, t1, t2, t3 = face
                v1 += Parameters.OBJ_INDEX_OFFSET
                v2 += Parameters.OBJ_INDEX_OFFSET
                v3 += Parameters.OBJ_INDEX_OFFSET
                t1 += Parameters.OBJ_INDEX_OFFSET
                t2 += Parameters.OBJ_INDEX_OFFSET
                t3 += Parameters.OBJ_INDEX_OFFSET
                obj_file.write(f"f {v1}/{t1} {v2}/{t2} {v3}/{t3}\n")

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
        """Build a unioned polygonal road surface from centerline entries.

        Arguments:
            road_entries (list[LineSurfaceEntry]): Road centerline entries.

        Returns:
            Polygon | MultiPolygon | None: Final connected road surface.
        """
        prepared_lines = self._prepare_surface_lines(road_entries)

        if not prepared_lines:
            return None

        components = self._build_road_components(prepared_lines)
        component_polygons = self._build_component_polygons(prepared_lines, components)
        return self._extract_disjoint_surface(component_polygons)

    def _prepare_surface_lines(
        self,
        road_entries: list[LineSurfaceEntry],
    ) -> list[tuple[shapely.LineString, float]]:
        """Prepare densified centerlines for surface generation.

        Arguments:
            road_entries (list[LineSurfaceEntry]): Raw road centerline entries.

        Returns:
            list[tuple[shapely.LineString, float]]: Densified lines with safe widths.
        """
        prepared_lines: list[tuple[shapely.LineString, float]] = []
        for linestring, width, _ in road_entries:
            if linestring.is_empty or linestring.length <= 0:
                continue

            dense_coords = self._densify_linestring_coords(
                linestring,
                target_segment_length=Parameters.INTERPOLATION_TARGET_SEGMENT_LENGTH,
            )
            if len(dense_coords) < 2:
                continue

            prepared_lines.append(
                (
                    shapely.LineString(dense_coords),
                    max(float(width), Parameters.ROAD_SURFACE_MIN_WIDTH),
                )
            )
        return prepared_lines

    def _build_component_polygons(
        self,
        prepared_lines: list[tuple[shapely.LineString, float]],
        components: list[list[int]],
    ) -> list[Polygon]:
        """Build unioned polygons for each connected road component.

        Arguments:
            prepared_lines (list[tuple[shapely.LineString, float]]): Densified surface lines.
            components (list[list[int]]): Connected-component indices.

        Returns:
            list[Polygon]: Polygon parts for all connected components.
        """
        component_polygons: list[Polygon] = []
        for component_indices in components:
            component_buffers = self._build_component_buffers(prepared_lines, component_indices)
            if not component_buffers:
                continue

            unioned_component = self._union_component_buffers(component_buffers)
            if unioned_component is None:
                continue
            component_polygons.extend(self._extract_polygons(unioned_component))
        return component_polygons

    def _build_component_buffers(
        self,
        prepared_lines: list[tuple[shapely.LineString, float]],
        component_indices: list[int],
    ) -> list[Polygon]:
        """Buffer all lines in one connected component.

        Arguments:
            prepared_lines (list[tuple[shapely.LineString, float]]): Densified surface lines.
            component_indices (list[int]): Indices belonging to one component.

        Returns:
            list[Polygon]: Buffered polygon parts for the component.
        """
        component_buffers: list[Polygon] = []
        for index in component_indices:
            component_line, component_width = prepared_lines[index]
            try:
                buffered = component_line.buffer(component_width, cap_style=2, join_style=1)
            except Exception as e:
                self.logger.debug("Failed to buffer road line: %s", e)
                continue

            if buffered.is_empty:
                continue
            component_buffers.extend(self._extract_polygons(buffered))
        return component_buffers

    def _union_component_buffers(self, component_buffers: list[Polygon]) -> Any | None:
        """Union buffered polygons for one connected component.

        Arguments:
            component_buffers (list[Polygon]): Buffered road polygons.

        Returns:
            Any | None: Unioned geometry or None on failure.
        """
        try:
            unioned_component = shapely.unary_union(component_buffers)
        except Exception as e:
            self.logger.debug("Failed to union connected road component: %s", e)
            return None

        if not unioned_component.is_valid:
            try:
                unioned_component = shapely.make_valid(unioned_component)
            except Exception:
                return unioned_component
        return unioned_component

    def _extract_disjoint_surface(
        self,
        component_polygons: list[Polygon],
    ) -> Polygon | MultiPolygon | None:
        """Remove accidental overlaps between disconnected component polygons.

        Arguments:
            component_polygons (list[Polygon]): Unioned polygons for connected road groups.

        Returns:
            Polygon | MultiPolygon | None: Final disjoint road surface.
        """
        if not component_polygons:
            return None

        disjoint_polygons: list[Polygon] = []
        occupied: Polygon | MultiPolygon | None = None
        for polygon in sorted(component_polygons, key=lambda poly: float(poly.area), reverse=True):
            candidate = polygon if occupied is None else polygon.difference(occupied)
            new_parts = self._extract_polygons(candidate)
            if not new_parts:
                occupied = polygon if occupied is None else shapely.unary_union([occupied, polygon])
                continue

            disjoint_polygons.extend(new_parts)
            occupied = (
                shapely.unary_union(new_parts)
                if occupied is None
                else shapely.unary_union([occupied, *new_parts])
            )

        if not disjoint_polygons:
            return None
        if len(disjoint_polygons) == 1:
            return disjoint_polygons[0]
        return shapely.MultiPolygon(disjoint_polygons)

    def _triangulate_road_surface(
        self,
        road_surface: Polygon | MultiPolygon,
        dem_image: np.ndarray,
        road_entries: list[LineSurfaceEntry],
    ) -> tuple[
        list[tuple[float, float, float]],
        list[tuple[int, int, int, int, int, int]],
        list[tuple[float, float]],
    ]:
        """Triangulate the connected road surface and sample DEM height per vertex.

        Arguments:
            road_surface (Polygon | MultiPolygon): Unioned road surface.
            dem_image (np.ndarray): DEM used for height sampling.
            road_entries (list[LineSurfaceEntry]): Source road centerline entries.

        Returns:
            tuple[list[tuple[float, float, float]], list[tuple[int, int, int, int, int, int]], list[tuple[float, float]]]:
                Vertices, faces, and UV coordinates.
        """
        polygons = self._extract_polygons(road_surface)
        if not polygons:
            return [], [], []

        sampling_step = self._get_network_sampling_step(road_entries)

        vertices: list[tuple[float, float, float]] = []
        faces: list[tuple[int, int, int, int, int, int]] = []
        uvs: list[tuple[float, float]] = []
        vertex_index: dict[tuple[int, int], int] = {}
        tile_size = max(Parameters.TEXTURE_TILE_SIZE_METERS, 1.0)
        texture_sources = self._build_texture_sources(road_entries)

        for polygon in polygons:
            polygon_points = self._build_polygon_points(polygon, road_entries, sampling_step)
            if len(polygon_points) < 3:
                continue

            point_cloud = shapely.MultiPoint(list(polygon_points.values()))
            raw_triangles = shapely.ops.triangulate(point_cloud)
            if not raw_triangles:
                continue

            for triangle in raw_triangles:
                if triangle.is_empty or triangle.area <= 0.0:
                    continue

                clipped = triangle.intersection(polygon)
                for coords in self._triangulate_clipped_geometry(clipped):
                    # Keep triangles clockwise in XY so after +90deg X-rotation normals face +Y.
                    if self._signed_triangle_area(coords) > 0.0:
                        coords[1], coords[2] = coords[2], coords[1]

                    triangle_source = self._select_triangle_uv_source(
                        triangle_coords=coords,
                        texture_sources=texture_sources,
                    )
                    triangle_face = self._append_triangle_mesh_data(
                        coords=coords,
                        dem_image=dem_image,
                        tile_size=tile_size,
                        triangle_source=triangle_source,
                        vertices=vertices,
                        uvs=uvs,
                        vertex_index=vertex_index,
                    )
                    if triangle_face is not None:
                        faces.append(triangle_face)

        return vertices, faces, uvs

    def _build_polygon_points(
        self,
        polygon: Polygon,
        road_entries: list[LineSurfaceEntry],
        sampling_step: float,
    ) -> dict[tuple[int, int], tuple[float, float]]:
        """Build a unique point cloud for one polygon triangulation pass.

        Arguments:
            polygon (Polygon): Road surface polygon.
            road_entries (list[LineSurfaceEntry]): Source road entries.
            sampling_step (float): Interior centerline sampling step.

        Returns:
            dict[tuple[int, int], tuple[float, float]]: Quantized point map.
        """
        polygon_points: dict[tuple[int, int], tuple[float, float]] = {}
        self._add_ring_points(polygon_points, polygon.exterior.coords)
        for interior in polygon.interiors:
            self._add_ring_points(polygon_points, interior.coords)

        representative = polygon.representative_point()
        self._add_point(polygon_points, float(representative.x), float(representative.y))
        self._add_centerline_points(
            points=polygon_points,
            road_entries=road_entries,
            road_surface=polygon,
            sampling_step=sampling_step,
        )
        return polygon_points

    def _append_triangle_mesh_data(
        self,
        coords: list[tuple[float, float]],
        dem_image: np.ndarray,
        tile_size: float,
        triangle_source: tuple[shapely.LineString, float] | None,
        vertices: list[tuple[float, float, float]],
        uvs: list[tuple[float, float]],
        vertex_index: dict[tuple[int, int], int],
    ) -> tuple[int, int, int, int, int, int] | None:
        """Append one triangle worth of mesh data.

        Arguments:
            coords (list[tuple[float, float]]): Triangle coordinates.
            dem_image (np.ndarray): DEM image for height sampling.
            tile_size (float): Texture tiling distance.
            triangle_source (tuple[shapely.LineString, float] | None): Selected UV source.
            vertices (list[tuple[float, float, float]]): Output vertex list.
            uvs (list[tuple[float, float]]): Output UV list.
            vertex_index (dict[tuple[int, int], int]): Quantized vertex lookup.

        Returns:
            tuple[int, int, int, int, int, int] | None: Face tuple or None if degenerate.
        """
        face_vertex_indices: list[int] = []
        face_uv_indices: list[int] = []
        for x, y in coords:
            idx = self._get_or_create_vertex(vertex_index, vertices, dem_image, x, y)
            face_vertex_indices.append(idx)

            uv = self._compute_triangle_vertex_uv(
                x=x,
                y=y,
                tile_size=tile_size,
                triangle_source=triangle_source,
            )
            face_uv_indices.append(len(uvs))
            uvs.append(uv)

        if len(set(face_vertex_indices)) != 3:
            return None

        return (
            face_vertex_indices[0],
            face_vertex_indices[1],
            face_vertex_indices[2],
            face_uv_indices[0],
            face_uv_indices[1],
            face_uv_indices[2],
        )

    def _get_or_create_vertex(
        self,
        vertex_index: dict[tuple[int, int], int],
        vertices: list[tuple[float, float, float]],
        dem_image: np.ndarray,
        x: float,
        y: float,
    ) -> int:
        """Get existing vertex index or create a new terrain-sampled vertex.

        Arguments:
            vertex_index (dict[tuple[int, int], int]): Quantized vertex lookup.
            vertices (list[tuple[float, float, float]]): Output vertex list.
            dem_image (np.ndarray): DEM image for height sampling.
            x (float): Vertex x coordinate.
            y (float): Vertex y coordinate.

        Returns:
            int: Vertex index.
        """
        key = self._point_key(x, y)
        idx = vertex_index.get(key)
        if idx is not None:
            return idx

        z = -float(self.get_z_coordinate_from_dem(dem_image, x, y))
        idx = len(vertices)
        vertex_index[key] = idx
        vertices.append((x, y, z))
        return idx

    def _build_texture_sources(
        self,
        road_entries: list[LineSurfaceEntry],
    ) -> list[TextureSource]:
        """Build per-road UV ownership regions so side roads are cut at dominant roads.

        Arguments:
            road_entries (list[LineSurfaceEntry]): Source road centerline entries.

        Returns:
            list[TextureSource]: Texture sources with non-overlapping ownership regions.
        """
        prepared = self._prepare_texture_candidates(road_entries)

        if not prepared:
            return []

        # Priority order: wider and longer roads remain continuous through intersections.
        order = sorted(
            range(len(prepared)),
            key=lambda idx: (prepared[idx][1], float(prepared[idx][0].length)),
            reverse=True,
        )

        blockers: list[Polygon | MultiPolygon] = []
        sources: list[TextureSource] = []
        for idx in order:
            linestring, width, base_influence = prepared[idx]
            owned = self._subtract_blockers(base_influence, blockers)

            normalized_owned = self._normalize_surface_geometry(owned)
            if normalized_owned is not None:
                sources.append(
                    TextureSource(
                        linestring=linestring,
                        width=width,
                        influence=normalized_owned,
                    )
                )

            blockers.append(base_influence)

        if not sources:
            return [
                TextureSource(linestring=line, width=width, influence=influence)
                for line, width, influence in prepared
            ]
        return sources

    def _prepare_texture_candidates(
        self,
        road_entries: list[LineSurfaceEntry],
    ) -> list[tuple[shapely.LineString, float, Polygon | MultiPolygon]]:
        """Prepare buffered ownership candidates for UV source selection.

        Arguments:
            road_entries (list[LineSurfaceEntry]): Source road centerline entries.

        Returns:
            list[tuple[shapely.LineString, float, Polygon | MultiPolygon]]: Densified lines,
                safe widths, and buffered ownership regions.
        """
        prepared: list[tuple[shapely.LineString, float, Polygon | MultiPolygon]] = []
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
            safe_width = max(float(width), Parameters.ROAD_TEXTURE_SOURCE_MIN_WIDTH)
            try:
                base_influence = dense_line.buffer(safe_width, cap_style=2, join_style=1)
            except Exception:
                continue

            normalized = self._normalize_surface_geometry(base_influence)
            if normalized is not None:
                prepared.append((dense_line, safe_width, normalized))
        return prepared

    def _subtract_blockers(
        self,
        owned: Polygon | MultiPolygon,
        blockers: list[Polygon | MultiPolygon],
    ) -> Any:
        """Subtract already-owned blocker regions from a candidate ownership polygon.

        Arguments:
            owned (Polygon | MultiPolygon): Candidate ownership region.
            blockers (list[Polygon | MultiPolygon]): Regions already claimed by dominant roads.

        Returns:
            Any: Remaining ownership geometry.
        """
        result: Any = owned
        for blocker in blockers:
            if result.is_empty:
                break
            if not result.intersects(blocker):
                continue
            try:
                result = result.difference(blocker)
            except Exception:
                continue
        return result

    def _normalize_surface_geometry(
        self,
        geometry: Any,
    ) -> Polygon | MultiPolygon | None:
        """Normalize arbitrary geometry into polygon or multipolygon surface.

        Arguments:
            geometry (Any): Input Shapely geometry.

        Returns:
            Polygon | MultiPolygon | None: Normalized polygonal surface.
        """
        polygons = self._extract_polygons(geometry)
        if not polygons:
            return None

        merged = shapely.unary_union(polygons)
        if isinstance(merged, (Polygon, MultiPolygon)):
            return merged

        fallback_polygons = self._extract_polygons(merged)
        if not fallback_polygons:
            return None
        if len(fallback_polygons) == 1:
            return fallback_polygons[0]
        return shapely.MultiPolygon(fallback_polygons)

    def _triangulate_clipped_geometry(
        self,
        geometry: Any,
    ) -> list[list[tuple[float, float]]]:
        """Triangulate a clipped geometry and return robust triangle coordinate triplets.

        Arguments:
            geometry (Any): Clipped geometry to triangulate.

        Returns:
            list[list[tuple[float, float]]]: Triangle coordinate triplets.
        """
        min_area = Parameters.ROAD_TRIANGULATION_MIN_AREA
        result: list[list[tuple[float, float]]] = []
        clipped_polygons = self._extract_polygons(geometry)

        for polygon in clipped_polygons:
            if polygon.is_empty or float(polygon.area) <= min_area:
                continue

            if len(polygon.interiors) == 0 and len(polygon.exterior.coords) == 4:
                coords = [(float(x), float(y)) for x, y in list(polygon.exterior.coords)[:3]]
                if abs(self._signed_triangle_area(coords)) > min_area:
                    result.append(coords)
                continue

            for triangle in shapely.ops.triangulate(polygon):
                if triangle.is_empty or float(triangle.area) <= min_area:
                    continue

                representative = triangle.representative_point()
                if not polygon.covers(representative):
                    continue

                coords = [(float(x), float(y)) for x, y in list(triangle.exterior.coords)[:3]]
                if abs(self._signed_triangle_area(coords)) <= min_area:
                    continue
                result.append(coords)

        return result

    def _build_road_components(
        self,
        lines: list[tuple[shapely.LineString, float]],
    ) -> list[list[int]]:
        """Build connectivity components so nearby parallel roads do not get merged.

        Arguments:
            lines (list[tuple[shapely.LineString, float]]): Densified lines and widths.

        Returns:
            list[list[int]]: Connected-component indices into the input line list.
        """
        if not lines:
            return []

        tolerance = Parameters.ROAD_INTERSECTION_TOLERANCE
        adjacency: list[set[int]] = [set() for _ in range(len(lines))]

        for i, (line_i, _) in enumerate(lines):
            for j in range(i + 1, len(lines)):
                line_j, _ = lines[j]
                if self._are_roads_connected(line_i, line_j, tolerance):
                    adjacency[i].add(j)
                    adjacency[j].add(i)

        visited: set[int] = set()
        components: list[list[int]] = []
        for start in range(len(lines)):
            if start in visited:
                continue

            stack = [start]
            component: list[int] = []
            visited.add(start)
            while stack:
                current = stack.pop()
                component.append(current)
                for neighbor in adjacency[current]:
                    if neighbor in visited:
                        continue
                    visited.add(neighbor)
                    stack.append(neighbor)

            components.append(component)

        return components

    def _are_roads_connected(
        self,
        line_a: shapely.LineString,
        line_b: shapely.LineString,
        tolerance: float,
    ) -> bool:
        """Return whether two roads are topologically related.

        Arguments:
            line_a (shapely.LineString): First road centerline.
            line_b (shapely.LineString): Second road centerline.
            tolerance (float): Endpoint connection tolerance.

        Returns:
            bool: True when roads intersect, touch, or connect at endpoints.
        """
        try:
            if line_a.intersects(line_b):
                return True
        except Exception:
            return False

        endpoint_pairs_a = [
            (Point(line_a.coords[0]), Point(line_a.coords[1])),
            (Point(line_a.coords[-1]), Point(line_a.coords[-2])),
        ]
        endpoint_pairs_b = [
            (Point(line_b.coords[0]), Point(line_b.coords[1])),
            (Point(line_b.coords[-1]), Point(line_b.coords[-2])),
        ]

        for endpoint, neighbor in endpoint_pairs_a:
            if self._endpoint_connects_to_line(endpoint, neighbor, line_b, tolerance):
                return True
        for endpoint, neighbor in endpoint_pairs_b:
            if self._endpoint_connects_to_line(endpoint, neighbor, line_a, tolerance):
                return True

        return False

    @staticmethod
    def _endpoint_connects_to_line(
        endpoint: Point,
        endpoint_neighbor: Point,
        other_line: shapely.LineString,
        tolerance: float,
    ) -> bool:
        """Return whether an endpoint is near and directed toward another line.

        Arguments:
            endpoint (Point): Endpoint to test.
            endpoint_neighbor (Point): Neighboring point that defines endpoint direction.
            other_line (shapely.LineString): Candidate connecting line.
            tolerance (float): Distance tolerance for the connection.

        Returns:
            bool: True when the endpoint approaches the other line.
        """
        distance = float(endpoint.distance(other_line))
        if distance > tolerance:
            return False

        projected = float(other_line.project(endpoint))
        closest = other_line.interpolate(projected)
        toward_x = float(closest.x - endpoint.x)
        toward_y = float(closest.y - endpoint.y)
        toward_len = float(np.hypot(toward_x, toward_y))
        if toward_len <= 1e-9:
            return True

        dir_x = float(endpoint.x - endpoint_neighbor.x)
        dir_y = float(endpoint.y - endpoint_neighbor.y)
        dir_len = float(np.hypot(dir_x, dir_y))
        if dir_len <= 1e-9:
            return False

        approach = (dir_x * toward_x + dir_y * toward_y) / (dir_len * toward_len)
        return approach > 0.2

    def _compute_triangle_vertex_uv(
        self,
        x: float,
        y: float,
        tile_size: float,
        triangle_source: tuple[shapely.LineString, float] | None,
    ) -> tuple[float, float]:
        """Compute per-corner UV in the triangle-selected mapping frame.

        Arguments:
            x (float): Vertex x coordinate.
            y (float): Vertex y coordinate.
            tile_size (float): Texture tiling size.
            triangle_source (tuple[shapely.LineString, float] | None): Selected UV source.

        Returns:
            tuple[float, float]: UV coordinates for the vertex.
        """
        if triangle_source is None:
            return (x / tile_size, y / tile_size)

        best_line, best_width = triangle_source
        point = Point(x, y)
        best_distance = float(best_line.distance(point))

        along = float(best_line.project(point))
        signed_lateral = self._signed_lateral_distance(best_line, point, along, best_distance)

        u = float(np.clip(0.5 + (signed_lateral / max(best_width, 1.0)), 0.0, 1.0))
        v = along / tile_size
        return (u, v)

    def _select_triangle_uv_source(
        self,
        triangle_coords: list[tuple[float, float]],
        texture_sources: list[TextureSource],
    ) -> tuple[shapely.LineString, float] | None:
        """Pick one centerline for the entire triangle using distance and direction fit.

        Arguments:
            triangle_coords (list[tuple[float, float]]): Triangle coordinates.
            texture_sources (list[TextureSource]): Candidate texture sources.

        Returns:
            tuple[shapely.LineString, float] | None: Winning centerline and width.
        """
        if not texture_sources:
            return None

        centroid_x = (triangle_coords[0][0] + triangle_coords[1][0] + triangle_coords[2][0]) / 3.0
        centroid_y = (triangle_coords[0][1] + triangle_coords[1][1] + triangle_coords[2][1]) / 3.0
        centroid = Point(centroid_x, centroid_y)

        candidate_pool = self._get_triangle_candidate_pool(
            centroid,
            centroid_x,
            centroid_y,
            texture_sources,
        )

        tri_direction = self._triangle_longest_edge_direction(triangle_coords)

        best_score = float("inf")
        best_source: tuple[shapely.LineString, float] | None = None
        for linestring, width in candidate_pool:
            score = self._score_triangle_source(
                triangle_coords,
                centroid,
                tri_direction,
                linestring,
                width,
            )
            if score < best_score:
                best_score = score
                best_source = (linestring, width)

        return best_source

    def _get_triangle_candidate_pool(
        self,
        centroid: Point,
        centroid_x: float,
        centroid_y: float,
        texture_sources: list[TextureSource],
    ) -> list[tuple[shapely.LineString, float]]:
        """Return owned or nearest texture sources for one triangle.

        Arguments:
            centroid (Point): Triangle centroid.
            centroid_x (float): Triangle centroid x.
            centroid_y (float): Triangle centroid y.
            texture_sources (list[TextureSource]): Candidate texture sources.

        Returns:
            list[tuple[shapely.LineString, float]]: Candidate source pool.
        """
        owned_sources: list[tuple[shapely.LineString, float]] = []
        for source in texture_sources:
            min_x, min_y, max_x, max_y = source.influence.bounds
            if not (min_x <= centroid_x <= max_x and min_y <= centroid_y <= max_y):
                continue
            if source.influence.covers(centroid):
                owned_sources.append((source.linestring, source.width))

        if owned_sources:
            return owned_sources

        preliminary_all: list[tuple[float, shapely.LineString, float]] = []
        for source in texture_sources:
            preliminary_all.append(
                (
                    float(source.linestring.distance(centroid)),
                    source.linestring,
                    source.width,
                )
            )
        preliminary_all.sort(key=lambda item: item[0])
        return [
            (line, width)
            for _, line, width in preliminary_all[: Parameters.ROAD_TRIANGLE_FALLBACK_SOURCE_COUNT]
        ]

    def _score_triangle_source(
        self,
        triangle_coords: list[tuple[float, float]],
        centroid: Point,
        tri_direction: tuple[float, float] | None,
        linestring: shapely.LineString,
        width: float,
    ) -> float:
        """Score one texture source for a triangle.

        Arguments:
            triangle_coords (list[tuple[float, float]]): Triangle coordinates.
            centroid (Point): Triangle centroid.
            tri_direction (tuple[float, float] | None): Dominant triangle direction.
            linestring (shapely.LineString): Candidate source centerline.
            width (float): Candidate source width.

        Returns:
            float: Lower score is better.
        """
        safe_width = max(width, Parameters.ROAD_TEXTURE_SOURCE_MIN_WIDTH)
        vertex_points = [Point(x, y) for x, y in triangle_coords]
        mean_distance = float(
            np.mean([linestring.distance(vertex_point) for vertex_point in vertex_points])
        )
        distance_score = mean_distance / safe_width

        direction_score = Parameters.ROAD_TRIANGLE_DIRECTION_BASE_SCORE
        if tri_direction is not None:
            along = float(linestring.project(centroid))
            tangent = self._line_tangent_direction(linestring, along)
            if tangent is not None:
                dot = abs(tri_direction[0] * tangent[0] + tri_direction[1] * tangent[1])
                direction_score = 1.0 - float(np.clip(dot, 0.0, 1.0))

        return distance_score + direction_score * Parameters.ROAD_TRIANGLE_DIRECTION_WEIGHT

    @staticmethod
    def _triangle_longest_edge_direction(
        triangle_coords: list[tuple[float, float]],
    ) -> tuple[float, float] | None:
        """Return normalized direction vector of the longest triangle edge.

        Arguments:
            triangle_coords (list[tuple[float, float]]): Triangle coordinates.

        Returns:
            tuple[float, float] | None: Normalized edge direction or None.
        """
        edges = [
            (
                triangle_coords[0],
                triangle_coords[1],
            ),
            (
                triangle_coords[1],
                triangle_coords[2],
            ),
            (
                triangle_coords[2],
                triangle_coords[0],
            ),
        ]

        longest_length = 0.0
        longest_vector: tuple[float, float] | None = None
        for start, end in edges:
            dx = float(end[0] - start[0])
            dy = float(end[1] - start[1])
            length = float(np.hypot(dx, dy))
            if length > longest_length:
                longest_length = length
                longest_vector = (dx, dy)

        if longest_vector is None or longest_length <= 1e-9:
            return None

        return (longest_vector[0] / longest_length, longest_vector[1] / longest_length)

    @staticmethod
    def _line_tangent_direction(
        linestring: shapely.LineString,
        along: float,
    ) -> tuple[float, float] | None:
        """Return normalized tangent vector of a linestring at a projected distance.

        Arguments:
            linestring (shapely.LineString): Source linestring.
            along (float): Projected distance along the linestring.

        Returns:
            tuple[float, float] | None: Normalized tangent vector or None.
        """
        line_length = float(linestring.length)
        if line_length <= 0.0:
            return None

        epsilon = min(
            Parameters.ROAD_TANGENT_EPSILON_MAX,
            max(
                line_length * Parameters.ROAD_TANGENT_EPSILON_RATIO,
                Parameters.ROAD_TANGENT_EPSILON_MIN,
            ),
        )
        start_d = max(0.0, along - epsilon)
        end_d = min(line_length, along + epsilon)
        p0 = linestring.interpolate(start_d)
        p1 = linestring.interpolate(end_d)

        dx = float(p1.x - p0.x)
        dy = float(p1.y - p0.y)
        tangent_len = float(np.hypot(dx, dy))
        if tangent_len <= 1e-9:
            return None

        return (dx / tangent_len, dy / tangent_len)

    @staticmethod
    def _signed_lateral_distance(
        linestring: shapely.LineString,
        point: Point,
        along: float,
        absolute_distance: float,
    ) -> float:
        """Return signed lateral distance of a point relative to local line tangent.

        Arguments:
            linestring (shapely.LineString): Source linestring.
            point (Point): Point to classify.
            along (float): Projected distance along the linestring.
            absolute_distance (float): Unsigned point-to-line distance.

        Returns:
            float: Signed lateral distance from the line.
        """
        line_length = float(linestring.length)
        if line_length <= 0.0:
            return 0.0

        epsilon = min(
            Parameters.ROAD_TANGENT_EPSILON_MAX,
            max(
                line_length * Parameters.ROAD_TANGENT_EPSILON_RATIO,
                Parameters.ROAD_TANGENT_EPSILON_MIN,
            ),
        )
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
        """Choose interior triangulation sampling step from source road widths.

        Arguments:
            road_entries (list[LineSurfaceEntry]): Source road entries.

        Returns:
            float: Interior sampling step in pixels.
        """
        widths = [max(float(entry.width), 1.0) for entry in road_entries]
        if not widths:
            return Parameters.INTERPOLATION_TARGET_SEGMENT_LENGTH

        median_width = float(np.median(widths))
        return float(
            np.clip(
                median_width,
                Parameters.ROAD_NETWORK_SAMPLING_MIN,
                Parameters.ROAD_NETWORK_SAMPLING_MAX,
            )
        )

    def _add_centerline_points(
        self,
        points: dict[tuple[int, int], tuple[float, float]],
        road_entries: list[LineSurfaceEntry],
        road_surface: Polygon | MultiPolygon,
        sampling_step: float,
    ) -> None:
        """Add interior samples along original centerlines to improve terrain fitting.

        Arguments:
            points (dict[tuple[int, int], tuple[float, float]]): Output point map.
            road_entries (list[LineSurfaceEntry]): Source road entries.
            road_surface (Polygon | MultiPolygon): Polygon receiving the samples.
            sampling_step (float): Sampling step along each centerline.
        """
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
        """Add ring coordinates to a unique XY point map.

        Arguments:
            points (dict[tuple[int, int], tuple[float, float]]): Output point map.
            ring_coords (Any): Ring coordinate sequence.
        """
        for x, y in ring_coords:
            self._add_point(points, float(x), float(y))

    def _add_point(
        self,
        points: dict[tuple[int, int], tuple[float, float]],
        x: float,
        y: float,
    ) -> None:
        """Store a point by quantized key to avoid near-duplicate vertices.

        Arguments:
            points (dict[tuple[int, int], tuple[float, float]]): Output point map.
            x (float): Point x coordinate.
            y (float): Point y coordinate.
        """
        points[self._point_key(x, y)] = (x, y)

    @staticmethod
    def _point_key(x: float, y: float) -> tuple[int, int]:
        """Return quantized key for robust float deduplication.

        Arguments:
            x (float): Point x coordinate.
            y (float): Point y coordinate.

        Returns:
            tuple[int, int]: Quantized coordinate key.
        """
        precision = Parameters.ROAD_POINT_KEY_PRECISION
        return (int(round(x * precision)), int(round(y * precision)))

    @staticmethod
    def _signed_triangle_area(coords: list[tuple[float, float]]) -> float:
        """Return signed 2D triangle area.

        Arguments:
            coords (list[tuple[float, float]]): Triangle coordinates.

        Returns:
            float: Signed area, positive for counter-clockwise order.
        """
        return 0.5 * (
            coords[0][0] * (coords[1][1] - coords[2][1])
            + coords[1][0] * (coords[2][1] - coords[0][1])
            + coords[2][0] * (coords[0][1] - coords[1][1])
        )

    def _extract_polygons(self, geometry: Any) -> list[Polygon]:
        """Extract polygon parts from any Shapely geometry container.

        Arguments:
            geometry (Any): Input Shapely geometry.

        Returns:
            list[Polygon]: Extracted polygon parts.
        """
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
