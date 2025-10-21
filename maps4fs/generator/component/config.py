"""This module contains the Config class for map settings and configuration."""

from __future__ import annotations

import os

import cv2

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

    def update_license_plates(self):
        if not self.game.license_plates_processing:
            self.logger.warning("License plates processing is not supported for this game.")
            return

        # region production constants
        COUNTRY_CODE_TOP = 169
        COUNTRY_CODE_BOTTOM = 252
        COUNTRY_CODE_LEFT = 74
        COUNTRY_CODE_RIGHT = 140

        # region debug values
        country_code = "SRB"
        eu_format = False
        # endregion

        # 1. open map.xml file
        # 2. find the <licensePlates> element
        # 3. update to use the PL license plates file
        # <licensePlates filename="map/licensePlates/licensePlatesPL.xml" />
        # 4. Find the licensePlatesPL.xml file in the map/licensePlates/ directory
        # 5. Find the following line:
        # <licensePlate filename="map/licensePlates/licensePlatesPL.i3d" node="0" />
        # WARNING: USE NODE="0" BECAUSE THERE ARE OTHER ENTRIES WITH licensePlate TAG!
        # 6. Inside the element find the <variations> element
        # 7. Inside the <variations> element, find the FIRST <variation> element
        # WARNING: THERE ARE MULTIPLE variation TAGS, USE THE FIRST ONE!
        # 8. Having the 1-3 letters as input of this method, find and update the following lines:
        # <value node="0|0" character="M" posX="-0.1712" numerical="false" alphabetical="true" />
        # <value node="0|1" character="F" posX="-0.1172" numerical="false" alphabetical="true" />
        # <value node="0|2" character="S" posX="-0.0632" numerical="false" alphabetical="true" />
        # We need character here, by default it's MFS, set to provided letters.
        # 9. Find the licensePlatesPL.i3d file in the map/licensePlates/ directory
        # 10. Find the <Files> section
        # 11. Find the following line:
        # <File fileId="12" filename="licensePlates_diffuse.png" />
        # 12. Having a boolean parameter in the fuction, update the filename (if needed) to:
        # <File fileId="12" filename="licensePlates_diffuseEU.png" />
        # or leave it as is for non-EU plates.
        # 13. Having country code parameter, and knowing exact coordinates of place in the
        # diffuse texture
        # 14. Calculate the pixel size of the box using hardcoded constants
        # 15. Knowing number of letters and box size, calculate the font size
        # 16. and the position where to insert the image with letters
        # 17. Insert the letters into the image and save file
        # WARNING: THIS TEXT IS ROTATED 90 DEGREES IN CLOCKWISE DIRECTION IN THE TEXTURE!
        pass
