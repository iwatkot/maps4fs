"""Standalone water component for mask, DEM subtraction, and water mesh generation."""

from __future__ import annotations

import os
from copy import deepcopy

import cv2
import numpy as np
import shapely
import trimesh
from trimesh import Trimesh

from maps4fs.generator.component.base.component_image import ImageComponent
from maps4fs.generator.component.base.component_mesh import MeshComponent
from maps4fs.generator.component.texture import Texture, TextureOptions
from maps4fs.generator.monitor import monitor_performance
from maps4fs.generator.settings import Parameters


class Water(MeshComponent, ImageComponent):
    """Generates water mask/meshes and applies optional DEM water-depth subtraction."""

    @monitor_performance
    def preprocess(self) -> None:
        output_size_multiplier = 1.5 if self.rotation else 1
        self.background_size = self.map_size + Parameters.BACKGROUND_DISTANCE * 2
        self.rotated_size = int(self.background_size * output_size_multiplier)

        self.background_directory = os.path.join(
            self.map_directory, Parameters.BACKGROUND_DIRECTORY
        )
        self.water_directory = os.path.join(self.map_directory, Parameters.WATER_DIRECTORY)
        self.assets_water_directory = os.path.join(
            self.map.assets_directory,
            Parameters.WATER_DIRECTORY,
        )
        os.makedirs(self.background_directory, exist_ok=True)
        os.makedirs(self.water_directory, exist_ok=True)
        os.makedirs(self.assets_water_directory, exist_ok=True)

        self.output_path = self.map.context.dem_path or os.path.join(
            self.background_directory,
            f"{Parameters.FULL}.png",
        )
        self.water_mask_path = os.path.join(self.water_directory, Parameters.WATER_MASK_FILENAME)
        self.not_substracted_path = os.path.join(self.background_directory, "not_substracted.png")

        self.map.context.water_mask_path = self.water_mask_path
        self.map.context.dem_not_subtracted_path = self.not_substracted_path

        self.flattened_water_dem: np.ndarray | None = None

    @monitor_performance
    def process(self) -> None:
        self.create_water_mask()

        if not os.path.isfile(self.output_path):
            self.logger.warning("DEM file not found for water processing: %s", self.output_path)
            return

        shutil_src = self.output_path
        shutil_dst = self.not_substracted_path
        if os.path.isfile(shutil_src):
            import shutil

            shutil.copyfile(shutil_src, shutil_dst)

        if self.map.dem_settings.water_depth:
            self.subtract_water_depth()

        if self.map.background_settings.generate_water:
            self.generate_water_assets()

    @monitor_performance
    def create_water_mask(self) -> None:
        """Create polygon-water mask image from background-tagged texture schema layers."""
        layers_schema = self.map.texture_schema
        if not layers_schema:
            self.logger.warning("No texture schema found.")
            return

        background_layers = []
        for layer in layers_schema:
            if layer.get("background") is True:
                layer_copy = deepcopy(layer)
                layer_copy["count"] = 1
                layer_copy["name"] = f"{layer['name']}_background"
                background_layers.append(layer_copy)

        if not background_layers:
            self.logger.warning("No background layers found for water mask generation.")
            return

        background_texture = Texture(
            self.game,
            self.map,
            map_size=self.background_size,
            map_rotated_size=self.rotated_size,
            options=TextureOptions(
                texture_custom_schema=background_layers,
                skip_scaling=True,
                channel="background",
                cap_style="flat",
            ),
        )
        background_texture.preprocess()
        background_texture.process()

        processed_layers = background_texture.get_background_layers()
        weights_directory = self.game.weights_dir_path
        background_paths = [layer.path(weights_directory) for layer in processed_layers]
        if not background_paths:
            self.logger.warning("No rendered background texture layers found for water mask.")
            return

        background_image: np.ndarray = np.zeros(
            (self.background_size, self.background_size), dtype=np.uint8
        )
        for path in background_paths:
            layer_image = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
            if layer_image is not None:
                background_image = cv2.add(background_image, layer_image)

        cv2.imwrite(self.water_mask_path, background_image)
        self.logger.debug("Water mask created: %s", self.water_mask_path)

    @staticmethod
    def _normalize_kernel_size(kernel_size: int, minimum: int = 3) -> int:
        """Return a valid odd kernel size for Gaussian blur."""
        try:
            kernel_size = int(kernel_size)
        except (TypeError, ValueError):
            kernel_size = minimum

        kernel_size = max(kernel_size, minimum)
        if kernel_size % 2 == 0:
            kernel_size += 1
        return kernel_size

    @staticmethod
    def _build_water_mask(
        image_mask: np.ndarray,
        mask_by: int = 255,
        erode_kernel: int | None = 3,
        erode_iter: int | None = 1,
    ) -> np.ndarray:
        """Build and optionally erode boolean water mask."""
        mask = image_mask == mask_by
        if erode_kernel and erode_iter:
            mask = cv2.erode(
                mask.astype(np.uint8),
                np.ones((erode_kernel, erode_kernel), np.uint8),
                iterations=erode_iter,
            ).astype(bool)
        return mask

    @classmethod
    def _smooth_dem_by_mask(
        cls,
        dem_image: np.ndarray,
        water_mask: np.ndarray,
        blur_radius: int,
    ) -> np.ndarray:
        """Smooth DEM over water mask while preserving broad elevation trends."""
        dem_float = dem_image.astype(np.float32)
        if not np.any(water_mask):
            return dem_float

        kernel_size = cls._normalize_kernel_size(blur_radius)
        mask_float = water_mask.astype(np.float32)

        weighted_dem = cv2.GaussianBlur(
            dem_float * mask_float,
            (kernel_size, kernel_size),
            sigmaX=0,
            sigmaY=0,
        )
        weights = cv2.GaussianBlur(
            mask_float,
            (kernel_size, kernel_size),
            sigmaX=0,
            sigmaY=0,
        )

        smoothed = dem_float.copy()
        valid_weights = weights > 1e-6
        smoothed[valid_weights] = weighted_dem[valid_weights] / weights[valid_weights]
        return smoothed

    @classmethod
    def build_flattened_water_dem(
        cls,
        dem_image: np.ndarray,
        water_mask: np.ndarray,
        subtract_by: int,
        blur_radius: int,
    ) -> np.ndarray:
        """Return a DEM with smoothed, depth-shifted elevations inside water mask."""
        smoothed_dem = cls._smooth_dem_by_mask(dem_image, water_mask, blur_radius)
        lowered = smoothed_dem - float(subtract_by)

        if np.issubdtype(dem_image.dtype, np.integer):
            dtype_info = np.iinfo(dem_image.dtype)
            lowered = np.clip(lowered, dtype_info.min, dtype_info.max)

        flattened_dem = dem_image.copy()
        flattened_dem[water_mask] = lowered[water_mask].astype(dem_image.dtype)
        return flattened_dem

    @staticmethod
    def _make_geometry_valid(geometry: object) -> object:
        """Return a valid geometry, attempting lightweight repairs when needed."""
        if geometry is None:
            return geometry

        if hasattr(geometry, "is_empty") and geometry.is_empty:
            return geometry

        try:
            if hasattr(geometry, "is_valid") and not geometry.is_valid:
                if hasattr(shapely, "make_valid"):
                    geometry = shapely.make_valid(geometry)
                else:
                    geometry = geometry.buffer(0)
        except Exception:
            return geometry

        return geometry

    @staticmethod
    def _extract_polygon_parts(geometry: object) -> list[shapely.Polygon]:
        """Extract non-empty polygon parts from Polygon/MultiPolygon/GeometryCollection."""
        polygon_cls = shapely.geometry.Polygon
        multi_polygon_cls = shapely.geometry.MultiPolygon
        geometry_collection_cls = shapely.geometry.GeometryCollection

        candidates: list[shapely.Polygon] = []
        if isinstance(geometry, polygon_cls):
            candidates = [geometry]
        elif isinstance(geometry, multi_polygon_cls):
            candidates = [geom for geom in geometry.geoms if isinstance(geom, polygon_cls)]
        elif isinstance(geometry, geometry_collection_cls):
            candidates = [geom for geom in geometry.geoms if isinstance(geom, polygon_cls)]

        result: list[shapely.Polygon] = []
        for polygon in candidates:
            if polygon.is_empty:
                continue
            if not polygon.is_valid:
                try:
                    polygon = polygon.buffer(0)
                except Exception:
                    continue
            if polygon.is_empty or polygon.area <= 1e-6:
                continue
            result.append(polygon)

        return result

    @staticmethod
    def _triangulate_polygon_2d(poly_2d: shapely.Polygon) -> tuple[np.ndarray, np.ndarray] | None:
        """Triangulate polygon and keep only triangles that lie inside the polygon."""
        triangles = shapely.ops.triangulate(poly_2d)
        if not triangles:
            return None

        vertices: list[list[float]] = []
        faces: list[list[int]] = []
        vertex_index: dict[tuple[float, float], int] = {}
        area_ratio_threshold = 0.995

        for triangle in triangles:
            if triangle.is_empty or triangle.area <= 1e-8:
                continue

            try:
                overlap_area = triangle.intersection(poly_2d).area
            except Exception:
                continue

            if overlap_area <= 1e-8:
                continue
            if overlap_area / triangle.area < area_ratio_threshold:
                continue

            coords = list(triangle.exterior.coords)[:-1]
            if len(coords) != 3:
                continue

            face: list[int] = []
            for x, y in coords:
                key = (round(float(x), 6), round(float(y), 6))
                idx = vertex_index.get(key)
                if idx is None:
                    idx = len(vertices)
                    vertex_index[key] = idx
                    vertices.append([float(x), float(y)])
                face.append(idx)

            if len(set(face)) == 3:
                faces.append(face)

        if not vertices or not faces:
            return None

        return np.asarray(vertices, dtype=np.float64), np.asarray(faces, dtype=np.int64)

    @staticmethod
    def _dedupe_linestring_points(
        points: list[tuple[int, int]] | list[tuple[float, float]],
    ) -> list[tuple[float, float]]:
        """Remove consecutive duplicate points from a linestring point sequence."""
        deduped: list[tuple[float, float]] = []
        for x, y in points:
            current = (float(x), float(y))
            if deduped and deduped[-1] == current:
                continue
            deduped.append(current)
        return deduped

    @monitor_performance
    def subtract_water_depth(self) -> None:
        """Subtract water depth from DEM where polygon-water mask is present."""
        if not os.path.isfile(self.water_mask_path):
            self.logger.warning("Water mask texture was not generated, skipping subtraction.")
            return

        water_mask_image = cv2.imread(self.water_mask_path, cv2.IMREAD_UNCHANGED)
        dem_image = cv2.imread(self.output_path, cv2.IMREAD_UNCHANGED)
        if water_mask_image is None or dem_image is None:
            self.logger.warning("DEM or water mask could not be read, skipping subtraction.")
            return

        z_scaling_factor: float = (
            self.map.context.mesh_z_scaling_factor
            if self.map.context.mesh_z_scaling_factor is not None
            else 257
        )
        subtract_by = int(self.map.dem_settings.water_depth * z_scaling_factor)
        flatten_applied = False

        if self.map.background_settings.flatten_water:
            try:
                water_mask = self._build_water_mask(
                    water_mask_image,
                    mask_by=255,
                    erode_kernel=3,
                    erode_iter=1,
                )
                if not np.any(water_mask):
                    self.logger.warning("No water pixels found in water mask image.")
                else:
                    dem_image = self.build_flattened_water_dem(
                        dem_image,
                        water_mask,
                        subtract_by=subtract_by,
                        blur_radius=self.map.background_settings.water_blurriness,
                    )
                    flatten_applied = True
            except Exception as e:
                self.logger.warning("Error occurred while flattening water: %s", e)

        if not flatten_applied:
            dem_image = self.subtract_by_mask(
                dem_image,
                water_mask_image,
                subtract_by=subtract_by,
                erode_kernel=3,
                erode_iter=1,
            )

        dem_image = self.blur_edges_by_mask(
            dem_image,
            water_mask_image,
            smaller_kernel=3,
            iterations=5,
            bigger_kernel=5,
        )

        if flatten_applied:
            self.flattened_water_dem = dem_image.copy()
        else:
            self.flattened_water_dem = None

        cv2.imwrite(self.output_path, dem_image)
        self.logger.debug("Water depth subtracted from DEM data: %s", self.output_path)

    @monitor_performance
    def generate_water_assets(self) -> None:
        """Generate polygon and polyline water assets."""
        self.logger.debug("Starting water generation for polygon/polyline assets...")

        try:
            self.generate_polyline_water()
        except Exception as e:
            self.logger.error("Error during polyline water generation: %s", e)

        try:
            self.generate_polygon_water()
        except Exception as e:
            self.logger.error("Error during polygon water generation: %s", e)

        self.convert_polygon_water_to_i3d()

    def convert_polygon_water_to_i3d(self) -> bool:
        """Convert polygon-water OBJ mesh to i3d and publish mesh centroid in context."""
        if not self.assets.polygon_water_mesh or not os.path.isfile(self.assets.polygon_water_mesh):
            self.logger.warning("Polygon water mesh not found, cannot convert to i3d.")
            return False

        try:
            mesh = trimesh.load_mesh(self.assets.polygon_water_mesh, force="mesh")
        except Exception as e:
            self.logger.error("Could not load polygon water mesh: %s", e)
            return False

        rotation_matrix = trimesh.transformations.rotation_matrix(-np.pi / 2, [1, 0, 0])
        mesh.apply_transform(rotation_matrix)
        center = mesh.vertices.mean(axis=0)

        background_dem = cv2.imread(self.not_substracted_path, cv2.IMREAD_UNCHANGED)
        if background_dem is not None:
            elevation = self.get_z_coordinate_from_dem(
                background_dem, int(center[0]), int(center[2])
            )
        else:
            elevation = float(center[1])

        self.map.context.set_mesh_position(
            Parameters.POLYGON_WATER,
            mesh_centroid_x=float(center[0]),
            mesh_centroid_y=float(elevation),
            mesh_centroid_z=float(center[2]),
        )

        try:
            i3d_polygon_water = self.mesh_to_i3d(
                mesh,
                output_dir=self.assets_water_directory,
                name=Parameters.POLYGON_WATER,
                water_mesh=True,
                rotate_mesh=False,
                center_mesh=True,
            )
            self.logger.debug(
                "Polygon water mesh converted to i3d successfully: %s", i3d_polygon_water
            )
            self.assets.polygon_water_i3d = i3d_polygon_water
            return True
        except Exception as e:
            self.logger.error("Could not convert polygon water mesh to i3d: %s", e)
            return False

    def generate_polygon_water(self) -> None:
        """Generate polygon-water mesh from background water polygons."""
        water_polygons = self.get_infolayer_data(Parameters.BACKGROUND, Parameters.WATER)
        if not water_polygons:
            self.logger.warning("No water polygons found in background info layer.")
            return

        polygons: list[shapely.Polygon] = []
        for polygon_points in water_polygons:
            if not polygon_points or len(polygon_points) < 3:
                continue

            polygon = shapely.Polygon(polygon_points)
            polygon = self._make_geometry_valid(polygon)
            polygon_parts = self._extract_polygon_parts(polygon)
            if not polygon_parts:
                continue

            for polygon_part in polygon_parts:
                buffered = polygon_part.buffer(Parameters.WATER_ADD_WIDTH, quad_segs=4)
                buffered = self._make_geometry_valid(buffered)
                polygons.extend(self._extract_polygon_parts(buffered))

        fitted_polygons: list[shapely.Polygon] = []
        for polygon in polygons:
            try:
                fitted_points = self.fit_object_into_bounds(
                    polygon_points=polygon.exterior.coords,
                    angle=self.rotation,
                    canvas_size=self.background_size,
                    rotated_canvas_size=self.rotated_size,
                )
                fitted_polygon = shapely.Polygon(fitted_points)
                fitted_polygon = self._make_geometry_valid(fitted_polygon)
                fitted_polygons.extend(self._extract_polygon_parts(fitted_polygon))
            except Exception as e:
                self.logger.debug("Could not fit water polygon into bounds: %s", e)

        if not fitted_polygons:
            self.logger.warning("No valid polygon water features generated.")
            return

        dem_override = (
            self.flattened_water_dem if self.map.background_settings.flatten_water else None
        )
        mesh = self.mesh_from_3d_polygons(fitted_polygons, dem_override=dem_override)
        if mesh is None:
            self.logger.warning("No mesh could be created from polygon water features.")
            return

        mesh = self.rotate_mesh(mesh)
        mesh = self.invert_faces(mesh)

        polygon_save_path = os.path.join(
            self.water_directory, Parameters.POLYGON_WATER_MESH_FILENAME
        )
        mesh.export(polygon_save_path)
        self.assets.polygon_water_mesh = polygon_save_path

    def generate_polyline_water(self) -> None:
        """Generate polyline-water i3d from background water polylines."""
        water_infos = self.get_infolayer_data(Parameters.BACKGROUND, Parameters.WATER_POLYLINES)
        if not water_infos:
            self.logger.warning("Water polylines data not found in background info layer.")
            return

        water_polygons: list[shapely.Polygon] = []
        for water_id, water_info in enumerate(water_infos, start=1):
            if not isinstance(water_info, dict):
                continue
            points = water_info.get(Parameters.POINTS)
            width = water_info.get(Parameters.WIDTH)
            if not points or len(points) < 2 or not width:
                self.logger.debug("Invalid water data for water ID %s: %s", water_id, water_info)
                continue

            try:
                fitted_water = self.fit_object_into_bounds(
                    linestring_points=points,
                    angle=self.rotation,
                    canvas_size=self.background_size,
                    rotated_canvas_size=self.rotated_size,
                )
                fitted_water = self._dedupe_linestring_points(fitted_water)
                if len(fitted_water) < 2:
                    continue

                linestring = shapely.LineString(fitted_water)
                if linestring.is_empty or linestring.length <= 1e-6:
                    continue
            except ValueError as e:
                self.logger.debug("Water %s could not be fitted/converted: %s", water_id, e)
                continue

            try:
                half_width = float(width) + float(Parameters.POLYLINE_WATER_WIDTH_EXTENSION)
                if half_width <= 0:
                    continue

                buffered = linestring.buffer(
                    half_width,
                    cap_style="flat",
                    join_style="round",
                    quad_segs=4,
                )
            except Exception as e:
                self.logger.debug("Could not buffer water polyline %s: %s", water_id, e)
                continue

            buffered = self._make_geometry_valid(buffered)
            polygon_parts = self._extract_polygon_parts(buffered)
            if not polygon_parts:
                self.logger.debug("Buffered water polyline %s yielded no polygon parts.", water_id)
                continue

            water_polygons.extend(polygon_parts)

        if not water_polygons:
            self.logger.warning("No valid water polylines found in background info layer.")
            return

        obj_output_path = os.path.join(
            self.water_directory, Parameters.POLYLINE_WATER_MESH_FILENAME
        )

        dem_image = cv2.imread(self.not_substracted_path, cv2.IMREAD_UNCHANGED)
        if dem_image is None:
            self.logger.error("Could not read DEM image for polyline water generation.")
            return

        polyline_dem_override = dem_image
        if self.map.background_settings.flatten_water and self.flattened_water_dem is not None:
            polyline_dem_override = self.flattened_water_dem

        mesh = self.mesh_from_3d_polygons(water_polygons, dem_override=polyline_dem_override)
        if mesh is None:
            self.logger.warning("No mesh could be created from polyline water features.")
            return

        mesh = self.invert_faces(mesh)

        mesh.export(obj_output_path)

        mesh = trimesh.load_mesh(obj_output_path, force="mesh", process=False)
        rotation_matrix = trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0])
        mesh.apply_transform(rotation_matrix)

        vertices = mesh.vertices
        center = vertices.mean(axis=0)
        mesh.vertices = vertices - center

        self.map.context.set_mesh_position(
            Parameters.POLYLINE_WATER,
            mesh_centroid_x=float(center[0]),
            mesh_centroid_y=float(center[1]),
            mesh_centroid_z=float(center[2]),
        )

        self.mesh_to_i3d(
            mesh,
            self.assets_water_directory,
            Parameters.POLYLINE_WATER,
            water_mesh=True,
            rotate_mesh=False,
            center_mesh=False,
        )

    def mesh_from_3d_polygons(
        self,
        polygons: list[shapely.Polygon],
        dem_override: np.ndarray | None = None,
    ) -> Trimesh | None:
        """Create one mesh from fitted water polygons."""
        all_vertices: list[np.ndarray] = []
        all_faces: list[np.ndarray] = []
        vertex_offset = 0

        if dem_override is not None:
            not_resized_dem = dem_override
        else:
            not_resized_dem = cv2.imread(self.not_substracted_path, cv2.IMREAD_UNCHANGED)
            if not_resized_dem is None:
                self.logger.warning(
                    "Could not read non-subtracted DEM: %s", self.not_substracted_path
                )
                return None

        for polygon in polygons:
            exterior_coords = np.array(polygon.exterior.coords)
            exterior_2d = exterior_coords[:, :2]
            poly_2d = shapely.geometry.Polygon(
                exterior_2d,
                [np.array(ring.coords)[:, :2] for ring in polygon.interiors],
            )

            poly_2d = self._make_geometry_valid(poly_2d)
            polygon_parts = self._extract_polygon_parts(poly_2d)
            if not polygon_parts:
                continue

            for polygon_part in polygon_parts:
                triangulated = self._triangulate_polygon_2d(polygon_part)
                if triangulated is None:
                    continue

                vertices_2d, faces = triangulated

                vertices_3d: list[list[float]] = []
                for v in vertices_2d:
                    z = self.get_z_coordinate_from_dem(not_resized_dem, float(v[0]), float(v[1]))
                    vertices_3d.append([float(v[0]), float(v[1]), float(-z)])
                vertices_3d_np = np.array(vertices_3d)

                faces = faces + vertex_offset
                all_vertices.append(vertices_3d_np)
                all_faces.append(faces)
                vertex_offset += len(vertices_3d_np)

        if not all_vertices:
            return None

        vertices = np.vstack(all_vertices)
        faces = np.vstack(all_faces)
        return trimesh.Trimesh(vertices=vertices, faces=faces, process=False)
