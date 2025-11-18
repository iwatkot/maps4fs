"""This module contains the Background component, which generates 3D obj files based on DEM data
around the map."""

from __future__ import annotations

import os
import shutil
from copy import deepcopy
from typing import Any, Literal

import cv2
import numpy as np
import shapely
import trimesh
from tqdm import tqdm
from trimesh import Trimesh

from maps4fs.generator.component.base.component_image import ImageComponent
from maps4fs.generator.component.base.component_mesh import MeshComponent
from maps4fs.generator.component.dem import DEM
from maps4fs.generator.component.texture import Texture
from maps4fs.generator.monitor import monitor_performance
from maps4fs.generator.settings import Parameters

SEGMENT_LENGTH = 2

# Note: the DEM types sorted by priority for usage with fallbacks.
# Starting from the most detailed to the least detailed.
SUPPORTED_DEM_TYPES = [
    Parameters.NOT_RESIZED_DEM_ROADS,
    Parameters.NOT_RESIZED_DEM_FOUNDATIONS,
    Parameters.NOT_RESIZED_DEM,
]


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

        self.background_directory = os.path.join(self.map_directory, "background")
        self.water_directory = os.path.join(self.map_directory, "water")
        os.makedirs(self.background_directory, exist_ok=True)
        os.makedirs(self.water_directory, exist_ok=True)

        self.textured_mesh_directory = os.path.join(self.background_directory, "textured_mesh")
        os.makedirs(self.textured_mesh_directory, exist_ok=True)

        self.assets_background_directory = os.path.join(self.map.assets_directory, "background")
        self.assets_water_directory = os.path.join(self.map.assets_directory, "water")
        os.makedirs(self.assets_background_directory, exist_ok=True)
        os.makedirs(self.assets_water_directory, exist_ok=True)

        self.water_resources_path = os.path.join(self.water_directory, "water_resources.png")

        self.output_path = os.path.join(self.background_directory, f"{Parameters.FULL}.png")
        if self.map.custom_background_path:
            self.validate_np_for_mesh(self.map.custom_background_path, self.map_size)
            shutil.copyfile(self.map.custom_background_path, self.output_path)

        self.not_substracted_path: str = os.path.join(
            self.background_directory, "not_substracted.png"
        )

        self.flatten_water_to: int | None = None

        self.dem = DEM(
            self.game,
            self.map,
            self.coordinates,
            self.background_size,
            self.rotated_size,
            self.rotation,
            self.map_directory,
            self.logger,
        )
        self.dem.preprocess()
        self.dem.set_output_resolution((self.rotated_size, self.rotated_size))
        self.dem.set_dem_path(self.output_path)

    def process(self) -> None:
        """Launches the component processing. Iterates over all tiles and processes them
        as a result the DEM files will be saved, then based on them the obj files will be
        generated."""
        self.create_background_textures()

        if not self.map.custom_background_path:
            self.dem.process()
            self.validate_np_for_mesh(self.output_path, self.map_size)
        else:
            custom_dem_data = cv2.imread(self.map.custom_background_path, cv2.IMREAD_UNCHANGED)
            self.dem.determine_height_scale(custom_dem_data, adjust=False)

        if self.map.dem_settings.water_depth:
            self.subtraction()

        cutted_dem_path = self.save_map_dem(self.output_path)
        shutil.copyfile(self.output_path, self.not_substracted_path)
        self.save_map_dem(
            self.output_path, save_path=self.not_resized_path(Parameters.NOT_RESIZED_DEM)
        )

        if self.map.background_settings.flatten_roads:
            self.flatten_roads()

        if self.game.additional_dem_name is not None:
            self.make_copy(cutted_dem_path, self.game.additional_dem_name)

        if self.map.background_settings.generate_background:
            self.generate_obj_files()
            if self.game.mesh_processing:
                self.logger.debug("Mesh processing is enabled, will decimate, texture and convert.")
                self.decimate_background_mesh()
                self.texture_background_mesh()
                background_conversion_result = self.convert_background_mesh_to_i3d()
                if background_conversion_result:
                    self.add_note_file(asset="background")
            else:
                self.logger.warning(
                    "Mesh processing is disabled for the game, skipping background mesh processing."
                )
        if self.map.background_settings.generate_water:
            self.generate_water_resources_obj()
            if self.game.mesh_processing:
                self.logger.debug("Mesh processing is enabled, will convert water mesh to i3d.")
                water_conversion_result = self.convert_water_mesh_to_i3d()
                if water_conversion_result:
                    self.add_note_file(asset="water")
            else:
                self.logger.warning(
                    "Mesh processing is disabled for the game, skipping water mesh processing."
                )

    def not_resized_paths(self) -> list[str]:
        """Returns the list of paths to all not resized DEM files.

        Returns:
            list[str] : The list of paths to all not resized DEM files.
        """
        return [self.not_resized_path(dem_type) for dem_type in SUPPORTED_DEM_TYPES]

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
        if dem_type not in SUPPORTED_DEM_TYPES:
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
            try:
                fitted_building = self.fit_object_into_bounds(
                    polygon_points=building, angle=self.rotation
                )
            except ValueError as e:
                self.logger.debug(
                    "Building could not be fitted into the map bounds with error: %s",
                    e,
                )
                continue

            # 1. Read the pixel values from the DEM image.
            # 2. Calculate the average pixel value of the building area.
            # 3. Set the pixel values in the DEM to the average pixel value.

            building_np = self.polygon_points_to_np(fitted_building)
            mask = np.zeros(dem_image.shape, dtype=np.uint8)

            try:
                cv2.fillPoly(mask, [building_np], 255)  # type: ignore
            except Exception as e:
                self.logger.debug("Could not create mask for building with error: %s", e)
                continue

            mean_value = cv2.mean(dem_image, mask=mask)[0]  # type: ignore
            mean_value = np.round(mean_value).astype(dem_image.dtype)
            self.logger.debug("Mean value of the building area: %s", mean_value)

            # Set the pixel values in the DEM to the average pixel value.
            dem_image[mask == 255] = mean_value

        return dem_image

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
        self.qgis_sequence()

        north, south, east, west = self.dem.bbox
        epsg3857_string = self.dem.get_epsg3857_string()
        epsg3857_string_with_margin = self.dem.get_epsg3857_string(add_margin=True)

        data = {
            "center_latitude": self.dem.coordinates[0],
            "center_longitude": self.dem.coordinates[1],
            "epsg3857_string": epsg3857_string,
            "epsg3857_string_with_margin": epsg3857_string_with_margin,
            "height": self.dem.map_size,
            "width": self.dem.map_size,
            "north": north,
            "south": south,
            "east": east,
            "west": west,
        }

        dem_info_sequence = self.dem.info_sequence()
        data["DEM"] = dem_info_sequence
        data["Mesh"] = self.mesh_info
        return data  # type: ignore

    def qgis_sequence(self) -> None:
        """Generates QGIS scripts for creating bounding box layers and rasterizing them."""
        qgis_layer = (f"Background_{Parameters.FULL}", *self.dem.get_espg3857_bbox())
        qgis_layer_with_margin = (
            f"Background_{Parameters.FULL}_margin",
            *self.dem.get_espg3857_bbox(add_margin=True),
        )
        self.create_qgis_scripts([qgis_layer, qgis_layer_with_margin])

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
        satellite_component = self.map.get_satellite_component()
        if not satellite_component:
            self.logger.warning("Satellite component not found, cannot texture background mesh.")
            return

        background_texture_path = satellite_component.assets.background

        if not background_texture_path or not os.path.isfile(background_texture_path):
            self.logger.warning("Background texture not found, cannot texture background mesh.")
            return

        decimated_background_mesh_path = self.assets.decimated_background_mesh
        if not decimated_background_mesh_path or not os.path.isfile(decimated_background_mesh_path):
            self.logger.warning(
                "Decimated background mesh not found, cannot texture background mesh."
            )
            return

        background_texture_resolution = self.get_background_texture_resolution(self.map_size)
        non_resized_texture_image = cv2.imread(background_texture_path, cv2.IMREAD_UNCHANGED)

        if non_resized_texture_image is None:
            self.logger.error(
                "Failed to read background texture image: %s", background_texture_path
            )
            return

        resized_texture_image = cv2.resize(
            non_resized_texture_image,  # type: ignore
            (background_texture_resolution, background_texture_resolution),
            interpolation=cv2.INTER_AREA,
        )

        resized_texture_save_path = os.path.join(
            self.textured_mesh_directory,
            "background_texture.jpg",
        )

        cv2.imwrite(resized_texture_save_path, resized_texture_image)
        self.logger.debug("Resized background texture saved: %s", resized_texture_save_path)

        decimated_mesh = trimesh.load_mesh(decimated_background_mesh_path, force="mesh")

        if decimated_mesh is None:
            self.logger.error("Failed to load decimated mesh after all retry attempts")
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
            self.assets.resized_background_texture = resized_texture_save_path
            self.logger.debug("Textured background mesh saved: %s", obj_save_path)
        except Exception as e:
            self.logger.error("Could not texture background mesh: %s", e)
            return

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

    def add_note_file(self, asset: Literal["background", "water"]) -> None:
        """Adds a note file to the background or water directory.

        Arguments:
            asset (Literal["background", "water"]): The asset type to add the note file to.
        """
        filename = "DO_NOT_USE_THESE_FILES.txt"
        note_template = (
            "Please find the ready-to-use {asset} i3d files in the {asset_directory} directory."
        )
        directory = {
            "background": self.background_directory,
            "water": self.water_directory,
        }

        content = (
            "The files in this directory can be used to create the mesh files manually in Blender. "
            "However, it's recommended to use the ready-to-use i3d files located in the assets "
            "directory. There you'll find the i3d files, that can be imported directly into the "
            "Giants Editor without any additional processing."
        )
        note = note_template.format(
            asset=asset,
            asset_directory=f"assets/{asset}",
        )

        file_path = os.path.join(directory[asset], filename)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content + "\n\n" + note)

    @monitor_performance
    def convert_water_mesh_to_i3d(self) -> bool:
        """Converts the line-based water mesh to i3d format.

        Returns:
            bool -- True if the conversion was successful, False otherwise.
        """
        if not self.assets.line_based_water_mesh or not os.path.isfile(
            self.assets.line_based_water_mesh
        ):
            self.logger.warning("Line-based water mesh not found, cannot convert to i3d.")
            return False

        try:
            mesh = trimesh.load_mesh(self.assets.line_based_water_mesh, force="mesh")
        except Exception as e:
            self.logger.error("Could not load line-based water mesh: %s", e)
            return False

        try:
            i3d_water_resources = self.mesh_to_i3d(
                mesh,
                output_dir=self.assets_water_directory,
                name=Parameters.WATER_RESOURCES,
                water_mesh=True,
            )
            self.logger.debug(
                "Water resources mesh converted to i3d successfully: %s", i3d_water_resources
            )
            self.assets.water_resources_i3d = i3d_water_resources
            return True
        except Exception as e:
            self.logger.error("Could not convert water mesh to i3d: %s", e)
            return False

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

        output_size = self.scaled_size + 1

        main_dem_path = self.game.dem_file_path(self.map_directory)

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
        preview_paths = self.dem_previews(self.game.dem_file_path(self.map_directory))

        background_dem_preview_path = os.path.join(self.previews_directory, "background_dem.png")
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
    def create_background_textures(self) -> None:
        """Creates background textures for the map."""
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
            return

        self.background_texture = Texture(
            self.game,
            self.map,
            self.coordinates,
            self.background_size,
            self.rotated_size,
            rotation=self.rotation,
            map_directory=self.map_directory,
            logger=self.logger,
            texture_custom_schema=background_layers,  # type: ignore
            skip_scaling=True,  # type: ignore
            info_layer_path=os.path.join(self.info_layers_directory, "background.json"),  # type: ignore
        )

        self.background_texture.preprocess()
        self.background_texture.process()

        processed_layers = self.background_texture.get_background_layers()
        weights_directory = self.game.weights_dir_path(self.map_directory)
        background_paths = [layer.path(weights_directory) for layer in processed_layers]
        self.logger.debug("Found %s background textures.", len(background_paths))

        if not background_paths:
            self.logger.warning("No background textures found.")
            return

        # Merge all images into one.
        background_image = np.zeros((self.background_size, self.background_size), dtype=np.uint8)
        for path in background_paths:
            background_layer = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
            background_image = cv2.add(background_image, background_layer)  # type: ignore

        cv2.imwrite(self.water_resources_path, background_image)

    @monitor_performance
    def subtraction(self) -> None:
        """Subtracts the water depth from the DEM data where the water resources are located."""
        if not self.water_resources_path:
            self.logger.warning("Water resources texture not found.")
            return
        if not os.path.isfile(self.water_resources_path):
            self.logger.warning("Water resources texture was not generated, skipping subtraction.")
            return

        water_resources_image = cv2.imread(self.water_resources_path, cv2.IMREAD_UNCHANGED)
        dem_image = cv2.imread(self.output_path, cv2.IMREAD_UNCHANGED)

        # fall back to default value for height_scale 255, it is defined as float | None
        # but it is always set at this point
        z_scaling_factor: float = (
            self.map.shared_settings.mesh_z_scaling_factor
            if self.map.shared_settings.mesh_z_scaling_factor is not None
            else 257
        )
        flatten_to = None
        subtract_by = int(self.map.dem_settings.water_depth * z_scaling_factor)

        if self.map.background_settings.flatten_water:
            try:
                # Check if there are any water pixels (255) in the water resources image.
                if not np.any(water_resources_image == 255):
                    self.logger.warning("No water pixels found in water resources image.")
                    return
                mask = water_resources_image == 255
                flatten_to = int(np.mean(dem_image[mask]) - subtract_by)  # type: ignore
                self.flatten_water_to = flatten_to  # type: ignore
            except Exception as e:
                self.logger.warning("Error occurred while flattening water: %s", e)

        dem_image = self.subtract_by_mask(
            dem_image,  # type: ignore
            water_resources_image,  # type: ignore
            subtract_by=subtract_by,
            flatten_to=flatten_to,
        )

        dem_image = self.blur_edges_by_mask(
            dem_image, water_resources_image, smaller_kernel=3, iterations=5, bigger_kernel=5  # type: ignore
        )

        # Save the modified dem_image back to the output path
        cv2.imwrite(self.output_path, dem_image)
        self.logger.debug("Water depth subtracted from DEM data: %s", self.output_path)

    def _get_blur_power(self) -> int:
        """Returns the blur power for the water resources to apply Gaussian blur.

        Returns:
            int: The blur power for the water resources.
        """
        blur_power = max(3, min(self.map.background_settings.water_blurriness, 99))
        if blur_power % 2 == 0:
            blur_power += 1

        return blur_power

    def generate_linebased_water(self) -> None:
        """Generates water resources based on line-based polylines from the background info layer.
        It creates polygons from the polylines, fits them into the map bounds, and generates a mesh.
        """
        self.logger.debug("Starting line-based water generation...")
        water_polygons = self.get_infolayer_data(Parameters.BACKGROUND, Parameters.WATER)
        if not water_polygons:
            self.logger.warning("No water polygons found in background info layer.")
            return

        self.logger.debug(
            "Found %s water polygons in background info layer.", len(water_polygons)  # type: ignore
        )

        polygons: list[shapely.Polygon] = []
        for polygon_points in water_polygons:
            if not polygon_points or len(polygon_points) < 2:
                self.logger.warning("Skipping polygon with insufficient points...")
                continue

            polygon = shapely.Polygon(polygon_points)

            if polygon.is_empty or not polygon.is_valid:
                self.logger.warning("Skipping empty or invalid polygon...")
                continue

            # Make Polygon a little bit bigger to hide under the terrain when creating water planes.
            polygon = polygon.buffer(Parameters.WATER_ADD_WIDTH, quad_segs=4)

            polygons.append(polygon)

        fitted_polygons = []
        for polygon in polygons:
            try:
                fitted_polygon_points = self.fit_object_into_bounds(
                    polygon_points=polygon.exterior.coords,
                    angle=self.rotation,
                    canvas_size=self.background_size,
                    xshift=-Parameters.BACKGROUND_DISTANCE,
                )
                fitted_polygon = shapely.Polygon(fitted_polygon_points)
                fitted_polygons.append(fitted_polygon)
            except Exception as e:
                self.logger.debug("Could not fit polygon into bounds with error: %s.", e)
                continue

        if not fitted_polygons:
            self.logger.warning("No valid water polygons created from polylines.")
            return

        # Create a mesh from the 3D polygons
        mesh = self.mesh_from_3d_polygons(fitted_polygons, single_z_value=self.flatten_water_to)
        if mesh is None:
            self.logger.warning("No mesh could be created from the water polygons.")
            return
        self.logger.debug("Created mesh from %s water polygons.", len(fitted_polygons))

        mesh = self.rotate_mesh(mesh)
        mesh = self.invert_faces(mesh)

        line_based_save_path = os.path.join(self.water_directory, "line_based_water.obj")
        mesh.export(line_based_save_path)
        self.logger.debug("Line-based water mesh saved to %s", line_based_save_path)

        self.assets.line_based_water_mesh = line_based_save_path

    def mesh_from_3d_polygons(
        self, polygons: list[shapely.Polygon], single_z_value: int | None = None
    ) -> Trimesh | None:
        """Create a simple mesh from a list of 3D shapely Polygons.
        Each polygon must be flat (all Z the same or nearly the same for each polygon).
        Returns a single Trimesh mesh.

        Arguments:
            polygons (list[shapely.Polygon]): List of 3D shapely Polygons to create the mesh from.
            single_z_value (int | None): The Z value to use for all vertices in the mesh.

        Returns:
            Trimesh: A single Trimesh object containing the mesh created from the polygons.
        """

        all_vertices = []
        all_faces = []
        vertex_offset = 0

        not_resized_dem = cv2.imread(
            self.not_resized_path(Parameters.NOT_RESIZED_DEM), cv2.IMREAD_UNCHANGED
        )

        for polygon in polygons:
            # Get exterior 3D coordinates
            exterior_coords = np.array(polygon.exterior.coords)
            # Project to 2D for triangulation
            exterior_2d = exterior_coords[:, :2]
            poly_2d = shapely.geometry.Polygon(
                exterior_2d, [np.array(ring.coords)[:, :2] for ring in polygon.interiors]
            )

            # Triangulate in 2D
            vertices_2d, faces = trimesh.creation.triangulate_polygon(poly_2d)
            # tris.vertices is 2D, tris.faces are indices

            # Map 2D triangulated vertices back to 3D by matching to original 3D coords
            vertices_3d = []
            for v in vertices_2d:
                # Find closest original 2D point to get Z
                dists = np.linalg.norm(exterior_2d - v[:2], axis=1)
                idx = np.argmin(dists)
                # z = exterior_coords[idx, 2]
                if not single_z_value:
                    z = self.get_z_coordinate_from_dem(
                        not_resized_dem, exterior_coords[idx, 0], exterior_coords[idx, 1]  # type: ignore
                    )
                else:
                    z = single_z_value
                vertices_3d.append([v[0], v[1], z])
            vertices_3d = np.array(vertices_3d)  # type: ignore

            faces = faces + vertex_offset
            all_vertices.append(vertices_3d)
            all_faces.append(faces)
            vertex_offset += len(vertices_3d)

        if not all_vertices:
            return None

        vertices = np.vstack(all_vertices)
        faces = np.vstack(all_faces)
        mesh = trimesh.Trimesh(vertices=vertices, faces=faces, process=False)
        return mesh

    @monitor_performance
    def generate_water_resources_obj(self) -> None:
        """Generates 3D obj files based on water resources data."""
        self.logger.debug("Starting water resources generation...")
        try:
            self.generate_linebased_water()
        except Exception as e:
            self.logger.error("Error during line-based water generation: %s", e)

        if not os.path.isfile(self.water_resources_path):
            self.logger.warning("Water resources texture not found.")
            return

        # Single channeled 8 bit image, where the water have values of 255, and the rest 0.
        plane_water = cv2.imread(self.water_resources_path, cv2.IMREAD_UNCHANGED)

        # Check if the image contains non-zero values.
        if not np.any(plane_water):  # type: ignore
            self.logger.debug("Water resources image is empty, skipping water generation.")
            return

        dilated_plane_water = cv2.dilate(
            plane_water.astype(np.uint8), np.ones((5, 5), np.uint8), iterations=5  # type: ignore
        ).astype(np.uint8)
        plane_save_path = os.path.join(self.water_directory, "plane_water.obj")
        self.plane_from_np(dilated_plane_water, plane_save_path, include_zeros=False)

        # Single channeled 16 bit DEM image of terrain.
        background_dem = cv2.imread(self.not_substracted_path, cv2.IMREAD_UNCHANGED)

        if self.map.output_size is not None:
            scaled_background_size = int(self.background_size * self.map.size_scale)
            plane_water = cv2.resize(
                plane_water,  # type: ignore
                (scaled_background_size, scaled_background_size),
                interpolation=cv2.INTER_NEAREST,
            )
            background_dem = cv2.resize(
                background_dem,  # type: ignore
                (scaled_background_size, scaled_background_size),
                interpolation=cv2.INTER_NEAREST,
            )

        if self.map.background_settings.water_blurriness:
            # Apply Gaussian blur to the background dem.
            blur_power = self._get_blur_power()
            background_dem = cv2.GaussianBlur(
                background_dem, (blur_power, blur_power), sigmaX=blur_power, sigmaY=blur_power  # type: ignore
            )

        # Remove all the values from the background dem where the plane_water is 0.
        background_dem[plane_water == 0] = 0  # type: ignore

        # Dilate the background dem to make the water more smooth.
        elevated_water = cv2.dilate(background_dem, np.ones((3, 3), np.uint16), iterations=10)  # type: ignore

        # Use the background dem as a mask to prevent the original values from being overwritten.
        mask = background_dem > 0  # type: ignore

        # Combine the dilated background dem with non-dilated background dem.
        elevated_water = np.where(mask, background_dem, elevated_water)  # type: ignore
        elevated_save_path = os.path.join(self.water_directory, "elevated_water.obj")

        self.assets.water_mesh = elevated_save_path

        self.plane_from_np(elevated_water, elevated_save_path, include_zeros=False)

    @monitor_performance
    def flatten_roads(self) -> None:
        """Flattens the roads in the DEM data by averaging the height values along the road polylines."""
        supported_files = [
            self.not_resized_path(Parameters.NOT_RESIZED_DEM_FOUNDATIONS),
            self.not_resized_path(Parameters.NOT_RESIZED_DEM),
        ]

        base_image_path = None
        for supported_file in supported_files:
            if not supported_file or not os.path.isfile(supported_file):
                continue

            base_image_path = supported_file
            break

        if not base_image_path:
            self.logger.warning("No DEM data found for flattening roads.")
            return

        dem_image = cv2.imread(base_image_path, cv2.IMREAD_UNCHANGED)
        if dem_image is None:
            self.logger.warning("Failed to read DEM data.")
            return

        roads_polylines = self.get_infolayer_data(Parameters.TEXTURES, Parameters.ROADS_POLYLINES)
        if not roads_polylines:
            self.logger.warning("No roads polylines found in textures info layer.")
            return

        self.logger.debug("Found %s roads polylines in textures info layer.", len(roads_polylines))

        full_mask = np.zeros(dem_image.shape, dtype=np.uint8)

        for road_polyline in tqdm(roads_polylines, desc="Flattening roads", unit="road"):
            points = road_polyline.get("points")
            width = road_polyline.get("width")
            if not points or not width:
                self.logger.warning("Skipping road with insufficient data: %s", road_polyline)
                continue

            try:
                fitted_road = self.fit_object_into_bounds(
                    linestring_points=points, angle=self.rotation
                )
            except ValueError as e:
                self.logger.debug(
                    "Road polyline could not be fitted into the map bounds with error: %s",
                    e,
                )
                continue

            polyline = shapely.LineString(fitted_road)

            total_length = polyline.length
            self.logger.debug("Total length of the road polyline: %s", total_length)

            # Step 1: Create complete road mask once
            road_mask = np.zeros(dem_image.shape, dtype=np.uint8)
            # OpenCV thickness is total width, not radius like Shapely buffer
            # So we need width * 4 to match the old buffer(width * 2) behavior
            line_thickness = int(width * 4)

            # Get densely sampled points for smooth road
            dense_sample_distance = min(SEGMENT_LENGTH, total_length / 100)  # At least 100 samples
            num_dense_points = max(100, int(total_length / dense_sample_distance))
            dense_distances = np.linspace(0, total_length, num_dense_points)
            dense_points = [polyline.interpolate(d) for d in dense_distances]
            dense_coords = np.array([(int(p.x), int(p.y)) for p in dense_points], dtype=np.int32)

            # Draw entire road at once
            if len(dense_coords) > 1:
                cv2.polylines(road_mask, [dense_coords], False, 255, thickness=line_thickness)

            # Step 2: Get all road pixels that need processing
            road_pixels = np.where(road_mask == 255)
            if len(road_pixels[0]) == 0:
                continue

            road_y, road_x = road_pixels
            self.logger.debug("Processing %s road pixels", len(road_y))

            # Step 3: Efficient distance-based smooth gradation
            # Use much larger segments (10-20x SEGMENT_LENGTH) but interpolate between them
            large_segment_length = SEGMENT_LENGTH * 15  # 30 units instead of 2
            num_large_segments = max(1, int(np.ceil(total_length / large_segment_length)))
            large_distances = np.linspace(0, total_length, num_large_segments + 1)

            # Calculate elevation values at large segment points
            segment_elevations = []
            for dist in large_distances:
                sample_point = polyline.interpolate(dist)
                sample_x, sample_y = int(sample_point.x), int(sample_point.y)

                # Sample elevation in small area around this point
                sample_radius = max(5, line_thickness // 4)
                y_min = max(0, sample_y - sample_radius)
                y_max = min(dem_image.shape[0], sample_y + sample_radius)
                x_min = max(0, sample_x - sample_radius)
                x_max = min(dem_image.shape[1], sample_x + sample_radius)

                if y_max > y_min and x_max > x_min:
                    sample_elevation = np.mean(dem_image[y_min:y_max, x_min:x_max])  # type: ignore
                else:
                    sample_elevation = (
                        dem_image[sample_y, sample_x]  # type: ignore
                        if 0 <= sample_y < dem_image.shape[0] and 0 <= sample_x < dem_image.shape[1]
                        else 0
                    )

                segment_elevations.append(sample_elevation)

            # Step 4: Interpolate elevations smoothly along entire road
            road_distances_from_start = []
            for i in range(len(road_y)):  # pylint: disable=consider-using-enumerate
                px, py = road_x[i], road_y[i]
                # Find closest point on polyline (approximation)
                closest_point = polyline.interpolate(polyline.project(shapely.Point(px, py)))
                distance_along_road = polyline.project(closest_point)
                road_distances_from_start.append(distance_along_road)

            road_distances_from_start = np.array(road_distances_from_start)  # type: ignore

            # Interpolate elevation values based on distance along road
            interpolated_elevations = np.interp(
                road_distances_from_start, large_distances, segment_elevations
            )

            # Step 5: Apply interpolated elevations to road pixels
            dem_image[road_y, road_x] = interpolated_elevations
            full_mask[road_y, road_x] = 255

        main_dem_path = self.game.dem_file_path(self.map_directory)
        dem_image = self.blur_by_mask(dem_image, full_mask, blur_radius=5)
        dem_image = self.blur_edges_by_mask(dem_image, full_mask)

        # Save the not resized DEM with flattened roads.
        cv2.imwrite(self.not_resized_path(Parameters.NOT_RESIZED_DEM_ROADS), dem_image)
        self.logger.debug(
            "Not resized DEM with flattened roads saved to: %s",
            self.not_resized_path(Parameters.NOT_RESIZED_DEM_ROADS),
        )

        output_size = dem_image.shape[0] + 1
        resized_dem = cv2.resize(
            dem_image, (output_size, output_size), interpolation=cv2.INTER_NEAREST
        )

        cv2.imwrite(main_dem_path, resized_dem)
        self.logger.debug("Flattened roads saved to DEM file: %s", main_dem_path)
