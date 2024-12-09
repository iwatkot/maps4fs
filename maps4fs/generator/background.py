"""This module contains the Background component, which generates 3D obj files based on DEM data
around the map."""

from __future__ import annotations

import os

import cv2
import numpy as np
import trimesh  # type: ignore

from maps4fs.generator.component import Component
from maps4fs.generator.dem import (
    DEFAULT_BLUR_RADIUS,
    DEFAULT_MULTIPLIER,
    DEFAULT_PLATEAU,
)
from maps4fs.generator.path_steps import DEFAULT_DISTANCE, PATH_FULL_NAME, get_steps
from maps4fs.generator.tile import Tile

RESIZE_FACTOR = 1 / 4
SIMPLIFY_FACTOR = 10
FULL_RESIZE_FACTOR = 1 / 8
FULL_SIMPLIFY_FACTOR = 20


class Background(Component):
    """Component for creating 3D obj files based on DEM data around the map.

    Args:
        coordinates (tuple[float, float]): The latitude and longitude of the center of the map.
        map_height (int): The height of the map in pixels.
        map_width (int): The width of the map in pixels.
        map_directory (str): The directory where the map files are stored.
        logger (Any, optional): The logger to use. Must have at least three basic methods: debug,
            info, warning. If not provided, default logging will be used.
    """

    def preprocess(self) -> None:
        """Prepares the component for processing. Registers the tiles around the map by moving
        clockwise from North, then clockwise."""
        self.tiles: list[Tile] = []
        origin = self.coordinates

        # Getting a list of 8 tiles around the map starting from the N(North) tile.
        for path_step in get_steps(self.map_height, self.map_width):
            # Getting the destination coordinates for the current tile.
            if path_step.angle is None:
                # For the case when generating the overview map, which has the same
                # center as the main map.
                tile_coordinates = self.coordinates
            else:
                tile_coordinates = path_step.get_destination(origin)

            # Create a Tile component, which is needed to save the DEM image.
            tile = Tile(
                game=self.game,
                coordinates=tile_coordinates,
                map_height=path_step.size[1],
                map_width=path_step.size[0],
                map_directory=self.map_directory,
                logger=self.logger,
                tile_code=path_step.code,
                auto_process=False,
                blur_radius=self.kwargs.get("blur_radius", DEFAULT_BLUR_RADIUS),
                multiplier=self.kwargs.get("multiplier", DEFAULT_MULTIPLIER),
                plateau=self.kwargs.get("plateau", DEFAULT_PLATEAU),
            )

            # Update the origin for the next tile.
            origin = tile_coordinates
            self.tiles.append(tile)
            self.logger.debug(
                "Registered tile: %s, coordinates: %s, size: %s",
                tile.code,
                tile_coordinates,
                path_step.size,
            )

    def process(self) -> None:
        """Launches the component processing. Iterates over all tiles and processes them
        as a result the DEM files will be saved, then based on them the obj files will be
        generated."""
        for tile in self.tiles:
            tile.process()

        self.generate_obj_files()

    def info_sequence(self) -> dict[str, dict[str, str | float | int]]:
        """Returns a dictionary with information about the tiles around the map.
        Adds the EPSG:3857 string to the data for convenient usage in QGIS.

        Returns:
            dict[str, dict[str, float | int]] -- A dictionary with information about the tiles.
        """
        data = {}
        self.qgis_sequence()

        for tile in self.tiles:
            north, south, east, west = tile.bbox
            epsg3857_string = tile.get_epsg3857_string()
            epsg3857_string_with_margin = tile.get_epsg3857_string(add_margin=True)

            tile_entry = {
                "center_latitude": tile.coordinates[0],
                "center_longitude": tile.coordinates[1],
                "epsg3857_string": epsg3857_string,
                "epsg3857_string_with_margin": epsg3857_string_with_margin,
                "height": tile.map_height,
                "width": tile.map_width,
                "north": north,
                "south": south,
                "east": east,
                "west": west,
            }
            if tile.code is not None:
                data[tile.code] = tile_entry

        return data  # type: ignore

    def qgis_sequence(self) -> None:
        """Generates QGIS scripts for creating bounding box layers and rasterizing them."""
        qgis_layers = [
            (f"Background_{tile.code}", *tile.get_espg3857_bbox()) for tile in self.tiles
        ]
        qgis_layers_with_margin = [
            (f"Background_{tile.code}_margin", *tile.get_espg3857_bbox(add_margin=True))
            for tile in self.tiles
        ]

        layers = qgis_layers + qgis_layers_with_margin

        self.create_qgis_scripts(layers)

    def generate_obj_files(self) -> None:
        """Iterates over all tiles and generates 3D obj files based on DEM data.
        If at least one DEM file is missing, the generation will be stopped at all.
        """
        for tile in self.tiles:
            # Read DEM data from the tile.
            dem_path = tile.dem_path
            if not os.path.isfile(dem_path):
                self.logger.warning("DEM file not found, generation will be stopped: %s", dem_path)
                return

            self.logger.info("DEM file for tile %s found: %s", tile.code, dem_path)

            base_directory = os.path.dirname(dem_path)
            save_path = os.path.join(base_directory, f"{tile.code}.obj")
            self.logger.debug("Generating obj file for tile %s in path: %s", tile.code, save_path)

            dem_data = cv2.imread(tile.dem_path, cv2.IMREAD_UNCHANGED)  # pylint: disable=no-member
            self.plane_from_np(tile.code, dem_data, save_path)  # type: ignore

    # pylint: disable=too-many-locals
    def plane_from_np(self, tile_code: str, dem_data: np.ndarray, save_path: str) -> None:
        """Generates a 3D obj file based on DEM data.

        Arguments:
            tile_code (str) -- The code of the tile.
            dem_data (np.ndarray) -- The DEM data as a numpy array.
            save_path (str) -- The path where the obj file will be saved.
        """
        if tile_code == PATH_FULL_NAME:
            resize_factor = FULL_RESIZE_FACTOR
            simplify_factor = FULL_SIMPLIFY_FACTOR
            self.logger.info("Generating a full map obj file")
        else:
            resize_factor = RESIZE_FACTOR
            simplify_factor = SIMPLIFY_FACTOR
        dem_data = cv2.resize(  # pylint: disable=no-member
            dem_data, (0, 0), fx=resize_factor, fy=resize_factor
        )
        self.logger.debug(
            "DEM data resized to shape: %s with factor: %s", dem_data.shape, resize_factor
        )

        # Invert the height values.
        dem_data = dem_data.max() - dem_data

        rows, cols = dem_data.shape
        x = np.linspace(0, cols - 1, cols)
        y = np.linspace(0, rows - 1, rows)
        x, y = np.meshgrid(x, y)
        z = dem_data

        self.logger.info(
            "Starting to generate a mesh for tile %s with shape: %s x %s. "
            "This may take a while...",
            tile_code,
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

        self.logger.info("Mesh generated with %s faces, will be simplified", len(mesh.faces))

        # Simplify the mesh to reduce the number of faces.
        mesh = mesh.simplify_quadric_decimation(face_count=len(faces) // simplify_factor)
        self.logger.debug("Mesh simplified to %s faces", len(mesh.faces))

        if tile_code == PATH_FULL_NAME:
            self.mesh_to_stl(mesh)

        mesh.export(save_path)
        self.logger.info("Obj file saved: %s", save_path)

    def mesh_to_stl(self, mesh: trimesh.Trimesh) -> None:
        """Converts the mesh to an STL file and saves it in the previews directory.
        Uses powerful simplification to reduce the size of the file since it will be used
        only for the preview.

        Arguments:
            mesh (trimesh.Trimesh) -- The mesh to convert to an STL file.
        """
        preview_path = os.path.join(self.previews_directory, "background_dem.stl")
        mesh = mesh.simplify_quadric_decimation(percent=0.05)
        mesh.export(preview_path)

        self.logger.info("STL file saved: %s", preview_path)

        self.stl_preview_path = preview_path  # pylint: disable=attribute-defined-outside-init

    def previews(self) -> list[str]:
        """Generates a preview by combining all tiles into one image.
        NOTE: The map itself is not included in the preview, so it will be empty.

        Returns:
            list[str] -- A list of paths to the preview images."""

        self.logger.info("Generating a preview image for the background DEM")

        image_height = self.map_height + DEFAULT_DISTANCE * 2
        image_width = self.map_width + DEFAULT_DISTANCE * 2
        self.logger.debug("Full size of the preview image: %s x %s", image_width, image_height)

        image = np.zeros((image_height, image_width), np.uint16)  # pylint: disable=no-member
        self.logger.debug("Empty image created: %s", image.shape)

        for tile in self.tiles:
            # pylint: disable=no-member
            if tile.code == PATH_FULL_NAME:
                continue
            tile_image = cv2.imread(tile.dem_path, cv2.IMREAD_UNCHANGED)

            self.logger.debug(
                "Tile %s image shape: %s, dtype: %s, max: %s, min: %s",
                tile.code,
                tile_image.shape,
                tile_image.dtype,
                tile_image.max(),
                tile_image.min(),
            )

            tile_height, tile_width = tile_image.shape
            self.logger.debug("Tile %s size: %s x %s", tile.code, tile_width, tile_height)

            # Calculate the position based on the tile code
            if tile.code == "N":
                x = DEFAULT_DISTANCE
                y = 0
            elif tile.code == "NE":
                x = self.map_width + DEFAULT_DISTANCE
                y = 0
            elif tile.code == "E":
                x = self.map_width + DEFAULT_DISTANCE
                y = DEFAULT_DISTANCE
            elif tile.code == "SE":
                x = self.map_width + DEFAULT_DISTANCE
                y = self.map_height + DEFAULT_DISTANCE
            elif tile.code == "S":
                x = DEFAULT_DISTANCE
                y = self.map_height + DEFAULT_DISTANCE
            elif tile.code == "SW":
                x = 0
                y = self.map_height + DEFAULT_DISTANCE
            elif tile.code == "W":
                x = 0
                y = DEFAULT_DISTANCE
            elif tile.code == "NW":
                x = 0
                y = 0

            # pylint: disable=possibly-used-before-assignment
            x2 = x + tile_width
            y2 = y + tile_height

            self.logger.debug(
                "Tile %s position. X from %s to %s, Y from %s to %s", tile.code, x, x2, y, y2
            )

            # pylint: disable=possibly-used-before-assignment
            image[y:y2, x:x2] = tile_image

        # Save image to the map directory.
        preview_path = os.path.join(self.previews_directory, "background_dem.png")

        # pylint: disable=no-member
        image = cv2.normalize(image, None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U)  # type: ignore
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)  # type: ignore
        cv2.imwrite(preview_path, image)

        return [preview_path, self.stl_preview_path]


# Creates tiles around the map.
# The one on corners 2048x2048, on sides and in the middle map_size x 2048.
# So 2048 is a distance FROM the edge of the map, but the other size depends on the map size.
# But for corner tiles it's always 2048.

# In the beginning we have coordinates of the central point of the map and it's size.
# We need to calculate the coordinates of central points all 8 tiles around the map.

# Latitude is a vertical line, Longitude is a horizontal line.

#                         2048
#                     |         |
# ____________________|_________|___
# |         |         |         |
# |    NW   |    N    |    NE   |    2048
# |_________|_________|_________|___
# |         |         |         |
# |    W    |    C    |    E    |
# |_________|_________|_________|
# |         |         |         |
# |    SW   |    S    |    SE   |
# |_________|_________|_________|
#
# N = C map_height / 2 + 1024; N_width = map_width; N_height = 2048
# NW = N - map_width / 2 - 1024; NW_width = 2048; NW_height = 2048
# and so on...

# lat, lon = 45.28565000315636, 20.237121355049904
# dst = 1024

# # N
# destination = distance(meters=dst).destination((lat, lon), 0)
# lat, lon = destination.latitude, destination.longitude
# print(lat, lon)
