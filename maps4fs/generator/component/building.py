"""Component for map buildings processing and generation."""

import json
import os
from typing import NamedTuple
from xml.etree import ElementTree as ET

import cv2
import numpy as np
from tqdm import tqdm

from maps4fs.generator.component.i3d import I3d
from maps4fs.generator.settings import Parameters
from maps4fs.generator.utils import get_region_by_coordinates

BUILDINGS_STARTING_NODE_ID = 10000
TOLERANCE_FACTOR = 0.3  # 30% size tolerance
DEFAULT_HEIGHT = 200


AREA_TYPES = {
    "residential": 10,
    "commercial": 20,
    "industrial": 30,
    "retail": 40,
    "farmyard": 50,
    "religious": 60,
    "recreation": 70,
}
PIXEL_TYPES = {v: k for k, v in AREA_TYPES.items()}


class BuildingEntry(NamedTuple):
    """Data structure for a building entry in the buildings schema."""

    file: str
    name: str
    width: float
    depth: float
    height: float
    type: str
    categories: list[str]
    regions: list[str]


class BuildingEntryCollection:
    """Collection of building entries with efficient lookup capabilities."""

    def __init__(self, building_entries: list[BuildingEntry], region: str):
        """Initialize the collection with a list of building entries for a specific region.

        Arguments:
            building_entries (list[BuildingEntry]): List of building entries to manage
            region (str): The region for this collection (filters entries to this region only)
        """
        self.region = region
        # Filter entries to only include the specified region
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
        All entries are already filtered by region during initialization.

        Arguments:
            category (str): Required building category
            width (float | None): Desired width (optional)
            depth (float | None): Desired depth (optional)
            tolerance (float): Size tolerance factor (0.3 = 30% tolerance)

        Returns:
            BuildingEntry | None: Best matching entry or None if no suitable match found
        """
        # Start with buildings of the required category (already filtered by region)
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

    def _calculate_match_score(
        self,
        entry: BuildingEntry,
        category: str,
        width: float | None,
        depth: float | None,
        tolerance: float,
    ) -> float:
        """Calculate a match score for a building entry.
        Region is already matched during initialization.

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
        """Get list of available building categories for this region."""
        return list(self.by_category.keys())

    def filter_by_category(self, category: str) -> list[BuildingEntry]:
        """Get all buildings of a specific category (already filtered by region)."""
        return self.by_category.get(category, [])


def building_category_type_to_pixel(building_category: str) -> int | None:
    """Returns the pixel value representation of the building category.
    If not found, returns None.

    Arguments:
        building_category (str | None): The building category type as a string.

    Returns:
        int | None: pixel value of the building category, or None if not found.
    """
    return AREA_TYPES.get(building_category)


def pixel_value_to_building_category_type(pixel_value: int) -> str:
    """Returns the building category type representation of the pixel value.
    If not found, returns "residential".

    Arguments:
        pixel_value (int | None): The pixel value to look up the building category for.

    Returns:
        str: building category of the pixel value, or "residential" if not found.
    """
    return PIXEL_TYPES.get(pixel_value, "residential")


