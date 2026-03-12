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
from maps4fs.generator.component.base.component_mesh import (
    LineSurfaceEntry,
    MeshComponent,
)
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

        self.flatten_water_to: int | None = None

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
        flatten_to = None
        subtract_by = int(self.map.dem_settings.water_depth * z_scaling_factor)

        if self.map.background_settings.flatten_water:
            try:
                if not np.any(water_mask_image == 255):
                    self.logger.warning("No water pixels found in water mask image.")
                    return
                mask = water_mask_image == 255
                flatten_to = int(np.mean(dem_image[mask]) - subtract_by)
                self.flatten_water_to = flatten_to
            except Exception as e:
                self.logger.warning("Error occurred while flattening water: %s", e)

        dem_image = self.subtract_by_mask(
            dem_image,
            water_mask_image,
            subtract_by=subtract_by,
            flatten_to=flatten_to,
        )
        dem_image = self.blur_edges_by_mask(
            dem_image,
            water_mask_image,
            smaller_kernel=3,
            iterations=5,
            bigger_kernel=5,
        )

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
            if not polygon_points or len(polygon_points) < 2:
                continue

            polygon = shapely.Polygon(polygon_points)
            if polygon.is_empty or not polygon.is_valid:
                continue

            polygons.append(polygon.buffer(Parameters.WATER_ADD_WIDTH, quad_segs=4))

        fitted_polygons: list[shapely.Polygon] = []
        for polygon in polygons:
            try:
                fitted_points = self.fit_object_into_bounds(
                    polygon_points=polygon.exterior.coords,
                    angle=self.rotation,
                    canvas_size=self.background_size,
                    rotated_canvas_size=self.rotated_size,
                )
                fitted_polygons.append(shapely.Polygon(fitted_points))
            except Exception as e:
                self.logger.debug("Could not fit water polygon into bounds: %s", e)

        if not fitted_polygons:
            self.logger.warning("No valid polygon water features generated.")
            return

        mesh = self.mesh_from_3d_polygons(fitted_polygons, single_z_value=self.flatten_water_to)
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

        water_entries: list[LineSurfaceEntry] = []
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
                linestring = shapely.LineString(fitted_water)
            except ValueError as e:
                self.logger.debug("Water %s could not be fitted/converted: %s", water_id, e)
                continue

            width += Parameters.POLYLINE_WATER_WIDTH_EXTENSION
            water_entries.append(LineSurfaceEntry(linestring=linestring, width=width))

        if not water_entries:
            self.logger.warning("No valid water polylines found in background info layer.")
            return

        interpolated = self.smart_interpolation(water_entries)
        split_entries = self.split_long_line_surfaces(interpolated)

        obj_output_path = os.path.join(
            self.water_directory, Parameters.POLYLINE_WATER_MESH_FILENAME
        )

        dem_image = cv2.imread(self.not_substracted_path, cv2.IMREAD_UNCHANGED)
        if dem_image is None:
            self.logger.error("Could not read DEM image for polyline water generation.")
            return

        self.create_textured_linestrings_mesh(
            split_entries, obj_output_path, dem_override=dem_image
        )

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
        self, polygons: list[shapely.Polygon], single_z_value: int | None = None
    ) -> Trimesh | None:
        """Create one mesh from fitted water polygons."""
        all_vertices: list[np.ndarray] = []
        all_faces: list[np.ndarray] = []
        vertex_offset = 0

        not_resized_dem = cv2.imread(self.not_substracted_path, cv2.IMREAD_UNCHANGED)
        if not_resized_dem is None:
            self.logger.warning("Could not read non-subtracted DEM: %s", self.not_substracted_path)
            return None

        for polygon in polygons:
            exterior_coords = np.array(polygon.exterior.coords)
            exterior_2d = exterior_coords[:, :2]
            poly_2d = shapely.geometry.Polygon(
                exterior_2d,
                [np.array(ring.coords)[:, :2] for ring in polygon.interiors],
            )

            vertices_2d, faces = trimesh.creation.triangulate_polygon(poly_2d)

            vertices_3d: list[list[float]] = []
            for v in vertices_2d:
                dists = np.linalg.norm(exterior_2d - v[:2], axis=1)
                idx = np.argmin(dists)
                if single_z_value is None:
                    z = self.get_z_coordinate_from_dem(
                        not_resized_dem,
                        exterior_coords[idx, 0],
                        exterior_coords[idx, 1],
                    )
                    z = -z
                else:
                    z = single_z_value
                vertices_3d.append([float(v[0]), float(v[1]), float(z)])
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
