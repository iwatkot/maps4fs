"""This module contains the Config class for map settings and configuration."""

from __future__ import annotations

import os
from typing import Any
from xml.etree.ElementTree import Element

import cv2
import numpy as np

from maps4fs.generator.component.base.component_image import ImageComponent
from maps4fs.generator.component.xml_document import XmlDocument
from maps4fs.generator.geo import get_country_by_coordinates
from maps4fs.generator.monitor import monitor_performance
from maps4fs.generator.settings import Parameters


# pylint: disable=R0903
class Config(ImageComponent):
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
        """Initialize Config component runtime state."""
        self.info: dict[str, Any] = {}
        self.xml_path = self.game.map_xml_path
        self.fog_parameters: dict[str, int] = {}

    def process(self) -> None:
        """Execute Config processing pipeline."""
        self._set_map_size()

        self._adjust_fog()

        self._ensure_precision_farming_support()

        self._set_overview()

        self.update_license_plates()

    @monitor_performance
    def _ensure_precision_farming_support(self) -> None:
        """Generate precision-farming assets and XML references."""
        soil_map_path = self._generate_soil_map_from_dem()
        if not soil_map_path:
            return

        self._update_i3d_soil_map_references(soil_map_path)
        self._update_map_xml_precision_farming(soil_map_path)

    def _generate_soil_map_from_dem(self) -> str | None:
        """Create precision-farming soil map PNG from the best available DEM variant.

        Returns:
            str | None: Absolute path to the generated soil map PNG, or None when DEM is missing.
        """
        dem_image = self.get_dem_image_with_fallback()
        if dem_image is None:
            self.logger.warning(
                "DEM image not found, precision farming soil map was not generated."
            )
            return None

        if dem_image.ndim == 3:
            dem_image = cv2.cvtColor(dem_image, cv2.COLOR_BGR2GRAY)

        soil_map_size = Parameters.SOIL_MAP_FIXED_SIZE
        resized_dem = cv2.resize(
            dem_image.astype(np.float32),
            (soil_map_size, soil_map_size),
            interpolation=cv2.INTER_LINEAR,
        )

        normalized_height_dst = np.empty_like(resized_dem, dtype=np.float32)
        normalized_height = cv2.normalize(
            resized_dem,
            normalized_height_dst,
            alpha=0.0,
            beta=1.0,
            norm_type=cv2.NORM_MINMAX,
        )

        slope_x = cv2.Sobel(normalized_height, cv2.CV_32F, 1, 0, ksize=3)
        slope_y = cv2.Sobel(normalized_height, cv2.CV_32F, 0, 1, ksize=3)
        slope: np.ndarray = np.asarray(cv2.magnitude(slope_x, slope_y), dtype=np.float32)
        if float(slope.max()) > 0:
            slope_normalized = np.empty_like(slope, dtype=np.float32)
            slope = cv2.normalize(
                slope,
                slope_normalized,
                alpha=0.0,
                beta=1.0,
                norm_type=cv2.NORM_MINMAX,
            )
        else:
            slope = np.zeros_like(normalized_height, dtype=np.float32)

        lowland_mask = normalized_height <= 0.30
        hilltop_mask = (normalized_height >= 0.72) & (slope <= 0.45)
        slope_mask = (~lowland_mask) & (~hilltop_mask) & (slope >= 0.22)
        loam_mask = ~(lowland_mask | hilltop_mask | slope_mask)

        soil_map = np.zeros((soil_map_size, soil_map_size, 3), dtype=np.uint8)
        soil_map[hilltop_mask] = Parameters.SOIL_COLOR_LOAMY_SAND
        soil_map[slope_mask] = Parameters.SOIL_COLOR_SANDY_LOAM
        soil_map[loam_mask] = Parameters.SOIL_COLOR_LOAM
        soil_map[lowland_mask] = Parameters.SOIL_COLOR_SILTY_CLAY

        soil_map_path = os.path.join(self.game.weights_dir_path, Parameters.INFO_LAYER_SOIL_MAP)
        cv2.imwrite(soil_map_path, soil_map)

        self.info["precision_farming"] = {
            "soil_map": soil_map_path,
            "soil_map_resolution": f"{soil_map_size}x{soil_map_size}",
        }
        self.logger.debug("Precision farming soil map created at: %s", soil_map_path)

        return soil_map_path

    def _update_i3d_soil_map_references(self, soil_map_path: str) -> None:
        """Ensure map.i3d contains soil map file and InfoLayer entries.

        Arguments:
            soil_map_path (str): Absolute path to generated soil map PNG.
        """
        if not os.path.isfile(self.game.i3d_file_path):
            self.logger.warning("I3D file not found, precision farming references were not added.")
            return

        soil_map_i3d_filename = self._relative_path_for_xml(
            soil_map_path, os.path.dirname(self.game.i3d_file_path)
        )

        with XmlDocument(self.game.i3d_file_path) as doc:
            if doc.get(self.game.config.i3d_files_xpath) is None:
                self.logger.warning(
                    "Files node not found in map.i3d, skipping soil map file reference."
                )
                return

            soil_file_id = self._ensure_i3d_soil_file_entry(doc, soil_map_i3d_filename)
            self._ensure_i3d_soil_info_layer(doc, soil_file_id)

    def _ensure_i3d_soil_file_entry(self, doc: XmlDocument, soil_filename: str) -> str:
        """Ensure Files section has an entry for soil map and return its file ID.

        Arguments:
            doc (XmlDocument): Parsed map.i3d wrapper.
            soil_filename (str): Soil PNG filename relative to map.i3d directory.

        Returns:
            str: File ID used by soil map File/InfoLayer references.
        """
        cfg = self.game.config
        info_layer_xpath = self.game.config.i3d_soil_map_info_layer_xpath
        soil_info_layer = doc.get(info_layer_xpath)

        if soil_info_layer is not None:
            file_id = soil_info_layer.get(cfg.i3d_attr_file_id)
            if file_id:
                file_xpath = cfg.i3d_file_by_id_xpath_template.format(file_id=file_id)
                if doc.get(file_xpath) is not None:
                    doc.set_attrs(file_xpath, **{cfg.i3d_attr_filename: soil_filename})
                    return file_id
                file_attrs = {
                    cfg.i3d_attr_file_id: file_id,
                    cfg.i3d_attr_filename: soil_filename,
                }
                doc.append_child(
                    cfg.i3d_files_xpath,
                    cfg.i3d_file_tag,
                    **file_attrs,
                )
                return file_id

        existing_file = doc.get(
            cfg.i3d_file_by_filename_xpath_template.format(filename=soil_filename)
        )
        if existing_file is not None:
            existing_file_id = existing_file.get(cfg.i3d_attr_file_id)
            if existing_file_id:
                return existing_file_id

        next_file_id = str(self._next_i3d_file_id(doc))
        file_attrs = {
            cfg.i3d_attr_file_id: next_file_id,
            cfg.i3d_attr_filename: soil_filename,
        }
        doc.append_child(
            cfg.i3d_files_xpath,
            cfg.i3d_file_tag,
            **file_attrs,
        )
        return next_file_id

    def _next_i3d_file_id(self, doc: XmlDocument) -> int:
        """Compute the next available numeric I3D file ID.

        Arguments:
            doc (XmlDocument): Parsed map.i3d wrapper.

        Returns:
            int: Next available file ID.
        """
        cfg = self.game.config
        file_ids = []
        for file_node in doc.find_all(cfg.i3d_all_file_nodes_xpath):
            file_id = file_node.get(cfg.i3d_attr_file_id)
            if file_id is None:
                continue
            try:
                file_ids.append(int(file_id))
            except ValueError:
                continue
        return (max(file_ids) + 1) if file_ids else 1

    def _ensure_i3d_soil_info_layer(self, doc: XmlDocument, soil_file_id: str) -> None:
        """Normalize soil/indoor InfoLayer schema and ordering in map.i3d.

        Arguments:
            doc (XmlDocument): Parsed map.i3d wrapper.
            soil_file_id (str): File ID that soilMap InfoLayer must reference.
        """
        cfg = self.game.config
        soil_layer_xpath = self.game.config.i3d_soil_map_info_layer_xpath
        indoor_layer_xpath = self.game.config.i3d_indoor_mask_info_layer_xpath

        # Normalize indoorMask to a simple runtime layer without Group children.
        if doc.get(indoor_layer_xpath) is not None:
            indoor_attrs = {
                cfg.i3d_attr_num_channels: Parameters.INDOOR_MASK_I3D_NUM_CHANNELS,
                cfg.i3d_attr_runtime: Parameters.I3D_TRUE,
            }
            doc.set_attrs(
                indoor_layer_xpath,
                **indoor_attrs,
            )
            doc.remove_element(cfg.i3d_indoor_mask_group_xpath)

        # Recreate soil layer to enforce exact structure (attrs + Group/Option children).
        doc.remove_element(soil_layer_xpath)
        soil_element = self._create_soil_info_layer_element(soil_file_id)

        # Prefer corrected order: soilMap immediately before indoorMask when available.
        if doc.insert_before(indoor_layer_xpath, soil_element):
            return

        # Fallbacks for templates that don't have indoorMask.
        if doc.insert_after(self.game.config.i3d_farmlands_info_layer_xpath, soil_element):
            return

        layers_xpath = self.game.config.i3d_layers_xpath
        soil_layer_attrs = {
            cfg.i3d_attr_name: Parameters.SOIL_MAP_I3D_LAYER_NAME,
            cfg.i3d_attr_file_id: soil_file_id,
            cfg.i3d_attr_num_channels: Parameters.SOIL_MAP_I3D_NUM_CHANNELS,
            cfg.i3d_attr_runtime: Parameters.I3D_TRUE,
        }
        doc.append_child(
            layers_xpath,
            Parameters.I3D_XML_TAG_INFO_LAYER,
            **soil_layer_attrs,
        )
        soil_group_attrs = {
            cfg.i3d_attr_name: Parameters.SOIL_MAP_I3D_GROUP_NAME,
            cfg.i3d_attr_first_channel: Parameters.SOIL_MAP_I3D_GROUP_FIRST_CHANNEL,
            cfg.i3d_attr_num_channels: Parameters.SOIL_MAP_I3D_NUM_CHANNELS,
        }
        doc.append_child(
            self.game.config.i3d_soil_map_info_layer_xpath,
            Parameters.I3D_XML_TAG_GROUP,
            **soil_group_attrs,
        )
        group_xpath = Parameters.SOIL_MAP_I3D_OPTION_GROUP_XPATH.format(
            soil_layer_xpath=self.game.config.i3d_soil_map_info_layer_xpath,
            group_name=Parameters.SOIL_MAP_I3D_GROUP_NAME,
        )
        outdoor_option_attrs = {
            cfg.i3d_attr_value: Parameters.SOIL_MAP_I3D_OPTION_OUTDOOR_VALUE,
            cfg.i3d_attr_name: Parameters.SOIL_MAP_I3D_OPTION_OUTDOOR_NAME,
        }
        doc.append_child(
            group_xpath,
            Parameters.I3D_XML_TAG_OPTION,
            **outdoor_option_attrs,
        )
        indoor_option_attrs = {
            cfg.i3d_attr_value: Parameters.SOIL_MAP_I3D_OPTION_INDOOR_VALUE,
            cfg.i3d_attr_name: Parameters.SOIL_MAP_I3D_OPTION_INDOOR_NAME,
        }
        doc.append_child(
            group_xpath,
            Parameters.I3D_XML_TAG_OPTION,
            **indoor_option_attrs,
        )

    def _create_soil_info_layer_element(self, soil_file_id: str) -> Element:
        """Build detached soilMap InfoLayer element with Group/Option children.

        Arguments:
            soil_file_id (str): File ID that soilMap layer should reference.

        Returns:
            Element: Detached InfoLayer XML element ready for insertion.
        """
        cfg = self.game.config
        soil_attrs = {
            cfg.i3d_attr_name: Parameters.SOIL_MAP_I3D_LAYER_NAME,
            cfg.i3d_attr_file_id: soil_file_id,
            cfg.i3d_attr_num_channels: Parameters.SOIL_MAP_I3D_NUM_CHANNELS,
            cfg.i3d_attr_runtime: Parameters.I3D_TRUE,
        }
        soil_element = XmlDocument.create_element(
            Parameters.I3D_XML_TAG_INFO_LAYER,
            soil_attrs,
        )

        group_attrs = {
            cfg.i3d_attr_name: Parameters.SOIL_MAP_I3D_GROUP_NAME,
            cfg.i3d_attr_first_channel: Parameters.SOIL_MAP_I3D_GROUP_FIRST_CHANNEL,
            cfg.i3d_attr_num_channels: Parameters.SOIL_MAP_I3D_NUM_CHANNELS,
        }
        group_element = XmlDocument.create_element(
            Parameters.I3D_XML_TAG_GROUP,
            group_attrs,
        )
        outdoor_option_attrs = {
            cfg.i3d_attr_value: Parameters.SOIL_MAP_I3D_OPTION_OUTDOOR_VALUE,
            cfg.i3d_attr_name: Parameters.SOIL_MAP_I3D_OPTION_OUTDOOR_NAME,
        }
        group_element.append(
            XmlDocument.create_element(
                Parameters.I3D_XML_TAG_OPTION,
                outdoor_option_attrs,
            )
        )
        indoor_option_attrs = {
            cfg.i3d_attr_value: Parameters.SOIL_MAP_I3D_OPTION_INDOOR_VALUE,
            cfg.i3d_attr_name: Parameters.SOIL_MAP_I3D_OPTION_INDOOR_NAME,
        }
        group_element.append(
            XmlDocument.create_element(
                Parameters.I3D_XML_TAG_OPTION,
                indoor_option_attrs,
            )
        )
        soil_element.append(group_element)

        return soil_element

    def _update_map_xml_precision_farming(self, soil_map_path: str) -> None:
        """Ensure map.xml references generated soil map through precisionFarming node.

        Arguments:
            soil_map_path (str): Absolute path to generated soil map PNG.
        """
        if not os.path.isfile(self.xml_path):
            self.logger.warning("Map XML not found, precision farming section was not added.")
            return

        soil_map_filename = self._relative_path_for_xml(
            soil_map_path, os.path.dirname(self.xml_path)
        )
        soil_map_grle_filename = (
            os.path.splitext(soil_map_filename)[0] + Parameters.SOIL_MAP_GRLE_EXTENSION
        )

        precision_xpath = self.game.config.map_xml_precision_farming_xpath
        soil_xpath = self.game.config.map_xml_precision_farming_soil_map_xpath
        with XmlDocument(self.xml_path) as doc:
            if doc.get(precision_xpath) is None:
                doc.append_child(".", Parameters.PRECISION_FARMING_TAG)

            if doc.get(soil_xpath) is None:
                doc.append_child(
                    precision_xpath, Parameters.SOIL_MAP_TAG, filename=soil_map_grle_filename
                )
            else:
                doc.set_attrs(soil_xpath, filename=soil_map_grle_filename)

    @staticmethod
    def _relative_path_for_xml(path: str, base_directory: str) -> str:
        """Convert absolute path into XML-safe relative path.

        Arguments:
            path (str): Absolute source path.
            base_directory (str): Base directory used for relative conversion.

        Returns:
            str: Relative path with forward slashes.
        """
        return os.path.relpath(path, start=base_directory).replace("\\", "/")

    def _set_map_size(self) -> None:
        """Update map dimensions in map.xml root attributes."""
        with XmlDocument(self.xml_path) as doc:
            doc.set_attrs(".", width=str(self.scaled_size), height=str(self.scaled_size))

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

        overview_data: dict[str, str | float | int] = {
            "south": south,
            "west": west,
            "north": north,
            "east": east,
            "height": self.map_size * 2,
            "width": self.map_size * 2,
        }

        data: dict[str, dict[str, str | float | int]] = {
            "Overview": overview_data,
        }
        if self.fog_parameters:
            data["Fog"] = dict(self.fog_parameters)

        data.update(self.info)

        return data

    @monitor_performance
    def _adjust_fog(self) -> None:
        """Adjust fog settings in environment.xml using DEM-derived elevation range."""
        self.logger.debug("Adjusting fog settings based on DEM and height scale...")
        environment_xml_path = self.game.environment_xml_path

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

        doc = XmlDocument(environment_xml_path)

        # Find the <latitude>40.6</latitude> element in the XML file.
        latitude_element = doc.get(self.game.config.env_latitude_xpath)
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
        for season in doc.find_all(self.game.config.env_seasons_xpath):
            # Example of the <heightFog> element:
            # <heightFog>
            #     <groundLevelDensity min="0.05" max="0.2" />
            #     <maxHeight min="420" max="600" />
            # </heightFog>
            # We need to adjust the maxheight min and max attributes.
            max_height_element = season.find(self.game.config.env_fog_max_height_xpath)
            if max_height_element is not None:
                max_height_element.set("min", str(minimum_height))
                max_height_element.set("max", str(maximum_height))
            self.logger.debug(
                "Adjusted fog settings for season '%s': min=%s, max=%s",
                season.get("name", "unknown"),
                minimum_height,
                maximum_height,
            )

        self.logger.debug("Fog adjusted and file will be saved to %s", environment_xml_path)
        doc.save()

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
        dem_path = self.game.dem_file_path
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
            doc = XmlDocument(self.game.i3d_file_path)
            terrain_elem = doc.get(self.game.config.i3d_terrain_xpath)
            if terrain_elem is None:
                raise ValueError("Height scale element not found in the I3D file.")
            hs = terrain_elem.get(Parameters.HEIGHT_SCALE)
            if hs is None:
                raise ValueError("Height scale not found in the I3D file.")
            height_scale = int(hs)
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
        """Generate overview texture and convert it to DDS."""
        overview_image_path = self.game.overview_file_path

        overview_path = self.map.context.satellite_overview_path
        if not overview_path:
            self.logger.warning(
                "Satellite overview path not set in context, overview generation will be skipped."
            )
            return

        if not os.path.isfile(overview_path):
            self.logger.warning(
                "Satellite overview image not found, overview generation will be skipped."
            )
            return

        satellite_images_directory = os.path.dirname(overview_path)
        overview_image = cv2.imread(overview_path, cv2.IMREAD_UNCHANGED)

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
        self.logger.debug("Overview image saved to: %s", resized_overview_path)

        if os.path.isfile(overview_image_path):
            try:
                os.remove(overview_image_path)
                self.logger.debug("Old overview image removed: %s", overview_image_path)
            except Exception as e:
                self.logger.warning("Failed to remove old overview image: %s", e)
                return

        self.convert_png_to_dds(resized_overview_path, overview_image_path)
        self.logger.debug("Overview image converted and saved to: %s", overview_image_path)

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
    def update_license_plates(self) -> None:
        """Update license-plate XML/I3D assets for map country."""
        license_plates_directory = self.game.license_plates_dir_path

        country_name = get_country_by_coordinates(self.map.coordinates).lower()
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
                Parameters.COUNTRY_CODE_LEFT,
                Parameters.COUNTRY_CODE_TOP,
                Parameters.COUNTRY_CODE_RIGHT,
                Parameters.COUNTRY_CODE_BOTTOM,
            )

            self.logger.debug("License plates updated successfully")
        except Exception as e:
            self.logger.error("Failed to update license plates: %s", e)
            return

        # Edit the map.xml only if all previous steps succeeded.
        self._update_map_xml_license_plates()

    def _update_map_xml_license_plates(self) -> None:
        """Ensure map.xml references local license plate definition file."""
        doc = XmlDocument(self.xml_path)
        root = doc.root

        # Find or create licensePlates element
        license_plates_element = root.find(self.game.config.map_xml_license_plates_xpath)
        if license_plates_element is not None:
            license_plates_element.set("filename", self.game.config.map_xml_license_plates_filename)
        else:
            license_plates_element = root.makeelement(
                "licensePlates", {"filename": self.game.config.map_xml_license_plates_filename}
            )
            root.append(license_plates_element)

        doc.save()
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
        xml_path = os.path.join(license_plates_directory, Parameters.LICENSE_PLATES_XML_FILENAME)
        if not os.path.isfile(xml_path):
            raise FileNotFoundError(f"License plates XML file not found: {xml_path}.")

        doc = XmlDocument(xml_path)
        root = doc.root

        # Find licensePlate with node="0"
        license_plate = None
        for plate in root.findall(self.game.config.lp_xml_license_plate_xpath):
            if plate.get("node") == "0":
                license_plate = plate
                break

        if license_plate is None:
            raise ValueError("Could not find licensePlate element with node='0'")

        # Find first variations/variation element
        variations = license_plate.find(self.game.config.lp_xml_variations_xpath)
        if variations is None:
            raise ValueError("Could not find variations element")

        variation = variations.find(self.game.config.lp_xml_variation_xpath)
        if variation is None:
            raise ValueError("Could not find first variation element")

        # 1. Update license plate prefix to ensure max 3 letters, uppercase.
        license_plate_prefix = license_plate_prefix.upper()[:3]

        # 2. Pad the prefix to exactly 3 characters with spaces if needed.
        license_plate_prefix = license_plate_prefix.ljust(3)
        self.info["license_plate_prefix"] = license_plate_prefix

        # 3. Position X values for the letters.
        pos_x_values = self.game.config.lp_xml_char_pos_x_values

        # 4. Update all 3 positions (0|0, 0|1, 0|2) to ensure proper formatting.
        # Always process exactly 3 positions, padding with spaces as needed.
        for i in range(3):
            letter = license_plate_prefix[i]  # This will be a space if padding was applied
            target_node = f"0|{i}"
            # Find existing value with this node ID.
            existing_value = None
            for value in variation.findall(self.game.config.lp_xml_value_xpath):
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
        doc.save()
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
        i3d_path = os.path.join(license_plates_directory, Parameters.LICENSE_PLATES_I3D_FILENAME)
        if not os.path.isfile(i3d_path):
            raise FileNotFoundError(f"License plates i3d file not found: {i3d_path}")

        doc = XmlDocument(i3d_path)
        root = doc.root

        # 2. Find File element with fileId="12"
        file_element = None
        for file_elem in root.findall(self.game.config.lp_i3d_file_elements_xpath):
            if file_elem.get("fileId") == self.game.config.lp_i3d_texture_file_id:
                file_element = file_elem
                break

        if file_element is None:
            raise ValueError("Could not find File element with fileId='12'")

        # 3. Update filename to point to local map directory (relative path).
        if eu_format:
            filename = self.game.config.lp_i3d_eu_texture_filename
        else:
            filename = self.game.config.lp_i3d_default_texture_filename

        file_element.set("filename", filename)

        # 4. Save the updated i3d XML.
        doc.save()
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
            texture_filename = self.game.config.lp_i3d_eu_texture_filename
        else:
            texture_filename = self.game.config.lp_i3d_default_texture_filename

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
        text_img: np.ndarray = np.zeros((large_canvas_size, large_canvas_size, 3), dtype=np.uint8)
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
            test_img: np.ndarray = np.zeros(
                (large_canvas_size, large_canvas_size, 3), dtype=np.uint8
            )
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
