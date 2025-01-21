"""This module contains the Background component, which generates 3D obj files based on DEM data
around the map."""

from __future__ import annotations

import json
import os
import shutil
from copy import deepcopy

import cv2
import numpy as np

from maps4fs.generator.component.base.component_image import ImageComponent
from maps4fs.generator.component.base.component_mesh import MeshComponent
from maps4fs.generator.component.texture import Texture
from maps4fs.generator.dem import DEM
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

        self.background_directory = os.path.join(self.map_directory, "background")
        self.water_directory = os.path.join(self.map_directory, "water")
        os.makedirs(self.background_directory, exist_ok=True)
        os.makedirs(self.water_directory, exist_ok=True)

        self.water_resources_path = os.path.join(self.water_directory, "water_resources.png")

        self.output_path = os.path.join(self.background_directory, f"{Parameters.FULL}.png")
        if self.map.custom_background_path:
            self.validate_np_for_mesh(self.map.custom_background_path, self.map_size)
            shutil.copyfile(self.map.custom_background_path, self.output_path)

        self.not_substracted_path: str = os.path.join(
            self.background_directory, "not_substracted.png"
        )
        self.not_resized_path: str = os.path.join(self.background_directory, "not_resized.png")

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

        shutil.copyfile(self.dem.dem_path, self.not_substracted_path)
        self.save_map_dem(self.dem.dem_path, save_path=self.not_resized_path)

        if self.map.dem_settings.water_depth:
            self.subtraction()

        cutted_dem_path = self.save_map_dem(self.dem.dem_path)
        if self.game.additional_dem_name is not None:
            self.make_copy(cutted_dem_path, self.game.additional_dem_name)

        if self.map.background_settings.generate_background:
            self.generate_obj_files()
        if self.map.background_settings.generate_water:
            self.generate_water_resources_obj()

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
        return data  # type: ignore

    def qgis_sequence(self) -> None:
        """Generates QGIS scripts for creating bounding box layers and rasterizing them."""
        qgis_layer = (f"Background_{Parameters.FULL}", *self.dem.get_espg3857_bbox())
        qgis_layer_with_margin = (
            f"Background_{Parameters.FULL}_margin",
            *self.dem.get_espg3857_bbox(add_margin=True),
        )
        self.create_qgis_scripts([qgis_layer, qgis_layer_with_margin])

    def generate_obj_files(self) -> None:
        """Iterates over all dems and generates 3D obj files based on DEM data.
        If at least one DEM file is missing, the generation will be stopped at all.
        """
        if not os.path.isfile(self.dem.dem_path):
            self.logger.error(
                "DEM file not found, generation will be stopped: %s", self.dem.dem_path
            )
            return

        self.logger.debug("DEM file for found: %s", self.dem.dem_path)

        filename = os.path.splitext(os.path.basename(self.dem.dem_path))[0]
        save_path = os.path.join(self.background_directory, f"{filename}.obj")
        self.logger.debug("Generating obj file in path: %s", save_path)

        dem_data = cv2.imread(self.dem.dem_path, cv2.IMREAD_UNCHANGED)
        self.plane_from_np(
            dem_data,
            save_path,
            create_preview=True,
            remove_center=self.map.background_settings.remove_center,
            include_zeros=False,
        )

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
        dem_data = self.cut_out_np(dem_data, half_size, return_cutout=True)

        if save_path:
            cv2.imwrite(save_path, dem_data)
            self.logger.debug("Not resized DEM saved: %s", save_path)
            return save_path

        output_size = self.map_size + 1

        main_dem_path = self.game.dem_file_path(self.map_directory)

        try:
            os.remove(main_dem_path)
        except FileNotFoundError:
            pass

        resized_dem_data = cv2.resize(
            dem_data, (output_size, output_size), interpolation=cv2.INTER_LINEAR
        )

        cv2.imwrite(main_dem_path, resized_dem_data)
        self.logger.debug("DEM cutout saved: %s", main_dem_path)

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
            z_scaling_factor=self.get_z_scaling_factor(),
            resize_factor=self.map.background_settings.resize_factor,
            apply_decimation=self.map.background_settings.apply_decimation,
            decimation_percent=self.map.background_settings.decimation_percent,
            decimation_agression=self.map.background_settings.decimation_agression,
            remove_center=remove_center,
            remove_size=self.map_size,
            disable_tqdm=self.map.is_public,
        )

        mesh.export(save_path)
        self.logger.debug("Obj file saved: %s", save_path)

        if create_preview:
            mesh.apply_scale([0.5, 0.5, 0.5])
            self.mesh_to_stl(mesh, save_path=self.stl_preview_path)

    def previews(self) -> list[str]:
        """Returns the path to the image previews paths and the path to the STL preview file.

        Returns:
            list[str] -- A list of paths to the previews.
        """
        preview_paths = self.dem_previews(self.game.dem_file_path(self.map_directory))

        background_dem_preview_path = os.path.join(self.previews_directory, "background_dem.png")
        background_dem_preview_image = cv2.imread(self.dem.dem_path, cv2.IMREAD_UNCHANGED)

        background_dem_preview_image = cv2.resize(
            background_dem_preview_image, (0, 0), fx=1 / 4, fy=1 / 4
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
        dem_data_rgb = cv2.cvtColor(dem_data, cv2.COLOR_GRAY2RGB)
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
        cv2.normalize(dem_data, dem_data_normalized, 0, 255, cv2.NORM_MINMAX)
        dem_data_colored = cv2.applyColorMap(dem_data_normalized, cv2.COLORMAP_JET)

        cv2.imwrite(colored_dem_path, dem_data_colored)
        return colored_dem_path

    def create_background_textures(self) -> None:
        """Creates background textures for the map."""
        if not os.path.isfile(self.game.texture_schema):
            self.logger.warning("Texture schema file not found: %s", self.game.texture_schema)
            return

        with open(self.game.texture_schema, "r", encoding="utf-8") as f:
            layers_schema = json.load(f)

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

    def subtraction(self) -> None:
        """Subtracts the water depth from the DEM data where the water resources are located."""
        if not self.water_resources_path:
            self.logger.warning("Water resources texture not found.")
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

        dem_image = self.subtract_by_mask(
            dem_image,
            water_resources_image,
            int(self.map.dem_settings.water_depth * z_scaling_factor),
        )

        # Save the modified dem_image back to the output path
        cv2.imwrite(self.output_path, dem_image)
        self.logger.debug("Water depth subtracted from DEM data: %s", self.output_path)

    def generate_water_resources_obj(self) -> None:
        """Generates 3D obj files based on water resources data."""
        if not os.path.isfile(self.water_resources_path):
            self.logger.warning("Water resources texture not found.")
            return

        # Single channeled 8 bit image, where the water have values of 255, and the rest 0.
        plane_water = cv2.imread(self.water_resources_path, cv2.IMREAD_UNCHANGED)

        # Check if the image contains non-zero values.
        if not np.any(plane_water):
            self.logger.debug("Water resources image is empty, skipping water generation.")
            return

        dilated_plane_water = cv2.dilate(
            plane_water.astype(np.uint8), np.ones((5, 5), np.uint8), iterations=5
        ).astype(np.uint8)
        plane_save_path = os.path.join(self.water_directory, "plane_water.obj")
        self.plane_from_np(dilated_plane_water, plane_save_path, include_zeros=False)

        # Single channeled 16 bit DEM image of terrain.
        background_dem = cv2.imread(self.not_substracted_path, cv2.IMREAD_UNCHANGED)

        # Remove all the values from the background dem where the plane_water is 0.
        background_dem[plane_water == 0] = 0

        # Dilate the background dem to make the water more smooth.
        elevated_water = cv2.dilate(background_dem, np.ones((3, 3), np.uint16), iterations=10)

        # Use the background dem as a mask to prevent the original values from being overwritten.
        mask = background_dem > 0

        # Combine the dilated background dem with non-dilated background dem.
        elevated_water = np.where(mask, background_dem, elevated_water)
        elevated_save_path = os.path.join(self.water_directory, "elevated_water.obj")

        self.plane_from_np(elevated_water, elevated_save_path, include_zeros=False)
