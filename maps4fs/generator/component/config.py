"""This module contains the Config class for map settings and configuration."""

from __future__ import annotations

import os

import cv2
import numpy as np

from maps4fs.generator.component.base.component_image import ImageComponent
from maps4fs.generator.component.base.component_xml import XMLComponent
from maps4fs.generator.settings import Parameters


# pylint: disable=R0903
class Config(XMLComponent, ImageComponent):
    """Component for map settings and configuration.

    Arguments:
        game (Game): The game instance for which the map is generated.
        coordinates (tuple[float, float]): The latitude and longitude of the center of the map.
        map_size (int): The size of the map in pixels (it's a square).
        map_rotated_size (int): The size of the map in pixels after rotation.
        rotation (int): The rotation angle of the map.
        map_directory (str): The directory where the map files are stored.
        logger (Any, optional): The logger to use. Must have at least three basic methods: debug,
            info, warning. If not provided, default logging will be used.
    """

    def preprocess(self) -> None:
        """Gets the path to the map XML file and saves it to the instance variable."""
        self.xml_path = self.game.map_xml_path(self.map_directory)
        self.fog_parameters: dict[str, int] = {}

    def process(self) -> None:
        """Sets the map size in the map.xml file."""
        self._set_map_size()

        if self.game.fog_processing:
            self._adjust_fog()

        self._set_overview()

        # Debug values for testing - can be made configurable later
        self.update_license_plates(country_code="SRB", eu_format=False)

    def _set_map_size(self) -> None:
        """Edits map.xml file to set correct map size."""
        tree = self.get_tree()
        if not tree:
            raise FileNotFoundError(f"Map XML file not found: {self.xml_path}")

        root = tree.getroot()
        data = {
            "width": str(self.scaled_size),
            "height": str(self.scaled_size),
        }

        for element in root.iter("map"):  # type: ignore
            self.update_element(element, data)
            break
        self.save_tree(tree)

    def info_sequence(self) -> dict[str, dict[str, str | float | int]]:
        """Returns information about the component.
        Overview section is needed to create the overview file (in-game map).

        Returns:
            dict[str, dict[str, str | float | int]]: Information about the component.
        """
        # The overview file is exactly 2X bigger than the map size, does not matter
        # if the map is 2048x2048 or 4096x4096, the overview will be 4096x4096
        # and the map will be in the center of the overview.
        # That's why the distance is set to the map height not as a half of it.
        bbox = self.get_bbox(distance=self.map_size)
        south, west, north, east = bbox
        epsg3857_string = self.get_epsg3857_string(bbox=bbox)
        epsg3857_string_with_margin = self.get_epsg3857_string(bbox=bbox, add_margin=True)

        self.qgis_sequence()

        overview_data = {
            "epsg3857_string": epsg3857_string,
            "epsg3857_string_with_margin": epsg3857_string_with_margin,
            "south": south,
            "west": west,
            "north": north,
            "east": east,
            "height": self.map_size * 2,
            "width": self.map_size * 2,
        }

        data = {
            "Overview": overview_data,
        }
        if self.fog_parameters:
            data["Fog"] = self.fog_parameters  # type: ignore

        return data  # type: ignore

    def qgis_sequence(self) -> None:
        """Generates QGIS scripts for creating bounding box layers and rasterizing them."""
        bbox = self.get_bbox(distance=self.map_size)
        espg3857_bbox = self.get_espg3857_bbox(bbox=bbox)
        espg3857_bbox_with_margin = self.get_espg3857_bbox(bbox=bbox, add_margin=True)

        qgis_layers = [("Overview_bbox", *espg3857_bbox)]
        qgis_layers_with_margin = [("Overview_bbox_with_margin", *espg3857_bbox_with_margin)]

        layers = qgis_layers + qgis_layers_with_margin

        self.create_qgis_scripts(layers)

    def _adjust_fog(self) -> None:
        """Adjusts the fog settings in the environment XML file based on the DEM and height scale."""
        self.logger.debug("Adjusting fog settings based on DEM and height scale...")
        try:
            environment_xml_path = self.game.get_environment_xml_path(self.map_directory)
        except NotImplementedError:
            self.logger.warning(
                "Game does not support environment XML file, fog adjustment will not be applied."
            )
            return

        if not environment_xml_path or not os.path.isfile(environment_xml_path):
            self.logger.warning(
                "Environment XML file not found, fog adjustment will not be applied."
            )
            return

        self.logger.debug("Will work with environment XML file: %s", environment_xml_path)

        dem_params = self._get_dem_meter_params()
        if not dem_params:
            return
        maximum_height, minimum_height = dem_params

        tree = self.get_tree(xml_path=environment_xml_path)
        root = tree.getroot()

        # Find the <latitude>40.6</latitude> element in the XML file.
        latitude_element = root.find("./latitude")  # type: ignore
        if latitude_element is not None:
            map_latitude = round(self.map.coordinates[0], 1)
            latitude_element.text = str(map_latitude)
            self.logger.debug(
                "Found latitude element and set it to: %s",
                latitude_element.text,
            )

        # The XML file contains 4 <fog> entries in different sections of <weather> representing
        # different seasons, such as <season name="spring">, <season name="summer">, etc.
        # We need to find them all and adjust the parameters accordingly.
        for season in root.findall(".//weather/season"):  # type: ignore
            # Example of the <heightFog> element:
            # <heightFog>
            #     <groundLevelDensity min="0.05" max="0.2" />
            #     <maxHeight min="420" max="600" />
            # </heightFog>
            # We need to adjust the maxheight min and max attributes.
            max_height_element = season.find("./fog/heightFog/maxHeight")
            data = {
                "min": str(minimum_height),
                "max": str(maximum_height),
            }
            self.update_element(max_height_element, data)  # type: ignore
            self.logger.debug(
                "Adjusted fog settings for season '%s': min=%s, max=%s",
                season.get("name", "unknown"),
                minimum_height,
                maximum_height,
            )

        self.logger.debug("Fog adjusted and file will be saved to %s", environment_xml_path)
        self.save_tree(tree, xml_path=environment_xml_path)

        self.fog_parameters = {
            "minimum_height": minimum_height,
            "maximum_height": maximum_height,
        }

    def _get_dem_meter_params(self) -> tuple[int, int] | None:
        """Reads the DEM file and returns the maximum and minimum height in meters.

        Returns:
            tuple[int, int] | None: Maximum and minimum height in meters or None if the DEM file
                is not found or cannot be read.
        """
        self.logger.debug("Reading DEM meter parameters...")
        dem_path = self.game.dem_file_path(self.map_directory)
        if not dem_path or not os.path.isfile(dem_path):
            self.logger.warning("DEM file not found, fog adjustment will not be applied.")
            return None

        dem_image = cv2.imread(dem_path, cv2.IMREAD_UNCHANGED)
        if dem_image is None:
            self.logger.warning("Failed to read DEM image, fog adjustment will not be applied.")
            return None
        dem_maximum_pixel = dem_image.max()
        dem_minimum_pixel = dem_image.min()

        self.logger.debug(
            "DEM read successfully. Max pixel: %d, Min pixel: %d",
            dem_maximum_pixel,
            dem_minimum_pixel,
        )

        try:
            height_scale = self.get_height_scale()
        except ValueError as e:
            self.logger.warning("Error getting height scale from I3D file: %s", e)
            return None
        self.logger.debug("Height scale from I3D file: %d", height_scale)

        dem_maximum_meter = int(dem_maximum_pixel / height_scale)
        dem_minimum_meter = int(dem_minimum_pixel / height_scale)
        self.logger.debug(
            "DEM maximum height in meters: %d, minimum height in meters: %d",
            dem_maximum_meter,
            dem_minimum_meter,
        )

        return dem_maximum_meter, dem_minimum_meter

    def _set_overview(self) -> None:
        """Generates and sets the overview image for the map."""
        try:
            overview_image_path = self.game.overview_file_path(self.map_directory)
        except NotImplementedError:
            self.logger.warning(
                "Game does not support overview image file, overview generation will be skipped."
            )
            return

        satellite_component = self.map.get_satellite_component()
        if not satellite_component:
            self.logger.warning(
                "Satellite component not found, overview generation will be skipped."
            )
            return

        if not satellite_component.assets.overview or not os.path.isfile(
            satellite_component.assets.overview
        ):
            self.logger.warning(
                "Satellite overview image not found, overview generation will be skipped."
            )
            return

        satellite_images_directory = os.path.dirname(satellite_component.assets.overview)
        overview_image = cv2.imread(satellite_component.assets.overview, cv2.IMREAD_UNCHANGED)

        if overview_image is None:
            self.logger.warning(
                "Failed to read satellite overview image, overview generation will be skipped."
            )
            return

        resized_overview_image = cv2.resize(
            overview_image,
            (Parameters.OVERVIEW_IMAGE_SIZE, Parameters.OVERVIEW_IMAGE_SIZE),
            interpolation=cv2.INTER_LINEAR,
        )

        resized_overview_path = os.path.join(
            satellite_images_directory,
            f"{Parameters.OVERVIEW_IMAGE_FILENAME}.png",
        )

        cv2.imwrite(resized_overview_path, resized_overview_image)
        self.logger.info("Overview image saved to: %s", resized_overview_path)

        if os.path.isfile(overview_image_path):
            try:
                os.remove(overview_image_path)
                self.logger.debug("Old overview image removed: %s", overview_image_path)
            except Exception as e:
                self.logger.warning("Failed to remove old overview image: %s", e)
                return

        self.convert_png_to_dds(resized_overview_path, overview_image_path)
        self.logger.info("Overview image converted and saved to: %s", overview_image_path)

    def update_license_plates(self, country_code: str = "SRB", eu_format: bool = False):
        """Updates license plates for the specified country.

        Args:
            country_code: 1-3 letter country code to display on plates
            eu_format: Whether to use EU format texture
        """
        if not self.game.license_plates_processing:
            self.logger.warning("License plates processing is not supported for this game.")
            return

        # Constants for country code position in texture
        COUNTRY_CODE_TOP = 169
        COUNTRY_CODE_BOTTOM = 252
        COUNTRY_CODE_LEFT = 74
        COUNTRY_CODE_RIGHT = 140

        self.logger.info(
            f"Updating license plates for country: {country_code}, EU format: {eu_format}"
        )

        try:
            # Step 1-3: Update map.xml to use PL license plates
            self._update_map_xml_license_plates()

            # Step 4-8: Update licensePlatesPL.xml with country code letters
            self._update_license_plates_xml(country_code)

            # Step 9-12: Update licensePlatesPL.i3d texture reference
            self._update_license_plates_i3d(eu_format)

            # Step 13-17: Generate texture with country code
            self._generate_license_plate_texture(
                country_code,
                eu_format,
                COUNTRY_CODE_LEFT,
                COUNTRY_CODE_TOP,
                COUNTRY_CODE_RIGHT,
                COUNTRY_CODE_BOTTOM,
            )

            self.logger.info("License plates updated successfully")

        except Exception as e:
            self.logger.error(f"Failed to update license plates: {e}")
            raise

    def _get_license_plates_directory(self) -> str:
        """Get the license plates directory path."""
        return os.path.join(self.map_directory, "map", "licensePlates")

    def _get_license_plates_xml_path(self) -> str:
        """Get the licensePlatesPL.xml file path."""
        return os.path.join(self._get_license_plates_directory(), "licensePlatesPL.xml")

    def _get_license_plates_i3d_path(self) -> str:
        """Get the licensePlatesPL.i3d file path."""
        return os.path.join(self._get_license_plates_directory(), "licensePlatesPL.i3d")

    def _update_map_xml_license_plates(self) -> None:
        """Update map.xml to reference PL license plates."""
        tree = self.get_tree()
        if not tree:
            raise FileNotFoundError(f"Map XML file not found: {self.xml_path}")

        root = tree.getroot()

        # Find or create licensePlates element
        license_plates_element = root.find(".//licensePlates")
        if license_plates_element is not None:
            license_plates_element.set("filename", "map/licensePlates/licensePlatesPL.xml")
        else:
            # Create new licensePlates element if it doesn't exist
            license_plates_element = tree.getroot().makeelement(
                "licensePlates", {"filename": "map/licensePlates/licensePlatesPL.xml"}
            )
            root.append(license_plates_element)

        self.save_tree(tree)
        self.logger.debug("Updated map.xml to use PL license plates")

    def _update_license_plates_xml(self, country_code: str) -> None:
        """Update licensePlatesPL.xml with country code letters."""
        xml_path = self._get_license_plates_xml_path()
        if not os.path.isfile(xml_path):
            raise FileNotFoundError(f"License plates XML file not found: {xml_path}")

        tree = self.get_tree(xml_path=xml_path)
        root = tree.getroot()

        # Find licensePlate with node="0"
        license_plate = None
        for plate in root.findall(".//licensePlate"):
            if plate.get("node") == "0":
                license_plate = plate
                break

        if license_plate is None:
            raise ValueError("Could not find licensePlate element with node='0'")

        # Find first variations/variation element
        variations = license_plate.find("variations")
        if variations is None:
            raise ValueError("Could not find variations element")

        variation = variations.find("variation")
        if variation is None:
            raise ValueError("Could not find first variation element")

        # Update country code letters
        country_code = country_code.upper()[:3]  # Ensure max 3 letters, uppercase

        # Position X values for the letters (from your constants)
        pos_x_values = ["-0.1712", "-0.1172", "-0.0632"]

        # Clear existing values and add new ones
        for value in variation.findall("value"):
            variation.remove(value)

        for i, letter in enumerate(country_code):
            value_elem = tree.getroot().makeelement(
                "value",
                {
                    "node": f"0|{i}",
                    "character": letter,
                    "posX": pos_x_values[i],
                    "numerical": "false",
                    "alphabetical": "true",
                },
            )
            variation.append(value_elem)

        self.save_tree(tree, xml_path=xml_path)
        self.logger.debug(f"Updated licensePlatesPL.xml with country code: {country_code}")

    def _update_license_plates_i3d(self, eu_format: bool) -> None:
        """Update licensePlatesPL.i3d texture reference."""
        i3d_path = self._get_license_plates_i3d_path()
        if not os.path.isfile(i3d_path):
            raise FileNotFoundError(f"License plates i3d file not found: {i3d_path}")

        tree = self.get_tree(xml_path=i3d_path)
        root = tree.getroot()

        # Find File element with fileId="12"
        file_element = None
        for file_elem in root.findall(".//File"):
            if file_elem.get("fileId") == "12":
                file_element = file_elem
                break

        if file_element is None:
            raise ValueError("Could not find File element with fileId='12'")

        # Update filename based on EU format
        if eu_format:
            filename = "$data/shared/licensePlates/licensePlates_diffuseEU.png"
        else:
            filename = "$data/shared/licensePlates/licensePlates_diffuse.png"

        file_element.set("filename", filename)

        self.save_tree(tree, xml_path=i3d_path)
        self.logger.debug(f"Updated licensePlatesPL.i3d texture reference to: {filename}")

    def _generate_license_plate_texture(
        self, country_code: str, eu_format: bool, left: int, top: int, right: int, bottom: int
    ) -> None:
        """Generate license plate texture with country code."""
        # Get the base texture filename
        if eu_format:
            texture_filename = "licensePlates_diffuseEU.png"
        else:
            texture_filename = "licensePlates_diffuse.png"

        # Path to the texture in the map directory
        texture_dir = os.path.join(self.map_directory, "map", "licensePlates")
        texture_path = os.path.join(texture_dir, texture_filename)

        # Create directory if it doesn't exist
        os.makedirs(texture_dir, exist_ok=True)

        # For now, copy from the game's default texture (this would need to be implemented
        # based on where the game stores its default textures)
        # TODO: Copy base texture from game files

        # Load or create base texture
        if os.path.isfile(texture_path):
            texture = cv2.imread(texture_path, cv2.IMREAD_UNCHANGED)
        else:
            # Create a basic texture if none exists (placeholder)
            texture = cv2.imread(
                f"$data/shared/licensePlates/{texture_filename}", cv2.IMREAD_UNCHANGED
            )
            if texture is None:
                # Create a blank RGBA texture as fallback
                texture = np.ones((512, 512, 4), dtype=np.uint8) * 255

        if texture is None:
            raise ValueError(f"Could not load base texture: {texture_path}")

        # Calculate text box dimensions
        box_width = right - left
        box_height = bottom - top

        # Calculate font size based on box size and number of letters - use most of the space
        # Make the font much bigger to utilize the available space better
        # Since we rotate 90 degrees, we need to account for swapped dimensions
        # Slightly bigger than before but still conservative
        initial_font_scale = min(box_height / (len(country_code) * 10), box_width / 22)

        # Test the font size and adjust if text fits after rotation
        font = cv2.FONT_HERSHEY_SIMPLEX
        thickness = 3  # Make it bold by increasing thickness
        font_scale = initial_font_scale

        # Create a large canvas to render text without clipping
        large_canvas_size = max(box_width, box_height) * 2

        # Iteratively reduce font size until rotated text fits
        for _ in range(15):  # More iterations for better fitting
            # Test on a large canvas first
            test_img = np.ones((large_canvas_size, large_canvas_size, 3), dtype=np.uint8) * 255
            text_size = cv2.getTextSize(country_code, font, font_scale, thickness)[0]

            # Center text on large canvas
            text_x = (large_canvas_size - text_size[0]) // 2
            text_y = (large_canvas_size + text_size[1]) // 2

            cv2.putText(
                test_img, country_code, (text_x, text_y), font, font_scale, (0, 0, 0), thickness
            )

            # Rotate the test image
            rotated_test = cv2.rotate(test_img, cv2.ROTATE_90_CLOCKWISE)

            # Find the bounding box of non-white pixels
            gray = cv2.cvtColor(rotated_test, cv2.COLOR_BGR2GRAY)
            coords = np.column_stack(np.where(gray < 255))

            if len(coords) > 0:
                y_min, x_min = coords.min(axis=0)
                y_max, x_max = coords.max(axis=0)
                rotated_width = x_max - x_min + 1
                rotated_height = y_max - y_min + 1

                # Check if the rotated text fits in our target box with good margin
                if rotated_width <= box_width * 0.90 and rotated_height <= box_height * 0.90:
                    break

            font_scale *= 0.93  # Reduce by 7% each iteration

        self.logger.debug(
            f"Box dimensions: {box_width}x{box_height} (from {left},{top} to {right},{bottom})"
        )
        self.logger.debug(f"Final font scale: {font_scale}, Original text size: {text_size}")
        if len(coords) > 0:
            self.logger.debug(f"Rotated text dimensions: {rotated_width}x{rotated_height}")

        # Create the actual text image
        text_img = np.ones((large_canvas_size, large_canvas_size, 3), dtype=np.uint8) * 255
        text_size = cv2.getTextSize(country_code, font, font_scale, thickness)[0]

        # Center text on canvas
        text_x = (large_canvas_size - text_size[0]) // 2
        text_y = (large_canvas_size + text_size[1]) // 2

        cv2.putText(
            text_img, country_code, (text_x, text_y), font, font_scale, (0, 0, 0), thickness
        )

        # Rotate the text
        rotated_text_rgb = cv2.rotate(text_img, cv2.ROTATE_90_CLOCKWISE)

        # Find bounding box and crop to content
        gray = cv2.cvtColor(rotated_text_rgb, cv2.COLOR_BGR2GRAY)
        coords = np.column_stack(np.where(gray < 255))

        if len(coords) > 0:
            y_min, x_min = coords.min(axis=0)
            y_max, x_max = coords.max(axis=0)

            # Crop to content with small padding
            padding = 2
            y_min = max(0, y_min - padding)
            x_min = max(0, x_min - padding)
            y_max = min(rotated_text_rgb.shape[0], y_max + padding)
            x_max = min(rotated_text_rgb.shape[1], x_max + padding)

            cropped_text_rgb = rotated_text_rgb[y_min:y_max, x_min:x_max]

            # Convert to RGBA with proper alpha
            cropped_height, cropped_width = cropped_text_rgb.shape[:2]
            rotated_text = np.zeros((cropped_height, cropped_width, 4), dtype=np.uint8)
            rotated_text[:, :, :3] = cropped_text_rgb

            # Set alpha: opaque for text (non-white), transparent for background
            text_mask = np.any(cropped_text_rgb < 255, axis=2)
            rotated_text[text_mask, 3] = 255  # Opaque text
            rotated_text[~text_mask, 3] = 0  # Transparent background
        else:
            # Fallback if no text found
            rotated_text = np.zeros((box_height, box_width, 4), dtype=np.uint8)

        # Ensure the texture is RGBA
        if texture.shape[2] == 3:
            # Convert RGB to RGBA
            texture_rgba = np.zeros((texture.shape[0], texture.shape[1], 4), dtype=np.uint8)
            texture_rgba[:, :, :3] = texture
            texture_rgba[:, :, 3] = 255  # Fully opaque
            texture = texture_rgba

        # Place the rotated text in the texture using alpha blending
        h, w = rotated_text.shape[:2]

        # Center the text within the target box
        center_x = left + (box_width - w) // 2
        center_y = top + (box_height - h) // 2

        # Ensure the centered text fits within texture bounds
        if (
            center_y >= 0
            and center_x >= 0
            and center_y + h <= texture.shape[0]
            and center_x + w <= texture.shape[1]
        ):
            # Extract the region where text will be placed
            texture_region = texture[center_y : center_y + h, center_x : center_x + w]

            # Alpha blend the text onto the texture
            alpha = rotated_text[:, :, 3:4] / 255.0

            # Blend only the RGB channels
            texture[center_y : center_y + h, center_x : center_x + w, :3] = (
                rotated_text[:, :, :3] * alpha + texture_region[:, :, :3] * (1 - alpha)
            ).astype(np.uint8)

            # Update alpha channel where text is present
            texture[center_y : center_y + h, center_x : center_x + w, 3] = np.maximum(
                texture_region[:, :, 3], rotated_text[:, :, 3]
            )

            self.logger.debug(
                f"Text placed at centered position: ({center_x},{center_y}) size: {w}x{h}"
            )
        else:
            self.logger.warning(
                f"Centered text position ({center_x},{center_y}) with size {w}x{h} would exceed texture bounds"
            )

        # Save the modified texture
        cv2.imwrite(texture_path, texture)
        self.logger.debug(
            f"Generated license plate texture with country code '{country_code}' at: {texture_path}"
        )
