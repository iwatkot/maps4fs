"""Component for map buildings processing and generation."""

from __future__ import annotations

import json
import os
from typing import Any, NamedTuple
from xml.etree import ElementTree as ET

import cv2
import numpy as np
from tqdm import tqdm

from maps4fs.generator.component.base.component_mesh import MeshComponent
from maps4fs.generator.component.xml_document import XmlDocument
from maps4fs.generator.geo import get_region_by_coordinates
from maps4fs.generator.settings import Parameters


class BuildingEntry(NamedTuple):
    """Data structure for a building entry in the buildings schema."""

    file: str
    name: str
    width: float
    depth: float
    categories: list[str]
    regions: list[str]
    type: str | None = None


class BuildingEntryCollection:
    """Collection of building entries with efficient lookup capabilities."""

    def __init__(
        self, building_entries: list[BuildingEntry], region: str, ignore_region: bool = False
    ):
        """Initialize the collection with a list of building entries for a specific region.

        Arguments:
            building_entries (list[BuildingEntry]): List of building entries to manage
            region (str): The region for this collection (filters entries to this region only)
            ignore_region (bool): If True, ignore region filtering and use all entries
        """
        self.region = region
        self.ignore_region = ignore_region

        # Filter entries based on ignore_region flag
        if ignore_region:
            self.entries = building_entries  # Use all entries regardless of region
        else:
            self.entries = [entry for entry in building_entries if region in entry.regions]

        # Create indices for faster lookup
        self._create_indices()

    def _create_indices(self) -> None:
        """Create indexed dictionaries for faster lookups."""
        self.by_category: dict[str, list[BuildingEntry]] = {}

        for entry in self.entries:
            # Index by each category (all entries are already filtered by region)
            for category in entry.categories:
                if category not in self.by_category:
                    self.by_category[category] = []
                self.by_category[category].append(entry)

    def find_best_match(
        self,
        category: str,
        width: float | None = None,
        depth: float | None = None,
        tolerance: float = 0.3,
    ) -> BuildingEntry | None:
        """Find the best matching building entry based on criteria.
        Entries are filtered by region during initialization unless ignore_region is True.

        Arguments:
            category (str): Required building category
            width (float | None): Desired width (optional)
            depth (float | None): Desired depth (optional)
            tolerance (float): Size tolerance factor (0.3 = 30% tolerance)

        Returns:
            BuildingEntry | None: Best matching entry or None if no suitable match found
        """
        # Start with buildings of the required category (filtered by region unless ignore_region is True)
        candidates = self.by_category.get(category, [])
        if not candidates:
            return None

        # Score each candidate
        scored_candidates = []
        for entry in candidates:
            score = self._calculate_match_score(entry, category, width, depth, tolerance)
            if score > 0:  # Only consider viable matches
                scored_candidates.append((score, entry))

        if not scored_candidates:
            return None

        # Return the highest scoring match
        scored_candidates.sort(key=lambda x: x[0], reverse=True)
        return scored_candidates[0][1]

    def find_best_match_with_orientation(
        self,
        category: str,
        width: float | None = None,
        depth: float | None = None,
        tolerance: float = 0.3,
    ) -> tuple[BuildingEntry | None, bool]:
        """Find the best matching building entry and determine if rotation is needed.

        Arguments:
            category (str): Required building category
            width (float | None): Desired width (optional)
            depth (float | None): Desired depth (optional)
            tolerance (float): Size tolerance factor (0.3 = 30% tolerance)

        Returns:
            tuple[BuildingEntry | None, bool]: Best matching entry and whether it needs 90° rotation
        """
        # Start with buildings of the required category
        candidates = self.by_category.get(category, [])
        if not candidates:
            return None, False

        # Score each candidate and track orientation
        scored_candidates = []
        for entry in candidates:
            score, needs_rotation = self._calculate_match_score_with_orientation(
                entry, category, width, depth, tolerance
            )
            if score > 0:  # Only consider viable matches
                scored_candidates.append((score, entry, needs_rotation))

        if not scored_candidates:
            return None, False

        # Return the highest scoring match with its orientation info
        scored_candidates.sort(key=lambda x: x[0], reverse=True)
        _, best_entry, needs_rotation = scored_candidates[0]
        return best_entry, needs_rotation

    def _calculate_match_score_with_orientation(
        self,
        entry: BuildingEntry,
        category: str,
        width: float | None,
        depth: float | None,
        tolerance: float,
    ) -> tuple[float, bool]:
        """Calculate a match score and determine orientation for a building entry.

        Returns:
            tuple[float, bool]: Match score and whether 90° rotation is needed
        """
        score = 0.0

        # Category match (required) - base score
        if category in entry.categories:
            score = 100.0
        else:
            return 0.0, False  # Category mismatch = no match

        # Size matching (if dimensions are provided)
        if width is not None and depth is not None:
            # Calculate how well the dimensions match (considering both orientations)
            size_score1 = self._calculate_size_match(
                entry.width, entry.depth, width, depth, tolerance
            )
            size_score2 = self._calculate_size_match(
                entry.width, entry.depth, depth, width, tolerance
            )

            # Determine which orientation is better
            if size_score1 >= size_score2:
                # Original orientation is better
                if size_score1 > 0:
                    score += size_score1 * 80.0
                    return score, False
                return 0.0, False
            if size_score2 > 0:
                score += size_score2 * 80.0
                return score, True
            return 0.0, False

        return score, False

    def _calculate_match_score(
        self,
        entry: BuildingEntry,
        category: str,
        width: float | None,
        depth: float | None,
        tolerance: float,
    ) -> float:
        """Calculate a match score for a building entry.
        Region is matched during initialization unless ignore_region is True.

        Returns:
            float: Match score (higher is better, 0 means no match)
        """
        score = 0.0

        # Category match (required) - base score
        if category in entry.categories:
            score = 100.0
        else:
            return 0.0  # Category mismatch = no match

        # Size matching (if dimensions are provided)
        if width is not None and depth is not None:
            # Calculate how well the dimensions match (considering both orientations)
            size_score1 = self._calculate_size_match(
                entry.width, entry.depth, width, depth, tolerance
            )
            size_score2 = self._calculate_size_match(
                entry.width, entry.depth, depth, width, tolerance
            )

            # Use the better orientation
            size_score = max(size_score1, size_score2)

            if size_score > 0:
                score += (
                    size_score * 80.0
                )  # Size match contributes up to 80 points (increased since no region bonus)
            else:
                return 0.0  # Size too different = no match

        return score

    def _calculate_size_match(
        self,
        entry_width: float,
        entry_depth: float,
        target_width: float,
        target_depth: float,
        tolerance: float,
    ) -> float:
        """Calculate how well building dimensions match target dimensions.

        Returns:
            float: Size match score between 0 and 1 (1 = perfect match)
        """
        width_ratio = min(entry_width, target_width) / max(entry_width, target_width)
        depth_ratio = min(entry_depth, target_depth) / max(entry_depth, target_depth)

        # Check if both dimensions are within tolerance
        if width_ratio < (1 - tolerance) or depth_ratio < (1 - tolerance):
            return 0.0

        # Calculate combined size score (average of both dimension matches)
        return (width_ratio + depth_ratio) / 2.0

    def get_available_categories(self) -> list[str]:
        """Get list of available building categories for this collection."""
        return list(self.by_category.keys())

    def filter_by_category(self, category: str) -> list[BuildingEntry]:
        """Get all buildings of a specific category (filtered by region unless ignore_region is True)."""
        return self.by_category.get(category, [])