class Building(I3d):
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
        try:
            buildings_schema_path = self.game.buildings_schema
        except ValueError as e:
            self.logger.warning("The game does not support buildings schema: %s", e)
            return

        custom_buildings_schema = self.kwargs.get("buildings_custom_schema")
        if not custom_buildings_schema:
            if not os.path.isfile(buildings_schema_path):
                self.logger.warning(
                    "Buildings schema file not found at path: %s. Skipping buildings generation.",
                    buildings_schema_path,
                )
                return

            try:
                with open(buildings_schema_path, "r", encoding="utf-8") as f:
                    buildings_schema = json.load(f)

                self.buildings_schema = buildings_schema

            except Exception as e:
                self.logger.warning(
                    "Failed to load buildings schema from path: %s with error: %s. Skipping buildings generation.",
                    buildings_schema_path,
                    e,
                )
        else:
            self.buildings_schema = custom_buildings_schema

        self.logger.info(
            "Buildings schema loaded successfully with %d objects.", len(self.buildings_schema)
        )

        self.xml_path = self.game.i3d_file_path(self.map_directory)

        buildings_directory = os.path.join(self.map.map_directory, "buildings")
        self.buildings_map_path = os.path.join(buildings_directory, "building_categories.png")
        os.makedirs(buildings_directory, exist_ok=True)

        texture_component = self.map.get_texture_component()
        if not texture_component:
            self.logger.warning("Texture component not found in the map.")
            return

        # Creating empty single-channel image for building categories.
        buildings_map_image = np.zeros((self.map.size, self.map.size), dtype=np.uint8)

        for layer in texture_component.get_building_category_layers():
            self.logger.info(
                "Processing building category layer: %s (%s)",
                layer.name,
                layer.building_category,
            )
            pixel_value = building_category_type_to_pixel(layer.building_category)  # type: ignore
            if pixel_value is None:
                self.logger.warning(
                    "Unknown building category '%s' for layer '%s'. Skipping.",
                    layer.building_category,
                    layer.name,
                )
                continue

            layer_path = layer.path(self.game.weights_dir_path(self.map.map_directory))
            if not layer_path or not os.path.isfile(layer_path):
                self.logger.warning("Layer texture file not found: %s. Skipping.", layer_path)
                continue

            layer_image = cv2.imread(layer_path, cv2.IMREAD_UNCHANGED)
            if layer_image is None:
                self.logger.warning("Failed to read layer image: %s. Skipping.", layer_path)
                continue

            mask = layer_image > 0
            buildings_map_image[mask] = pixel_value

        # Save the buildings map image
        cv2.imwrite(self.buildings_map_path, buildings_map_image)
        self.logger.info("Building categories map saved to: %s", self.buildings_map_path)

        building_entries = []
        for building_entry in self.buildings_schema:
            building = BuildingEntry(**building_entry)
            building_entries.append(building)

        region = get_region_by_coordinates(self.coordinates)

        self.buildings_collection = BuildingEntryCollection(building_entries, region)
        self.logger.info(
            "Buildings collection created with %d buildings for region '%s'.",
            len(self.buildings_collection.entries),
            region,
        )

    def process(self) -> None:
        """Process and place buildings on the map based on the buildings map image and schema."""
        if not hasattr(self, "buildings_map_path") or not os.path.isfile(self.buildings_map_path):
            self.logger.warning(
                "Buildings map path is not set or file does not exist. Skipping process step."
            )
            return

        buildings_map_image = cv2.imread(self.buildings_map_path, cv2.IMREAD_UNCHANGED)
        if buildings_map_image is None:
            self.logger.warning("Failed to read buildings map image. Skipping process step.")
            return

        self.logger.info("Buildings map categories file found, processing...")

        buildings = self.get_infolayer_data(Parameters.TEXTURES, Parameters.BUILDINGS)
        if not buildings:
            self.logger.warning("Buildings data not found in textures info layer.")
            return

        self.logger.info("Found %d building entries to process.", len(buildings))

        # Initialize tracking for XML modifications
        tree = self.get_tree()
        root = tree.getroot()

        if root is None:
            self.logger.warning("Failed to get root element from I3D XML tree.")
            return

        # Find the Scene element
        scene_node = root.find(".//Scene")
        if scene_node is None:
            self.logger.warning("Scene element not found in I3D file.")
            return

        # Find or create the Files section
        files_section = root.find("Files")
        if files_section is None:
            files_section = ET.SubElement(root, "Files")

        # Find or create the buildings transform group in the scene
        buildings_group = self._find_or_create_buildings_group(scene_node)

        # Track used building files to avoid duplicates (file_path -> file_id mapping)
        used_building_files = {}
        file_id_counter = BUILDINGS_STARTING_NODE_ID
        node_id_counter = BUILDINGS_STARTING_NODE_ID + 1000

        not_resized_dem = self.get_not_resized_dem(with_foundations=True)
        if not_resized_dem is None:
            self.logger.warning("Not resized DEM not found.")
            return

        for building in tqdm(buildings, desc="Placing buildings", unit="building"):
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

            # 1. Identify the center point of the building polygon.
            center_point = np.mean(fitted_building, axis=0).astype(int)
            x, y = center_point
            self.logger.info("Center point of building polygon: %s", center_point)

            pixel_value = buildings_map_image[y, x]
            self.logger.info("Pixel value at center point: %s", pixel_value)

            category = pixel_value_to_building_category_type(pixel_value)
            self.logger.info("Building category at center point: %s", category)

            # 2. Obtain building dimensions and rotation using minimum area bounding rectangle
            polygon_np = self.polygon_points_to_np(fitted_building)
            width, depth, rotation_angle = self._get_polygon_dimensions_and_rotation(polygon_np)
            self.logger.info(
                "Building dimensions: width=%d, depth=%d, rotation=%d°",
                width,
                depth,
                rotation_angle,
            )

            # 3. Find the best matching building from the collection (region already filtered)
            best_match = self.buildings_collection.find_best_match(
                category=category,
                width=width,
                depth=depth,
                tolerance=TOLERANCE_FACTOR,
            )

            if best_match:
                self.logger.debug(
                    f"Best building match: {best_match.name} ({best_match.width}x{best_match.depth})"
                )

                # Get world coordinates
                x_center, y_center = self.top_left_coordinates_to_center(center_point)
                try:
                    z = self.get_z_coordinate_from_dem(not_resized_dem, x, y)
                except Exception as e:
                    self.logger.warning(
                        "Failed to get Z coordinate from DEM at (%d, %d) with error: %s. Using default height %d.",
                        x,
                        y,
                        e,
                        DEFAULT_HEIGHT,
                    )
                    z = DEFAULT_HEIGHT

                # * Disabled for now, maybe re-enable later.
                # Calculate scale factors to match the polygon size
                # scale_width = width / best_match.width
                # scale_depth = depth / best_match.depth
                # scale_height = 1.0  # Keep original height for now

                self.logger.info(
                    "World coordinates for building: x=%.3f, y=%.3f, z=%.3f",
                    x_center,
                    y_center,
                    z,
                )
                # self.logger.info(
                #     "Scale factors: width=%.4f, depth=%.4f, height=%.4f",
                #     scale_width,
                #     scale_depth,
                #     scale_height,
                # )

                # Add building file to Files section if not already present
                file_id = None
                if best_match.file not in used_building_files:
                    file_id = file_id_counter
                    file_element = ET.SubElement(files_section, "File")
                    file_element.set("fileId", str(file_id))
                    file_element.set("filename", best_match.file)
                    used_building_files[best_match.file] = file_id
                    file_id_counter += 1
                else:
                    file_id = used_building_files[best_match.file]

                # Create building instance in the buildings group
                building_node = ET.SubElement(buildings_group, "ReferenceNode")
                building_node.set("name", f"{best_match.name}_{node_id_counter}")
                building_node.set("translation", f"{x_center:.3f} {z:.3f} {y_center:.3f}")
                building_node.set("rotation", f"0 {rotation_angle:.3f} 0")
                # building_node.set(
                #     "scale", f"{scale_width:.4f} {scale_height:.4f} {scale_depth:.4f}"
                # )
                building_node.set("referenceId", str(file_id))
                building_node.set("nodeId", str(node_id_counter))

                node_id_counter += 1

            else:
                self.logger.debug(
                    f"No suitable building found for category '{category}' with dimensions {width:.2f}x{depth:.2f}"
                )
                continue

        # Save the modified XML tree
        self.save_tree(tree)
        self.logger.info("Buildings placement completed and saved to map.i3d")

    def _get_polygon_dimensions_and_rotation(
        self, polygon_points: np.ndarray
    ) -> tuple[float, float, float]:
        """Calculate width, depth, and rotation angle of a polygon using minimum area bounding rectangle.

        Arguments:
            polygon_points (np.ndarray): Array of polygon points with shape (n, 2)

        Returns:
            tuple[float, float, float]: width, depth, and rotation angle in degrees
        """
        # Convert to the format expected by cv2.minAreaRect (needs to be float32)
        points = polygon_points.astype(np.float32)

        # Find the minimum area bounding rectangle
        rect = cv2.minAreaRect(points)

        # rect contains: ((center_x, center_y), (width, height), angle)
        (_, _), (width, height), angle = rect

        # OpenCV's minAreaRect returns angle in range [-90, 0) for the longer side
        # We need to convert this to a proper world rotation angle

        # First, ensure width is the longer dimension
        if width < height:
            # Swap dimensions
            width, height = height, width
            # When we swap dimensions, we need to adjust the angle by 90 degrees
            angle = angle + 90.0

        # Convert OpenCV angle to world rotation angle
        # OpenCV angle is measured from the horizontal axis, counter-clockwise
        # But we want the angle in degrees for Y-axis rotation in 3D space
        rotation_angle = -angle  # Negative because 3D rotation is clockwise positive

        # Normalize to [0, 360) range
        while rotation_angle < 0:
            rotation_angle += 360
        while rotation_angle >= 360:
            rotation_angle -= 360

        return width, height, rotation_angle

    def _find_or_create_buildings_group(self, scene_node: ET.Element) -> ET.Element:
        """Find or create the buildings transform group in the scene.

        Arguments:
            scene_node (ET.Element): The scene element of the XML tree

        Returns:
            ET.Element: The buildings transform group element
        """
        # Look for existing buildings group in the scene
        for transform_group in scene_node.iter("TransformGroup"):
            if transform_group.get("name") == "buildings":
                return transform_group

        # Create new buildings group if not found using the proper element creation method
        buildings_group = self.create_element(
            "TransformGroup",
            {
                "name": "buildings",
                "translation": "0 0 0",
                "nodeId": str(BUILDINGS_STARTING_NODE_ID),
            },
        )

        scene_node.append(buildings_group)
        return buildings_group

    def info_sequence(self) -> dict[str, dict[str, str | float | int]]:
        return {}
