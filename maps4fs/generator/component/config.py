"""This module contains the Config class for map settings and configuration."""

from __future__ import annotations

import os
from typing import Any

import cv2
import numpy as np

import maps4fs.generator.utils as mfsutils
from maps4fs.generator.component.base.component_image import ImageComponent
from maps4fs.generator.component.base.component_xml import XMLComponent
from maps4fs.generator.monitor import monitor_performance
from maps4fs.generator.settings import Parameters

# Defines coordinates for country block on the license plate texture.
COUNTRY_CODE_TOP = 169
COUNTRY_CODE_BOTTOM = 252
COUNTRY_CODE_LEFT = 74
COUNTRY_CODE_RIGHT = 140

LICENSE_PLATES_XML_FILENAME = "licensePlatesPL.xml"
LICENSE_PLATES_I3D_FILENAME = "licensePlatesPL.i3d"


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
        self.info: dict[str, Any] = {}
        self.xml_path = self.game.map_xml_path(self.map_directory)
        self.fog_parameters: dict[str, int] = {}

    def process(self) -> None:
        """Sets the map size in the map.xml file."""
        self._set_map_size()

        if self.game.fog_processing:
            self._adjust_fog()

        self._set_overview()

        self.update_license_plates()

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

        data.update(self.info)

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

    @monitor_performance
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

    @monitor_performance
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

    @property
    def supported_countries(self) -> dict[str, str]:
        """Returns a dictionary of supported countries and their corresponding country codes.

        Returns:
            dict[str, str]: Supported countries and their country codes.
        """
        return {
            "germany": "DE",
            "austria": "A",
            "switzerland": "CH",
            "france": "F",
            "italy": "I",
            "spain": "E",
            "portugal": "P",
            "netherlands": "NL",
            "belgium": "B",
            "luxembourg": "L",
            "poland": "PL",
            "czech republic": "CZ",
            "slovakia": "SK",
            "hungary": "H",
            "slovenia": "SLO",
            "croatia": "HR",
            "bosnia and herzegovina": "BIH",
            "serbia": "SRB",
            "north macedonia": "MKD",
            "greece": "GR",
            "turkey": "TR",
        }

    @property
    def eu_countries(self) -> set[str]:
        """Returns a set of country codes that are in the European Union.

        Returns:
            set[str]: Set of country codes in the EU.
        """
        return {
            "DE",
            "A",
            "CH",
            "F",
            "I",
            "E",
            "P",
            "NL",
            "B",
            "L",
            "PL",
            "CZ",
            "SK",
            "H",
            "SLO",
            "HR",
        }

    @monitor_performance
    def update_license_plates(self):
        """Updates license plates for the specified country."""
        try:
            license_plates_directory = self.game.license_plates_dir_path(self.map_directory)
        except NotImplementedError:
            self.logger.warning("Game does not support license plates processing.")
            return

        country_name = mfsutils.get_country_by_coordinates(self.map.coordinates).lower()
        self.info["license_plate_country_name"] = country_name
        if country_name not in self.supported_countries:
            self.logger.warning(
                "License plates processing is not supported for country: %s.", country_name
            )
            return

        # Get license plate country code and EU format.
        country_code = self.supported_countries[country_name]
        eu_format = country_code in self.eu_countries
        self.info["license_plate_country_code"] = country_code
        self.info["license_plate_eu_format"] = eu_format

        self.logger.debug(
            "Updating license plates for country: %s, EU format: %s",
            country_name,
            eu_format,
        )

        license_plates_prefix = self.map.i3d_settings.license_plate_prefix
        if len(license_plates_prefix) < 1 or len(license_plates_prefix) > 3:
            self.logger.error(
                "Invalid license plate prefix: %s. It must be 1 to 3 characters long.",
                license_plates_prefix,
            )
            return

        try:
            # 1. Update licensePlatesPL.xml with license plate prefix.
            self._update_license_plates_xml(license_plates_directory, license_plates_prefix)

            # 2. Update licensePlatesPL.i3d texture reference depending on EU format.
            self._update_license_plates_i3d(license_plates_directory, eu_format)

            # 3. Generate texture with country code.
            self._generate_license_plate_texture(
                license_plates_directory,
                country_code,
                eu_format,
                COUNTRY_CODE_LEFT,
                COUNTRY_CODE_TOP,
                COUNTRY_CODE_RIGHT,
                COUNTRY_CODE_BOTTOM,
            )

            self.logger.debug("License plates updated successfully")
        except Exception as e:
            self.logger.error("Failed to update license plates: %s", e)
            return

        # Edit the map.xml only if all previous steps succeeded.
        self._update_map_xml_license_plates()

    def _update_map_xml_license_plates(self) -> None:
        """Update map.xml to reference PL license plates.

        Raises:
            FileNotFoundError: If the map XML file is not found.
            ValueError: If the map XML root element is None.
        """
        tree = self.get_tree()
        if not tree:
            raise FileNotFoundError(f"Map XML file not found: {self.xml_path}")

        root = tree.getroot()

        if root is None:
            raise ValueError("Map XML root element is None.")

        # Find or create licensePlates element
        license_plates_element = root.find(".//licensePlates")
        if license_plates_element is not None:
            license_plates_element.set("filename", "map/licensePlates/licensePlatesPL.xml")
        else:
            # Create new licensePlates element if it doesn't exist
            license_plates_element = root.makeelement(
                "licensePlates", {"filename": "map/licensePlates/licensePlatesPL.xml"}
            )
            root.append(license_plates_element)

        self.save_tree(tree)
        self.logger.debug("Updated map.xml to use PL license plates")

    def _update_license_plates_xml(
        self, license_plates_directory: str, license_plate_prefix: str
    ) -> None:
        """Update licensePlatesPL.xml with license plate prefix.

        Arguments:
            license_plates_directory (str): Directory where license plates XML is located.
            license_plate_prefix (str): The prefix to set on the license plates.

        Raises:
            FileNotFoundError: If the license plates XML file is not found.
            ValueError: If required XML elements are not found.
        """
        xml_path = os.path.join(license_plates_directory, LICENSE_PLATES_XML_FILENAME)
        if not os.path.isfile(xml_path):
            raise FileNotFoundError(f"License plates XML file not found: {xml_path}.")

        tree = self.get_tree(xml_path=xml_path)
        root = tree.getroot()
        if root is None:
            raise ValueError("License plates XML root element is None.")

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

        # 1. Update license plate prefix to ensure max 3 letters, uppercase.
        license_plate_prefix = license_plate_prefix.upper()[:3]

        # 2. Pad the prefix to exactly 3 characters with spaces if needed.
        license_plate_prefix = license_plate_prefix.ljust(3)
        self.info["license_plate_prefix"] = license_plate_prefix

        # 3. Position X values for the letters.
        pos_x_values = ["-0.1712", "-0.1172", "-0.0632"]  # ? DO WE REALLY NEED THEM?

        # 4. Update all 3 positions (0|0, 0|1, 0|2) to ensure proper formatting.
        # Always process exactly 3 positions, padding with spaces as needed.
        for i in range(3):
            letter = license_plate_prefix[i]  # This will be a space if padding was applied
            target_node = f"0|{i}"
            # Find existing value with this node ID.
            existing_value = None
            for value in variation.findall("value"):
                if value.get("node") == target_node:
                    existing_value = value
                    break

            if existing_value is not None:
                # Update existing value.
                existing_value.set("character", letter)
                existing_value.set("posX", pos_x_values[i])
                existing_value.set("numerical", "false")
                existing_value.set("alphabetical", "true")
            else:
                # Create new value if it doesn't exist.
                value_elem = root.makeelement(
                    "value",
                    {
                        "node": target_node,
                        "character": letter,
                        "posX": pos_x_values[i],
                        "numerical": "false",
                        "alphabetical": "true",
                    },
                )
                # Insert at the beginning to maintain order.
                variation.insert(i, value_elem)

        # 5. Save the updated XML.
        self.save_tree(tree, xml_path=xml_path)
        self.logger.debug(
            "Updated licensePlatesPL.xml with license plate prefix: %s", license_plate_prefix
        )

    def _update_license_plates_i3d(self, license_plates_directory: str, eu_format: bool) -> None:
        """Update licensePlatesPL.i3d texture reference.

        Arguments:
            license_plates_directory (str): Directory where license plates i3d is located.
            eu_format (bool): Whether to use EU format texture.

        Raises:
            FileNotFoundError: If the license plates i3d file is not found.
            ValueError: If required XML elements are not found.
        """
        i3d_path = os.path.join(license_plates_directory, LICENSE_PLATES_I3D_FILENAME)
        if not os.path.isfile(i3d_path):
            raise FileNotFoundError(f"License plates i3d file not found: {i3d_path}")

        # 1. Load the i3d XML.
        tree = self.get_tree(xml_path=i3d_path)
        root = tree.getroot()

        if root is None:
            raise ValueError("License plates i3d XML root element is None.")

        # 2. Find File element with fileId="12"
        file_element = None
        for file_elem in root.findall(".//File"):
            if file_elem.get("fileId") == "12":
                file_element = file_elem
                break

        if file_element is None:
            raise ValueError("Could not find File element with fileId='12'")

        # 3. Update filename to point to local map directory (relative path).
        if eu_format:
            filename = "licensePlates_diffuseEU.png"
        else:
            filename = "licensePlates_diffuse.png"

        file_element.set("filename", filename)

        # 4. Save the updated i3d XML.
        self.save_tree(tree, xml_path=i3d_path)
        self.logger.debug("Updated licensePlatesPL.i3d texture reference to: %s", filename)

    @monitor_performance
    def _generate_license_plate_texture(
        self,
        license_plates_directory: str,
        country_code: str,
        eu_format: bool,
        left: int,
        top: int,
        right: int,
        bottom: int,
    ) -> None:
        """Generate license plate texture with country code.

        Arguments:
            license_plates_directory (str): Directory where license plates textures are located.
            country_code (str): The country code to render on the license plate.
            eu_format (bool): Whether to use EU format texture.
            left (int): Left coordinate of the country code box.
            top (int): Top coordinate of the country code box.
            right (int): Right coordinate of the country code box.
            bottom (int): Bottom coordinate of the country code box.

        Raises:
            FileNotFoundError: If the base texture file is not found.
            ValueError: If there is an error generating the texture.
        """
        # 1. Define the path to the base texture depending on EU format.
        if eu_format:
            texture_filename = "licensePlates_diffuseEU.png"
        else:
            texture_filename = "licensePlates_diffuse.png"

        # 2. Check if the base texture file exists.
        texture_path = os.path.join(license_plates_directory, texture_filename)
        if not os.path.isfile(texture_path):
            self.logger.warning("Base texture file not found: %s.", texture_path)
            raise FileNotFoundError(f"Base texture file not found: {texture_path}")

        # 3. Load the base texture.
        texture = cv2.imread(texture_path, cv2.IMREAD_UNCHANGED)
        if texture is None:
            raise ValueError(f"Could not load base texture: {texture_path}")

        # 4. Calculate text box dimensions.
        box_width = right - left
        box_height = bottom - top

        # 5. Define font and fit text in rotated box.
        font = cv2.FONT_HERSHEY_SIMPLEX
        thickness = 3
        font_scale, large_canvas_size = self.fit_text_in_rotated_box(
            country_code,
            box_width,
            box_height,
            font,
            thickness,
        )

        # 6. Create the actual text image (black background for white text).
        text_img = np.zeros((large_canvas_size, large_canvas_size, 3), dtype=np.uint8)
        text_size = cv2.getTextSize(country_code, font, font_scale, thickness)[0]

        # 7. Center text on canvas.
        text_x = (large_canvas_size - text_size[0]) // 2
        text_y = (large_canvas_size + text_size[1]) // 2

        # 8. Use white text on black background with anti-aliasing.
        cv2.putText(
            text_img,
            country_code,
            (text_x, text_y),
            font,
            font_scale,
            (255, 255, 255),
            thickness,
            lineType=cv2.LINE_AA,
        )

        # 9. Rotate the text image 90 degrees clockwise.
        rotated_text_rgb = cv2.rotate(text_img, cv2.ROTATE_90_CLOCKWISE)

        # 10. Find bounding box and crop to content (looking for white pixels).
        gray = cv2.cvtColor(rotated_text_rgb, cv2.COLOR_BGR2GRAY)
        coords = np.column_stack(np.where(gray > 0))

        # 11. Crop the rotated text image to the bounding box of the text.
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

            # Set alpha: opaque for text (white pixels), transparent for background
            text_mask = np.any(cropped_text_rgb > 0, axis=2)
            rotated_text[text_mask, 3] = 255  # Opaque text
            rotated_text[~text_mask, 3] = 0  # Transparent background
        else:
            raise ValueError("No text found in the generated image.")

        # 12. Ensure the texture is RGBA.
        if texture.shape[2] == 3:
            # Convert RGB to RGBA
            texture_rgba = np.zeros((texture.shape[0], texture.shape[1], 4), dtype=np.uint8)
            texture_rgba[:, :, :3] = texture
            texture_rgba[:, :, 3] = 255  # Fully opaque
            texture = texture_rgba

        # 13. Place the rotated text in the texture.
        h, w = rotated_text.shape[:2]

        # 14. Center the text within the target box.
        center_x = left + (box_width - w) // 2
        center_y = top + (box_height - h) // 2

        # 15. Ensure the centered text fits within texture bounds.
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
                "Text placed at centered position: (%s,%s) size: %sx%s",
                center_x,
                center_y,
                w,
                h,
            )
        else:
            self.logger.warning(
                "Centered text position (%s,%s) with size %sx%s would exceed texture bounds",
                center_x,
                center_y,
                w,
                h,
            )

        # 16. Save the modified texture.
        cv2.imwrite(texture_path, texture)
        self.logger.debug(
            "Generated license plate texture with country code %s at: %s",
            country_code,
            texture_path,
        )

    def fit_text_in_rotated_box(
        self,
        text: str,
        box_width: int,
        box_height: int,
        font: int,
        thickness: int,
    ) -> tuple[float, int]:
        """Fits text into a rotated box by adjusting font size.

        Arguments:
            text (str): The text to fit.
            box_width (int): The width of the box.
            box_height (int): The height of the box.
            font (int): The OpenCV font to use.
            thickness (int): The thickness of the text.

        Returns:
            tuple[float, int]: The calculated font scale and the size of the large canvas used.
        """
        font_scale = min(box_height / (len(text) * 10), box_width / 22)

        # Create a large canvas to render text without clipping
        large_canvas_size = max(box_width, box_height) * 2

        # Iteratively reduce font size until rotated text fits
        for _ in range(15):  # More iterations for better fitting
            # Test on a large canvas first (black background for white text)
            test_img = np.zeros((large_canvas_size, large_canvas_size, 3), dtype=np.uint8)
            text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]

            # Center text on large canvas
            text_x = (large_canvas_size - text_size[0]) // 2
            text_y = (large_canvas_size + text_size[1]) // 2

            # Use white text for testing with anti-aliasing
            cv2.putText(
                test_img,
                text,
                (text_x, text_y),
                font,
                font_scale,
                (255, 255, 255),
                thickness,
                lineType=cv2.LINE_AA,  # Anti-aliasing for smooth edges
            )

            # Rotate the test image
            rotated_test = cv2.rotate(test_img, cv2.ROTATE_90_CLOCKWISE)

            # Find the bounding box of non-black pixels
            gray = cv2.cvtColor(rotated_test, cv2.COLOR_BGR2GRAY)
            coords = np.column_stack(np.where(gray > 0))

            if len(coords) > 0:
                y_min, x_min = coords.min(axis=0)
                y_max, x_max = coords.max(axis=0)
                rotated_width = x_max - x_min + 1
                rotated_height = y_max - y_min + 1

                # Check if the rotated text fits in our target box with good margin
                if rotated_width <= box_width * 0.90 and rotated_height <= box_height * 0.90:
                    break

            font_scale *= 0.93  # Reduce by 7% each iteration

        self.logger.debug("Final font scale: %s, Original text size: %s", font_scale, text_size)
        if len(coords) > 0:
            self.logger.debug("Rotated text dimensions: %sx%s", rotated_width, rotated_height)

        return font_scale, large_canvas_size
