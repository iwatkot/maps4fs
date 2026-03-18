"""Soil component for soil map generation and XML wiring."""

from __future__ import annotations

import os
from xml.etree.ElementTree import Element

import cv2
import numpy as np

from maps4fs.generator.component.base.component_image import ImageComponent
from maps4fs.generator.component.xml_document import XmlDocument
from maps4fs.generator.monitor import monitor_performance
from maps4fs.generator.settings import Parameters


class Soil(ImageComponent):
    """Generate soil map and update map XML/I3D references."""

    def preprocess(self) -> None:
        """Initialize runtime state for Soil component."""
        self.soil_map_path: str | None = None

    @monitor_performance
    def process(self) -> None:
        """Generate soil map and ensure required XML entries are present."""
        soil_map_path = self._generate_soil_map_from_dem()
        if not soil_map_path:
            return

        self.soil_map_path = soil_map_path

        self._update_i3d_soil_map_references(soil_map_path)
        self._update_map_xml_precision_farming(soil_map_path)

    @monitor_performance
    def previews(self) -> list[str]:
        """Generate debug previews for the generated soil map.

        Returns:
            list[str]: Paths to the created preview images.
        """
        soil_map_path = self.soil_map_path or os.path.join(
            self.game.weights_dir_path, Parameters.INFO_LAYER_SOIL_MAP
        )

        if not os.path.isfile(soil_map_path):
            self.logger.warning("Soil map not found for preview generation: %s", soil_map_path)
            return []

        soil_map = cv2.imread(soil_map_path, cv2.IMREAD_UNCHANGED)
        if soil_map is None:
            self.logger.warning("Could not read soil map for preview generation: %s", soil_map_path)
            return []

        if soil_map.ndim == 3:
            soil_map = cv2.cvtColor(soil_map, cv2.COLOR_BGR2GRAY)

        normalized_preview_path = os.path.join(self.previews_directory, "soil_map_normalized.png")
        colored_preview_path = os.path.join(self.previews_directory, "soil_map_colored.png")

        normalized = cv2.normalize(
            soil_map,
            dst=np.empty_like(soil_map),
            alpha=0,
            beta=255,
            norm_type=cv2.NORM_MINMAX,
            dtype=cv2.CV_8U,
        )

        cv2.imwrite(normalized_preview_path, normalized)

        colored = cv2.applyColorMap(normalized, cv2.COLORMAP_JET)
        cv2.imwrite(colored_preview_path, colored)

        return [normalized_preview_path, colored_preview_path]

    def _generate_soil_map_from_dem(self) -> str | None:
        """Create soil map PNG from the best available DEM variant.

        Returns:
            str | None: Absolute path to generated soil map PNG, or None when DEM is missing.
        """
        dem_image = self.get_dem_image_with_fallback()
        if dem_image is None:
            self.logger.warning("DEM image not found, soil map was not generated.")
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

        soil_map = self._classify_soils(normalized_height)

        soil_map_path = os.path.join(self.game.weights_dir_path, Parameters.INFO_LAYER_SOIL_MAP)
        cv2.imwrite(soil_map_path, soil_map)

        values, counts = np.unique(soil_map, return_counts=True)
        class_distribution = {
            int(value): float(count / soil_map.size) for value, count in zip(values, counts)
        }

        self.update_generation_info(
            {
                "soil_map": soil_map_path,
                "soil_map_resolution": f"{soil_map_size}x{soil_map_size}",
                "soil_values": [0, 1, 2, 3],
                "soil_distribution": class_distribution,
            }
        )
        self.logger.debug("Soil map created at: %s", soil_map_path)

        return soil_map_path

    def _classify_soils(self, normalized_height: np.ndarray) -> np.ndarray:
        """Classify soils from normalized elevation and terrain-derived proxies.

        Arguments:
            normalized_height (np.ndarray): DEM normalized to [0, 1].

        Returns:
            np.ndarray: Soil class map with values 0..3.
        """
        slope_x = cv2.Sobel(normalized_height, cv2.CV_32F, 1, 0, ksize=3)
        slope_y = cv2.Sobel(normalized_height, cv2.CV_32F, 0, 1, ksize=3)
        slope = np.asarray(cv2.magnitude(slope_x, slope_y), dtype=np.float32)
        slope = self._normalize_to_unit(slope)

        wetness = self._build_local_wetness(normalized_height, slope)

        breakline_mask, break_strength = self._build_breakline_mask(normalized_height, slope)

        height_q60 = float(np.quantile(normalized_height, 0.60))
        height_q75 = float(np.quantile(normalized_height, 0.75))

        slope_q30 = float(np.quantile(slope, 0.30))
        slope_q50 = float(np.quantile(slope, 0.50))
        slope_q70 = float(np.quantile(slope, 0.70))
        slope_q85 = float(np.quantile(slope, 0.85))

        wet_q75 = float(np.quantile(wetness, 0.75))
        wet_q85 = float(np.quantile(wetness, 0.85))

        high = normalized_height >= height_q75
        mid_or_high = normalized_height >= height_q60

        flat = slope <= slope_q30
        moderate = (slope > slope_q30) & (slope <= slope_q70)
        steep = slope >= slope_q70
        very_steep = slope >= slope_q85

        very_wet = wetness >= wet_q85
        wet = wetness >= wet_q75

        # Allow wet pockets on elevated plateaus by using local wetness, not global low elevation.
        silty_clay_mask = very_wet & (flat | (slope <= slope_q50))
        loamy_sand_mask = (high & steep) | (mid_or_high & very_steep)

        # Escarpments and abrupt relief changes should not collapse to loam.
        breakline_sandy_mask = breakline_mask & ~silty_clay_mask
        breakline_loamy_sand_mask = breakline_sandy_mask & high & (slope >= slope_q50)

        sandy_loam_mask = (moderate | (wet & steep)) & ~silty_clay_mask & ~loamy_sand_mask
        sandy_loam_mask = sandy_loam_mask | breakline_sandy_mask
        loamy_sand_mask = loamy_sand_mask | breakline_loamy_sand_mask
        loam_mask = ~(silty_clay_mask | loamy_sand_mask | sandy_loam_mask)

        soil_map = np.full(normalized_height.shape, Parameters.SOIL_VALUE_LOAM, dtype=np.uint8)
        soil_map[loamy_sand_mask] = Parameters.SOIL_VALUE_LOAMY_SAND
        soil_map[sandy_loam_mask] = Parameters.SOIL_VALUE_SANDY_LOAM
        soil_map[loam_mask] = Parameters.SOIL_VALUE_LOAM
        soil_map[silty_clay_mask] = Parameters.SOIL_VALUE_SILTY_CLAY

        soil_map = self._smooth_soil_classes(soil_map)
        soil_map = self._majority_filter(soil_map, kernel_size=5, iterations=2)

        # Re-apply hard constraints after smoothing.
        soil_map[silty_clay_mask] = Parameters.SOIL_VALUE_SILTY_CLAY
        soil_map[breakline_sandy_mask] = Parameters.SOIL_VALUE_SANDY_LOAM
        soil_map[breakline_loamy_sand_mask] = Parameters.SOIL_VALUE_LOAMY_SAND

        self.logger.debug(
            (
                "Soil classifier stats: breakline_ratio=%.3f, mean_break_strength=%.3f, "
                "mean_wetness=%.3f"
            ),
            float(np.mean(breakline_mask.astype(np.float32))),
            float(np.mean(break_strength)),
            float(np.mean(wetness)),
        )

        return soil_map

    def _build_local_wetness(self, normalized_height: np.ndarray, slope: np.ndarray) -> np.ndarray:
        """Estimate local wetness from multi-scale depressions and low slope.

        Arguments:
            normalized_height (np.ndarray): DEM normalized to [0, 1].
            slope (np.ndarray): Slope proxy normalized to [0, 1].

        Returns:
            np.ndarray: Wetness score in [0, 1].
        """
        local_mean_small = cv2.GaussianBlur(normalized_height, (0, 0), sigmaX=3.0, sigmaY=3.0)
        local_mean_large = cv2.GaussianBlur(normalized_height, (0, 0), sigmaX=9.0, sigmaY=9.0)

        depression_small = self._normalize_to_unit(
            np.clip(local_mean_small - normalized_height, 0.0, None)
        )
        depression_large = self._normalize_to_unit(
            np.clip(local_mean_large - normalized_height, 0.0, None)
        )

        inverse_slope = 1.0 - slope
        wetness = (0.45 * depression_small) + (0.35 * depression_large) + (0.20 * inverse_slope)
        return self._normalize_to_unit(np.asarray(wetness, dtype=np.float32))

    @staticmethod
    def _normalize_to_unit(image: np.ndarray) -> np.ndarray:
        """Normalize a float image to [0, 1], returning zeros for constant input."""
        image = np.asarray(image, dtype=np.float32)
        if float(image.max()) <= float(image.min()):
            return np.zeros_like(image, dtype=np.float32)
        normalized = np.empty_like(image, dtype=np.float32)
        return np.asarray(
            cv2.normalize(
                image,
                dst=normalized,
                alpha=0.0,
                beta=1.0,
                norm_type=cv2.NORM_MINMAX,
            ),
            dtype=np.float32,
        )

    def _build_breakline_mask(
        self, normalized_height: np.ndarray, slope: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray]:
        """Build a mask of abrupt terrain transitions (scarps/breaklines)."""
        kernel = np.ones((5, 5), np.uint8)
        local_max = cv2.dilate(normalized_height, kernel)
        local_min = cv2.erode(normalized_height, kernel)
        local_relief = np.asarray(local_max - local_min, dtype=np.float32)
        local_relief = self._normalize_to_unit(local_relief)

        curvature = np.abs(cv2.Laplacian(normalized_height, cv2.CV_32F, ksize=3))
        curvature = self._normalize_to_unit(np.asarray(curvature, dtype=np.float32))

        break_strength = np.maximum(local_relief, curvature)
        break_q85 = float(np.quantile(break_strength, 0.85))
        slope_q50 = float(np.quantile(slope, 0.50))

        breakline_mask = (break_strength >= break_q85) & (slope >= slope_q50)
        return breakline_mask, break_strength

    @staticmethod
    def _smooth_soil_classes(soil_map: np.ndarray) -> np.ndarray:
        """Apply light majority-like smoothing on class map to reduce speckle noise."""
        return cv2.medianBlur(soil_map, 3)

    @staticmethod
    def _majority_filter(
        soil_map: np.ndarray, kernel_size: int = 5, iterations: int = 1
    ) -> np.ndarray:
        """Apply class-wise local majority filtering to reduce tiny worm-like regions."""
        result = soil_map.copy()
        classes = np.array(
            [
                Parameters.SOIL_VALUE_LOAMY_SAND,
                Parameters.SOIL_VALUE_SANDY_LOAM,
                Parameters.SOIL_VALUE_LOAM,
                Parameters.SOIL_VALUE_SILTY_CLAY,
            ],
            dtype=np.uint8,
        )

        for _ in range(iterations):
            class_votes: list[np.ndarray] = []
            for cls in classes:
                mask = (result == cls).astype(np.float32)
                votes = cv2.boxFilter(
                    mask, ddepth=-1, ksize=(kernel_size, kernel_size), normalize=False
                )
                class_votes.append(votes)

            stacked_votes = np.stack(class_votes, axis=0)
            winner_idx = np.argmax(stacked_votes, axis=0)
            result = classes[winner_idx]

        return result.astype(np.uint8)

    def _update_i3d_soil_map_references(self, soil_map_path: str) -> None:
        """Ensure map.i3d contains soil map file and InfoLayer entries.

        Arguments:
            soil_map_path (str): Absolute path to generated soil map PNG.
        """
        if not os.path.isfile(self.game.i3d_file_path):
            self.logger.warning("I3D file not found, soil references were not added.")
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
        """Ensure Files section has a soil map entry and return its file ID.

        Arguments:
            doc (XmlDocument): Parsed map.i3d wrapper.
            soil_filename (str): Soil PNG filename relative to map.i3d directory.

        Returns:
            str: File ID used by soil map File/InfoLayer references.
        """
        cfg = self.game.config
        info_layer_xpath = cfg.i3d_soil_map_info_layer_xpath
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
                doc.append_child(cfg.i3d_files_xpath, cfg.i3d_file_tag, **file_attrs)
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
        doc.append_child(cfg.i3d_files_xpath, cfg.i3d_file_tag, **file_attrs)
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
        soil_layer_xpath = cfg.i3d_soil_map_info_layer_xpath
        indoor_layer_xpath = cfg.i3d_indoor_mask_info_layer_xpath

        if doc.get(indoor_layer_xpath) is not None:
            indoor_attrs = {
                cfg.i3d_attr_num_channels: Parameters.INDOOR_MASK_I3D_NUM_CHANNELS,
                cfg.i3d_attr_runtime: Parameters.I3D_TRUE,
            }
            doc.set_attrs(indoor_layer_xpath, **indoor_attrs)
            doc.remove_element(cfg.i3d_indoor_mask_group_xpath)

        doc.remove_element(soil_layer_xpath)
        soil_element = self._create_soil_info_layer_element(soil_file_id)

        if doc.insert_before(indoor_layer_xpath, soil_element):
            return

        if doc.insert_after(cfg.i3d_farmlands_info_layer_xpath, soil_element):
            return

        layers_xpath = cfg.i3d_layers_xpath
        soil_layer_attrs = {
            cfg.i3d_attr_name: Parameters.SOIL_MAP_I3D_LAYER_NAME,
            cfg.i3d_attr_file_id: soil_file_id,
            cfg.i3d_attr_num_channels: Parameters.SOIL_MAP_I3D_NUM_CHANNELS,
            cfg.i3d_attr_runtime: Parameters.I3D_TRUE,
        }
        doc.append_child(layers_xpath, Parameters.I3D_XML_TAG_INFO_LAYER, **soil_layer_attrs)

        soil_group_attrs = {
            cfg.i3d_attr_name: Parameters.SOIL_MAP_I3D_GROUP_NAME,
            cfg.i3d_attr_first_channel: Parameters.SOIL_MAP_I3D_GROUP_FIRST_CHANNEL,
            cfg.i3d_attr_num_channels: Parameters.SOIL_MAP_I3D_NUM_CHANNELS,
        }
        doc.append_child(
            cfg.i3d_soil_map_info_layer_xpath,
            Parameters.I3D_XML_TAG_GROUP,
            **soil_group_attrs,
        )

        group_xpath = Parameters.SOIL_MAP_I3D_OPTION_GROUP_XPATH.format(
            soil_layer_xpath=cfg.i3d_soil_map_info_layer_xpath,
            group_name=Parameters.SOIL_MAP_I3D_GROUP_NAME,
        )

        options = [
            (
                Parameters.SOIL_MAP_I3D_OPTION_LOAMY_SAND_VALUE,
                Parameters.SOIL_MAP_I3D_OPTION_LOAMY_SAND_NAME,
            ),
            (
                Parameters.SOIL_MAP_I3D_OPTION_SANDY_LOAM_VALUE,
                Parameters.SOIL_MAP_I3D_OPTION_SANDY_LOAM_NAME,
            ),
            (Parameters.SOIL_MAP_I3D_OPTION_LOAM_VALUE, Parameters.SOIL_MAP_I3D_OPTION_LOAM_NAME),
            (
                Parameters.SOIL_MAP_I3D_OPTION_SILTY_CLAY_VALUE,
                Parameters.SOIL_MAP_I3D_OPTION_SILTY_CLAY_NAME,
            ),
        ]
        for value, name in options:
            option_attrs = {cfg.i3d_attr_value: value, cfg.i3d_attr_name: name}
            doc.append_child(group_xpath, Parameters.I3D_XML_TAG_OPTION, **option_attrs)

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
        soil_element = XmlDocument.create_element(Parameters.I3D_XML_TAG_INFO_LAYER, soil_attrs)

        group_attrs = {
            cfg.i3d_attr_name: Parameters.SOIL_MAP_I3D_GROUP_NAME,
            cfg.i3d_attr_first_channel: Parameters.SOIL_MAP_I3D_GROUP_FIRST_CHANNEL,
            cfg.i3d_attr_num_channels: Parameters.SOIL_MAP_I3D_NUM_CHANNELS,
        }
        group_element = XmlDocument.create_element(Parameters.I3D_XML_TAG_GROUP, group_attrs)

        options = [
            (
                Parameters.SOIL_MAP_I3D_OPTION_LOAMY_SAND_VALUE,
                Parameters.SOIL_MAP_I3D_OPTION_LOAMY_SAND_NAME,
            ),
            (
                Parameters.SOIL_MAP_I3D_OPTION_SANDY_LOAM_VALUE,
                Parameters.SOIL_MAP_I3D_OPTION_SANDY_LOAM_NAME,
            ),
            (Parameters.SOIL_MAP_I3D_OPTION_LOAM_VALUE, Parameters.SOIL_MAP_I3D_OPTION_LOAM_NAME),
            (
                Parameters.SOIL_MAP_I3D_OPTION_SILTY_CLAY_VALUE,
                Parameters.SOIL_MAP_I3D_OPTION_SILTY_CLAY_NAME,
            ),
        ]
        for value, name in options:
            option_attrs = {cfg.i3d_attr_value: value, cfg.i3d_attr_name: name}
            group_element.append(
                XmlDocument.create_element(Parameters.I3D_XML_TAG_OPTION, option_attrs)
            )

        soil_element.append(group_element)
        return soil_element

    def _update_map_xml_precision_farming(self, soil_map_path: str) -> None:
        """Ensure map.xml references generated soil map through precisionFarming node.

        Arguments:
            soil_map_path (str): Absolute path to generated soil map PNG.
        """
        map_xml_path = self.game.map_xml_path
        if not os.path.isfile(map_xml_path):
            self.logger.warning("Map XML not found, precision farming section was not added.")
            return

        soil_map_filename = self._relative_path_for_xml(
            soil_map_path, os.path.dirname(map_xml_path)
        )
        soil_map_grle_filename = (
            os.path.splitext(soil_map_filename)[0] + Parameters.SOIL_MAP_GRLE_EXTENSION
        )

        cfg = self.game.config
        precision_xpath = cfg.map_xml_precision_farming_xpath
        soil_xpath = cfg.map_xml_precision_farming_soil_map_xpath
        with XmlDocument(map_xml_path) as doc:
            if doc.get(precision_xpath) is None:
                doc.append_child(".", Parameters.PRECISION_FARMING_TAG)

            if doc.get(soil_xpath) is None:
                doc.append_child(
                    precision_xpath,
                    Parameters.SOIL_MAP_TAG,
                    filename=soil_map_grle_filename,
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
