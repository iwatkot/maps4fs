from __future__ import annotations

import os
from typing import TYPE_CHECKING, NamedTuple

import cv2
import numpy as np
import trimesh
from geopy.distance import distance

from maps4fs.generator.tile import Tile

if TYPE_CHECKING:
    from maps4fs.generator.map import Map

DEFAULT_DISTANCE = 2048


class PathInfo(NamedTuple):
    code: str
    angle: int
    distance: int
    size: tuple[int, int]


class Background:
    def __init__(self, map: Map):
        self.map = map
        self.center_latitude = map.coordinates[0]
        self.center_longitude = map.coordinates[1]
        self.map_height = map.height
        self.map_width = map.width
        self.map_directory = map.map_directory
        self.logger = map.logger

        self.tiles: list[Tile] = []
        self.register_tiles()

    def register_tiles(self):
        # Move clockwise from N and calculate coordinates and sizes for each tile.
        origin = (self.center_latitude, self.center_longitude)
        half_width = int(self.map_width / 2)
        half_height = int(self.map_height / 2)

        paths = [
            PathInfo(
                "N", 0, half_height + DEFAULT_DISTANCE / 2, (self.map_width, DEFAULT_DISTANCE)
            ),
            PathInfo(
                "NE", 90, half_width + DEFAULT_DISTANCE / 2, (DEFAULT_DISTANCE, DEFAULT_DISTANCE)
            ),
            PathInfo(
                "E", 180, half_height + DEFAULT_DISTANCE / 2, (self.map_height, DEFAULT_DISTANCE)
            ),
            PathInfo(
                "SE", 180, half_height + DEFAULT_DISTANCE / 2, (DEFAULT_DISTANCE, DEFAULT_DISTANCE)
            ),
            PathInfo(
                "S", 270, half_width + DEFAULT_DISTANCE / 2, (self.map_width, DEFAULT_DISTANCE)
            ),
            PathInfo(
                "SW", 270, half_width + DEFAULT_DISTANCE / 2, (DEFAULT_DISTANCE, DEFAULT_DISTANCE)
            ),
            PathInfo(
                "W", 0, half_height + DEFAULT_DISTANCE / 2, (self.map_height, DEFAULT_DISTANCE)
            ),
            PathInfo(
                "NW", 0, half_height + DEFAULT_DISTANCE / 2, (DEFAULT_DISTANCE, DEFAULT_DISTANCE)
            ),
        ]

        for path in paths:
            destination = distance(meters=path.distance).destination(origin, path.angle)
            tile_coordinates = (destination.latitude, destination.longitude)

            tile = Tile(
                game=self.map.game,
                coordinates=tile_coordinates,
                map_height=path.size[1],
                map_width=path.size[0],
                map_directory=self.map_directory,
                logger=self.logger,
                tile_code=path.code,
                auto_process=False,
                blur_radius=0,
                multiplier=10,
            )

            origin = tile_coordinates
            self.tiles.append(tile)

    def process(self):
        for tile in self.tiles:
            tile.process()

        self.debug()
        self.generate_obj_files()

    def generate_obj_files(self):
        for tile in self.tiles:
            # Read DEM data from the tile.
            dem_path = tile._dem_path
            base_directory = os.path.dirname(dem_path)
            save_path = os.path.join(base_directory, f"{tile.code}.obj")
            dem_data = cv2.imread(tile._dem_path, cv2.IMREAD_UNCHANGED)
            self.plane_from_np(dem_data, save_path)

    def plane_from_np(self, dem_data: np.ndarray, save_path: str):
        # We need to apply gaussian blur to the DEM data to make it smooth.
        dem_data = cv2.normalize(dem_data, None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U)

        # resize to 25% of the original size
        dem_data = cv2.resize(dem_data, (0, 0), fx=0.25, fy=0.25)

        dem_data = cv2.GaussianBlur(dem_data, (51, 51), sigmaX=40, sigmaY=40)

        rows, cols = dem_data.shape
        x = np.linspace(0, cols - 1, cols)
        y = np.linspace(0, rows - 1, rows)
        x, y = np.meshgrid(x, y)
        z = dem_data

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

        faces = np.array(faces)
        mesh = trimesh.Trimesh(vertices=vertices, faces=faces)
        mesh.export(save_path)

    def debug(self):
        # Merge all tiles into one image for debugging purposes.
        # Center tile not exists, fill it with black color.

        image_height = self.map_height + DEFAULT_DISTANCE * 2
        image_width = self.map_width + DEFAULT_DISTANCE * 2

        image = np.zeros((image_height, image_width, 3), np.uint8)

        for tile in self.tiles:
            tile_image = cv2.imread(tile._dem_path)
            if tile.code == "N":
                x = DEFAULT_DISTANCE
                y = 0
            elif tile.code == "NE":
                x = image_width - DEFAULT_DISTANCE
                y = 0
            elif tile.code == "E":
                x = image_width - DEFAULT_DISTANCE
                y = DEFAULT_DISTANCE
            elif tile.code == "SE":
                x = image_width - DEFAULT_DISTANCE
                y = image_height - DEFAULT_DISTANCE
            elif tile.code == "S":
                x = DEFAULT_DISTANCE
                y = image_height - DEFAULT_DISTANCE
            elif tile.code == "SW":
                x = 0
                y = image_height - DEFAULT_DISTANCE
            elif tile.code == "W":
                x = 0
                y = DEFAULT_DISTANCE
            elif tile.code == "NW":
                x = 0
                y = 0

            image[y : y + tile.map_height, x : x + tile.map_width] = tile_image

        # Save image to the map directory.
        cv2.imwrite(f"{self.map_directory}/background.png", image)

    # def parse_code(self, tile_code: str):
    #     half_width = int(self.map_width / 2)
    #     half_height = int(self.map_height / 2)
    #     offset = DEFAULT_DISTANCE / 2


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
