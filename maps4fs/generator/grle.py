"""This module contains the GRLE class for generating InfoLayer PNG files based on GRLE schema."""

import json
import os
from random import choice, randint
from xml.etree import ElementTree as ET

import cv2
import numpy as np
from shapely.geometry import Polygon  # type: ignore
from tqdm import tqdm

from maps4fs.generator.component import Component
from maps4fs.generator.texture import PREVIEW_MAXIMUM_SIZE, Texture

ISLAND_DISTORTION = 0.3


def plant_to_pixel_value(plant_name: str) -> int | None:
    """Returns the pixel value representation of the plant.
    If not found, returns None.

    Arguments:
        plant_name (str): name of the plant

    Returns:
        int | None: pixel value of the plant or None if not found.
    """
    plants = {
        "smallDenseMix": 33,
        "meadow": 131,
    }
    return plants.get(plant_name)


# pylint: disable=W0223
class GRLE(Component):
    """Component for to generate InfoLayer PNG files based on GRLE schema.

    Arguments:
        game (Game): The game instance for which the map is generated.
        coordinates (tuple[float, float]): The latitude and longitude of the center of the map.
        map_size (int): The size of the map in pixels.
        map_rotated_size (int): The size of the map in pixels after rotation.
        rotation (int): The rotation angle of the map.
        map_directory (str): The directory where the map files are stored.
        logger (Any, optional): The logger to use. Must have at least three basic methods: debug,
            info, warning. If not provided, default logging will be used.
    """

    _grle_schema: dict[str, float | int | str] | None = None

    def preprocess(self) -> None:
        """Gets the path to the map I3D file from the game instance and saves it to the instance
        attribute. If the game does not support I3D files, the attribute is set to None."""
        self.preview_paths: dict[str, str] = {}

        try:
            grle_schema_path = self.game.grle_schema
        except ValueError:
            self.logger.warning("GRLE schema processing is not implemented for this game.")
            return

        try:
            with open(grle_schema_path, "r", encoding="utf-8") as file:
                self._grle_schema = json.load(file)
            self.logger.debug("GRLE schema loaded from: %s.", grle_schema_path)
        except (json.JSONDecodeError, FileNotFoundError) as error:
            self.logger.error("Error loading GRLE schema from %s: %s.", grle_schema_path, error)
            self._grle_schema = None

    def process(self) -> None:
        """Generates InfoLayer PNG files based on the GRLE schema."""
        if not self._grle_schema:
            self.logger.debug("GRLE schema is not obtained, skipping the processing.")
            return

        for info_layer in tqdm(self._grle_schema, desc="Preparing GRLE files", unit="layer"):
            if isinstance(info_layer, dict):
                file_path = os.path.join(
                    self.game.weights_dir_path(self.map_directory), info_layer["name"]
                )

                height = int(self.map_size * info_layer["height_multiplier"])
                width = int(self.map_size * info_layer["width_multiplier"])
                channels = info_layer["channels"]
                data_type = info_layer["data_type"]

                # Create the InfoLayer PNG file with zeros.
                if channels == 1:
                    info_layer_data = np.zeros((height, width), dtype=data_type)
                else:
                    info_layer_data = np.zeros((height, width, channels), dtype=data_type)
                self.logger.debug("Shape of %s: %s.", info_layer["name"], info_layer_data.shape)
                cv2.imwrite(file_path, info_layer_data)
                self.logger.debug("InfoLayer PNG file %s created.", file_path)
            else:
                self.logger.warning("Invalid InfoLayer schema: %s.", info_layer)

        self._add_farmlands()
        if self.game.code == "FS25":
            self.logger.debug("Game is %s, plants will be added.", self.game.code)
            self._add_plants()
        else:
            self.logger.warning("Adding plants it's not supported for the %s.", self.game.code)

    def previews(self) -> list[str]:
        """Returns a list of paths to the preview images (empty list).
        The component does not generate any preview images so it returns an empty list.

        Returns:
            list[str]: An empty list.
        """
        preview_paths = []
        for preview_name, preview_path in self.preview_paths.items():
            save_path = os.path.join(self.previews_directory, f"{preview_name}.png")
            # Resize the preview image to the maximum size allowed for previews.
            image = cv2.imread(preview_path, cv2.IMREAD_GRAYSCALE)
            if image.shape[0] > PREVIEW_MAXIMUM_SIZE or image.shape[1] > PREVIEW_MAXIMUM_SIZE:
                image = cv2.resize(image, (PREVIEW_MAXIMUM_SIZE, PREVIEW_MAXIMUM_SIZE))
            image_normalized = np.empty_like(image)
            cv2.normalize(image, image_normalized, 0, 255, cv2.NORM_MINMAX)
            image_colored = cv2.applyColorMap(image_normalized, cv2.COLORMAP_JET)
            cv2.imwrite(save_path, image_colored)
            preview_paths.append(save_path)

            with_fields_save_path = os.path.join(
                self.previews_directory, f"{preview_name}_with_fields.png"
            )
            image_with_fields = self.overlay_fields(image_colored)
            if image_with_fields is None:
                continue
            cv2.imwrite(with_fields_save_path, image_with_fields)
            preview_paths.append(with_fields_save_path)

        return preview_paths

    def overlay_fields(self, farmlands_np: np.ndarray) -> np.ndarray | None:
        """Overlay fields on the farmlands preview image.

        Arguments:
            farmlands_np (np.ndarray): The farmlands preview image.

        Returns:
            np.ndarray | None: The farmlands preview image with fields overlayed on top of it.
        """
        texture_component: Texture | None = self.map.get_component("Texture")  # type: ignore
        if not texture_component:
            self.logger.warning("Texture component not found in the map.")
            return None

        fields_layer = texture_component.get_layer_by_usage("field")
        fields_layer_path = fields_layer.get_preview_or_path(  # type: ignore
            self.game.weights_dir_path(self.map_directory)
        )
        if not fields_layer_path or not os.path.isfile(fields_layer_path):
            self.logger.warning("Fields layer not found in the texture component.")
            return None
        fields_np = cv2.imread(fields_layer_path)
        # Resize fields_np to the same size as farmlands_np.
        fields_np = cv2.resize(fields_np, (farmlands_np.shape[1], farmlands_np.shape[0]))

        # use fields_np as base layer and overlay farmlands_np on top of it with 50% alpha blending.
        return cv2.addWeighted(fields_np, 0.5, farmlands_np, 0.5, 0)

    # pylint: disable=R0801, R0914, R0915
    def _add_farmlands(self) -> None:
        """Adds farmlands to the InfoLayer PNG file."""

        textures_info_layer_path = self.get_infolayer_path("textures")
        if not textures_info_layer_path:
            return

        with open(textures_info_layer_path, "r", encoding="utf-8") as textures_info_layer_file:
            textures_info_layer = json.load(textures_info_layer_file)

        farmlands = []
        farmyards: list[list[tuple[int, int]]] | None = textures_info_layer.get("farmyards")
        if farmyards and self.map.grle_settings.add_farmyards:
            farmlands.extend(farmyards)
            self.logger.debug("Found %s farmyards in textures info layer.", len(farmyards))

        fields: list[list[tuple[int, int]]] | None = textures_info_layer.get("fields")
        if not fields:
            self.logger.warning("Fields data not found in textures info layer.")
            return
        farmlands.extend(fields)

        self.logger.debug("Found %s fields in textures info layer.", len(fields))

        info_layer_farmlands_path = os.path.join(
            self.game.weights_dir_path(self.map_directory), "infoLayer_farmlands.png"
        )

        self.logger.debug(
            "Adding farmlands to the InfoLayer PNG file: %s.", info_layer_farmlands_path
        )

        if not os.path.isfile(info_layer_farmlands_path):
            self.logger.warning("InfoLayer PNG file %s not found.", info_layer_farmlands_path)
            return

        image = cv2.imread(info_layer_farmlands_path, cv2.IMREAD_UNCHANGED)
        farmlands_xml_path = os.path.join(self.map_directory, "map/config/farmlands.xml")
        if not os.path.isfile(farmlands_xml_path):
            self.logger.warning("Farmlands XML file %s not found.", farmlands_xml_path)
            return

        tree = ET.parse(farmlands_xml_path)
        farmlands_xml = tree.find("farmlands")

        # Not using enumerate because in case of the error, we do not increment
        # the farmland_id. So as a result we do not have a gap in the farmland IDs.
        farmland_id = 1

        for farmland_data in tqdm(farmlands, desc="Adding farmlands", unit="farmland"):
            try:
                fitted_field = self.fit_object_into_bounds(
                    polygon_points=farmland_data,
                    margin=self.map.grle_settings.farmland_margin,
                    angle=self.rotation,
                )
            except ValueError as e:
                self.logger.debug(
                    "Farmland %s could not be fitted into the map bounds with error: %s",
                    farmland_id,
                    e,
                )
                continue

            self.logger.debug("Fitted field %s contains %s points.", farmland_id, len(fitted_field))

            field_np = np.array(fitted_field, np.int32)
            field_np = field_np.reshape((-1, 1, 2))

            self.logger.debug(
                "Created a numpy array and reshaped it. Number of points: %s", len(field_np)
            )

            # Infolayer image is 1/2 of the size of the map image, that's why we need to divide
            # the coordinates by 2.
            field_np = field_np // 2
            self.logger.debug("Divided the coordinates by 2.")

            try:
                cv2.fillPoly(image, [field_np], farmland_id)  # type: ignore
            except Exception as e:  # pylint: disable=W0718
                self.logger.debug(
                    "Farmland %s could not be added to the InfoLayer PNG file with error: %s",
                    farmland_id,
                    e,
                )
                continue

            # Add the field to the farmlands XML.
            farmland = ET.SubElement(farmlands_xml, "farmland")  # type: ignore
            farmland.set("id", str(farmland_id))
            farmland.set("priceScale", "1")
            farmland.set("npcName", "FORESTER")

            farmland_id += 1

        tree.write(farmlands_xml_path)

        self.logger.debug("Farmlands added to the farmlands XML file: %s.", farmlands_xml_path)

        cv2.imwrite(info_layer_farmlands_path, image)
        self.logger.debug(
            "Farmlands added to the InfoLayer PNG file: %s.", info_layer_farmlands_path
        )

        self.preview_paths["farmlands"] = info_layer_farmlands_path  # type: ignore

    # pylint: disable=R0915
    def _add_plants(self) -> None:
        """Adds plants to the InfoLayer PNG file."""
        # 1. Get the path to the densityMap_fruits.png.
        # 2. Get the path to the base layer (grass).
        # 3. Detect non-zero areas in the base layer (it's where the plants will be placed).
        texture_component: Texture | None = self.map.get_component("Texture")  # type: ignore
        if not texture_component:
            self.logger.warning("Texture component not found in the map.")
            return

        grass_layer = texture_component.get_layer_by_usage("grass")
        if not grass_layer:
            self.logger.warning("Grass layer not found in the texture component.")
            return

        weights_directory = self.game.weights_dir_path(self.map_directory)
        grass_image_path = grass_layer.get_preview_or_path(weights_directory)
        self.logger.debug("Grass image path: %s.", grass_image_path)

        forest_layer = texture_component.get_layer_by_usage("forest")
        forest_image = None
        if forest_layer:
            forest_image_path = forest_layer.get_preview_or_path(weights_directory)
            self.logger.debug("Forest image path: %s.", forest_image_path)
            if forest_image_path:

                forest_image = cv2.imread(forest_image_path, cv2.IMREAD_UNCHANGED)

        if not grass_image_path or not os.path.isfile(grass_image_path):
            self.logger.warning("Base image not found in %s.", grass_image_path)
            return

        density_map_fruit_path = os.path.join(
            self.game.weights_dir_path(self.map_directory), "densityMap_fruits.png"
        )

        self.logger.debug("Density map for fruits path: %s.", density_map_fruit_path)

        if not os.path.isfile(density_map_fruit_path):
            self.logger.warning("Density map for fruits not found in %s.", density_map_fruit_path)
            return

        # Single channeled 8-bit image, where non-zero values (255) are where the grass is.
        grass_image = cv2.imread(grass_image_path, cv2.IMREAD_UNCHANGED)

        # Density map of the fruits is 2X size of the base image, so we need to resize it.
        # We'll resize the base image to make it bigger, so we can compare the values.
        grass_image = cv2.resize(
            grass_image,
            (grass_image.shape[1] * 2, grass_image.shape[0] * 2),
            interpolation=cv2.INTER_NEAREST,
        )
        if forest_image is not None:
            forest_image = cv2.resize(
                forest_image,
                (forest_image.shape[1] * 2, forest_image.shape[0] * 2),
                interpolation=cv2.INTER_NEAREST,
            )

            # Add non zero values from the forest image to the grass image.
            grass_image[forest_image != 0] = 255

        # B and G channels remain the same (zeros), while we change the R channel.
        possible_R_values = [65, 97, 129, 161, 193, 225]  # pylint: disable=C0103

        base_layer_pixel_value = plant_to_pixel_value(
            self.map.grle_settings.base_grass  # type:ignore
        )
        if not base_layer_pixel_value:
            base_layer_pixel_value = 131

        def create_island_of_plants(image: np.ndarray, count: int) -> np.ndarray:
            """Create an island of plants in the image.

            Arguments:
                image (np.ndarray): The image where the island of plants will be created.
                count (int): The number of islands of plants to create.

            Returns:
                np.ndarray: The image with the islands of plants.
            """
            for _ in tqdm(range(count), desc="Adding islands of plants", unit="island"):
                # Randomly choose the value for the island.
                plant_value = choice(possible_R_values)
                # Randomly choose the size of the island.
                island_size = randint(
                    self.map.grle_settings.plants_island_minimum_size,  # type:ignore
                    self.map.grle_settings.plants_island_maximum_size,  # type:ignore
                )
                # Randomly choose the position of the island.
                x = randint(0, image.shape[1] - island_size)
                y = randint(0, image.shape[0] - island_size)

                try:
                    polygon_points = get_rounded_polygon(
                        num_vertices=self.map.grle_settings.plants_island_vertex_count,
                        center=(x + island_size // 2, y + island_size // 2),
                        radius=island_size // 2,
                        rounding_radius=self.map.grle_settings.plants_island_rounding_radius,
                    )
                    if not polygon_points:
                        continue

                    nodes = np.array(polygon_points, np.int32)  # type: ignore
                    cv2.fillPoly(image, [nodes], plant_value)  # type: ignore
                except Exception:  # pylint: disable=W0703
                    continue

            return image

        def get_rounded_polygon(
            num_vertices: int, center: tuple[int, int], radius: int, rounding_radius: int
        ) -> list[tuple[int, int]] | None:
            """Get a randomly rounded polygon.

            Arguments:
                num_vertices (int): The number of vertices of the polygon.
                center (tuple[int, int]): The center of the polygon.
                radius (int): The radius of the polygon.
                rounding_radius (int): The rounding radius of the polygon.

            Returns:
                list[tuple[int, int]] | None: The rounded polygon.
            """
            angle_offset = np.pi / num_vertices
            angles = np.linspace(0, 2 * np.pi, num_vertices, endpoint=False) + angle_offset
            random_angles = angles + np.random.uniform(
                -ISLAND_DISTORTION, ISLAND_DISTORTION, num_vertices
            )  # Add randomness to angles
            random_radii = radius + np.random.uniform(
                -radius * ISLAND_DISTORTION, radius * ISLAND_DISTORTION, num_vertices
            )  # Add randomness to radii

            points = [
                (center[0] + np.cos(a) * r, center[1] + np.sin(a) * r)
                for a, r in zip(random_angles, random_radii)
            ]
            polygon = Polygon(points)
            buffered_polygon = polygon.buffer(rounding_radius, resolution=16)
            rounded_polygon = list(buffered_polygon.exterior.coords)
            if not rounded_polygon:
                return None
            return rounded_polygon

        grass_image_copy = grass_image.copy()
        if forest_image is not None:
            # Add the forest layer to the base image, to merge the masks.
            grass_image_copy[forest_image != 0] = base_layer_pixel_value

        grass_image_copy[grass_image != 0] = base_layer_pixel_value

        # Add islands of plants to the base image.
        island_count = int(self.map_size * self.map.grle_settings.plants_island_percent // 100)
        self.logger.debug("Adding %s islands of plants to the base image.", island_count)
        if self.map.grle_settings.random_plants:
            grass_image_copy = create_island_of_plants(grass_image_copy, island_count)
            self.logger.debug("Added %s islands of plants to the base image.", island_count)

        # Sligtly reduce the size of the grass_image, that we'll use as mask.
        kernel = np.ones((3, 3), np.uint8)
        grass_image = cv2.erode(grass_image, kernel, iterations=1)

        # Remove the values where the base image has zeros.
        grass_image_copy[grass_image == 0] = 0
        self.logger.debug("Removed the values where the base image has zeros.")

        # Set zeros on all sides of the image
        grass_image_copy[0, :] = 0  # Top side
        grass_image_copy[-1, :] = 0  # Bottom side
        grass_image_copy[:, 0] = 0  # Left side
        grass_image_copy[:, -1] = 0  # Right side

        # After painting it with base grass, we'll create multiple islands of different plants.
        # On the final step, we'll remove all the values which in pixels
        # where zerons in the original base image (so we don't paint grass where it should not be).

        # Three channeled 8-bit image, where non-zero values are the
        # different types of plants (only in the R channel).
        density_map_fruits = cv2.imread(density_map_fruit_path, cv2.IMREAD_UNCHANGED)
        self.logger.debug("Density map for fruits loaded, shape: %s.", density_map_fruits.shape)

        # Put the updated base image as the B channel in the density map.
        density_map_fruits[:, :, 0] = grass_image_copy
        self.logger.debug("Updated base image added as the B channel in the density map.")

        # Save the updated density map.
        # Ensure that order of channels is correct because CV2 uses BGR and we need RGB.
        density_map_fruits = cv2.cvtColor(density_map_fruits, cv2.COLOR_BGR2RGB)
        cv2.imwrite(density_map_fruit_path, density_map_fruits)
        self.logger.debug("Updated density map for fruits saved in %s.", density_map_fruit_path)