class BuildingPlacement(NamedTuple):
    """Prepared building placement data used for schema matching and XML creation."""

    category: str
    width: float
    depth: float
    rotation_angle: float
    x: int
    y: int
    x_center: int
    y_center: int
    z: float


class Building(MeshComponent):
    """Component for map buildings processing and generation.

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
        """Preprocess and prepare buildings schema and buildings map image."""
        self.info: dict[str, Any] = {}
        if not self._is_generation_enabled():
            return
        if not self._load_buildings_schema():
            return

        self.xml_path = self.game.i3d_file_path

        if not self._prepare_buildings_category_map():
            return

        self._initialize_buildings_collection()

    def _is_generation_enabled(self) -> bool:
        """Return True when building generation is enabled in map settings."""
        if self.map.building_settings.generate_buildings:
            return True

        self.logger.debug("Building generation is disabled in the map settings.")
        return False

    def _load_buildings_schema(self) -> bool:
        """Load buildings schema from custom map config or default game file."""
        custom_buildings_schema = self.map.buildings_custom_schema
        if custom_buildings_schema:
            self.buildings_schema = custom_buildings_schema
            self.logger.debug(
                "Custom buildings schema loaded successfully with %d objects.",
                len(self.buildings_schema),
            )
            return True

        try:
            buildings_schema_path = self.game.buildings_schema
        except ValueError as e:
            self.logger.warning("The game does not support buildings schema: %s", e)
            return False

        if not os.path.isfile(buildings_schema_path):
            self.logger.warning(
                "Buildings schema file not found at path: %s. Skipping buildings generation.",
                buildings_schema_path,
            )
            return False

        try:
            with open(buildings_schema_path, "r", encoding="utf-8") as f:
                self.buildings_schema = json.load(f)
        except Exception as e:
            self.logger.warning(
                "Failed to load buildings schema from path: %s with error: %s. Skipping buildings generation.",
                buildings_schema_path,
                e,
            )
            return False

        self.logger.debug(
            "Buildings schema loaded successfully with %d objects.",
            len(self.buildings_schema),
        )
        return True

    def _prepare_buildings_category_map(self) -> bool:
        """Build a category raster that maps pixels to building categories."""
        buildings_directory = os.path.join(self.map.map_directory, Parameters.BUILDINGS_DIRECTORY)
        self.buildings_map_path = os.path.join(
            buildings_directory,
            Parameters.BUILDING_CATEGORIES_FILENAME,
        )
        os.makedirs(buildings_directory, exist_ok=True)

        if not self.map.context.texture_layers:
            self.logger.warning("Texture layers not found in context.")
            return False

        map_size = self.map.output_size or self.map.size
        buildings_map_image = np.zeros((map_size, map_size), dtype=np.uint8)

        for layer in self.map.context.get_building_category_layers():
            self._paint_building_category_layer(buildings_map_image, layer)

        cv2.imwrite(self.buildings_map_path, buildings_map_image)
        self.logger.debug("Building categories map saved to: %s", self.buildings_map_path)
        return True

    def _paint_building_category_layer(self, buildings_map_image: np.ndarray, layer: Any) -> None:
        """Paint one category layer into the category raster."""
        self.logger.debug(
            "Processing building category layer: %s (%s)",
            layer.name,
            layer.building_category,
        )

        pixel_value = Parameters.AREA_TYPES.get(layer.building_category)
        if pixel_value is None:
            self.logger.warning(
                "Unknown building category '%s' for layer '%s'. Skipping.",
                layer.building_category,
                layer.name,
            )
            return

        layer_path = layer.path(self.game.weights_dir_path)
        if not layer_path or not os.path.isfile(layer_path):
            self.logger.warning("Layer texture file not found: %s. Skipping.", layer_path)
            return

        layer_image = cv2.imread(layer_path, cv2.IMREAD_UNCHANGED)
        if layer_image is None:
            self.logger.warning("Failed to read layer image: %s. Skipping.", layer_path)
            return

        buildings_map_image[layer_image > 0] = pixel_value

    def _initialize_buildings_collection(self) -> None:
        """Prepare region-scoped building entries for fast matching during placement."""
        building_entries = [
            BuildingEntry(**building_entry) for building_entry in self.buildings_schema
        ]
        region, ignore_region = self._resolve_region_settings()

        self.buildings_collection = BuildingEntryCollection(building_entries, region, ignore_region)

        self.info["building_region"] = region
        self.info["ignore_building_region"] = ignore_region
        self.info["total_buildings_in_schema"] = len(self.buildings_collection.entries)

        if ignore_region:
            self.logger.debug(
                "Buildings collection created with %d buildings ignoring region restrictions.",
                len(self.buildings_collection.entries),
            )
            return

        self.logger.debug(
            "Buildings collection created with %d buildings for region '%s'.",
            len(self.buildings_collection.entries),
            region,
        )

    def _resolve_region_settings(self) -> tuple[str, bool]:
        """Resolve selected region and whether regional filtering must be disabled."""
        region_setting = self.map.building_settings.region
        if region_setting == Parameters.AUTO_REGION:
            return get_region_by_coordinates(self.coordinates), False
        if region_setting == Parameters.ALL_REGIONS:
            return Parameters.ALL_REGIONS, True
        return region_setting, False

    def process(self) -> None:
        """Process and place buildings on the map."""
        try:
            self.add_buildings()
        except Exception as e:
            self.logger.warning("An error occurred during buildings processing: %s", e)

    # pylint: disable=too-many-return-statements
    def add_buildings(self) -> None:
        """Process and place buildings on the map based on the buildings map image and schema."""
        loaded_inputs = self._load_processing_inputs()
        if loaded_inputs is None:
            return
        buildings_map_image, buildings, not_resized_dem = loaded_inputs

        prepared_document = self._prepare_i3d_targets()
        if prepared_document is None:
            return
        doc, files_section, buildings_group = prepared_document

        added_buildings_count = self._place_buildings(
            buildings,
            buildings_map_image,
            not_resized_dem,
            files_section,
            buildings_group,
        )
        self.logger.debug("Total buildings placed: %d of %d", added_buildings_count, len(buildings))

        self.info["total_buildings_placed"] = added_buildings_count
        self.info["total_buildings_attempted"] = len(buildings)

        # Save the modified XML tree
        doc.save()
        self.logger.debug("Buildings placement completed and saved to map.i3d")

    def _place_buildings(
        self,
        buildings: list[dict[str, Any]],
        buildings_map_image: np.ndarray,
        not_resized_dem: np.ndarray,
        files_section: ET.Element,
        buildings_group: ET.Element,
    ) -> int:
        """Place buildings into the I3D tree and return number of successfully placed entries."""
        used_building_files: dict[str, int] = {}
        file_id_counter = Parameters.BUILDINGS_STARTING_NODE_ID
        node_id_counter = Parameters.BUILDINGS_STARTING_NODE_ID + 1000
        placed_count = 0

        for building_data in tqdm(buildings, desc="Placing buildings", unit="building"):
            placed, file_id_counter, node_id_counter = self._place_single_building(
                building_data,
                buildings_map_image,
                not_resized_dem,
                files_section,
                buildings_group,
                used_building_files,
                file_id_counter,
                node_id_counter,
            )
            if placed:
                placed_count += 1

        return placed_count

    def _place_single_building(
        self,
        building_data: dict[str, Any],
        buildings_map_image: np.ndarray,
        not_resized_dem: np.ndarray,
        files_section: ET.Element,
        buildings_group: ET.Element,
        used_building_files: dict[str, int],
        file_id_counter: int,
        node_id_counter: int,
    ) -> tuple[bool, int, int]:
        """Attempt to place one building and return (placed, next_file_id, next_node_id)."""
        placement = self._prepare_building_placement(
            building_data,
            buildings_map_image,
            not_resized_dem,
        )
        if placement is None:
            return False, file_id_counter, node_id_counter

        best_match, needs_rotation = self.buildings_collection.find_best_match_with_orientation(
            category=placement.category,
            width=placement.width,
            depth=placement.depth,
            tolerance=self.map.building_settings.tolerance_factor / 100,
        )
        if best_match is None:
            self.logger.debug(
                "No suitable building found for category '%s' with dimensions %.2fx%.2f",
                placement.category,
                placement.width,
                placement.depth,
            )
            return False, file_id_counter, node_id_counter

        self.logger.debug(
            "Best building match: %s: %d x %d, needs_rotation: %s",
            best_match.name,
            best_match.width,
            best_match.depth,
            needs_rotation,
        )

        file_id, next_file_id = self._ensure_building_file_id(
            files_section,
            used_building_files,
            best_match.file,
            file_id_counter,
        )

        self._append_building_reference(
            buildings_group,
            best_match,
            node_id_counter,
            file_id,
            placement,
            needs_rotation,
        )
        return True, next_file_id, node_id_counter + 1

    def _load_processing_inputs(
        self,
    ) -> tuple[np.ndarray, list[dict[str, Any]], np.ndarray] | None:
        """Load and validate all required inputs before building placement starts."""
        if not hasattr(self, "buildings_map_path") or not os.path.isfile(self.buildings_map_path):
            self.logger.warning(
                "Buildings map path is not set or file does not exist. Skipping process step."
            )
            return None

        if not self.buildings_collection.entries:
            self.logger.warning(
                "No buildings found in the collection. Buildings generation will be skipped.",
            )
            return None

        buildings_map_image = cv2.imread(self.buildings_map_path, cv2.IMREAD_UNCHANGED)
        if buildings_map_image is None:
            self.logger.warning("Failed to read buildings map image. Skipping process step.")
            return None

        self.logger.debug("Buildings map categories file found, processing...")

        buildings = self.get_infolayer_data(Parameters.TEXTURES, Parameters.BUILDINGS)
        if not buildings:
            self.logger.warning("Buildings data not found in textures info layer.")
            return None

        not_resized_dem = self.get_dem_image_with_fallback(start_at=1)
        if not_resized_dem is None:
            self.logger.warning("Not resized DEM not found.")
            return None

        self.logger.debug("Found %d building entries to process.", len(buildings))
        return buildings_map_image, buildings, not_resized_dem

    def _prepare_i3d_targets(self) -> tuple[XmlDocument, ET.Element, ET.Element] | None:
        """Open map I3D XML and return document sections required for building placement."""
        doc = XmlDocument(self.xml_path)
        scene_node = doc.get(self.game.config.i3d_scene_xpath)
        if scene_node is None:
            self.logger.warning("Scene element not found in I3D file.")
            return None

        files_section = doc.get(self.game.config.i3d_files_xpath)
        if files_section is None:
            files_section = doc.append_child(".", self.game.config.i3d_files_section_tag)

        buildings_group = self._find_or_create_buildings_group(scene_node)
        return doc, files_section, buildings_group

    def _prepare_building_placement(
        self,
        building_data: dict[str, Any],
        buildings_map_image: np.ndarray,
        not_resized_dem: np.ndarray,
    ) -> BuildingPlacement | None:
        """Build placement candidate from source polygon, tags, category map and DEM."""
        building = building_data.get(Parameters.POINTS)
        building_osm_tags = building_data.get(Parameters.TAGS)
        if not building:
            self.logger.debug("Skipping building entry with missing points data.")
            return None

        try:
            fitted_building = self.fit_object_into_bounds(
                polygon_points=building, angle=self.rotation
            )
        except ValueError as e:
            self.logger.debug(
                "Building could not be fitted into the map bounds with error: %s",
                e,
            )
            return None

        center_point = np.mean(fitted_building, axis=0).astype(int)
        x, y = map(int, center_point)
        x = int(np.clip(x, 0, buildings_map_image.shape[1] - 1))
        y = int(np.clip(y, 0, buildings_map_image.shape[0] - 1))
        self.logger.debug("Center point of building polygon: (%d, %d)", x, y)

        category = self._resolve_building_category(building_osm_tags, buildings_map_image, x, y)

        polygon_np = self.polygon_points_to_np(fitted_building)
        width, depth, rotation_angle = self.polygon_dimensions_and_rotation(polygon_np)
        self.logger.debug(
            "Building dimensions: width=%.2f, depth=%.2f, rotation=%.2f°",
            width,
            depth,
            rotation_angle,
        )

        x_center, y_center = self.top_left_coordinates_to_center((x, y))
        try:
            z = self.get_z_coordinate_from_dem(not_resized_dem, x, y)
        except Exception as e:
            self.logger.warning(
                "Failed to get Z coordinate from DEM at (%d, %d) with error: %s. Using default height %d.",
                x,
                y,
                e,
                Parameters.DEFAULT_HEIGHT,
            )
            z = Parameters.DEFAULT_HEIGHT

        self.logger.debug(
            "World coordinates for building: x=%.3f, y=%.3f, z=%.3f",
            x_center,
            y_center,
            z,
        )

        return BuildingPlacement(
            category=category,
            width=width,
            depth=depth,
            rotation_angle=rotation_angle,
            x=x,
            y=y,
            x_center=x_center,
            y_center=y_center,
            z=z,
        )

    def _resolve_building_category(
        self,
        building_osm_tags: dict[str, Any] | None,
        buildings_map_image: np.ndarray,
        x: int,
        y: int,
    ) -> str:
        """Resolve building category prioritizing OSM tags and falling back to map pixel."""
        if building_osm_tags:
            category = self._match_category_from_osm_tags(building_osm_tags)
            self.logger.debug(
                "Building category matched from OSM tags: %s (tags: %s)",
                category,
                building_osm_tags,
            )
            if category:
                return category

        pixel_value = int(buildings_map_image[y, x])
        self.logger.debug("Pixel value at center point: %s", pixel_value)
        category = Parameters.PIXEL_TYPES.get(pixel_value, Parameters.DEFAULT_BUILDING_CATEGORY)
        self.logger.debug("Building category from pixel-based method: %s", category)
        return category

    def _ensure_building_file_id(
        self,
        files_section: ET.Element,
        used_building_files: dict[str, int],
        building_file: str,
        next_file_id: int,
    ) -> tuple[int, int]:
        """Return file ID for building asset, appending a <File> node when first encountered."""
        if building_file in used_building_files:
            return used_building_files[building_file], next_file_id

        file_id = next_file_id
        cfg = self.game.config
        file_element = XmlDocument.create_element(
            cfg.i3d_file_tag,
            {
                cfg.i3d_attr_file_id: str(file_id),
                cfg.i3d_attr_filename: building_file,
            },
        )
        files_section.append(file_element)
        used_building_files[building_file] = file_id
        return file_id, next_file_id + 1

    def _append_building_reference(
        self,
        buildings_group: ET.Element,
        best_match: BuildingEntry,
        node_id: int,
        file_id: int,
        placement: BuildingPlacement,
        needs_rotation: bool,
    ) -> None:
        """Append a placed building reference node to the buildings transform group."""
        final_rotation = placement.rotation_angle
        if needs_rotation:
            final_rotation = (final_rotation + 90.0) % 360.0
            self.logger.debug(
                "Building needs 90° rotation: original=%.1f°, final=%.1f°",
                placement.rotation_angle,
                final_rotation,
            )

        cfg = self.game.config
        building_node = XmlDocument.create_element(
            cfg.i3d_reference_node_tag,
            {
                cfg.i3d_attr_name: f"{best_match.name}_{node_id}",
                cfg.i3d_attr_translation: (
                    f"{placement.x_center:.3f} {placement.z:.3f} {placement.y_center:.3f}"
                ),
                cfg.i3d_attr_rotation: f"0 {final_rotation:.3f} 0",
                cfg.i3d_attr_reference_id: str(file_id),
                cfg.i3d_attr_node_id: str(node_id),
            },
        )
        buildings_group.append(building_node)

    def _match_category_from_osm_tags(self, building_osm_tags: dict[str, Any]) -> str | None:
        """Match building category based on OSM tags from texture schema layers.

        This method prioritizes OSM tag matching over pixel-based detection by checking if any
        tags from the building match tags defined in texture schema layers.

        Arguments:
            building_osm_tags (dict[str, Any]): Dictionary of OSM tags from the building

        Returns:
            str | None: Matched building category or None if no match found
        """
        building_category_layers = self.map.context.get_building_category_layers()

        for layer in building_category_layers:
            if not layer.tags:
                continue

            # Check if any of the layer's tags match any of the building's tags
            for tag_key, tag_values in layer.tags.items():
                if tag_key not in building_osm_tags:
                    continue

                building_tag_value = building_osm_tags[tag_key]

                # Handle both single value and list of values in schema
                matched = False
                if isinstance(tag_values, list):
                    matched = building_tag_value in tag_values
                else:
                    matched = building_tag_value == tag_values

                if matched:
                    self.logger.debug(
                        "Matched building category '%s' from OSM tag %s=%s",
                        layer.building_category,
                        tag_key,
                        building_tag_value,
                    )
                    return layer.building_category

        return None

    def _find_or_create_buildings_group(self, scene_node: ET.Element) -> ET.Element:
        """Find or create the buildings transform group in the scene.

        Arguments:
            scene_node (ET.Element): The scene element of the XML tree

        Returns:
            ET.Element: The buildings transform group element
        """
        cfg = self.game.config

        # Look for existing buildings group in the scene
        for transform_group in scene_node.iter(cfg.i3d_transform_group_tag):
            if transform_group.get(cfg.i3d_attr_name) == cfg.i3d_buildings_group_name:
                return transform_group

        # Create new buildings group if not found using the proper element creation method
        buildings_group = XmlDocument.create_element(
            cfg.i3d_transform_group_tag,
            {
                cfg.i3d_attr_name: cfg.i3d_buildings_group_name,
                cfg.i3d_attr_translation: cfg.i3d_zero_translation,
                cfg.i3d_attr_node_id: str(Parameters.BUILDINGS_STARTING_NODE_ID),
            },
        )

        scene_node.append(buildings_group)
        return buildings_group

    def info_sequence(self) -> dict[str, Any]:
        """Return information about the building processing as a dictionary.

        Returns:
            dict[str, Any]: Information about building processing.
        """
        return self.info
