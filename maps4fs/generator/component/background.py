"""This module contains the Background component, which generates 3D obj files based on DEM data
around the map."""

from __future__ import annotations

import os
import shutil
from typing import Any

import cv2
import numpy as np
import shapely
import trimesh
from tqdm import tqdm
from trimesh import Trimesh

from maps4fs.generator.component.base.component_image import ImageComponent
from maps4fs.generator.component.base.component_mesh import MeshComponent
from maps4fs.generator.monitor import monitor_performance
from maps4fs.generator.settings import Parameters


class Background(MeshComponent, ImageComponent):
    """Component for creating 3D obj files based on DEM data around the map.

    Arguments:
        game (Game): The game instance for which the map is generated.
        coordinates (tuple[float, float]): The latitude and longitude of the center of the map.
        map_size (int): The size of the map in pixels (it's a square).
        rotated_map_size (int): The size of the map in pixels after rotation.
        rotation (int): The rotation angle of the map.
        map_directory (str): The directory where the map files are stored.
        logger (Any, optional): The logger to use. Must have at least three basic methods: debug,
            info, warning. If not provided, default logging will be used.
    """

    @monitor_performance
    def preprocess(self) -> None:
        """Registers the DEMs for the background terrain."""
        self.stl_preview_path = os.path.join(self.previews_directory, "background_dem.stl")

        if self.rotation:
            self.logger.debug("Rotation is enabled: %s.", self.rotation)
            output_size_multiplier = 1.5
        else:
            output_size_multiplier = 1

        self.background_size = self.map_size + Parameters.BACKGROUND_DISTANCE * 2
        self.rotated_size = int(self.background_size * output_size_multiplier)
        self.mesh_info: list[dict[str, Any]] = []

        self.background_directory = os.path.join(
            self.map_directory, Parameters.BACKGROUND_DIRECTORY
        )
        os.makedirs(self.background_directory, exist_ok=True)

        self.textured_mesh_directory = os.path.join(
            self.background_directory,
            Parameters.TEXTURED_MESH_DIRECTORY,
        )
        os.makedirs(self.textured_mesh_directory, exist_ok=True)

        self.assets_background_directory = os.path.join(
            self.map.assets_directory,
            Parameters.BACKGROUND_DIRECTORY,
        )
        os.makedirs(self.assets_background_directory, exist_ok=True)

        self.output_path = self.map.context.dem_path or os.path.join(
            self.background_directory,
            f"{Parameters.FULL}.png",
        )
        self.not_substracted_path: str = self.map.context.dem_not_subtracted_path or os.path.join(
            self.background_directory, "not_substracted.png"
        )

    def process(self) -> None:
        """Launches the component processing. Iterates over all tiles and processes them
        as a result the DEM files will be saved, then based on them the obj files will be
        generated."""
        cutted_dem_path = self._prepare_main_dem()

        if self.game.additional_dem_name is not None:
            self.make_copy(cutted_dem_path, self.game.additional_dem_name)

        self._generate_optional_assets()
        self.process_road_masks()

    def _prepare_main_dem(self) -> str:
        """Prepare and save DEM outputs used by downstream generation steps."""
        if not os.path.isfile(self.output_path):
            raise FileNotFoundError(
                f"Background DEM not found. Expected DEM component output: {self.output_path}"
            )

        self.validate_np_for_mesh(self.output_path, self.map_size)

        if not os.path.isfile(self.not_substracted_path):
            shutil.copyfile(self.output_path, self.not_substracted_path)

        cutted_dem_path = self.save_map_dem(self.output_path)
        self.save_map_dem(
            self.output_path, save_path=self.not_resized_path(Parameters.NOT_RESIZED_DEM)
        )

        if self.map.background_settings.flatten_roads:
            self.flatten_roads()

        return cutted_dem_path

    def _generate_optional_assets(self) -> None:
        """Generate optional background terrain assets based on settings."""
        if self.map.background_settings.generate_background:
            self.generate_obj_files()
            self.decimate_background_mesh()
            self.texture_background_mesh()
            self.convert_background_mesh_to_i3d()

    def not_resized_paths(self) -> list[str]:
        """Returns the list of paths to all not resized DEM files.

        Returns:
            list[str] : The list of paths to all not resized DEM files.
        """
        return [self.not_resized_path(dem_type) for dem_type in Parameters.SUPPORTED_DEM_TYPES]

    def not_resized_path(self, dem_type: str) -> str:
        """Returns the path to the specified not resized DEM file.

        Arguments:
            dem_type (str): The type of the DEM file. Must be one of the SUPPORTED_DEM_TYPES.

        Raises:
            ValueError: If the dem_type is not supported.

        Returns:
            str: The path to the specified not resized DEM file.
        """
        if not dem_type.endswith(".png"):
            dem_type += ".png"
        if dem_type not in Parameters.SUPPORTED_DEM_TYPES:
            raise ValueError(f"Unsupported dem_type: {dem_type}")

        return os.path.join(self.background_directory, dem_type)

    @monitor_performance
    def create_foundations(self, dem_image: np.ndarray) -> np.ndarray:
        """Creates foundations for buildings based on the DEM data.

        Arguments:
            dem_image (np.ndarray): The DEM data as a numpy array.

        Returns:
            np.ndarray: The DEM data with the foundations added.
        """
        buildings = self.get_infolayer_data(Parameters.TEXTURES, Parameters.BUILDINGS)
        if not buildings:
            self.logger.warning("Buildings data not found in textures info layer.")
            return dem_image

        self.logger.debug("Found %s buildings in textures info layer.", len(buildings))

        for building in tqdm(buildings, desc="Creating foundations", unit="building"):
            mask = self._get_building_mask(building, dem_image.shape)
            if mask is None:
                continue

            mean_value = np.round(cv2.mean(dem_image, mask=mask)[0]).astype(dem_image.dtype)  # type: ignore
            dem_image[mask == 255] = mean_value

        return dem_image

    def _get_building_mask(
        self,
        building: list[tuple[int, int]],
        dem_shape: tuple[int, ...],
    ) -> np.ndarray | None:
        """Create a raster mask for one building footprint in DEM coordinates."""
        try:
            fitted_building = self.fit_object_into_bounds(
                polygon_points=building,
                angle=self.rotation,
            )
        except ValueError as e:
            self.logger.debug("Building could not be fitted into the map bounds: %s", e)
            return None

        building_np = self.polygon_points_to_np(fitted_building)
        mask = np.zeros(dem_shape, dtype=np.uint8)
        try:
            cv2.fillPoly(mask, [building_np], 255)  # type: ignore
            return mask
        except Exception as e:
            self.logger.debug("Could not create building mask: %s", e)
            return None

    def make_copy(self, dem_path: str, dem_name: str) -> None:
        """Copies DEM data to additional DEM file.

        Arguments:
            dem_path (str): Path to the DEM file.
            dem_name (str): Name of the additional DEM file.
        """
        dem_directory = os.path.dirname(dem_path)

        additional_dem_path = os.path.join(dem_directory, dem_name)

        shutil.copyfile(dem_path, additional_dem_path)
        self.logger.debug("Additional DEM data was copied to %s.", additional_dem_path)

    def info_sequence(self) -> dict[str, str | float | int]:
        """Returns a dictionary with information about the background terrain.
        Adds the EPSG:3857 string to the data for convenient usage in QGIS.

        Returns:
            dict[str, str, float | int] -- A dictionary with information about the background
                terrain.
        """
        north, south, east, west = self.bbox

        data = {
            "center_latitude": self.coordinates[0],
            "center_longitude": self.coordinates[1],
            "height": self.map_size,
            "width": self.map_size,
            "north": north,
            "south": south,
            "east": east,
            "west": west,
        }
        data["Mesh"] = self.mesh_info
        return data  # type: ignore

    @monitor_performance
    def generate_obj_files(self) -> None:
        """Iterates over all dems and generates 3D obj files based on DEM data.
        If at least one DEM file is missing, the generation will be stopped at all.
        """
        if not os.path.isfile(self.output_path):
            self.logger.error(
                "DEM file not found, generation will be stopped: %s", self.output_path
            )
            return

        self.logger.debug("DEM file for found: %s", self.output_path)

        filename = os.path.splitext(os.path.basename(self.output_path))[0]
        save_path = os.path.join(self.background_directory, f"{filename}.obj")
        self.logger.debug("Generating obj file in path: %s", save_path)

        self.assets.background_mesh = save_path

        dem_data = cv2.imread(self.output_path, cv2.IMREAD_UNCHANGED)

        if self.map.output_size is not None:
            scaled_background_size = int(self.background_size * self.map.size_scale)
            dem_data = cv2.resize(
                dem_data,  # type: ignore
                (scaled_background_size, scaled_background_size),
                interpolation=cv2.INTER_NEAREST,
            )

        self.plane_from_np(
            dem_data,  # type: ignore
            save_path,
            create_preview=True,
            remove_center=self.map.background_settings.remove_center,
        )

    @staticmethod
    def get_decimate_factor(map_size: int) -> float:
        """Returns the decimation factor based on the map size.

        Arguments:
            map_size (int): The size of the map in pixels.

        Raises:
            ValueError: If the map size is too large for decimation.

        Returns:
            float -- The decimation factor.
        """
        thresholds = {
            2048: 0.1,
            4096: 0.05,
            8192: 0.025,
            16384: 0.0125,
        }
        for threshold, factor in thresholds.items():
            if map_size <= threshold:
                return factor
        raise ValueError(
            "Map size is too large for decimation, perform manual decimation in Blender."
        )

    @staticmethod
    def get_background_texture_resolution(map_size: int) -> int:
        """Returns the background texture resolution based on the map size.

        Arguments:
            map_size (int): The size of the map in pixels.

        Returns:
            int -- The background texture resolution.
        """
        resolutions = {
            2048: 2048,
            4096: Parameters.MAXIMUM_BACKGROUND_TEXTURE_SIZE,
            8192: Parameters.MAXIMUM_BACKGROUND_TEXTURE_SIZE,
            16384: Parameters.MAXIMUM_BACKGROUND_TEXTURE_SIZE,
        }
        for threshold, resolution in resolutions.items():
            if map_size <= threshold:
                return resolution
        return Parameters.MAXIMUM_BACKGROUND_TEXTURE_SIZE

    @monitor_performance
    def decimate_background_mesh(self) -> None:
        """Decimates the background mesh based on the map size."""
        if not self.assets.background_mesh or not os.path.isfile(self.assets.background_mesh):
            self.logger.warning("Background mesh not found, cannot generate i3d background.")
            return

        try:
            mesh = trimesh.load_mesh(self.assets.background_mesh, force="mesh")
        except Exception as e:
            self.logger.error("Could not load background mesh: %s", e)
            return

        try:
            decimate_factor = self.get_decimate_factor(self.map_size)
        except ValueError as e:
            self.logger.error("Could not determine decimation factor: %s", e)
            return

        decimated_save_path = os.path.join(
            self.background_directory, f"{Parameters.DECIMATED_BACKGROUND}.obj"
        )
        try:
            self.logger.debug("Decimating background mesh with factor %s.", decimate_factor)
            decimated_mesh = self.decimate_mesh(mesh, decimate_factor)
            self.logger.debug("Decimation completed.")
        except Exception as e:
            self.logger.error("Could not decimate background mesh: %s", e)
            return

        decimated_mesh.export(decimated_save_path)
        self.logger.debug("Decimated background mesh saved: %s", decimated_save_path)

        self.assets.decimated_background_mesh = decimated_save_path

    @monitor_performance
    def texture_background_mesh(self) -> None:
        """Textures the background mesh using satellite imagery."""
        decimated_background_mesh_path = self.assets.decimated_background_mesh
        if not decimated_background_mesh_path or not os.path.isfile(decimated_background_mesh_path):
            self.logger.warning(
                "Decimated background mesh not found, cannot texture background mesh."
            )
            return

        texture_bundle = self._prepare_background_texture_bundle()
        if texture_bundle is None:
            return
        resized_texture_save_path, texture_for_i3d = texture_bundle

        try:
            decimated_mesh = trimesh.load_mesh(decimated_background_mesh_path, force="mesh")
        except Exception as e:
            self.logger.error("Could not load decimated background mesh: %s", e)
            return

        try:
            obj_save_path, mtl_save_path = self.texture_mesh(
                decimated_mesh,
                resized_texture_save_path,
                output_directory=self.textured_mesh_directory,
                output_name="background_textured_mesh",
            )

            self.assets.textured_background_mesh = obj_save_path
            self.assets.textured_background_mtl = mtl_save_path
            self.assets.resized_background_texture = texture_for_i3d
            self.logger.debug("Textured background mesh saved: %s", obj_save_path)
        except Exception as e:
            self.logger.error("Could not texture background mesh: %s", e)
            return

    def _prepare_background_texture_bundle(self) -> tuple[str, str] | None:
        """Load, resize, and optionally convert the background texture to DDS."""
        background_texture_path = self.map.context.satellite_background_path
        if not background_texture_path or not os.path.isfile(background_texture_path):
            self.logger.warning("Background texture not found, cannot texture background mesh.")
            return None

        resolution = self.get_background_texture_resolution(self.map_size)
        source_image = cv2.imread(background_texture_path, cv2.IMREAD_UNCHANGED)
        if source_image is None:
            self.logger.error(
                "Failed to read background texture image: %s", background_texture_path
            )
            return None

        resized_texture_image = cv2.resize(
            source_image,  # type: ignore
            (resolution, resolution),
            interpolation=cv2.INTER_AREA,
        )
        resized_texture_save_path = os.path.join(
            self.textured_mesh_directory, "background_texture.jpg"
        )
        cv2.imwrite(resized_texture_save_path, resized_texture_image)

        dds_texture_save_path = os.path.join(self.textured_mesh_directory, "background_texture.dds")
        texture_for_i3d = resized_texture_save_path
        try:
            self.convert_png_to_dds(resized_texture_save_path, dds_texture_save_path)
            texture_for_i3d = dds_texture_save_path
        except Exception as e:
            self.logger.warning("Could not convert background texture to DDS: %s", e)

        return resized_texture_save_path, texture_for_i3d

    @monitor_performance
    def convert_background_mesh_to_i3d(self) -> bool:
        """Converts the textured background mesh to i3d format.

        Returns:
            bool -- True if the conversion was successful, False otherwise.
        """
        if not self.assets.textured_background_mesh or not os.path.isfile(
            self.assets.textured_background_mesh
        ):
            self.logger.warning("Textured background mesh not found, cannot convert to i3d.")
            return False

        if not self.assets.resized_background_texture or not os.path.isfile(
            self.assets.resized_background_texture
        ):
            self.logger.warning("Resized background texture not found, cannot convert to i3d.")
            return False

        try:
            mesh = trimesh.load_mesh(self.assets.textured_background_mesh, force="mesh")
        except Exception as e:
            self.logger.error("Could not load textured background mesh: %s", e)
            return False

        # Compute terrain max elevation and save for GE positioning.
        # The mesh is built with z_vertex = (pixel - max_pixel) * z_factor (inverted),
        # so T_y = max_pixel * z_factor maps every vertex back to its real elevation.
        try:
            background_dem = cv2.imread(self.not_substracted_path, cv2.IMREAD_UNCHANGED)
            if background_dem is not None:
                z_factor = self.get_z_scaling_factor(ignore_height_scale_multiplier=True)
                max_elevation = float(np.max(background_dem) * z_factor)
                self.map.context.set_mesh_position(
                    Parameters.BACKGROUND_TERRAIN,
                    mesh_centroid_y=max_elevation,
                )
                self.logger.debug("Background terrain T_y (max elevation): %.4f m", max_elevation)
        except Exception as e:
            self.logger.warning("Could not save background terrain elevation: %s", e)

        try:
            i3d_background_terrain = self.mesh_to_i3d(
                mesh,
                output_dir=self.assets_background_directory,
                name=Parameters.BACKGROUND_TERRAIN,
                texture_path=self.assets.resized_background_texture,
                water_mesh=False,
            )
            self.logger.debug(
                "Background mesh converted to i3d successfully: %s", i3d_background_terrain
            )
            self.assets.background_terrain_i3d = i3d_background_terrain
            return True
        except Exception as e:
            self.logger.error("Could not convert background mesh to i3d: %s", e)
            return False

    def map_dem_size(self) -> int:
        """Returns the size of the map DEM.

        Returns:
            int -- The size of the map DEM.
        """
        return self.scaled_size + 1

    def save_map_dem(self, dem_path: str, save_path: str | None = None) -> str:
        """Cuts out the center of the DEM (the actual map) and saves it as a separate file.

        Arguments:
            dem_path (str): The path to the DEM file.
            save_path (str, optional): The path where the cutout DEM file will be saved.

        Returns:
            str -- The path to the cutout DEM file.
        """
        dem_data = cv2.imread(dem_path, cv2.IMREAD_UNCHANGED)
        half_size = self.map_size // 2
        dem_data = self.cut_out_np(dem_data, half_size, return_cutout=True)  # type: ignore

        if save_path:
            cv2.imwrite(save_path, dem_data)
            self.logger.debug("Not resized DEM saved: %s", save_path)
            return save_path

        if self.map.dem_settings.add_foundations:
            dem_data = self.create_foundations(dem_data)
            cv2.imwrite(self.not_resized_path(Parameters.NOT_RESIZED_DEM_FOUNDATIONS), dem_data)
            self.logger.debug(
                "Not resized DEM with foundations saved: %s",
                self.not_resized_path(Parameters.NOT_RESIZED_DEM_FOUNDATIONS),
            )

        output_size = self.map_dem_size()

        main_dem_path = self.game.dem_file_path

        try:
            os.remove(main_dem_path)
        except FileNotFoundError:
            pass

        resized_dem_data = cv2.resize(
            dem_data, (output_size, output_size), interpolation=cv2.INTER_NEAREST
        )

        cv2.imwrite(main_dem_path, resized_dem_data)
        self.logger.debug("DEM cutout saved: %s", main_dem_path)

        self.assets.dem = main_dem_path

        return main_dem_path

    def plane_from_np(
        self,
        dem_data: np.ndarray,
        save_path: str,
        include_zeros: bool = True,
        create_preview: bool = False,
        remove_center: bool = False,
    ) -> None:
        """Generates a 3D obj file based on DEM data.

        Arguments:
            dem_data (np.ndarray) -- The DEM data as a numpy array.
            save_path (str) -- The path where the obj file will be saved.
            include_zeros (bool, optional) -- If True, the mesh will include the zero height values.
            create_preview (bool, optional) -- If True, a simplified mesh will be saved as an STL.
            remove_center (bool, optional) -- If True, the center of the mesh will be removed.
                This setting is used for a Background Terrain, where the center part where the
                playable area is will be cut out.
        """
        mesh = self.mesh_from_np(
            dem_data,
            include_zeros=include_zeros,
            z_scaling_factor=self.get_z_scaling_factor(ignore_height_scale_multiplier=True),
            remove_center=remove_center,
            remove_size=self.scaled_size,
            logger=self.logger,
        )

        try:
            self.update_mesh_info(save_path, mesh)
        except Exception as e:
            self.logger.error("Could not update mesh info: %s", e)

        mesh.export(save_path)
        self.logger.debug("Obj file saved: %s", save_path)

        if create_preview:
            try:
                mesh.apply_scale([0.5, 0.5, 0.5])
                self.mesh_to_stl(mesh, save_path=self.stl_preview_path)
            except Exception as e:
                self.logger.error("Could not create STL preview: %s", e)

    def update_mesh_info(self, save_path: str, mesh: Trimesh) -> None:
        """Updates the mesh info with the data from the mesh.

        Arguments:
            save_path (str): The path where the mesh is saved.
            mesh (Trimesh): The mesh to get the data from.
        """
        filename = os.path.splitext(os.path.basename(save_path))[0]
        x_size, y_size, z_size = mesh.extents
        x_center, y_center, z_center = mesh.centroid

        entry = {
            "name": filename,
            "x_size": round(x_size, 4),
            "y_size": round(y_size, 4),
            "z_size": round(z_size, 4),
            "x_center": round(x_center, 4),
            "y_center": round(y_center, 4),
            "z_center": round(z_center, 4),
        }

        self.mesh_info.append(entry)

    def previews(self) -> list[str]:
        """Returns the path to the image previews paths and the path to the STL preview file.

        Returns:
            list[str] -- A list of paths to the previews.
        """
        preview_paths = self.dem_previews(self.game.dem_file_path)

        background_dem_preview_path = os.path.join(self.previews_directory, "background_dem.png")

        if not os.path.isfile(self.output_path):
            self.logger.warning("DEM file not found for preview generation: %s", self.output_path)
            return []

        background_dem_preview_image = cv2.imread(self.output_path, cv2.IMREAD_UNCHANGED)

        background_dem_preview_image = cv2.resize(
            background_dem_preview_image, (0, 0), fx=1 / 4, fy=1 / 4  # type: ignore
        )
        background_dem_preview_image = cv2.normalize(
            background_dem_preview_image,
            dst=np.empty_like(background_dem_preview_image),
            alpha=0,
            beta=255,
            norm_type=cv2.NORM_MINMAX,
            dtype=cv2.CV_8U,
        )
        background_dem_preview_image = cv2.cvtColor(
            background_dem_preview_image, cv2.COLOR_GRAY2BGR
        )

        cv2.imwrite(background_dem_preview_path, background_dem_preview_image)
        preview_paths.append(background_dem_preview_path)

        if os.path.isfile(self.stl_preview_path):
            preview_paths.append(self.stl_preview_path)

        return preview_paths

    def dem_previews(self, image_path: str) -> list[str]:
        """Get list of preview images.

        Arguments:
            image_path (str): Path to the DEM file.

        Returns:
            list[str]: List of preview images.
        """
        self.logger.debug("Starting DEM previews generation.")
        return [self.grayscale_preview(image_path), self.colored_preview(image_path)]

    def grayscale_preview(self, image_path: str) -> str:
        """Converts DEM image to grayscale RGB image and saves it to the map directory.
        Returns path to the preview image.

        Arguments:
            image_path (str): Path to the DEM file.

        Returns:
            str: Path to the preview image.
        """
        grayscale_dem_path = os.path.join(self.previews_directory, "dem_grayscale.png")

        self.logger.debug("Creating grayscale preview of DEM data in %s.", grayscale_dem_path)

        dem_data = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        dem_data_rgb = cv2.cvtColor(dem_data, cv2.COLOR_GRAY2RGB)  # type: ignore
        cv2.imwrite(grayscale_dem_path, dem_data_rgb)
        return grayscale_dem_path

    def colored_preview(self, image_path: str) -> str:
        """Converts DEM image to colored RGB image and saves it to the map directory.
        Returns path to the preview image.

        Arguments:
            image_path (str): Path to the DEM file.

        Returns:
            list[str]: List with a single path to the DEM file
        """
        colored_dem_path = os.path.join(self.previews_directory, "dem_colored.png")

        self.logger.debug("Creating colored preview of DEM data in %s.", colored_dem_path)

        dem_data = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)

        # Create an empty array with the same shape and type as dem_data.
        dem_data_normalized = np.empty_like(dem_data)

        # Normalize the DEM data to the range [0, 255]
        cv2.normalize(dem_data, dem_data_normalized, 0, 255, cv2.NORM_MINMAX)  # type: ignore
        dem_data_colored = cv2.applyColorMap(dem_data_normalized, cv2.COLORMAP_JET)

        cv2.imwrite(colored_dem_path, dem_data_colored)
        return colored_dem_path

    @monitor_performance
    def flatten_roads(self) -> None:
        """Flattens the roads in the DEM data by averaging the height values along the road polylines."""
        dem_image = self._load_roads_base_dem()
        if dem_image is None:
            return

        roads_polylines = self.get_infolayer_data(Parameters.TEXTURES, Parameters.ROADS_POLYLINES)
        if not roads_polylines:
            self.logger.warning("No roads polylines found in textures info layer.")
            return

        self.logger.debug("Found %s roads polylines in textures info layer.", len(roads_polylines))

        full_mask = np.zeros(dem_image.shape, dtype=np.uint8)

        for road_polyline in tqdm(roads_polylines, desc="Flattening roads", unit="road"):
            road_result = self._flatten_single_road(road_polyline, dem_image)
            if road_result is None:
                continue

            road_y, road_x, interpolated_elevations = road_result
            dem_image[road_y, road_x] = interpolated_elevations
            full_mask[road_y, road_x] = 255

        main_dem_path = self.game.dem_file_path
        dem_image = self.blur_by_mask(dem_image, full_mask, blur_radius=5)
        dem_image = self.blur_edges_by_mask(dem_image, full_mask)

        # Save the not resized DEM with flattened roads.
        cv2.imwrite(self.not_resized_path(Parameters.NOT_RESIZED_DEM_ROADS), dem_image)
        self.logger.debug(
            "Not resized DEM with flattened roads saved to: %s",
            self.not_resized_path(Parameters.NOT_RESIZED_DEM_ROADS),
        )

        output_size = self.map_dem_size()
        resized_dem = cv2.resize(
            dem_image, (output_size, output_size), interpolation=cv2.INTER_NEAREST
        )

        cv2.imwrite(main_dem_path, resized_dem)
        self.logger.debug("Flattened roads saved to DEM file: %s", main_dem_path)

    def _load_roads_base_dem(self) -> np.ndarray | None:
        """Load the highest-priority DEM available for road flattening."""
        candidate_paths = [
            self.not_resized_path(Parameters.NOT_RESIZED_DEM_FOUNDATIONS),
            self.not_resized_path(Parameters.NOT_RESIZED_DEM),
        ]
        for candidate_path in candidate_paths:
            if not os.path.isfile(candidate_path):
                continue

            dem_image = cv2.imread(candidate_path, cv2.IMREAD_UNCHANGED)
            if dem_image is not None:
                return dem_image

        self.logger.warning("No DEM data found for flattening roads.")
        return None

    def _flatten_single_road(
        self,
        road_polyline: dict[str, Any],
        dem_image: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray] | None:
        """Return target pixels and interpolated elevations for one road polyline."""
        points = road_polyline.get("points")
        width = road_polyline.get("width")
        if not points or not width:
            self.logger.warning("Skipping road with insufficient data: %s", road_polyline)
            return None

        try:
            fitted_road = self.fit_object_into_bounds(linestring_points=points, angle=self.rotation)
        except ValueError as e:
            self.logger.debug("Road polyline could not be fitted into bounds: %s", e)
            return None

        polyline = shapely.LineString(fitted_road)
        total_length = polyline.length
        if total_length <= 0:
            return None

        line_thickness = int(width * 4)
        road_mask = np.zeros(dem_image.shape, dtype=np.uint8)
        dense_sample_distance = min(Parameters.SEGMENT_LENGTH, total_length / 100)
        num_dense_points = max(100, int(total_length / dense_sample_distance))
        dense_distances = np.linspace(0, total_length, num_dense_points)
        dense_points = [polyline.interpolate(d) for d in dense_distances]
        dense_coords = np.array([(int(p.x), int(p.y)) for p in dense_points], dtype=np.int32)
        if len(dense_coords) > 1:
            cv2.polylines(road_mask, [dense_coords], False, 255, thickness=line_thickness)

        road_pixels = np.where(road_mask == 255)
        if len(road_pixels[0]) == 0:
            return None
        road_y, road_x = road_pixels

        large_segment_length = Parameters.SEGMENT_LENGTH * 15
        num_large_segments = max(1, int(np.ceil(total_length / large_segment_length)))
        large_distances = np.linspace(0, total_length, num_large_segments + 1)

        segment_elevations = []
        for dist in large_distances:
            sample_point = polyline.interpolate(dist)
            sample_x, sample_y = int(sample_point.x), int(sample_point.y)
            sample_radius = max(5, line_thickness // 4)
            y_min = max(0, sample_y - sample_radius)
            y_max = min(dem_image.shape[0], sample_y + sample_radius)
            x_min = max(0, sample_x - sample_radius)
            x_max = min(dem_image.shape[1], sample_x + sample_radius)

            if y_max > y_min and x_max > x_min:
                sample_elevation = np.mean(dem_image[y_min:y_max, x_min:x_max])
            elif 0 <= sample_y < dem_image.shape[0] and 0 <= sample_x < dem_image.shape[1]:
                sample_elevation = dem_image[sample_y, sample_x]
            else:
                sample_elevation = 0
            segment_elevations.append(sample_elevation)

        road_distances_from_start = np.array(
            [
                polyline.project(polyline.interpolate(polyline.project(shapely.Point(px, py))))
                for px, py in zip(road_x, road_y)
            ]
        )
        interpolated_elevations = np.interp(
            road_distances_from_start,
            large_distances,
            segment_elevations,
        )
        return road_y, road_x, interpolated_elevations

    def process_road_masks(self) -> None:
        """Reads road mask images from the roads directory and saves bounding-box position
        data for each mask so the GE can position the road meshes correctly."""
        roads_directory = os.path.join(self.map_directory, "roads")
        if not os.path.isdir(roads_directory):
            self.logger.warning("Roads directory not found, skipping road mask processing.")
            return

        dem_image = self.get_dem_image_with_fallback()
        if dem_image is None:
            self.logger.warning("DEM image not found, skipping road mask processing.")
            return

        # Get all files in directory ending with _mask.png
        mask_files = [f for f in os.listdir(roads_directory) if f.endswith("_mask.png")]

        for mask_file in mask_files:
            mask_path = os.path.join(roads_directory, mask_file)
            mask = cv2.imread(mask_path, cv2.IMREAD_UNCHANGED)
            if mask is None:
                self.logger.warning("Could not read mask file: %s, skipping.", mask_path)
                continue
            if not np.any(mask):
                self.logger.warning(
                    "No non-zero pixels found in rotated mask, skipping road mask processing."
                )
                continue

            extremes = self.get_dem_extremes_by_mask(dem_image, mask)
            if extremes is None:
                self.logger.warning("No valid pixels found in DEM image for road mask, skipping.")
                continue

            (min_x, min_y, _), (max_x, max_y, _) = extremes

            min_z = self.get_z_coordinate_from_dem(dem_image, min_x, min_y)
            max_z = self.get_z_coordinate_from_dem(dem_image, max_x, max_y)

            # Compute the true pixel centroid of the mask (mean of all non-zero pixel coords).
            # This matches where mesh.vertices -= center places the mesh origin.
            ys, xs = np.where(mask > 0)
            centroid_x = int(np.mean(xs))
            centroid_y = int(np.mean(ys))

            base_filename = os.path.splitext(mask_file)[0].replace("_mask", "")
            self.map.context.set_mesh_position(
                base_filename,
                mesh_centroid_x=float(centroid_x),
                mesh_centroid_y=float((min_z + max_z) / 2),
                mesh_centroid_z=float(centroid_y),
            )

            try:
                os.remove(mask_path)
                self.logger.debug("Temporary road mask %s removed.", mask_path)
            except Exception as e:
                self.logger.warning(
                    "Error removing temporary road mask %s: %s.", mask_path, repr(e)
                )
