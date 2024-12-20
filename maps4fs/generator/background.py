"""This module contains the Background component, which generates 3D obj files based on DEM data
around the map."""

from __future__ import annotations

import os
import shutil

import cv2
import numpy as np
import trimesh  # type: ignore

from maps4fs.generator.component import Component
from maps4fs.generator.dem import (
    DEFAULT_BLUR_RADIUS,
    DEFAULT_MULTIPLIER,
    DEFAULT_PLATEAU,
    DEM,
)

DEFAULT_DISTANCE = 2048
RESIZE_FACTOR = 1 / 8
FULL_NAME = "FULL"
FULL_PREVIEW_NAME = "PREVIEW"
ELEMENTS = [FULL_NAME, FULL_PREVIEW_NAME]


class Background(Component):
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

    # pylint: disable=R0801
    def preprocess(self) -> None:
        """Registers the DEMs for the background terrain."""
        self.light_version = self.kwargs.get("light_version", False)
        self.stl_preview_path: str | None = None

        if self.rotation:
            self.logger.debug("Rotation is enabled: %s.", self.rotation)
            output_size_multiplier = 1.5
        else:
            output_size_multiplier = 1

        background_size = self.map_size + DEFAULT_DISTANCE * 2
        rotated_size = int(background_size * output_size_multiplier)

        self.background_directory = os.path.join(self.map_directory, "background")
        os.makedirs(self.background_directory, exist_ok=True)

        autoprocesses = [self.kwargs.get("auto_process", False), False]
        dems = []

        for name, autoprocess in zip(ELEMENTS, autoprocesses):
            dem = DEM(
                self.game,
                self.coordinates,
                background_size,
                rotated_size,
                self.rotation,
                self.map_directory,
                self.logger,
                auto_process=autoprocess,
                blur_radius=self.kwargs.get("blur_radius", DEFAULT_BLUR_RADIUS),
                multiplier=self.kwargs.get("multiplier", DEFAULT_MULTIPLIER),
                plateau=self.kwargs.get("plateau", DEFAULT_PLATEAU),
            )
            dem.preprocess()
            dem.is_preview = self.is_preview(name)  # type: ignore
            dem.set_output_resolution((rotated_size, rotated_size))
            dem.set_dem_path(os.path.join(self.background_directory, f"{name}.png"))
            dems.append(dem)

        self.dems = dems

    def is_preview(self, name: str) -> bool:
        """Checks if the DEM is a preview.

        Arguments:
            name (str): The name of the DEM.

        Returns:
            bool: True if the DEM is a preview, False otherwise.
        """
        return name == FULL_PREVIEW_NAME

    def process(self) -> None:
        """Launches the component processing. Iterates over all tiles and processes them
        as a result the DEM files will be saved, then based on them the obj files will be
        generated."""
        for dem in self.dems:
            dem.process()
            if not dem.is_preview:  # type: ignore
                cutted_dem_path = self.cutout(dem.dem_path)
                if self.game.additional_dem_name is not None:
                    self.make_copy(cutted_dem_path, self.game.additional_dem_name)

        if not self.light_version:
            self.generate_obj_files()
        else:
            self.logger.info("Light version is enabled, obj files will not be generated.")

    def make_copy(self, dem_path: str, dem_name: str) -> None:
        """Copies DEM data to additional DEM file.

        Arguments:
            dem_path (str): Path to the DEM file.
            dem_name (str): Name of the additional DEM file.
        """
        dem_directory = os.path.dirname(dem_path)

        additional_dem_path = os.path.join(dem_directory, dem_name)

        shutil.copyfile(dem_path, additional_dem_path)
        self.logger.info("Additional DEM data was copied to %s.", additional_dem_path)

    def info_sequence(self) -> dict[str, str | float | int]:
        """Returns a dictionary with information about the background terrain.
        Adds the EPSG:3857 string to the data for convenient usage in QGIS.

        Returns:
            dict[str, str, float | int] -- A dictionary with information about the background
                terrain.
        """
        self.qgis_sequence()

        dem = self.dems[0]

        north, south, east, west = dem.bbox
        epsg3857_string = dem.get_epsg3857_string()
        epsg3857_string_with_margin = dem.get_epsg3857_string(add_margin=True)

        data = {
            "center_latitude": dem.coordinates[0],
            "center_longitude": dem.coordinates[1],
            "epsg3857_string": epsg3857_string,
            "epsg3857_string_with_margin": epsg3857_string_with_margin,
            "height": dem.map_size,
            "width": dem.map_size,
            "north": north,
            "south": south,
            "east": east,
            "west": west,
        }
        return data  # type: ignore

    def qgis_sequence(self) -> None:
        """Generates QGIS scripts for creating bounding box layers and rasterizing them."""
        qgis_layer = (f"Background_{FULL_NAME}", *self.dems[0].get_espg3857_bbox())
        qgis_layer_with_margin = (
            f"Background_{FULL_NAME}_margin",
            *self.dems[0].get_espg3857_bbox(add_margin=True),
        )
        self.create_qgis_scripts([qgis_layer, qgis_layer_with_margin])

    def generate_obj_files(self) -> None:
        """Iterates over all dems and generates 3D obj files based on DEM data.
        If at least one DEM file is missing, the generation will be stopped at all.
        """
        for dem in self.dems:
            if not os.path.isfile(dem.dem_path):
                self.logger.warning(
                    "DEM file not found, generation will be stopped: %s", dem.dem_path
                )
                return

            self.logger.debug("DEM file for found: %s", dem.dem_path)

            filename = os.path.splitext(os.path.basename(dem.dem_path))[0]
            save_path = os.path.join(self.background_directory, f"{filename}.obj")
            self.logger.debug("Generating obj file in path: %s", save_path)

            dem_data = cv2.imread(dem.dem_path, cv2.IMREAD_UNCHANGED)  # pylint: disable=no-member
            self.plane_from_np(dem_data, save_path, is_preview=dem.is_preview)  # type: ignore

    # pylint: disable=too-many-locals
    def cutout(self, dem_path: str) -> str:
        """Cuts out the center of the DEM (the actual map) and saves it as a separate file.

        Arguments:
            dem_path (str): The path to the DEM file.

        Returns:
            str -- The path to the cutout DEM file.
        """
        dem_data = cv2.imread(dem_path, cv2.IMREAD_UNCHANGED)  # pylint: disable=no-member

        center = (dem_data.shape[0] // 2, dem_data.shape[1] // 2)
        half_size = self.map_size // 2
        x1 = center[0] - half_size
        x2 = center[0] + half_size
        y1 = center[1] - half_size
        y2 = center[1] + half_size
        dem_data = dem_data[x1:x2, y1:y2]

        output_size = self.map_size + 1

        main_dem_path = self.game.dem_file_path(self.map_directory)

        try:
            os.remove(main_dem_path)
        except FileNotFoundError:
            pass

        # pylint: disable=no-member
        resized_dem_data = cv2.resize(
            dem_data, (output_size, output_size), interpolation=cv2.INTER_LINEAR
        )

        cv2.imwrite(main_dem_path, resized_dem_data)  # pylint: disable=no-member
        self.logger.info("DEM cutout saved: %s", main_dem_path)

        return main_dem_path

    # pylint: disable=too-many-locals
    def plane_from_np(self, dem_data: np.ndarray, save_path: str, is_preview: bool = False) -> None:
        """Generates a 3D obj file based on DEM data.

        Arguments:
            dem_data (np.ndarray) -- The DEM data as a numpy array.
            save_path (str) -- The path where the obj file will be saved.
            is_preview (bool, optional) -- If True, the preview mesh will be generated.
        """
        dem_data = cv2.resize(  # pylint: disable=no-member
            dem_data, (0, 0), fx=RESIZE_FACTOR, fy=RESIZE_FACTOR
        )
        self.logger.debug(
            "DEM data resized to shape: %s with factor: %s", dem_data.shape, RESIZE_FACTOR
        )

        # Invert the height values.
        dem_data = dem_data.max() - dem_data

        rows, cols = dem_data.shape
        x = np.linspace(0, cols - 1, cols)
        y = np.linspace(0, rows - 1, rows)
        x, y = np.meshgrid(x, y)
        z = dem_data

        self.logger.debug(
            "Starting to generate a mesh for with shape: %s x %s. This may take a while...",
            cols,
            rows,
        )

        vertices = np.column_stack([x.ravel(), y.ravel(), z.ravel()])
        faces = []

        for i in range(rows - 1):
            for j in range(cols - 1):
                top_left = i * cols + j
                top_right = top_left + 1
                bottom_left = top_left + cols
                bottom_right = bottom_left + 1

                faces.append([top_left, bottom_left, bottom_right])
                faces.append([top_left, bottom_right, top_right])

        faces = np.array(faces)  # type: ignore
        mesh = trimesh.Trimesh(vertices=vertices, faces=faces)

        # Apply rotation: 180 degrees around Y-axis and Z-axis
        rotation_matrix_y = trimesh.transformations.rotation_matrix(np.pi, [0, 1, 0])
        rotation_matrix_z = trimesh.transformations.rotation_matrix(np.pi, [0, 0, 1])
        mesh.apply_transform(rotation_matrix_y)
        mesh.apply_transform(rotation_matrix_z)

        if is_preview:
            # Simplify the preview mesh to reduce the size of the file.
            mesh = mesh.simplify_quadric_decimation(face_count=len(mesh.faces) // 2**7)

            # Apply scale to make the preview mesh smaller in the UI.
            mesh.apply_scale([0.5, 0.5, 0.5])
            self.mesh_to_stl(mesh)
        else:
            multiplier = self.kwargs.get("multiplier", DEFAULT_MULTIPLIER)
            if multiplier != 1:
                z_scaling_factor = 1 / multiplier
            else:
                z_scaling_factor = 1 / 2**5
            self.logger.debug("Z scaling factor: %s", z_scaling_factor)
            mesh.apply_scale([1 / RESIZE_FACTOR, 1 / RESIZE_FACTOR, z_scaling_factor])

        mesh.export(save_path)
        self.logger.debug("Obj file saved: %s", save_path)

    def mesh_to_stl(self, mesh: trimesh.Trimesh) -> None:
        """Converts the mesh to an STL file and saves it in the previews directory.
        Uses powerful simplification to reduce the size of the file since it will be used
        only for the preview.

        Arguments:
            mesh (trimesh.Trimesh) -- The mesh to convert to an STL file.
        """
        preview_path = os.path.join(self.previews_directory, "background_dem.stl")
        mesh.export(preview_path)

        self.logger.info("STL file saved: %s", preview_path)

        self.stl_preview_path = preview_path  # pylint: disable=attribute-defined-outside-init

    # pylint: disable=no-member
    def previews(self) -> list[str]:
        """Returns the path to the image previews paths and the path to the STL preview file.

        Returns:
            list[str] -- A list of paths to the previews.
        """
        preview_paths = self.dem_previews(self.game.dem_file_path(self.map_directory))
        for dem in self.dems:
            if dem.is_preview:  # type: ignore
                background_dem_preview_path = os.path.join(
                    self.previews_directory, "background_dem.png"
                )
                background_dem_preview_image = cv2.imread(dem.dem_path, cv2.IMREAD_UNCHANGED)

                background_dem_preview_image = cv2.resize(
                    background_dem_preview_image, (0, 0), fx=1 / 4, fy=1 / 4
                )
                background_dem_preview_image = cv2.normalize(  # type: ignore
                    background_dem_preview_image, None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U
                )
                background_dem_preview_image = cv2.cvtColor(
                    background_dem_preview_image, cv2.COLOR_GRAY2BGR
                )

                cv2.imwrite(background_dem_preview_path, background_dem_preview_image)
                preview_paths.append(background_dem_preview_path)

        if self.stl_preview_path:
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

        self.logger.debug(
            "DEM data before normalization. Shape: %s, dtype: %s. Min: %s, max: %s.",
            dem_data.shape,
            dem_data.dtype,
            dem_data.min(),
            dem_data.max(),
        )

        # Create an empty array with the same shape and type as dem_data.
        dem_data_normalized = np.empty_like(dem_data)

        # Normalize the DEM data to the range [0, 255]
        cv2.normalize(dem_data, dem_data_normalized, 0, 255, cv2.NORM_MINMAX)
        self.logger.debug(
            "DEM data after normalization. Shape: %s, dtype: %s. Min: %s, max: %s.",
            dem_data_normalized.shape,
            dem_data_normalized.dtype,
            dem_data_normalized.min(),
            dem_data_normalized.max(),
        )
        dem_data_colored = cv2.applyColorMap(dem_data_normalized, cv2.COLORMAP_JET)

        cv2.imwrite(colored_dem_path, dem_data_colored)
        return colored_dem_path
