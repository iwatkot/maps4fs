"""This module contains the GRLE class for generating InfoLayer PNG files based on GRLE schema."""

from __future__ import annotations

import json
import os
from random import choice, randint
from typing import NamedTuple

import cv2
import numpy as np
from shapely.geometry import Polygon
from tqdm import tqdm

from maps4fs.generator.component.base.component_image import ImageComponent
from maps4fs.generator.component.layer import Layer
from maps4fs.generator.component.xml_document import XmlDocument
from maps4fs.generator.monitor import monitor_performance
from maps4fs.generator.settings import Parameters


class GRLELayer(NamedTuple):
    """Named tuple for GRLE layer.

    Arguments:
        name (str): name of the layer including file extension (e.g., "infoLayer_tipCollision.png").
        height_multiplier (float): multiplier for the height of the layer relative to the map size.
        width_multiplier (float): multiplier for the width of the layer relative to the map size.
        channels (int): number of channels in the layer (e.g., 1 for grayscale, 3 for RGB).
        data_type (str): data type of the layer (e.g., "uint8", "float32").
    """

    name: str
    height_multiplier: float
    width_multiplier: float
    channels: int
    data_type: str


class GRLE(ImageComponent):
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
        self.xml_path = self.game.farmlands_xml_path

    def _read_grle_schema(self) -> list[GRLELayer]:
        """Load and parse GRLE schema layers from the game configuration.

        Returns:
            list[GRLELayer]: Parsed GRLE layers, or an empty list on read/parse errors.
        """
        grle_schema_path = self.game.grle_schema

        try:
            with open(grle_schema_path, "r", encoding="utf-8") as file:
                grle_schema = json.load(file)
            self.logger.debug("GRLE schema loaded from: %s.", grle_schema_path)
        except (json.JSONDecodeError, FileNotFoundError) as error:
            self.logger.error("Error loading GRLE schema from %s: %s.", grle_schema_path, error)
            grle_schema = None

        try:
            return [
                GRLELayer(
                    name=layer["name"],
                    height_multiplier=layer["height_multiplier"],
                    width_multiplier=layer["width_multiplier"],
                    channels=layer["channels"],
                    data_type=layer["data_type"],
                )
                for layer in grle_schema
            ]

        except (KeyError, TypeError) as e:
            self.logger.error("Error parsing GRLE schema: %s.", e)
            return []

    @monitor_performance
    def process(self) -> None:
        """Generate all GRLE info layers and populate them with generated content."""
        grle_schema = self._read_grle_schema()
        if not grle_schema:
            self.logger.debug("GRLE schema is not obtained, skipping the processing.")
            return

        for info_layer in tqdm(grle_schema, desc="Preparing GRLE files", unit="layer"):
            file_path = os.path.join(self.game.weights_dir_path, info_layer.name)

            height = int(self.scaled_size * info_layer.height_multiplier)
            width = int(self.scaled_size * info_layer.width_multiplier)
            channels = info_layer.channels
            data_type = info_layer.data_type
            info_layer_data: np.ndarray

            # Create the InfoLayer PNG file with zeros.
            if channels == 1:
                info_layer_data = np.zeros((height, width), dtype=data_type)
            else:
                info_layer_data = np.zeros((height, width, channels), dtype=data_type)
            self.logger.debug("Shape of %s: %s.", info_layer.name, info_layer_data.shape)
            cv2.imwrite(file_path, info_layer_data)
            self.logger.debug("InfoLayer PNG file %s created.", file_path)

        self.grle_schema = grle_schema

        self._add_farmlands()
        if self.map.grle_settings.add_grass:
            self._add_plants()
        self._process_environment()
        self._process_indoor()

    def get_info_layer_by_name(self, name: str) -> GRLELayer | None:
        """Returns the GRLELayer object for the given name.

        Arguments:
            name (str): The name of the InfoLayer PNG file.

        Returns:
            GRLELayer | None: The GRLELayer object if found, else None.
        """
        if not hasattr(self, "grle_schema") or not isinstance(self.grle_schema, list):
            return None
        for layer in self.grle_schema:
            if layer.name == name:
                return layer
        return None

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
            if image is None:
                self.logger.warning("Preview source could not be loaded: %s", preview_path)
                continue
            if (
                image.shape[0] > Parameters.PREVIEW_MAXIMUM_SIZE
                or image.shape[1] > Parameters.PREVIEW_MAXIMUM_SIZE
            ):
                image = cv2.resize(
                    image, (Parameters.PREVIEW_MAXIMUM_SIZE, Parameters.PREVIEW_MAXIMUM_SIZE)
                )
            image_normalized = np.empty_like(image)
            cv2.normalize(image, image_normalized, 0, 255, cv2.NORM_MINMAX)
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
        fields_layer = self.map.context.get_layer_by_usage("field")
        if not fields_layer:
            self.logger.debug("Fields layer not found in the texture component.")
            return None

        fields_layer_path = fields_layer.get_preview_or_path(self.game.weights_dir_path)
        if not fields_layer_path or not os.path.isfile(fields_layer_path):
            self.logger.debug("Fields layer not found in the texture component.")
            return None
        fields_np = cv2.imread(fields_layer_path)
        if fields_np is None:
            self.logger.debug("Fields preview image could not be loaded: %s", fields_layer_path)
            return None
        # Resize fields_np to the same size as farmlands_np.
        fields_np = cv2.resize(fields_np, (farmlands_np.shape[1], farmlands_np.shape[0]))

        # use fields_np as base layer and overlay farmlands_np on top of it with 50% alpha blending.
        return cv2.addWeighted(fields_np, 0.5, farmlands_np, 0.5, 0)

    @monitor_performance
    def _add_farmlands(self) -> None:
        """Add farmlands polygons to the farmland info layer and update farmlands XML."""
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

        info_layer_farmlands_path = self.game.farmlands_path

        self.logger.debug(
            "Adding farmlands to the InfoLayer PNG file: %s.", info_layer_farmlands_path
        )

        if not os.path.isfile(info_layer_farmlands_path):
            self.logger.warning("InfoLayer PNG file %s not found.", info_layer_farmlands_path)
            return

        image = cv2.imread(info_layer_farmlands_path, cv2.IMREAD_UNCHANGED)
        if image is None:
            self.logger.warning(
                "Could not read farmlands info layer image: %s", info_layer_farmlands_path
            )
            return

        doc = XmlDocument(self.xml_path)
        if doc.get("farmlands") is None:
            raise ValueError("Farmlands XML element not found in the farmlands XML file.")

        doc.set_attrs("farmlands", pricePerHa=str(self.map.grle_settings.base_price))

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

            # divide argument depends on the width and height multipliers of the farmlands info layer.
            # By default, it's 2, since farmlands is 0.5 to the map size in both width and height.
            farmlands_grle_layer = self.get_info_layer_by_name(Parameters.INFO_LAYER_FARMLANDS)
            if not farmlands_grle_layer:
                self.logger.error("Farmlands InfoLayer PNG file not found in the GRLE schema.")
                return

            if not farmlands_grle_layer.height_multiplier == farmlands_grle_layer.width_multiplier:
                self.logger.error(
                    "Farmlands InfoLayer PNG file has different height and width multipliers, "
                    "which is not supported by Giants Editor."
                )
                raise ValueError(
                    "Farmlands InfoLayer PNG file has different height and width multipliers."
                )

            divide = int(1 / farmlands_grle_layer.height_multiplier)
            self.logger.debug("Using divide value of %s for farmland ID %s.", divide, farmland_id)

            farmland_np = self.polygon_points_to_np(fitted_farmland, divide=divide)

            if farmland_id > Parameters.FARMLAND_ID_LIMIT:
                self.logger.warning(
                    "Farmland ID limit reached. Skipping the rest of the farmlands. "
                    "Giants Editor supports maximum 254 farmlands."
                )
                break

            try:
                cv2.fillPoly(image, [farmland_np], (float(farmland_id),))
            except Exception as e:
                self.logger.debug(
                    "Farmland %s could not be added to the InfoLayer PNG file with error: %s",
                    farmland_id,
                    e,
                )
                continue

            doc.append_child(
                "farmlands",
                "farmland",
                id=str(farmland_id),
                priceScale="1",
                npcName="FORESTER",
            )

            farmland_id += 1

        doc.save()

        # Replace all the zero values on the info layer image with 255.
        if self.map.grle_settings.fill_empty_farmlands:
            image[image == 0] = 255

        cv2.imwrite(info_layer_farmlands_path, image)

        self.assets.farmlands = info_layer_farmlands_path

        self.preview_paths["farmlands"] = info_layer_farmlands_path

    @monitor_performance
    def _add_plants(self) -> None:
        """Generate foliage values and write them into densityMap_fruits channel 0."""
        grass_layer = self.map.context.get_layer_by_usage("grass")
        if not grass_layer:
            self.logger.warning("Grass layer not found in the texture component.")
            return

        weights_directory = self.game.weights_dir_path
        grass_image_path = grass_layer.get_preview_or_path(weights_directory)
        self.logger.debug("Grass image path: %s.", grass_image_path)

        forest_layer = self.map.context.get_layer_by_usage("forest")
        forest_image = None
        if forest_layer:
            forest_image_path = forest_layer.get_preview_or_path(weights_directory)
            self.logger.debug("Forest image path: %s.", forest_image_path)
            if forest_image_path:

                forest_image = cv2.imread(forest_image_path, cv2.IMREAD_UNCHANGED)

        if not grass_image_path or not os.path.isfile(grass_image_path):
            self.logger.warning("Base image not found in %s.", grass_image_path)
            return

        density_map_fruit_path = self.game.density_map_fruits_path

        self.logger.debug("Density map for fruits path: %s.", density_map_fruit_path)

        if not os.path.isfile(density_map_fruit_path):
            self.logger.warning("Density map for fruits not found in %s.", density_map_fruit_path)
            return

        grass_image = self._load_binary_mask_image(grass_image_path, "grass")
        if grass_image is None:
            return

        use_extended_foliage_values, height_multiplier, width_multiplier = (
            self._get_foliage_density_settings()
        )
        if height_multiplier <= 0 or width_multiplier <= 0:
            return

        self.map.context.foliage_density_map_uint16 = use_extended_foliage_values

        grass_image = self._resize_and_merge_grass_forest_masks(
            grass_image,
            forest_image,
            height_multiplier,
            width_multiplier,
        )

        base_grass = self.map.grle_settings.base_grass
        base_layer_pixel_value = self._get_base_grass_pixel_value(
            str(base_grass),
            use_extended_foliage_values,
        )

        placement_mask = self._build_placement_mask(grass_image)
        grass_image_copy = self._create_base_grass_image(
            grass_image.shape,
            placement_mask,
            base_layer_pixel_value,
            use_extended_foliage_values,
        )

        # Create organic diversity directly inside the valid placement mask.
        island_count = int(self.scaled_size * Parameters.PLANTS_ISLAND_PERCENT // 100)
        self.logger.debug(
            "Generating organic plants with target complexity value %s.", island_count
        )
        if self.map.grle_settings.random_plants:
            grass_image_copy = self.create_organic_plant_diversity(
                grass_image_copy,
                placement_mask,
                island_count,
                use_extended_foliage_values=use_extended_foliage_values,
            )
            self.logger.debug("Organic plant diversity generated.")

        # Safety pass: enforce mask after all operations.
        grass_image_copy[~placement_mask] = 0

        grass_image_copy = self.remove_edge_pixel_values(grass_image_copy)

        if not self._save_plants_to_density_map(density_map_fruit_path, grass_image_copy):
            return

        self.assets.plants = density_map_fruit_path

        self.logger.debug("Updated density map for fruits saved in %s.", density_map_fruit_path)

    def _load_binary_mask_image(self, image_path: str, image_kind: str) -> np.ndarray | None:
        """Load an image and normalize it to a binary uint8 mask.

        Arguments:
            image_path (str): Source image path.
            image_kind (str): Human-readable image type used in logs.

        Returns:
            np.ndarray | None: Binary mask where non-zero means active pixels, or None on failure.
        """
        image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
        if image is None:
            self.logger.warning("Could not load %s mask image: %s", image_kind, image_path)
            return None

        if image.ndim == 3:
            return np.any(image > 0, axis=2).astype(np.uint8) * Parameters.PLANT_BINARY_MASK_VALUE

        return (image > 0).astype(np.uint8) * Parameters.PLANT_BINARY_MASK_VALUE

    def _get_foliage_density_settings(self) -> tuple[bool, int, int]:
        """Resolve foliage bit depth mode and density map resize multipliers.

        Returns:
            tuple[bool, int, int]:
                - Whether uint16 foliage encoding is active.
                - Height multiplier for density map dimensions.
                - Width multiplier for density map dimensions.
        """
        grle_density_map_fruits = self.get_info_layer_by_name(Parameters.DENSITY_MAP_FRUITS)
        if not grle_density_map_fruits:
            self.logger.error(
                "Density map for fruits InfoLayer PNG file not found in the GRLE schema."
            )
            return False, 0, 0

        normalized_dtype = str(grle_density_map_fruits.data_type).strip().lower()
        use_extended_foliage_values = normalized_dtype in {"uint16", "np.uint16", "numpy.uint16"}

        height_multiplier = int(grle_density_map_fruits.height_multiplier)
        width_multiplier = int(grle_density_map_fruits.width_multiplier)
        self.logger.debug(
            "Resizing grass and forest images with height multiplier %s and width multiplier %s.",
            height_multiplier,
            width_multiplier,
        )
        return use_extended_foliage_values, height_multiplier, width_multiplier

    def _resize_and_merge_grass_forest_masks(
        self,
        grass_image: np.ndarray,
        forest_image: np.ndarray | None,
        height_multiplier: int,
        width_multiplier: int,
    ) -> np.ndarray:
        """Resize grass and optional forest masks, then merge them into one mask.

        Arguments:
            grass_image (np.ndarray): Base grass mask image.
            forest_image (np.ndarray | None): Optional forest mask image.
            height_multiplier (int): Y-axis scale factor to density map size.
            width_multiplier (int): X-axis scale factor to density map size.

        Returns:
            np.ndarray: Resized binary mask with forest pixels merged into grass mask.
        """
        resized_grass = cv2.resize(
            grass_image,
            (grass_image.shape[1] * width_multiplier, grass_image.shape[0] * height_multiplier),
            interpolation=cv2.INTER_NEAREST,
        )

        if forest_image is None:
            return resized_grass

        prepared_forest = self._prepare_optional_forest_mask(
            forest_image,
            height_multiplier,
            width_multiplier,
        )
        if prepared_forest is None:
            return resized_grass

        resized_grass[prepared_forest != 0] = Parameters.PLANT_BINARY_MASK_VALUE
        return resized_grass

    def _prepare_optional_forest_mask(
        self,
        forest_image: np.ndarray,
        height_multiplier: int,
        width_multiplier: int,
    ) -> np.ndarray | None:
        """Normalize and resize optional forest mask to density map resolution.

        Arguments:
            forest_image (np.ndarray): Source forest mask image.
            height_multiplier (int): Y-axis scale factor to density map size.
            width_multiplier (int): X-axis scale factor to density map size.

        Returns:
            np.ndarray | None: Resized binary forest mask, or None if conversion fails.
        """
        if forest_image.ndim == 3:
            forest_image = (
                np.any(forest_image > 0, axis=2).astype(np.uint8)
                * Parameters.PLANT_BINARY_MASK_VALUE
            )
        else:
            forest_image = (forest_image > 0).astype(np.uint8) * Parameters.PLANT_BINARY_MASK_VALUE

        return cv2.resize(
            forest_image,
            (
                forest_image.shape[1] * width_multiplier,
                forest_image.shape[0] * height_multiplier,
            ),
            interpolation=cv2.INTER_NEAREST,
        )

    def _build_placement_mask(self, grass_image: np.ndarray) -> np.ndarray:
        """Create the final valid placement mask for plant generation.

        Arguments:
            grass_image (np.ndarray): Resized binary grass mask.

        Returns:
            np.ndarray: Boolean mask where True indicates plant placement is allowed.
        """
        placement_mask = grass_image != 0
        kernel_size = Parameters.PLANT_MASK_EROSION_KERNEL_SIZE
        kernel = np.ones((kernel_size, kernel_size), np.uint8)
        placement_mask = (
            cv2.erode(
                placement_mask.astype(np.uint8),
                kernel,
                iterations=Parameters.PLANT_MASK_EROSION_ITERATIONS,
            )
            > 0
        )

        placement_mask_frame = self.remove_edge_pixel_values(
            placement_mask.astype(np.uint8) * Parameters.PLANT_BINARY_MASK_VALUE
        )
        return placement_mask_frame > 0

    def _create_base_grass_image(
        self,
        shape: tuple[int, ...],
        placement_mask: np.ndarray,
        base_layer_pixel_value: int,
        use_extended_foliage_values: bool,
    ) -> np.ndarray:
        """Create an output image prefilled with base grass value in valid pixels.

        Arguments:
            shape (tuple[int, ...]): Target image shape.
            placement_mask (np.ndarray): Boolean valid placement mask.
            base_layer_pixel_value (int): Base foliage value to write.
            use_extended_foliage_values (bool): Whether uint16 output mode is active.

        Returns:
            np.ndarray: Initialized base image in uint8 or uint16 format.
        """
        dtype = np.uint16 if use_extended_foliage_values else np.uint8
        grass_image_copy = np.zeros(shape, dtype=dtype)
        grass_image_copy[placement_mask] = base_layer_pixel_value
        return grass_image_copy

    def _save_plants_to_density_map(
        self,
        density_map_fruit_path: str,
        grass_image_copy: np.ndarray,
    ) -> bool:
        """Write generated plant values into densityMap_fruits and save it.

        Arguments:
            density_map_fruit_path (str): Path to densityMap_fruits image file.
            grass_image_copy (np.ndarray): Generated channel-0 foliage values.

        Returns:
            bool: True if the file was updated and saved, False if loading failed.
        """
        density_map_fruits = cv2.imread(density_map_fruit_path, cv2.IMREAD_UNCHANGED)
        if density_map_fruits is None:
            self.logger.warning("Could not load density map for fruits: %s", density_map_fruit_path)
            return False
        self.logger.debug("Density map for fruits loaded, shape: %s.", density_map_fruits.shape)

        if grass_image_copy.dtype != density_map_fruits.dtype:
            grass_image_copy = grass_image_copy.astype(density_map_fruits.dtype)

        density_map_fruits[:, :, 0] = grass_image_copy
        self.logger.debug("Updated base image added as the B channel in the density map.")

        density_map_fruits = cv2.cvtColor(density_map_fruits, cv2.COLOR_BGR2RGB)
        cv2.imwrite(density_map_fruit_path, density_map_fruits)
        return True

    def _get_base_grass_pixel_value(
        self, base_grass: str, use_extended_foliage_values: bool
    ) -> int:
        """Return base grass pixel value for uint8 or uint16 mode.

        Arguments:
            base_grass (str): Base grass type key from settings.
            use_extended_foliage_values (bool): Whether uint16 foliage mode is active.

        Returns:
            int: Pixel value to write into densityMap_fruits channel for base grass.
        """
        bit_depth = 16 if use_extended_foliage_values else 8
        plant_values = Parameters.PLANT_PIXEL_VALUES_BY_BIT_DEPTH.get(bit_depth, {})
        default_pixel_value = Parameters.DEFAULT_GRASS_PIXEL_VALUE_BY_BIT_DEPTH[bit_depth]
        return plant_values.get(base_grass) or default_pixel_value

    @monitor_performance
    def create_organic_plant_diversity(
        self,
        image: np.ndarray,
        placement_mask: np.ndarray,
        complexity_value: int,
        use_extended_foliage_values: bool = False,
    ) -> np.ndarray:
        """Create organic, non-overlapping plant diversity within a valid mask.

        Arguments:
            image (np.ndarray): Base foliage image with base grass values already written.
            placement_mask (np.ndarray): Boolean mask of pixels where plants are allowed.
            complexity_value (int): Legacy complexity input used to scale variation density.
            use_extended_foliage_values (bool): Whether uint16 foliage mode is active.

        Returns:
            np.ndarray: Updated image with organic plant diversity.
        """
        bit_depth = 16 if use_extended_foliage_values else 8
        possible_values = list(Parameters.PLANT_ISLAND_PIXEL_VALUES_BY_BIT_DEPTH.get(bit_depth, []))
        if not possible_values:
            return image

        valid_mask = placement_mask.astype(bool)
        valid_pixels = int(np.count_nonzero(valid_mask))
        if valid_pixels == 0:
            return image

        height, width = image.shape[:2]

        valid_mask_u8 = valid_mask.astype(np.uint8)
        macro_mask = self._build_macro_plant_mask(valid_mask, height, width)
        coverage = self._calculate_plant_coverage(complexity_value)

        # Build diversity independently in each connected region, so roads split vegetation naturally.
        num_labels, label_map = cv2.connectedComponents(valid_mask_u8, connectivity=8)
        smooth_size = Parameters.PLANT_SMOOTH_KERNEL_SIZE
        smooth_kernel = np.ones((smooth_size, smooth_size), np.uint8)
        assigned_mask = np.zeros_like(valid_mask, dtype=bool)
        large_sigma, small_sigma, selector_sigma = self._get_component_noise_sigmas(height, width)

        for label in range(1, num_labels):
            component_mask = label_map == label
            component_macro = macro_mask & component_mask
            component_pixels = int(np.count_nonzero(component_macro))
            if component_pixels < Parameters.PLANT_COMPONENT_MIN_PIXELS:
                continue

            component_diversity = self._build_component_diversity_mask(
                component_macro,
                height,
                width,
                coverage,
                smooth_kernel,
                large_sigma,
                small_sigma,
            )

            if np.count_nonzero(component_diversity) == 0:
                continue

            self._assign_component_plant_values(
                image,
                component_diversity,
                possible_values,
                selector_sigma,
                assigned_mask,
                height,
                width,
            )

        # Add sparse single plants and tiny clumps for micro diversity, including near edges.
        self._apply_micro_plant_diversity(
            image,
            valid_mask,
            valid_pixels,
            possible_values,
            coverage,
        )

        return image

    def _build_macro_plant_mask(
        self,
        valid_mask: np.ndarray,
        height: int,
        width: int,
    ) -> np.ndarray:
        """Create macro placement mask offset from invalid borders with randomized wobble.

        Arguments:
            valid_mask (np.ndarray): Boolean mask of all valid foliage pixels.
            height (int): Image height.
            width (int): Image width.

        Returns:
            np.ndarray: Boolean mask suitable for large-scale plant patch generation.
        """
        valid_mask_u8 = valid_mask.astype(np.uint8)
        distance_to_invalid = cv2.distanceTransform(valid_mask_u8, cv2.DIST_L2, 3)
        edge_buffer_px = max(
            Parameters.PLANT_EDGE_BUFFER_MIN,
            min(
                Parameters.PLANT_EDGE_BUFFER_MAX,
                float(max(height, width)) / Parameters.PLANT_EDGE_BUFFER_DIVISOR,
            ),
        )

        edge_jitter_sigma_coarse = max(
            Parameters.PLANT_EDGE_JITTER_COARSE_SIGMA_MIN,
            float(max(height, width)) / Parameters.PLANT_EDGE_JITTER_COARSE_SIGMA_DIVISOR,
        )
        edge_jitter_sigma_fine = max(
            Parameters.PLANT_EDGE_JITTER_FINE_SIGMA_MIN,
            float(max(height, width)) / Parameters.PLANT_EDGE_JITTER_FINE_SIGMA_DIVISOR,
        )

        edge_jitter_noise_coarse = cv2.GaussianBlur(
            np.random.random((height, width)).astype(np.float32),
            (0, 0),
            edge_jitter_sigma_coarse,
        )
        edge_jitter_noise_fine = cv2.GaussianBlur(
            np.random.random((height, width)).astype(np.float32),
            (0, 0),
            edge_jitter_sigma_fine,
        )
        edge_jitter_noise = (
            edge_jitter_noise_coarse * Parameters.PLANT_EDGE_JITTER_COARSE_WEIGHT
            + edge_jitter_noise_fine * Parameters.PLANT_EDGE_JITTER_FINE_WEIGHT
        )
        normalized_edge_jitter = np.empty_like(edge_jitter_noise)
        edge_jitter_noise = cv2.normalize(
            edge_jitter_noise,
            normalized_edge_jitter,
            alpha=Parameters.PLANT_EDGE_JITTER_NORMALIZE_ALPHA,
            beta=Parameters.PLANT_EDGE_JITTER_NORMALIZE_BETA,
            norm_type=cv2.NORM_MINMAX,
            dtype=cv2.CV_32F,
        )

        local_edge_buffer = np.clip(
            edge_buffer_px * (1.0 + edge_jitter_noise),
            Parameters.PLANT_EDGE_BUFFER_CLIP_MIN,
            edge_buffer_px * Parameters.PLANT_EDGE_BUFFER_CLIP_MAX_FACTOR,
        )
        return valid_mask & (distance_to_invalid >= local_edge_buffer)

    def _calculate_plant_coverage(self, complexity_value: int) -> float:
        """Calculate macro diversity coverage ratio from complexity input.

        Arguments:
            complexity_value (int): Complexity value used to scale variation density.

        Returns:
            float: Coverage ratio in the configured min/max range.
        """
        return min(
            Parameters.PLANT_COVERAGE_MAX,
            max(
                Parameters.PLANT_COVERAGE_MIN,
                Parameters.PLANT_COVERAGE_BASE
                + (complexity_value / max(1, self.scaled_size))
                * Parameters.PLANT_COVERAGE_COMPLEXITY_SCALE,
            ),
        )

    def _get_component_noise_sigmas(self, height: int, width: int) -> tuple[float, float, float]:
        """Return Gaussian blur sigmas used by component and selector noise layers.

        Arguments:
            height (int): Image height.
            width (int): Image width.

        Returns:
            tuple[float, float, float]: Large, small, and selector blur sigma values.
        """
        max_dim = float(max(height, width))
        large_sigma = max(
            Parameters.PLANT_COMPONENT_LARGE_SIGMA_MIN,
            max_dim / Parameters.PLANT_COMPONENT_LARGE_SIGMA_DIVISOR,
        )
        small_sigma = max(
            Parameters.PLANT_COMPONENT_SMALL_SIGMA_MIN,
            max_dim / Parameters.PLANT_COMPONENT_SMALL_SIGMA_DIVISOR,
        )
        selector_sigma = max(
            Parameters.PLANT_SELECTOR_SIGMA_MIN,
            max_dim / Parameters.PLANT_SELECTOR_SIGMA_DIVISOR,
        )
        return large_sigma, small_sigma, selector_sigma

    def _build_component_diversity_mask(
        self,
        component_macro: np.ndarray,
        height: int,
        width: int,
        coverage: float,
        smooth_kernel: np.ndarray,
        large_sigma: float,
        small_sigma: float,
    ) -> np.ndarray:
        """Build and smooth one connected component's diversity mask from blended noise.

        Arguments:
            component_macro (np.ndarray): Macro mask for a single connected component.
            height (int): Image height.
            width (int): Image width.
            coverage (float): Target component coverage ratio.
            smooth_kernel (np.ndarray): Morphology kernel used for open/close smoothing.
            large_sigma (float): Sigma for coarse noise layer.
            small_sigma (float): Sigma for fine noise layer.

        Returns:
            np.ndarray: Smoothed boolean diversity mask for the component.
        """
        component_large_noise = cv2.GaussianBlur(
            np.random.random((height, width)).astype(np.float32),
            (0, 0),
            large_sigma,
        )
        component_small_noise = cv2.GaussianBlur(
            np.random.random((height, width)).astype(np.float32),
            (0, 0),
            small_sigma,
        )
        component_noise = (
            component_large_noise * Parameters.PLANT_COMPONENT_LARGE_NOISE_WEIGHT
            + component_small_noise * Parameters.PLANT_COMPONENT_SMALL_NOISE_WEIGHT
        )

        threshold = float(np.quantile(component_noise[component_macro], 1.0 - coverage))
        component_diversity_bool = component_macro & (component_noise >= threshold)

        component_diversity_u8 = cv2.morphologyEx(
            component_diversity_bool.astype(np.uint8),
            cv2.MORPH_OPEN,
            smooth_kernel,
            iterations=Parameters.PLANT_SMOOTH_ITERATIONS,
        )
        component_diversity_u8 = cv2.morphologyEx(
            component_diversity_u8,
            cv2.MORPH_CLOSE,
            smooth_kernel,
            iterations=Parameters.PLANT_SMOOTH_ITERATIONS,
        )
        component_diversity = component_diversity_u8.astype(bool)
        component_diversity &= component_macro
        return component_diversity

    def _assign_component_plant_values(
        self,
        image: np.ndarray,
        component_diversity: np.ndarray,
        possible_values: list[int],
        selector_sigma: float,
        assigned_mask: np.ndarray,
        height: int,
        width: int,
    ) -> None:
        """Assign disjoint plant-value bands inside one component diversity mask.

        Arguments:
            image (np.ndarray): Output foliage image to update.
            component_diversity (np.ndarray): Boolean component diversity mask.
            possible_values (list[int]): Plant pixel values available for assignment.
            selector_sigma (float): Blur sigma for selector noise.
            assigned_mask (np.ndarray): Global mask tracking already assigned pixels.
            height (int): Image height.
            width (int): Image width.
        """
        selector_noise = cv2.GaussianBlur(
            np.random.random((height, width)).astype(np.float32),
            (0, 0),
            selector_sigma,
        )
        selector_values = selector_noise[component_diversity]
        quantile_edges = np.linspace(0.0, 1.0, len(possible_values) + 1)

        for idx, plant_value in enumerate(possible_values):
            low_q = float(np.quantile(selector_values, quantile_edges[idx]))
            high_q = float(np.quantile(selector_values, quantile_edges[idx + 1]))
            if idx == len(possible_values) - 1:
                band_mask = component_diversity & (selector_noise >= low_q)
            else:
                band_mask = (
                    component_diversity & (selector_noise >= low_q) & (selector_noise < high_q)
                )
            band_mask &= ~assigned_mask
            image[band_mask] = plant_value
            assigned_mask |= band_mask

    def _apply_micro_plant_diversity(
        self,
        image: np.ndarray,
        valid_mask: np.ndarray,
        valid_pixels: int,
        possible_values: list[int],
        coverage: float,
    ) -> None:
        """Apply sparse single-pixel and tiny-clump diversity across valid mask.

        Arguments:
            image (np.ndarray): Output foliage image to update.
            valid_mask (np.ndarray): Boolean mask of valid placement pixels.
            valid_pixels (int): Number of valid pixels in the mask.
            possible_values (list[int]): Plant pixel values available for assignment.
            coverage (float): Coverage ratio used to derive sprinkle density.
        """
        sprinkle_ratio = min(
            Parameters.PLANT_MICRO_SPRINKLE_RATIO_MAX,
            max(
                Parameters.PLANT_MICRO_SPRINKLE_RATIO_MIN,
                coverage / Parameters.PLANT_MICRO_SPRINKLE_RATIO_DIVISOR,
            ),
        )
        sprinkle_count = int(valid_pixels * sprinkle_ratio)
        if sprinkle_count <= 0:
            return

        available_y, available_x = np.where(valid_mask)
        sample_size = min(sprinkle_count, available_y.size)
        if sample_size <= 0:
            return

        selected_indices = np.random.choice(available_y.size, size=sample_size, replace=False)
        sprinkle_y = available_y[selected_indices]
        sprinkle_x = available_x[selected_indices]
        sprinkle_values = np.random.choice(possible_values, size=sample_size)
        image[sprinkle_y, sprinkle_x] = sprinkle_values

        clump_mask = np.zeros_like(valid_mask, dtype=np.uint8)
        clump_mask[sprinkle_y, sprinkle_x] = Parameters.PLANT_BINARY_MASK_VALUE
        clump_kernel_size = Parameters.PLANT_MICRO_CLUMP_KERNEL_SIZE
        clump_kernel = np.ones((clump_kernel_size, clump_kernel_size), np.uint8)
        clump_mask_bool = (
            cv2.dilate(
                clump_mask,
                clump_kernel,
                iterations=Parameters.PLANT_MICRO_CLUMP_ITERATIONS,
            )
            > 0
        )
        clump_mask_bool &= valid_mask

        clump_count = int(np.count_nonzero(clump_mask_bool))
        if clump_count <= 0:
            return

        random_clump_values = np.random.choice(possible_values, size=clump_count)
        image[clump_mask_bool] = random_clump_values

    @monitor_performance
    def create_island_of_plants(
        self,
        image: np.ndarray,
        count: int,
        use_extended_foliage_values: bool = False,
    ) -> np.ndarray:
        """Create an island of plants in the image.

        Arguments:
            image (np.ndarray): The image where the island of plants will be created.
            count (int): The number of islands of plants to create.
            use_extended_foliage_values (bool): Whether uint16 foliage mode is active.

        Returns:
            np.ndarray: The input image with randomly generated plant islands.
        """
        # B and G channels remain the same (zeros), while we change the R channel.
        bit_depth = 16 if use_extended_foliage_values else 8
        possible_r_values = list(
            Parameters.PLANT_ISLAND_PIXEL_VALUES_BY_BIT_DEPTH.get(bit_depth, [])
        )

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
        """Populate environment info layer using area type and water texture masks."""
        info_layer_environment_path = self.game.environment_path
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

        texture_component = self.map.context
        if not texture_component.texture_layers:
            self.logger.warning("Texture layers not found in context.")
            return

        for layer in texture_component.get_area_type_layers():
            pixel_value = Parameters.ENVIRONMENT_AREA_TYPES.get(layer.area_type)
            if pixel_value is None:
                continue
            weight_image = self.get_resized_weight(layer, environment_size)
            if weight_image is None:
                self.logger.warning("Weight image for area type layer not found in %s.", layer.name)
                continue
            environment_image[weight_image > 0] = pixel_value

        for layer in texture_component.get_water_area_layers():
            weight_image = self.get_resized_weight(layer, environment_size)
            if weight_image is None:
                self.logger.warning(
                    "Weight image for water area layer not found in %s.", layer.name
                )
                continue
            water_mask = weight_image > 0
            environment_image[water_mask] = environment_image[water_mask] + int(
                Parameters.WATER_AREA_PIXEL_VALUE
            )

        cv2.imwrite(info_layer_environment_path, environment_image)
        self.logger.debug("Environment InfoLayer PNG file saved: %s.", info_layer_environment_path)
        self.preview_paths["environment"] = info_layer_environment_path

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
        weight_image_path = layer.get_preview_or_path(self.game.weights_dir_path)
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
            weight_image.astype(np.uint8),
            np.ones((dilations, dilations), np.uint8),
            iterations=dilations,
        )

        return dilated_weight_image

    def _process_indoor(self) -> None:
        """Populate indoor info layer from indoor texture masks."""
        info_layer_indoor_path = self.game.indoor_mask_path
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

        texture_context = self.map.context
        if not texture_context.texture_layers:
            self.logger.warning("Texture layers not found in context.")
            return

        for layer in texture_context.get_indoor_layers():
            weight_image = self.get_resized_weight(layer, indoor_mask_size, dilations=0)
            if weight_image is None:
                self.logger.warning("Weight image for indoor layer not found in %s.", layer.name)
                continue

            indoor_mask_image[weight_image > 0] = 1

        cv2.imwrite(info_layer_indoor_path, indoor_mask_image)
        self.logger.debug("Indoor InfoLayer PNG file saved: %s.", info_layer_indoor_path)
        self.preview_paths["indoor"] = info_layer_indoor_path
