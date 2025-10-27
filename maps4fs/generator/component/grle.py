"""This module contains the GRLE class for generating InfoLayer PNG files based on GRLE schema."""

import json
import os
from random import choice, randint

import cv2
import numpy as np
from shapely.geometry import Polygon
from tqdm import tqdm

from maps4fs.generator.component.base.component_image import ImageComponent
from maps4fs.generator.component.base.component_xml import XMLComponent
from maps4fs.generator.component.layer import Layer
from maps4fs.generator.monitor import monitor_performance
from maps4fs.generator.settings import Parameters

# This value sums up the pixel value of the basic area type to convert it from "No Water" to "Near Water".
# For example, if the basic area type is "city" (1), then the pixel value for "near water" will be 9.
WATER_AREA_PIXEL_VALUE = 8


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


def area_type_to_pixel_value(area_type: str) -> int | None:
    """Returns the pixel value representation of the area type.
    If not found, returns None.

    Arguments:
        area_type (str): name of the area type

    Returns:
        int | None: pixel value of the area type or None if not found.
    """
    area_types = {
        "open_land": 0,
        "city": 1,
        "village": 2,
        "harbor": 3,
        "industrial": 4,
        "open_water": 5,
    }
    return area_types.get(area_type)


class GRLE(ImageComponent, XMLComponent):
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

    def preprocess(self) -> None:
        """Gets the path to the map I3D file from the game instance and saves it to the instance
        attribute. If the game does not support I3D files, the attribute is set to None."""
        self.preview_paths: dict[str, str] = {}
        try:
            self.xml_path = self.game.get_farmlands_xml_path(self.map_directory)
        except NotImplementedError:
            self.logger.warning("Farmlands XML file processing is not implemented for this game.")
            self.xml_path = None

    def _read_grle_schema(self) -> dict[str, float | int | str] | None:
        try:
            grle_schema_path = self.game.grle_schema
        except ValueError:
            self.logger.warning("GRLE schema processing is not implemented for this game.")
            return None

        try:
            with open(grle_schema_path, "r", encoding="utf-8") as file:
                grle_schema = json.load(file)
            self.logger.debug("GRLE schema loaded from: %s.", grle_schema_path)
        except (json.JSONDecodeError, FileNotFoundError) as error:
            self.logger.error("Error loading GRLE schema from %s: %s.", grle_schema_path, error)
            grle_schema = None

        return grle_schema

    @monitor_performance
    def process(self) -> None:
        """Generates InfoLayer PNG files based on the GRLE schema."""
        grle_schema = self._read_grle_schema()
        if not grle_schema:
            self.logger.debug("GRLE schema is not obtained, skipping the processing.")
            return

        for info_layer in tqdm(grle_schema, desc="Preparing GRLE files", unit="layer"):
            if isinstance(info_layer, dict):
                file_path = os.path.join(
                    self.game.weights_dir_path(self.map_directory), info_layer["name"]
                )

                height = int(self.scaled_size * info_layer["height_multiplier"])
                width = int(self.scaled_size * info_layer["width_multiplier"])
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
        if self.game.plants_processing and self.map.grle_settings.add_grass:
            self._add_plants()
        if self.game.environment_processing:
            self._process_environment()
            self._process_indoor()

    @monitor_performance
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
            if (
                image.shape[0] > Parameters.PREVIEW_MAXIMUM_SIZE  # type: ignore
                or image.shape[1] > Parameters.PREVIEW_MAXIMUM_SIZE  # type: ignore
            ):
                image = cv2.resize(
                    image, (Parameters.PREVIEW_MAXIMUM_SIZE, Parameters.PREVIEW_MAXIMUM_SIZE)  # type: ignore
                )
            image_normalized = np.empty_like(image)
            cv2.normalize(image, image_normalized, 0, 255, cv2.NORM_MINMAX)  # type: ignore
            image_colored = cv2.applyColorMap(image_normalized, cv2.COLORMAP_JET)
            cv2.imwrite(save_path, image_colored)
            preview_paths.append(save_path)

            if preview_name != "farmlands":
                continue

            with_fields_save_path = os.path.join(
                self.previews_directory, f"{preview_name}_with_fields.png"
            )
            image_with_fields = self.overlay_fields(image_colored)
            if image_with_fields is None:
                continue
            cv2.imwrite(with_fields_save_path, image_with_fields)
            preview_paths.append(with_fields_save_path)

        return preview_paths

    @monitor_performance
    def overlay_fields(self, farmlands_np: np.ndarray) -> np.ndarray | None:
        """Overlay fields on the farmlands preview image.

        Arguments:
            farmlands_np (np.ndarray): The farmlands preview image.

        Returns:
            np.ndarray | None: The farmlands preview image with fields overlayed on top of it.
        """
        fields_layer = self.map.get_texture_layer(by_usage="field")
        if not fields_layer:
            self.logger.debug("Fields layer not found in the texture component.")
            return None

        fields_layer_path = fields_layer.get_preview_or_path(
            self.game.weights_dir_path(self.map_directory)
        )
        if not fields_layer_path or not os.path.isfile(fields_layer_path):
            self.logger.debug("Fields layer not found in the texture component.")
            return None
        fields_np = cv2.imread(fields_layer_path)
        # Resize fields_np to the same size as farmlands_np.
        fields_np = cv2.resize(fields_np, (farmlands_np.shape[1], farmlands_np.shape[0]))  # type: ignore

        # use fields_np as base layer and overlay farmlands_np on top of it with 50% alpha blending.
        return cv2.addWeighted(fields_np, 0.5, farmlands_np, 0.5, 0)

    @monitor_performance
    def _add_farmlands(self) -> None:
        """Adds farmlands to the InfoLayer PNG file."""
        farmlands = []

        fields = self.get_infolayer_data(Parameters.TEXTURES, Parameters.FIELDS)
        if fields:
            self.logger.debug("Found %s fields in textures info layer.", len(fields))
            farmlands.extend(fields)

        farmyards = self.get_infolayer_data(Parameters.TEXTURES, Parameters.FARMYARDS)
        if farmyards and self.map.grle_settings.add_farmyards:
            farmlands.extend(farmyards)
            self.logger.debug("Found %s farmyards in textures info layer.", len(farmyards))

        if not farmlands:
            self.logger.warning(
                "No farmlands was obtained from fields or farmyards, skipping the processing."
            )
            return

        info_layer_farmlands_path = self.game.get_farmlands_path(self.map_directory)

        self.logger.debug(
            "Adding farmlands to the InfoLayer PNG file: %s.", info_layer_farmlands_path
        )

        if not os.path.isfile(info_layer_farmlands_path):
            self.logger.warning("InfoLayer PNG file %s not found.", info_layer_farmlands_path)
            return

        image = cv2.imread(info_layer_farmlands_path, cv2.IMREAD_UNCHANGED)

        tree = self.get_tree()
        root = tree.getroot()
        farmlands_node = root.find("farmlands")  # type: ignore
        if farmlands_node is None:
            raise ValueError("Farmlands XML element not found in the farmlands XML file.")

        self.update_element(farmlands_node, {"pricePerHa": str(self.map.grle_settings.base_price)})

        farmland_id = 1

        for farmland in tqdm(farmlands, desc="Adding farmlands", unit="farmland"):
            try:
                fitted_farmland = self.fit_object_into_bounds(
                    polygon_points=farmland,
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

            farmland_np = self.polygon_points_to_np(fitted_farmland, divide=2)

            if farmland_id > Parameters.FARMLAND_ID_LIMIT:
                self.logger.warning(
                    "Farmland ID limit reached. Skipping the rest of the farmlands. "
                    "Giants Editor supports maximum 254 farmlands."
                )
                break

            try:
                cv2.fillPoly(image, [farmland_np], (float(farmland_id),))  # type: ignore
            except Exception as e:
                self.logger.debug(
                    "Farmland %s could not be added to the InfoLayer PNG file with error: %s",
                    farmland_id,
                    e,
                )
                continue

            data = {
                "id": str(farmland_id),
                "priceScale": "1",
                "npcName": "FORESTER",
            }
            self.create_subelement(farmlands_node, "farmland", data)

            farmland_id += 1

        self.save_tree(tree)

        # Replace all the zero values on the info layer image with 255.
        if self.map.grle_settings.fill_empty_farmlands:
            image[image == 0] = 255  # type: ignore

        cv2.imwrite(info_layer_farmlands_path, image)  # type: ignore

        self.assets.farmlands = info_layer_farmlands_path

        self.preview_paths["farmlands"] = info_layer_farmlands_path

    @monitor_performance
    def _add_plants(self) -> None:
        """Adds plants to the InfoLayer PNG file."""
        grass_layer = self.map.get_texture_layer(by_usage="grass")
        if not grass_layer:
            self.logger.warning("Grass layer not found in the texture component.")
            return

        weights_directory = self.game.weights_dir_path(self.map_directory)
        grass_image_path = grass_layer.get_preview_or_path(weights_directory)
        self.logger.debug("Grass image path: %s.", grass_image_path)

        forest_layer = self.map.get_texture_layer(by_usage="forest")
        forest_image = None
        if forest_layer:
            forest_image_path = forest_layer.get_preview_or_path(weights_directory)
            self.logger.debug("Forest image path: %s.", forest_image_path)
            if forest_image_path:

                forest_image = cv2.imread(forest_image_path, cv2.IMREAD_UNCHANGED)

        if not grass_image_path or not os.path.isfile(grass_image_path):
            self.logger.warning("Base image not found in %s.", grass_image_path)
            return

        density_map_fruit_path = self.game.get_density_map_fruits_path(self.map_directory)

        self.logger.debug("Density map for fruits path: %s.", density_map_fruit_path)

        if not os.path.isfile(density_map_fruit_path):
            self.logger.warning("Density map for fruits not found in %s.", density_map_fruit_path)
            return

        # Single channeled 8-bit image, where non-zero values (255) are where the grass is.
        grass_image = cv2.imread(grass_image_path, cv2.IMREAD_UNCHANGED)

        # Density map of the fruits is 2X size of the base image, so we need to resize it.
        # We'll resize the base image to make it bigger, so we can compare the values.
        grass_image = cv2.resize(
            grass_image,  # type: ignore
            (grass_image.shape[1] * 2, grass_image.shape[0] * 2),  # type: ignore
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

        base_grass = self.map.grle_settings.base_grass
        if isinstance(base_grass, tuple):
            base_grass = base_grass[0]

        base_layer_pixel_value = plant_to_pixel_value(str(base_grass))
        if not base_layer_pixel_value:
            base_layer_pixel_value = 131

        grass_image_copy = grass_image.copy()
        if forest_image is not None:
            # Add the forest layer to the base image, to merge the masks.
            grass_image_copy[forest_image != 0] = base_layer_pixel_value

        grass_image_copy[grass_image != 0] = base_layer_pixel_value

        # Add islands of plants to the base image.
        island_count = int(self.scaled_size * Parameters.PLANTS_ISLAND_PERCENT // 100)
        self.logger.debug("Adding %s islands of plants to the base image.", island_count)
        if self.map.grle_settings.random_plants:
            grass_image_copy = self.create_island_of_plants(grass_image_copy, island_count)
            self.logger.debug("Added %s islands of plants to the base image.", island_count)

        # Sligtly reduce the size of the grass_image, that we'll use as mask.
        kernel = np.ones((3, 3), np.uint8)
        grass_image = cv2.erode(grass_image, kernel, iterations=1)

        # Remove the values where the base image has zeros.
        grass_image_copy[grass_image == 0] = 0
        self.logger.debug("Removed the values where the base image has zeros.")

        grass_image_copy = self.remove_edge_pixel_values(grass_image_copy)

        # Three channeled 8-bit image, where non-zero values are the
        # different types of plants (only in the R channel).
        density_map_fruits = cv2.imread(density_map_fruit_path, cv2.IMREAD_UNCHANGED)
        self.logger.debug("Density map for fruits loaded, shape: %s.", density_map_fruits.shape)  # type: ignore

        # Put the updated base image as the B channel in the density map.
        density_map_fruits[:, :, 0] = grass_image_copy  # type: ignore
        self.logger.debug("Updated base image added as the B channel in the density map.")

        # Save the updated density map.
        # Ensure that order of channels is correct because CV2 uses BGR and we need RGB.
        density_map_fruits = cv2.cvtColor(density_map_fruits, cv2.COLOR_BGR2RGB)  # type: ignore
        cv2.imwrite(density_map_fruit_path, density_map_fruits)

        self.assets.plants = density_map_fruit_path

        self.logger.debug("Updated density map for fruits saved in %s.", density_map_fruit_path)

    @monitor_performance
    def create_island_of_plants(self, image: np.ndarray, count: int) -> np.ndarray:
        """Create an island of plants in the image.

        Arguments:
            image (np.ndarray): The image where the island of plants will be created.
            count (int): The number of islands of plants to create.

        Returns:
            np.ndarray: The image with the islands of plants.
        """
        # B and G channels remain the same (zeros), while we change the R channel.
        possible_r_values = [65, 97, 129, 161, 193, 225]

        for _ in tqdm(range(count), desc="Adding islands of plants", unit="island"):
            # Randomly choose the value for the island.
            plant_value = choice(possible_r_values)
            # Randomly choose the size of the island.
            island_size = randint(
                Parameters.PLANTS_ISLAND_MINIMUM_SIZE,
                Parameters.PLANTS_ISLAND_MAXIMUM_SIZE,
            )
            # Randomly choose the position of the island.
            x = randint(0, image.shape[1] - island_size)
            y = randint(0, image.shape[0] - island_size)

            try:
                polygon_points = self.get_rounded_polygon(
                    num_vertices=Parameters.PLANTS_ISLAND_VERTEX_COUNT,
                    center=(x + island_size // 2, y + island_size // 2),
                    radius=island_size // 2,
                    rounding_radius=Parameters.PLANTS_ISLAND_ROUNDING_RADIUS,
                )
                if not polygon_points:
                    continue

                nodes = np.array(polygon_points, np.int32)
                cv2.fillPoly(image, [nodes], (float(plant_value),))
            except Exception:
                continue

        return image

    @staticmethod
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
        island_distortion = 0.3

        angle_offset = np.pi / num_vertices
        angles = np.linspace(0, 2 * np.pi, num_vertices, endpoint=False) + angle_offset
        random_angles = angles + np.random.uniform(
            -island_distortion, island_distortion, num_vertices
        )  # Add randomness to angles
        random_radii = radius + np.random.uniform(
            -radius * island_distortion, radius * island_distortion, num_vertices
        )  # Add randomness to radii

        points = [
            (center[0] + np.cos(a) * r, center[1] + np.sin(a) * r)
            for a, r in zip(random_angles, random_radii)
        ]
        polygon = Polygon(points)
        buffered_polygon = polygon.buffer(rounding_radius, quad_segs=16)
        rounded_polygon = list(buffered_polygon.exterior.coords)
        if not rounded_polygon:
            return None
        return rounded_polygon

    @staticmethod
    def remove_edge_pixel_values(image_np: np.ndarray) -> np.ndarray:
        """Remove the edge pixel values from the image.

        Arguments:
            image_np (np.ndarray): The image to remove the edge pixel values from.

        Returns:
            np.ndarray: The image with the edge pixel values removed.
        """
        # Set zeros on all sides of the image
        image_np[0, :] = 0  # Top side
        image_np[-1, :] = 0  # Bottom side
        image_np[:, 0] = 0  # Left side
        image_np[:, -1] = 0  # Right side
        return image_np

    @monitor_performance
    def _process_environment(self) -> None:
        info_layer_environment_path = self.game.get_environment_path(self.map_directory)
        if not info_layer_environment_path or not os.path.isfile(info_layer_environment_path):
            self.logger.warning(
                "Environment InfoLayer PNG file not found in %s.", info_layer_environment_path
            )
            return

        self.logger.debug(
            "Processing environment InfoLayer PNG file: %s.", info_layer_environment_path
        )

        environment_image = cv2.imread(info_layer_environment_path, cv2.IMREAD_UNCHANGED)
        if environment_image is None:
            self.logger.error("Failed to read the environment InfoLayer PNG file.")
            return

        self.logger.debug(
            "Environment InfoLayer PNG file loaded, shape: %s.", environment_image.shape
        )

        environment_size = int(environment_image.shape[0])

        # 1. Get the texture layers that contain "area_type" property.
        # 2. Read the corresponding weight image (not the dissolved ones!).
        # 3. Resize it to match the environment image size (probably 1/4 of the texture size).
        # 4. Dilate the texture mask to make it little bit bigger.
        # 5. Set the corresponding pixel values of the environment image to the pixel value of the area type.
        # 6. Get the texture layer that "area_water" is True.
        # 7. Same as resize, dilate, etc.
        # 8. Sum the current pixel value with the WATER_AREA_PIXEL_VALUE.

        texture_component = self.map.get_texture_component()
        if not texture_component:
            self.logger.warning("Texture component not found in the map.")
            return

        for layer in texture_component.get_area_type_layers():
            pixel_value = area_type_to_pixel_value(layer.area_type)  # type: ignore
            # * Not enabled for now.
            # * If the layer is invisible, we need to draw the mask from the info layer.
            # if layer.invisible:
            #     self.logger.debug("Processing invisible area type layer: %s.", layer.name)
            #     if layer.info_layer:
            #         self.logger.debug("Info layer available: %s.", layer.info_layer)
            #         weight_image = self.draw_invisible_layer_mask(layer, environment_size)
            #     else:
            #         self.logger.debug("No info layer available for layer: %s.", layer.name)
            #         continue
            # else:
            weight_image = self.get_resized_weight(layer, environment_size)  # type: ignore
            if weight_image is None:
                self.logger.warning("Weight image for area type layer not found in %s.", layer.name)
                continue
            environment_image[weight_image > 0] = pixel_value  # type: ignore

        for layer in texture_component.get_water_area_layers():
            pixel_value = WATER_AREA_PIXEL_VALUE
            weight_image = self.get_resized_weight(layer, environment_size)
            if weight_image is None:
                self.logger.warning(
                    "Weight image for water area layer not found in %s.", layer.name
                )
                continue
            environment_image[weight_image > 0] += pixel_value  # type: ignore

        cv2.imwrite(info_layer_environment_path, environment_image)
        self.logger.debug("Environment InfoLayer PNG file saved: %s.", info_layer_environment_path)
        self.preview_paths["environment"] = info_layer_environment_path

    # def draw_invisible_layer_mask(self, layer: Layer, resize_to: int) -> np.ndarray:
    #     """Draw the mask for the invisible layer.

    #     Arguments:
    #         layer (Layer): The layer for which to draw the mask.
    #         resize_to (int): The size to which the mask should be resized.

    #     Returns:
    #         np.ndarray: The resized mask.
    #     """
    #     mask = np.zeros((self.map.size, self.map.size), dtype=np.uint8)
    #     polygons = self.get_infolayer_data(Parameters.TEXTURES, layer.info_layer)
    #     self.logger.debug("Found %d polygons in info layer %s.", len(polygons), layer.info_layer)

    #     for polygon in polygons:
    #         try:
    #             fitted_polygon = self.fit_object_into_bounds(
    #                 polygon_points=polygon,
    #                 # margin=self.map.grle_settings.farmland_margin,
    #                 angle=self.rotation,
    #             )
    #         except ValueError as e:
    #             self.logger.debug(
    #                 "Polygon could not be fitted into the map bounds with error: %s",
    #                 e,
    #             )
    #             continue
    #         polygon_np = self.polygon_points_to_np(fitted_polygon)

    #         try:
    #             cv2.fillPoly(mask, [polygon_np], (float(255),))  # type: ignore
    #         except Exception as e:
    #             self.logger.debug(
    #                 "Polygon could not be added to the mask with error: %s",
    #                 e,
    #             )
    #             continue

    #     resized_mask = cv2.resize(
    #         mask,
    #         (resize_to, resize_to),
    #         interpolation=cv2.INTER_NEAREST,
    #     )

    #     return resized_mask

    @monitor_performance
    def get_resized_weight(
        self, layer: Layer, resize_to: int, dilations: int = 3
    ) -> np.ndarray | None:
        """Get the resized weight image for a given layer.

        Arguments:
            layer (Layer): The layer for which to get the weight image.
            resize_to (int): The size to which the weight image should be resized.
            dilations (int): The number of dilations to apply to the weight image.

        Returns:
            np.ndarray | None: The resized and dilated weight image, or None if the image could not be loaded.
        """
        weight_image_path = layer.get_preview_or_path(
            self.game.weights_dir_path(self.map_directory)
        )
        self.logger.debug("Weight image path for area type layer: %s.", weight_image_path)

        if not weight_image_path or not os.path.isfile(weight_image_path):
            self.logger.warning(
                "Weight image for area type layer not found in %s.", weight_image_path
            )
            return None

        weight_image = cv2.imread(weight_image_path, cv2.IMREAD_UNCHANGED)
        if weight_image is None:
            self.logger.error("Failed to read the weight image for area type layer.")
            return None

        self.logger.debug("Weight image for area type layer loaded, shape: %s.", weight_image.shape)

        # Resize the weight image to match the environment image size.
        weight_image = cv2.resize(
            weight_image,
            (resize_to, resize_to),
            interpolation=cv2.INTER_NEAREST,
        )

        self.logger.debug(
            "Resized weight image for area type layer, new shape: %s.", weight_image.shape
        )

        if dilations <= 0:
            return weight_image

        dilated_weight_image = cv2.dilate(
            weight_image.astype(np.uint8), np.ones((dilations, dilations), np.uint8), iterations=dilations  # type: ignore
        )

        return dilated_weight_image

    def _process_indoor(self) -> None:
        """Processes the indoor layers."""
        info_layer_indoor_path = self.game.get_indoor_mask_path(self.map_directory)
        if not info_layer_indoor_path or not os.path.isfile(info_layer_indoor_path):
            self.logger.warning(
                "Indoor InfoLayer PNG file not found in %s.", info_layer_indoor_path
            )
            return

        indoor_mask_image = cv2.imread(info_layer_indoor_path, cv2.IMREAD_UNCHANGED)
        if indoor_mask_image is None:
            self.logger.warning(
                "Failed to read the indoor InfoLayer PNG file %s.", info_layer_indoor_path
            )
            return

        indoor_mask_size = int(indoor_mask_image.shape[0])
        self.logger.debug("Indoor InfoLayer PNG file loaded, shape: %s.", indoor_mask_image.shape)

        texture_component = self.map.get_texture_component()
        if not texture_component:
            self.logger.warning("Texture component not found in the map.")
            return

        for layer in texture_component.get_indoor_layers():
            weight_image = self.get_resized_weight(layer, indoor_mask_size, dilations=0)
            if weight_image is None:
                self.logger.warning("Weight image for indoor layer not found in %s.", layer.name)
                continue

            indoor_mask_image[weight_image > 0] = 1

        cv2.imwrite(info_layer_indoor_path, indoor_mask_image)
        self.logger.debug("Indoor InfoLayer PNG file saved: %s.", info_layer_indoor_path)
        self.preview_paths["indoor"] = info_layer_indoor_path
