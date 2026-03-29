"""Module with Texture class for generating textures for the map using OSM data."""

from __future__ import annotations

import json
import os
import shutil
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Literal, cast

import cv2
import numpy as np
import osmnx as ox
from tqdm import tqdm

from maps4fs.generator.component.base.component_image import ImageComponent
from maps4fs.generator.component.layer import Layer
from maps4fs.generator.monitor import monitor_performance
from maps4fs.generator.osm_pipeline import (
    LatLonProjector,
    OSMNXFeatureSource,
    OSMRasterPipeline,
)
from maps4fs.generator.osm_pipeline.rasterizer import OSMGeometryRasterizer
from maps4fs.generator.settings import Parameters


@dataclass(frozen=True)
class TextureOptions:
    """Runtime options for Texture generation."""

    texture_custom_schema: list[dict[str, Any]] | None = None
    skip_scaling: bool = False
    channel: Literal["textures", "background", "extended"] = "textures"
    cap_style: str = "round"


class Texture(ImageComponent):
    """Class which generates textures for the map using OSM data.

    Attributes:
        weights_dir (str): Path to the directory with weights.
        name (str): Name of the texture.
        tags (dict[str, str | list[str] | bool]): Dictionary of tags to search for.
        width (int | None): Width of the polygon in meters (only for LineString).
        color (tuple[int, int, int]): Color of the layer in BGR format.
    """

    def __init__(
        self,
        game,
        map,
        *,
        map_size: int | None = None,
        map_rotated_size: int | None = None,
        options: TextureOptions | None = None,
    ):
        self.options = options or TextureOptions()
        self.osm_pipeline: OSMRasterPipeline | None = None
        super().__init__(
            game,
            map,
            map_size=map_size,
            map_rotated_size=map_rotated_size,
        )

    def preprocess(self) -> None:
        """Preprocesses the data before the generation."""
        self._weights_dir: str = self.game.weights_dir_path
        self.procedural_dir = os.path.join(self._weights_dir, Parameters.MASKS_DIRECTORY)
        os.makedirs(self.procedural_dir, exist_ok=True)

        self.cap_style = self.options.cap_style
        self.read_layers(self.get_schema())

    def read_layers(self, layers_schema: list[dict[str, Any]]) -> None:
        """Reads layers from the schema.

        Arguments:
            layers_schema (list[dict[str, Any]]): Schema with layers for textures.
        """
        try:
            self.layers = [Layer.from_json(layer) for layer in layers_schema]
            self.logger.debug("Loaded %s layers.", len(self.layers))
        except Exception as e:
            raise ValueError(f"Error loading texture layers: {e}") from e

        # Publish layer metadata only for the main texture pass.
        # Background texture pass uses a reduced schema and must not overwrite these layers.
        if self.options.channel == Parameters.TEXTURE_CHANNEL_TEXTURES:
            self.map.context.texture_layers = self.layers

    def get_schema(self) -> list[dict[str, Any]]:
        """Returns schema with layers for textures.

        Raises:
            FileNotFoundError: If the schema file is not found.
            ValueError: If there is an error loading the schema.
            ValueError: If the schema is not a list of dictionaries.

        Returns:
            dict[str, Any]: Schema with layers for textures.
        """
        custom_schema = self.options.texture_custom_schema or self.map.texture_custom_schema
        if custom_schema:
            layers_schema = custom_schema
            self.logger.debug("Custom schema loaded with %s layers.", len(layers_schema))
        else:
            if not os.path.isfile(self.game.texture_schema):
                raise FileNotFoundError(
                    f"Texture layers schema not found: {self.game.texture_schema}"
                )

            try:
                with open(self.game.texture_schema, "r", encoding="utf-8") as f:
                    layers_schema = json.load(f)
            except json.JSONDecodeError as e:
                raise ValueError(f"Error loading texture layers schema: {e}") from e

        if not isinstance(layers_schema, list):
            raise ValueError("Texture layers schema must be a list of dictionaries.")
        return layers_schema

    def get_base_layer(self) -> Layer | None:
        """Returns base layer.

        Returns:
            Layer | None: Base layer.
        """
        for layer in self.layers:
            if layer.priority == 0:
                return layer
        return None

    def get_background_layers(self) -> list[Layer]:
        """Returns list of background layers.

        Returns:
            list[Layer]: List of background layers.
        """
        return [layer for layer in self.layers if layer.background]

    def get_layer_by_usage(self, usage: str) -> Layer | None:
        """Returns layer by usage.

        Arguments:
            usage (str): Usage of the layer.

        Returns:
            Layer | None: Layer.
        """
        for layer in self.layers:
            if layer.usage == usage:
                return layer
        return None

    def get_layers_by_usage(self, usage: str) -> list[Layer]:
        """Returns layer by usage.

        Arguments:
            usage (str): Usage of the layer.

        Returns:
            list[Layer]: List of layers.
        """
        return [layer for layer in self.layers if layer.usage == usage]

    def get_area_type_layers(self, area_type: str | None = None) -> list[Layer]:
        """Returns layers by area type. If area_type is None, returns all layers
        with area_type set (not None).

        Arguments:
            area_type (str | None): Area type of the layer.

        Returns:
            list[Layer]: List of layers.
        """
        if area_type is None:
            return [layer for layer in self.layers if layer.area_type is not None]
        return [layer for layer in self.layers if layer.area_type == area_type]

    def get_water_area_layers(self) -> list[Layer]:
        """Returns layers which are water areas.

        Returns:
            list[Layer]: List of layers which are water areas.
        """
        return [layer for layer in self.layers if layer.area_water]

    def get_indoor_layers(self) -> list[Layer]:
        """Returns layers which are indoor areas.

        Returns:
            list[Layer]: List of layers which are indoor areas.
        """
        return [layer for layer in self.layers if layer.indoor]

    def get_building_category_layers(self) -> list[Layer]:
        """Returns layers which have building category defined.

        Returns:
            list[Layer]: List of layers which have building category defined.
        """
        return [layer for layer in self.layers if layer.building_category is not None]

    def process(self) -> None:
        """Processes the data to generate textures."""
        self._prepare_weights()
        self._read_parameters()
        self._build_osm_pipeline()
        self.draw()
        self.rotate_textures()
        self.merge_into()

        if not self.options.skip_scaling:
            self.scale_textures()

        self.add_borders()
        if self.map.texture_settings.dissolve:
            self.dissolve()
        self.copy_procedural()

        for layer in self.layers:
            self.assets[layer.name] = layer.path(self._weights_dir)

    def _iter_layer_output_paths(self, layer: Layer, include_preview: bool = False) -> list[str]:
        """Return generated file paths for a layer, optionally including preview image."""
        paths = layer.paths(self._weights_dir)
        if include_preview:
            paths.append(layer.path_preview(self._weights_dir))
        return paths

    @staticmethod
    def _is_drawable_layer(layer: Layer) -> bool:
        """Return whether a layer has OSM tags and should be drawn."""
        return layer.tags is not None or layer.precise_tags is not None

    @staticmethod
    def _has_tag_textures(layer: Layer) -> bool:
        """Return whether a layer has tag-based textures that can be rotated."""
        return bool(layer.tags or layer.precise_tags)

    def _load_layer_image(self, layer_path: str) -> np.ndarray | None:
        """Read a layer image and log if it cannot be loaded."""
        image = cv2.imread(layer_path, cv2.IMREAD_UNCHANGED)
        if image is None:
            self.logger.warning("Could not read layer image: %s", layer_path)
        return image

    @monitor_performance
    def add_borders(self) -> None:
        """Iterates over all the layers and picks the one which have the border propety defined.
        Borders are distance from the edge of the map on each side (top, right, bottom, left).
        On the layers those pixels will be removed (value set to 0). If the base layer exist in
        the schema, those pixel values (not 0) will be added as 255 to the base layer."""
        base_layer = self.get_base_layer()
        base_layer_image = None
        if base_layer:
            base_layer_image = cv2.imread(base_layer.path(self._weights_dir), cv2.IMREAD_UNCHANGED)

        layers_with_borders = [layer for layer in self.layers if layer.border is not None]

        for layer in layers_with_borders:
            # Read the image.
            # Read pixels on borders with specified width (border property).
            # Where the pixel value is 255 - set it to 255 in base layer image.
            # And set it to 0 in the current layer image.
            layer_image = cv2.imread(layer.path(self._weights_dir), cv2.IMREAD_UNCHANGED)
            if layer_image is None:
                continue
            border = layer.border
            if not border:
                continue

            self.transfer_border(layer_image, base_layer_image, border)

            cv2.imwrite(layer.path(self._weights_dir), layer_image)
            self.logger.debug("Borders added to layer %s.", layer.name)

        if base_layer and base_layer_image is not None:
            cv2.imwrite(base_layer.path(self._weights_dir), base_layer_image)

    def copy_procedural(self) -> None:
        """Copies some of the textures to use them as mask for procedural generation.
        Creates an empty blockmask if it does not exist."""
        self._ensure_blockmask()
        pg_layers_by_type = self._collect_procedural_sources()

        if not pg_layers_by_type:
            self.logger.debug("No procedural layers found.")
            return

        for procedural_layer_name, texture_paths in pg_layers_by_type.items():
            self._save_procedural_layer(procedural_layer_name, texture_paths)

    def _ensure_blockmask(self) -> None:
        """Ensure procedural BLOCKMASK file exists."""
        blockmask_path = os.path.join(self.procedural_dir, Parameters.BLOCKMASK_FILENAME)
        if os.path.isfile(blockmask_path):
            return
        self.logger.debug("%s not found, creating an empty file.", Parameters.BLOCKMASK_FILENAME)
        img = np.zeros((self.scaled_size, self.scaled_size), dtype=np.uint8)
        cv2.imwrite(blockmask_path, img)

    def _collect_procedural_sources(self) -> dict[str, list[str]]:
        """Collect source texture paths grouped by procedural layer name."""
        pg_layers_by_type: dict[str, list[str]] = defaultdict(list)
        for layer in self.layers:
            if not layer.procedural:
                continue
            texture_path = layer.get_preview_or_path(self._weights_dir)
            for procedural_layer_name in layer.procedural:
                pg_layers_by_type[procedural_layer_name].append(texture_path)
        return pg_layers_by_type

    def _save_procedural_layer(self, procedural_layer_name: str, texture_paths: list[str]) -> None:
        """Write a procedural layer from one or multiple source textures."""
        procedural_save_path = os.path.join(
            self.procedural_dir,
            f"{procedural_layer_name}{Parameters.PNG_EXTENSION}",
        )
        if len(texture_paths) > 1:
            merged_texture = np.zeros((self.scaled_size, self.scaled_size), dtype=np.uint8)
            for texture_path in texture_paths:
                texture = cv2.imread(texture_path, cv2.IMREAD_UNCHANGED)
                if texture is None:
                    continue
                merged_texture[texture == 255] = 255
            cv2.imwrite(procedural_save_path, merged_texture)
            self.logger.debug(
                "Procedural file %s merged from %s textures.",
                procedural_save_path,
                len(texture_paths),
            )
            return

        if len(texture_paths) == 1:
            shutil.copyfile(texture_paths[0], procedural_save_path)
            self.logger.debug(
                "Procedural file %s copied from %s.", procedural_save_path, texture_paths[0]
            )

    def get_layer_by_name(self, layer_name: str) -> Layer | None:
        """Returns the layer with the given name.

        Arguments:
            layer_name: The name of the layer to retrieve.

        Returns:
            The layer with the given name, or None if not found.
        """
        for layer in self.layers:
            if layer.name == layer_name:
                return layer
        return None

    @monitor_performance
    def merge_into(self) -> None:
        """Merges the content of layers into their target layers."""
        for layer in self.layers:
            if not layer.merge_into:
                continue
            self._merge_single_layer(layer)

    def _merge_single_layer(self, layer: Layer) -> None:
        """Merge one layer into its configured target and clear source content."""
        if layer.merge_into is None:
            return
        target_layer = self.get_layer_by_name(layer.merge_into)
        if target_layer is None:
            self.logger.debug("Target layer %s not found for %s.", layer.merge_into, layer.name)
            return

        target_path = target_layer.path(self._weights_dir)
        source_path = layer.path(self._weights_dir)

        target_layer_image = self._load_layer_image(target_path)
        layer_image = self._load_layer_image(source_path)
        if target_layer_image is None or layer_image is None:
            return

        if target_layer_image.shape != layer_image.shape:
            self.logger.warning(
                "Layer %s and target layer %s have different shapes, skipping merge.",
                layer.name,
                target_layer.name,
            )
            return

        merged_image = cv2.add(target_layer_image, layer_image)
        cv2.imwrite(target_path, merged_image)
        self.logger.debug("Merged layer %s into %s.", layer.name, target_layer.name)

        cv2.imwrite(source_path, np.zeros_like(layer_image))
        self.logger.debug("Cleared layer %s.", layer.name)

    @monitor_performance
    def rotate_textures(self) -> None:
        """Rotates textures of the layers which have tags."""
        if not self.rotation:
            return

        for layer in tqdm(self.layers, desc="Rotating textures", unit="layer"):
            if not self._has_tag_textures(layer):
                self.logger.debug(
                    "Skipping rotation of layer %s because it has no tags.", layer.name
                )
                continue
            self.logger.debug("Rotating layer %s.", layer.name)
            for layer_path in self._iter_layer_output_paths(layer, include_preview=True):
                if os.path.isfile(layer_path):
                    self.rotate_image(
                        layer_path,
                        self.rotation,
                        output_height=self.map_size,
                        output_width=self.map_size,
                    )

    @monitor_performance
    def scale_textures(self) -> None:
        """Resizes all the textures to the map output size."""
        if not self.map.output_size:
            self.logger.debug("No output size defined, skipping scaling.")
            return

        for layer in tqdm(self.layers, desc="Scaling textures", unit="layer"):
            for layer_path in self._iter_layer_output_paths(layer, include_preview=True):
                self._scale_texture_file(layer_path)

    def _scale_texture_file(self, layer_path: str) -> None:
        """Scale one texture file to map output size if it exists."""
        if not os.path.isfile(layer_path):
            self.logger.debug("Layer %s not found, skipping scaling.", layer_path)
            return

        self.logger.debug("Scaling layer %s.", layer_path)
        img = self._load_layer_image(layer_path)
        if img is None or self.map.output_size is None:
            return
        scaled = cv2.resize(
            img,
            (self.map.output_size, self.map.output_size),
            interpolation=cv2.INTER_NEAREST,
        )
        cv2.imwrite(layer_path, scaled)

    def _read_parameters(self) -> None:
        """Reads map parameters from OSM data, such as:
        - minimum and maximum coordinates
        """
        bbox = ox.utils_geo.bbox_from_point(self.coordinates, dist=self.map_rotated_size / 2)
        self.minimum_x, self.minimum_y, self.maximum_x, self.maximum_y = bbox

    def _build_osm_pipeline(self) -> None:
        """Create standalone OSM source+rasterizer pipeline for this texture run."""
        projector = LatLonProjector(
            minimum_x=self.minimum_x,
            minimum_y=self.minimum_y,
            maximum_x=self.maximum_x,
            maximum_y=self.maximum_y,
            raster_size=self.map_rotated_size,
        )
        source = OSMNXFeatureSource(
            bbox=self.new_bbox,
            custom_osm_path=self.map.custom_osm,
            use_cache=self.map.texture_settings.use_cache,
            requests_timeout=Parameters.OSM_REQUESTS_TIMEOUT,
            logger=self.logger,
        )
        rasterizer = OSMGeometryRasterizer(
            projector=projector,
            cap_style=self.cap_style,
            fields_padding=self.map.texture_settings.fields_padding,
            logger=self.logger,
        )
        self.osm_pipeline = OSMRasterPipeline(
            source=source, rasterizer=rasterizer, logger=self.logger
        )

    def info_sequence(self) -> dict[str, Any]:
        """Returns the JSON representation of the generation info for textures."""
        useful_attributes = [
            "coordinates",
            "bbox",
            "map_size",
            "rotation",
            "minimum_x",
            "minimum_y",
            "maximum_x",
            "maximum_y",
        ]
        return {attr: getattr(self, attr, None) for attr in useful_attributes}

    @monitor_performance
    def _prepare_weights(self) -> None:
        self.logger.debug("Starting preparing weights from %s layers.", len(self.layers))

        for layer in tqdm(self.layers, desc="Preparing weights", unit="layer"):
            self._generate_weights(layer)
        self.logger.debug("Prepared weights for %s layers.", len(self.layers))

    def _generate_weights(self, layer: Layer) -> None:
        """Generates weight files for textures. Each file is a numpy array of zeros and
            dtype uint8 (0-255).

        Arguments:
            layer (Layer): Layer with textures and tags.
        """
        if layer.tags is None and layer.precise_tags is None:
            size = (self.map_size, self.map_size)
        else:
            size = (self.map_rotated_size, self.map_rotated_size)
        postfix = (
            Parameters.WEIGHT_FILE_POSTFIX if not layer.exclude_weight else Parameters.PNG_EXTENSION
        )
        if layer.count == 0:
            filepaths = [os.path.join(self._weights_dir, layer.name + postfix)]
        else:
            filepaths = [
                os.path.join(self._weights_dir, layer.name + str(i).zfill(2) + postfix)
                for i in range(1, layer.count + 1)
            ]

        for filepath in filepaths:
            img = np.zeros(size, dtype=np.uint8)
            cv2.imwrite(filepath, img)

    @property
    def layers(self) -> list[Layer]:
        """Returns list of layers with textures and tags from textures.json.

        Returns:
            list[Layer]: List of layers.
        """
        return self._layers

    @layers.setter
    def layers(self, layers: list[Layer]) -> None:
        """Sets list of layers with textures and tags.

        Arguments:
            layers (list[Layer]): List of layers.
        """
        self._layers = layers

    def layers_by_priority(self) -> list[Layer]:
        """Returns list of layers sorted by priority: None priority layers are first,
        then layers are sorted by priority (descending).

        Returns:
            list[Layer]: List of layers sorted by priority.
        """
        return sorted(
            self.layers,
            key=lambda _layer: (
                _layer.priority is not None,
                -_layer.priority if _layer.priority is not None else float("inf"),
            ),
        )

    def save_road_mask(self, layer: Layer, layer_image: np.ndarray) -> None:
        """Processes road mask for the layer and saves it to the corresponding file.

        Arguments:
            layer (Layer): Layer with textures and tags.
            layer_image (np.ndarray): Layer image.
        """
        if not layer.road_texture:
            return

        roads_directory = os.path.join(self.map_directory, Parameters.ROADS_DIRECTORY)
        os.makedirs(roads_directory, exist_ok=True)
        mask_path = os.path.join(
            roads_directory,
            f"{layer.road_texture}_mask{Parameters.PNG_EXTENSION}",
        )

        cv2.imwrite(mask_path, layer_image)
        self.rotate_image(
            mask_path, self.rotation, output_height=self.map_size, output_width=self.map_size
        )

    @monitor_performance
    def draw(self) -> None:
        """Iterates over layers and fills them with polygons from OSM data."""
        layers = [layer for layer in self.layers_by_priority() if self._is_drawable_layer(layer)]
        self._prefetch_osm_data(layers)

        info_layer_data: dict[str, list[Any]] = defaultdict(list)
        cumulative_image: np.ndarray | None = None

        for layer in tqdm(layers, desc="Drawing textures", unit="layer"):
            cumulative_image = self._draw_single_layer(
                layer,
                info_layer_data,
                cumulative_image,
            )

        self._publish_info_layer_data(info_layer_data)

        if cumulative_image is not None:
            self.draw_base_layer(cumulative_image)

    def _prefetch_osm_data(self, layers: list[Layer]) -> None:
        """Prefetch unique OSM queries in parallel to reduce Overpass wait time."""
        if self.osm_pipeline is None:
            return

        tags_to_prefetch: list[dict[str, str | list[str] | bool]] = []
        for layer in layers:
            tags = self._resolve_layer_tags_for_prefetch(layer)
            if tags is not None:
                tags_to_prefetch.append(tags)

        if not tags_to_prefetch:
            return

        self.osm_pipeline.prefetch(
            tags_to_prefetch,
            max_workers=Parameters.OSM_PREFETCH_WORKERS,
        )

    def _resolve_layer_tags_for_prefetch(
        self,
        layer: Layer,
    ) -> dict[str, str | list[str] | bool] | None:
        """Resolve tags for prefetch without emitting per-layer debug logs."""
        if self.map.texture_settings.use_precise_tags and layer.precise_tags:
            return layer.precise_tags
        return layer.tags

    def _draw_single_layer(
        self,
        layer: Layer,
        info_layer_data: dict[str, list[Any]],
        cumulative_image: np.ndarray | None,
    ) -> np.ndarray | None:
        """Draw one layer and update cumulative mask image."""
        if self.map.texture_settings.skip_drains and layer.usage == Parameters.DRAIN:
            self.logger.debug("Skipping layer %s because of the usage.", layer.name)
            return cumulative_image

        if layer.priority == 0:
            self.logger.debug(
                "Found base layer %s. Postponing that to be the last layer drawn.", layer.name
            )
            return cumulative_image

        layer_path = layer.path(self._weights_dir)
        self.logger.debug("Drawing layer %s.", layer_path)
        layer_image = self._load_layer_image(layer_path)
        if layer_image is None:
            return cumulative_image

        if cumulative_image is None:
            self.logger.debug("First layer, creating new cumulative image.")
            cumulative_image = layer_image

        mask = cv2.bitwise_not(cumulative_image)
        self._draw_layer(layer, info_layer_data, layer_image)

        if layer.road_texture:
            self.save_road_mask(layer, layer_image)

        self._add_roads(layer, info_layer_data)

        if layer.external:
            output_image = layer_image
        else:
            output_image = cv2.bitwise_and(layer_image, mask)
            cumulative_image = cv2.bitwise_or(cumulative_image, output_image)

        cv2.imwrite(layer_path, output_image)
        self.logger.debug("Texture %s saved.", layer_path)
        return cumulative_image

    def _publish_info_layer_data(self, info_layer_data: dict[str, list[Any]]) -> None:
        """Publish drawn info-layer data into map context."""
        ctx = self.map.context
        if self.options.channel == Parameters.TEXTURE_CHANNEL_TEXTURES:
            ctx.fields = cast(list[Any], info_layer_data.get(Parameters.FIELDS, []))
            ctx.buildings = cast(
                list[list[tuple[int, int]]], info_layer_data.get(Parameters.BUILDINGS, [])
            )
            ctx.farmyards = cast(
                list[list[tuple[int, int]]], info_layer_data.get(Parameters.FARMYARDS, [])
            )
            ctx.forest = cast(
                list[list[tuple[int, int]]], info_layer_data.get(Parameters.FOREST, [])
            )
            ctx.water = cast(list[list[tuple[int, int]]], info_layer_data.get(Parameters.WATER, []))
            ctx.roads_polylines = cast(
                list[dict[str, Any]], info_layer_data.get(Parameters.ROADS_POLYLINES, [])
            )
            ctx.electricity_lines_polylines = cast(
                list[dict[str, Any]],
                info_layer_data.get(Parameters.ELECTRICITY_LINES_POLYLINES, []),
            )
            ctx.electricity_poles_points = cast(
                list[dict[str, Any]],
                info_layer_data.get(Parameters.ELECTRICITY_POLES_POINTS, []),
            )
            ctx.water_polylines = cast(
                list[dict[str, Any]], info_layer_data.get(Parameters.WATER_POLYLINES, [])
            )
            self.logger.debug(
                "Map context populated: %d fields, %d buildings, %d roads, %d electricity lines, %d electricity poles, %d water polylines.",
                len(ctx.fields),
                len(ctx.buildings),
                len(ctx.roads_polylines),
                len(ctx.electricity_lines_polylines),
                len(ctx.electricity_poles_points),
                len(ctx.water_polylines),
            )
            return

        if self.options.channel == Parameters.TEXTURE_CHANNEL_EXTENDED:
            shift_pixels = self._extended_channel_shift_pixels()
            ctx.extended_roads_polylines = self._shift_polyline_entries(
                cast(list[dict[str, Any]], info_layer_data.get(Parameters.ROADS_POLYLINES, [])),
                shift_pixels,
            )
            ctx.extended_electricity_lines_polylines = self._shift_polyline_entries(
                cast(
                    list[dict[str, Any]],
                    info_layer_data.get(Parameters.ELECTRICITY_LINES_POLYLINES, []),
                ),
                shift_pixels,
            )
            ctx.extended_electricity_poles_points = self._shift_point_entries(
                cast(
                    list[dict[str, Any]],
                    info_layer_data.get(Parameters.ELECTRICITY_POLES_POINTS, []),
                ),
                shift_pixels,
            )
            self.logger.debug(
                "Extended context populated: %d roads, %d electricity lines, %d electricity poles (shift=%d).",
                len(ctx.extended_roads_polylines),
                len(ctx.extended_electricity_lines_polylines),
                len(ctx.extended_electricity_poles_points),
                shift_pixels,
            )
            return

        ctx.background_water = cast(
            list[list[tuple[int, int]]], info_layer_data.get(Parameters.WATER, [])
        )
        ctx.background_water_polylines = cast(
            list[dict[str, Any]], info_layer_data.get(Parameters.WATER_POLYLINES, [])
        )
        self.logger.debug(
            "Background context populated: %d water polygons, %d water polylines.",
            len(ctx.background_water),
            len(ctx.background_water_polylines),
        )

    def _extended_channel_shift_pixels(self) -> int:
        """Return center-alignment shift from extended to base rotated canvas."""
        delta_rotated = self.map_rotated_size - self.map.rotated_size
        if delta_rotated <= 0:
            return 0
        return int(round((delta_rotated / 2) * self.map.size_scale))

    def _shift_polyline_entries(
        self,
        entries: list[dict[str, Any]],
        shift_pixels: int,
    ) -> list[dict[str, Any]]:
        """Shift polyline entry coordinates by a fixed pixel delta along both axes."""
        if shift_pixels == 0:
            return [dict(entry) for entry in entries if isinstance(entry, dict)]

        shifted_entries: list[dict[str, Any]] = []
        for entry in entries:
            if not isinstance(entry, dict):
                continue

            points = entry.get(Parameters.POINTS)
            shifted_points: list[tuple[int, int]] = []
            if isinstance(points, list):
                for point in points:
                    if not isinstance(point, (list, tuple)) or len(point) < 2:
                        continue
                    shifted_points.append(
                        (int(point[0]) - shift_pixels, int(point[1]) - shift_pixels)
                    )

            shifted_entry = dict(entry)
            shifted_entry[Parameters.POINTS] = shifted_points
            shifted_entries.append(shifted_entry)
        return shifted_entries

    def _shift_point_entries(
        self,
        entries: list[dict[str, Any]],
        shift_pixels: int,
    ) -> list[dict[str, Any]]:
        """Shift point entry coordinates by a fixed pixel delta along both axes."""
        if shift_pixels == 0:
            return [dict(entry) for entry in entries if isinstance(entry, dict)]

        shifted_entries: list[dict[str, Any]] = []
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            point = entry.get(Parameters.POINT)
            if not isinstance(point, (list, tuple)) or len(point) < 2:
                continue

            shifted_entry = dict(entry)
            shifted_entry[Parameters.POINT] = (
                int(point[0]) - shift_pixels,
                int(point[1]) - shift_pixels,
            )
            shifted_entries.append(shifted_entry)
        return shifted_entries

    def _draw_layer(
        self, layer: Layer, info_layer_data: dict[str, list[Any]], layer_image: np.ndarray
    ) -> None:
        """Draws polygons from OSM data on the layer image and updates the info layer data.

        Arguments:
            layer (Layer): Layer with textures and tags.
            info_layer_data (dict[list[list[int]]]): Dictionary to store info layer data.
            layer_image (np.ndarray): Layer image.
        """
        tags = self._resolve_layer_tags(layer)
        if tags is None:
            return

        if self.osm_pipeline is None:
            raise RuntimeError("OSM pipeline is not initialized. Call process() first.")

        is_fields = layer.info_layer == Parameters.FIELDS
        for polygon, holes, osm_tags, geom_type in self.osm_pipeline.polygons(
            tags, layer.width, is_fields
        ):
            if not len(polygon) > 2:
                self.logger.debug("Skipping polygon with less than 3 points.")
                continue
            self._append_info_layer_entry(
                layer, polygon, holes, osm_tags, geom_type, info_layer_data
            )
            self._fill_layer_polygon(layer, layer_image, polygon, holes)

        self._add_points(layer, tags, info_layer_data, layer_image)

    def _resolve_layer_tags(self, layer: Layer) -> dict[str, str | list[str] | bool] | None:
        """Resolve OSM tags for a layer, honoring precise-tags setting."""
        tags = layer.tags
        if self.map.texture_settings.use_precise_tags and layer.precise_tags:
            self.logger.debug(
                "Using precise tags: %s for layer %s.", layer.precise_tags, layer.name
            )
            tags = layer.precise_tags
        return tags

    def _append_info_layer_entry(
        self,
        layer: Layer,
        polygon: np.ndarray,
        holes: list[np.ndarray],
        osm_tags: dict[str, Any],
        geom_type: str,
        info_layer_data: dict[str, list[Any]],
    ) -> None:
        """Append a polygon entry to info layer collection if layer requires it."""
        if not layer.info_layer:
            return

        if layer.info_layer == Parameters.WATER and geom_type != "Polygon":
            # Skip buffered line artifacts for water polygon info.
            return

        scaled_points = self.np_array_to_scaled_points(polygon, self.map.size_scale)
        scaled_holes = [self.np_array_to_scaled_points(hole, self.map.size_scale) for hole in holes]
        entry: Any
        if layer.info_layer == Parameters.FIELDS:
            entry = {
                Parameters.POINTS: scaled_points,
                Parameters.IS_FIELD: True,
            }
            if scaled_holes:
                entry[Parameters.HOLES] = scaled_holes
            if layer.save_tags:
                entry[Parameters.TAGS] = osm_tags
        elif layer.save_tags:
            entry = {Parameters.POINTS: scaled_points, Parameters.TAGS: osm_tags}
        else:
            entry = scaled_points

        info_layer_data[layer.info_layer].append(entry)

    def _fill_layer_polygon(
        self,
        layer: Layer,
        layer_image: np.ndarray,
        polygon: np.ndarray,
        holes: list[np.ndarray],
    ) -> None:
        """Fill one polygon into layer image if layer is visible."""
        if layer.invisible:
            return
        try:
            cv2.fillPoly(layer_image, [polygon], color=255)
            if holes:
                cv2.fillPoly(layer_image, holes, color=0)
        except Exception as e:
            self.logger.warning("Error drawing polygon: %s.", repr(e))

    def _add_roads(self, layer: Layer, info_layer_data: dict[str, list[Any]]) -> None:
        """Adds roads to the info layer data.

        Arguments:
            layer (Layer): Layer with textures and tags.
            info_layer_data (dict[list[list[int]]]): Dictionary to store info layer data.
        """
        linestring_infolayers = [
            Parameters.ROADS,
            Parameters.WATER,
            Parameters.ELECTRICITY_LINES,
        ]

        if layer.info_layer in linestring_infolayers:
            if self.osm_pipeline is None:
                raise RuntimeError("OSM pipeline is not initialized. Call process() first.")

            tags = self._resolve_layer_tags(layer)
            if tags is None:
                return

            for linestring, osm_tags in self.osm_pipeline.linestrings(tags):
                linestring = self.scale_point_tuples(linestring, self.map.size_scale)
                linestring_entry = {
                    Parameters.POINTS: linestring,
                    Parameters.TAGS: osm_tags if layer.save_tags else str(tags),
                    Parameters.WIDTH: layer.width,
                    Parameters.ROAD_TEXTURE: layer.road_texture,
                    Parameters.ELECTRICITY_CATEGORY: layer.electricity_category,
                    Parameters.ELECTRICITY_RADIUS: layer.electricity_radius,
                }
                info_layer_data[f"{layer.info_layer}_polylines"].append(linestring_entry)

    def _add_points(
        self,
        layer: Layer,
        tags: dict[str, str | list[str] | bool],
        info_layer_data: dict[str, list[Any]],
        layer_image: np.ndarray,
    ) -> None:
        """Adds point features to info layer data and optionally draws them."""
        if not layer.info_layer:
            return

        if self.osm_pipeline is None:
            raise RuntimeError("OSM pipeline is not initialized. Call process() first.")

        for point, osm_tags in self.osm_pipeline.points(tags):
            scaled_point = self.scale_point_tuples([point], self.map.size_scale)[0]
            point_entry = {
                Parameters.POINT: scaled_point,
                Parameters.TAGS: osm_tags if layer.save_tags else str(tags),
            }
            info_layer_data[f"{layer.info_layer}_points"].append(point_entry)

            if layer.invisible:
                continue

            radius = max(1, int(layer.width or 1))
            try:
                cv2.circle(layer_image, point, radius=radius, color=255, thickness=-1)
            except Exception as e:
                self.logger.warning("Error drawing point: %s.", repr(e))

    @monitor_performance
    def dissolve(self) -> None:
        """Dissolves textures of the layers with tags into sublayers for them to look more
        natural in the game.
        Iterates over all layers with tags and reads the first texture, checks if the file
        contains any non-zero values (255), splits those non-values between different weight
        files of the corresponding layer and saves the changes to the files.
        """
        for layer in tqdm(self.layers, desc="Dissolving textures", unit="layer"):
            self.dissolve_layer(layer)

    def dissolve_layer(self, layer: Layer) -> None:
        """Dissolves texture of the layer into sublayers."""
        if not layer.tags:
            self.logger.debug("Layer %s has no tags, there's nothing to dissolve.", layer.name)
            return
        layer_path = layer.path(self._weights_dir)
        layer_paths = layer.paths(self._weights_dir)

        if len(layer_paths) < 2:
            self.logger.debug("Layer %s has only one texture, skipping.", layer.name)
            return

        self.logger.debug("Dissolving layer from %s to %s.", layer_path, layer_paths)
        layer_image = self._load_layer_image(layer_path)
        if layer_image is None:
            self.logger.debug("Layer %s image not found, skipping.", layer.name)
            return

        if not self._has_non_zero_pixels(layer_image):
            self.logger.debug(
                "Layer %s does not contain any non-zero values, skipping.", layer.name
            )
            return

        cv2.imwrite(layer.path_preview(self._weights_dir), layer_image.copy())
        sublayers = self._build_dissolved_sublayers(layer_image, layer.count)
        self._write_sublayers(sublayers, layer_paths)

        self.logger.debug("Dissolved layer %s.", layer.name)

    @staticmethod
    def _has_non_zero_pixels(image: np.ndarray) -> bool:
        """Return whether an image contains at least one non-zero pixel."""
        return bool(np.any(image > 0))

    def _build_dissolved_sublayers(self, layer_image: np.ndarray, count: int) -> list[np.ndarray]:
        """Split non-zero pixels randomly into count binary sublayers."""
        mask = layer_image > 0
        random_assignment = np.random.randint(0, count, size=layer_image.shape)
        return [
            np.where(mask & (random_assignment == idx), 255, 0).astype(np.uint8)
            for idx in range(count)
        ]

    @staticmethod
    def _write_sublayers(sublayers: list[np.ndarray], layer_paths: list[str]) -> None:
        """Write generated dissolved sublayers to disk paths."""
        for sublayer, sublayer_path in zip(sublayers, layer_paths):
            cv2.imwrite(sublayer_path, sublayer)

    def draw_base_layer(self, cumulative_image: np.ndarray) -> None:
        """Draws base layer and saves it into the png file.
        Base layer is the last layer to be drawn, it fills the remaining area of the map.

        Arguments:
            cumulative_image (np.ndarray): Cumulative image with all layers.
        """
        base_layer = self.get_base_layer()
        if base_layer is not None:
            layer_path = base_layer.path(self._weights_dir)
            self.logger.debug("Drawing base layer %s.", layer_path)
            img = cv2.bitwise_not(cumulative_image)
            cv2.imwrite(layer_path, img)
            self.logger.debug("Base texture %s saved.", layer_path)

    @monitor_performance
    def previews(self) -> list[str]:
        """Invokes methods to generate previews. Returns list of paths to previews.

        Returns:
            list[str]: List of paths to previews.
        """
        preview_paths = []
        preview_paths.append(self._osm_preview())
        return preview_paths

    def _osm_preview(self) -> str:
        """Merges layers into one image and saves it into the png file.

        Returns:
            str: Path to the preview.
        """
        scaling_factor = Parameters.PREVIEW_MAXIMUM_SIZE / self.map_size

        preview_size = (
            int(self.map_size * scaling_factor),
            int(self.map_size * scaling_factor),
        )
        self.logger.debug(
            "Scaling factor: %s. Preview size: %s.",
            scaling_factor,
            preview_size,
        )

        active_layers = [
            layer
            for layer in self.layers
            if layer.tags is not None or layer.precise_tags is not None
        ]
        self.logger.debug("Following layers have tag textures: %s.", len(active_layers))

        images = [
            cv2.resize(image, preview_size)
            for layer in active_layers
            for image in [
                cv2.imread(layer.get_preview_or_path(self._weights_dir), cv2.IMREAD_UNCHANGED)
            ]
            if image is not None
        ]
        colors = [layer.color for layer in active_layers]
        color_images = []
        for img, color in zip(images, colors):
            color_img = np.zeros((img.shape[0], img.shape[1], 3), dtype=np.uint8)
            color_img[img > 0] = cast(tuple[int, int, int] | list[int], color)
            color_images.append(color_img)
        if color_images:
            merged = cast(np.ndarray, np.sum(color_images, axis=0, dtype=np.uint8))
        else:
            merged = np.zeros((preview_size[1], preview_size[0], 3), dtype=np.uint8)
        self.logger.debug(
            "Merged layers into one image. Shape: %s, dtype: %s.",
            merged.shape,
            merged.dtype,
        )
        preview_path = os.path.join(
            self.previews_directory,
            Parameters.TEXTURES_OSM_PREVIEW_FILENAME,
        )

        cv2.imwrite(preview_path, merged)
        self.logger.debug("Preview saved to %s.", preview_path)
        return preview_path
