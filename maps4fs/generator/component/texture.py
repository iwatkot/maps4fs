"""Module with Texture class for generating textures for the map using OSM data."""

from __future__ import annotations

import json
import os
import shutil
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Literal

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
    channel: Literal["textures", "background"] = "textures"
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
        self._weights_dir = self.game.weights_dir_path
        self.procedural_dir = os.path.join(self._weights_dir, "masks")
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
        if self.options.channel == "textures":
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
            border = layer.border
            if not border:
                continue

            self.transfer_border(layer_image, base_layer_image, border)  # type: ignore

            cv2.imwrite(layer.path(self._weights_dir), layer_image)  # type: ignore
            self.logger.debug("Borders added to layer %s.", layer.name)

        if base_layer_image is not None:
            cv2.imwrite(base_layer.path(self._weights_dir), base_layer_image)  # type: ignore

    def copy_procedural(self) -> None:
        """Copies some of the textures to use them as mask for procedural generation.
        Creates an empty blockmask if it does not exist."""
        blockmask_path = os.path.join(self.procedural_dir, "BLOCKMASK.png")
        if not os.path.isfile(blockmask_path):
            self.logger.debug("BLOCKMASK.png not found, creating an empty file.")
            img = np.zeros((self.scaled_size, self.scaled_size), dtype=np.uint8)
            cv2.imwrite(blockmask_path, img)

        pg_layers_by_type = defaultdict(list)
        for layer in self.layers:
            if layer.procedural:
                # Get path to the original file.
                texture_path = layer.get_preview_or_path(self._weights_dir)
                for procedural_layer_name in layer.procedural:
                    pg_layers_by_type[procedural_layer_name].append(texture_path)

        if not pg_layers_by_type:
            self.logger.debug("No procedural layers found.")
            return

        for procedural_layer_name, texture_paths in pg_layers_by_type.items():
            procedural_save_path = os.path.join(self.procedural_dir, f"{procedural_layer_name}.png")
            if len(texture_paths) > 1:
                # If there are more than one texture, merge them.
                merged_texture = np.zeros((self.scaled_size, self.scaled_size), dtype=np.uint8)
                for texture_path in texture_paths:
                    texture = cv2.imread(texture_path, cv2.IMREAD_UNCHANGED)
                    merged_texture[texture == 255] = 255
                cv2.imwrite(procedural_save_path, merged_texture)
                self.logger.debug(
                    "Procedural file %s merged from %s textures.",
                    procedural_save_path,
                    len(texture_paths),
                )
            elif len(texture_paths) == 1:
                # Otherwise, copy the texture.
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
            if layer.merge_into:
                target_layer = self.get_layer_by_name(layer.merge_into)
                if target_layer:
                    target_layer_image = cv2.imread(
                        target_layer.path(self._weights_dir), cv2.IMREAD_UNCHANGED
                    )
                    layer_image = cv2.imread(layer.path(self._weights_dir), cv2.IMREAD_UNCHANGED)
                    if target_layer_image is not None and layer_image is not None:
                        if target_layer_image.shape != layer_image.shape:
                            self.logger.warning(
                                "Layer %s and target layer %s have different shapes, skipping merge.",
                                layer.name,
                                target_layer.name,
                            )
                            continue
                        target_layer_image = cv2.add(target_layer_image, layer_image)
                        cv2.imwrite(target_layer.path(self._weights_dir), target_layer_image)
                    self.logger.debug("Merged layer %s into %s.", layer.name, target_layer.name)

                    # Clear the content of the layer which have merge_into property.
                    cv2.imwrite(layer.path(self._weights_dir), np.zeros_like(layer_image))
                    self.logger.debug("Cleared layer %s.", layer.name)

    @monitor_performance
    def rotate_textures(self) -> None:
        """Rotates textures of the layers which have tags."""
        if self.rotation:
            # Iterate over the layers which have tags and rotate them.
            for layer in tqdm(self.layers, desc="Rotating textures", unit="layer"):
                if layer.tags or layer.precise_tags:
                    self.logger.debug("Rotating layer %s.", layer.name)
                    layer_paths = layer.paths(self._weights_dir)
                    layer_paths += [layer.path_preview(self._weights_dir)]
                    for layer_path in layer_paths:
                        if os.path.isfile(layer_path):
                            self.rotate_image(
                                layer_path,
                                self.rotation,
                                output_height=self.map_size,
                                output_width=self.map_size,
                            )
                else:
                    self.logger.debug(
                        "Skipping rotation of layer %s because it has no tags.", layer.name
                    )

    @monitor_performance
    def scale_textures(self) -> None:
        """Resizes all the textures to the map output size."""
        if not self.map.output_size:
            self.logger.debug("No output size defined, skipping scaling.")
            return

        for layer in tqdm(self.layers, desc="Scaling textures", unit="layer"):
            layer_paths = layer.paths(self._weights_dir)
            layer_paths += [layer.path_preview(self._weights_dir)]

            for layer_path in layer_paths:
                if os.path.isfile(layer_path):
                    self.logger.debug("Scaling layer %s.", layer_path)
                    img = cv2.imread(layer_path, cv2.IMREAD_UNCHANGED)
                    img = cv2.resize(
                        img,  # type: ignore
                        (self.map.output_size, self.map.output_size),
                        interpolation=cv2.INTER_NEAREST,
                    )
                    cv2.imwrite(layer_path, img)
                else:
                    self.logger.debug("Layer %s not found, skipping scaling.", layer_path)

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
            requests_timeout=10,
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
    def _prepare_weights(self):
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
        postfix = "_weight.png" if not layer.exclude_weight else ".png"
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

        roads_directory = os.path.join(self.map_directory, "roads")
        os.makedirs(roads_directory, exist_ok=True)
        mask_path = os.path.join(roads_directory, f"{layer.road_texture}_mask.png")

        cv2.imwrite(mask_path, layer_image)
        self.rotate_image(
            mask_path, self.rotation, output_height=self.map_size, output_width=self.map_size
        )

    @monitor_performance
    def draw(self) -> None:
        """Iterates over layers and fills them with polygons from OSM data."""
        layers = self.layers_by_priority()
        layers = [
            layer for layer in layers if layer.tags is not None or layer.precise_tags is not None
        ]

        cumulative_image = None

        # Dictionary to store info layer data.
        # Key is a layer.info_layer, value is a list of polygon points as tuples (x, y).
        info_layer_data: dict[str, list[list[int]]] = defaultdict(list)

        for layer in tqdm(layers, desc="Drawing textures", unit="layer"):
            if self.map.texture_settings.skip_drains and layer.usage == "drain":
                self.logger.debug("Skipping layer %s because of the usage.", layer.name)
                continue
            if layer.priority == 0:
                self.logger.debug(
                    "Found base layer %s. Postponing that to be the last layer drawn.", layer.name
                )
                continue
            layer_path = layer.path(self._weights_dir)
            self.logger.debug("Drawing layer %s.", layer_path)
            layer_image = cv2.imread(layer_path, cv2.IMREAD_UNCHANGED)

            if cumulative_image is None:
                self.logger.debug("First layer, creating new cumulative image.")
                cumulative_image = layer_image

            mask = cv2.bitwise_not(cumulative_image)  # type: ignore
            self._draw_layer(layer, info_layer_data, layer_image)  # type: ignore

            if layer.road_texture:
                self.save_road_mask(layer, layer_image)  # type: ignore

            self._add_roads(layer, info_layer_data)

            if not layer.external:
                output_image = cv2.bitwise_and(layer_image, mask)  # type: ignore
                cumulative_image = cv2.bitwise_or(cumulative_image, output_image)  # type: ignore
            else:
                output_image = layer_image  # type: ignore

            cv2.imwrite(layer_path, output_image)
            self.logger.debug("Texture %s saved.", layer_path)

        # Populate map.context so later components consume in-memory data only.
        ctx = self.map.context
        if self.options.channel == "textures":
            ctx.fields = info_layer_data.get("fields", [])  # type: ignore[assignment]
            ctx.buildings = info_layer_data.get("buildings", [])  # type: ignore[assignment]
            ctx.farmyards = info_layer_data.get("farmyards", [])  # type: ignore[assignment]
            ctx.forest = info_layer_data.get("forest", [])  # type: ignore[assignment]
            ctx.water = info_layer_data.get("water", [])  # type: ignore[assignment]
            ctx.roads_polylines = info_layer_data.get("roads_polylines", [])  # type: ignore[assignment]
            ctx.water_polylines = info_layer_data.get("water_polylines", [])  # type: ignore[assignment]
            self.logger.debug(
                "Map context populated: %d fields, %d buildings, %d roads, %d water polylines.",
                len(ctx.fields),
                len(ctx.buildings),
                len(ctx.roads_polylines),
                len(ctx.water_polylines),
            )
        else:
            # Background texture: populate background-specific context fields.
            ctx.background_water = info_layer_data.get("water", [])  # type: ignore[assignment]
            ctx.background_water_polylines = info_layer_data.get("water_polylines", [])  # type: ignore[assignment]
            self.logger.debug(
                "Background context populated: %d water polygons, %d water polylines.",
                len(ctx.background_water),
                len(ctx.background_water_polylines),
            )

        if cumulative_image is not None:
            self.draw_base_layer(cumulative_image)

    def _draw_layer(
        self, layer: Layer, info_layer_data: dict[str, list[list[int]]], layer_image: np.ndarray
    ) -> None:
        """Draws polygons from OSM data on the layer image and updates the info layer data.

        Arguments:
            layer (Layer): Layer with textures and tags.
            info_layer_data (dict[list[list[int]]]): Dictionary to store info layer data.
            layer_image (np.ndarray): Layer image.
        """
        tags = layer.tags
        if self.map.texture_settings.use_precise_tags:
            if layer.precise_tags:
                self.logger.debug(
                    "Using precise tags: %s for layer %s.", layer.precise_tags, layer.name
                )
                tags = layer.precise_tags

        if tags is None:
            return

        if self.osm_pipeline is None:
            raise RuntimeError("OSM pipeline is not initialized. Call process() first.")

        is_fields = layer.info_layer == "fields"
        for polygon, osm_tags, geom_type in self.osm_pipeline.polygons(
            tags, layer.width, is_fields
        ):
            if not len(polygon) > 2:
                self.logger.debug("Skipping polygon with less than 3 points.")
                continue
            if layer.info_layer:
                # For the water info layer, skip linestring-buffered entries — they are
                # handled by the separate line_surface_water mesh (water_resources_line_surface).
                if layer.info_layer == "water" and geom_type != "Polygon":
                    pass
                else:
                    if layer.save_tags:
                        entry = {
                            Parameters.POINTS: self.np_to_polygon_points(polygon),  # type: ignore
                            Parameters.TAGS: osm_tags,
                        }
                    else:
                        entry = self.np_to_polygon_points(polygon)  # type: ignore
                    info_layer_data[layer.info_layer].append(entry)  # type: ignore
            if not layer.invisible:
                try:
                    cv2.fillPoly(layer_image, [polygon], color=255)  # type: ignore
                except Exception as e:
                    self.logger.warning("Error drawing polygon: %s.", repr(e))
                    continue

    def _add_roads(self, layer: Layer, info_layer_data: dict[str, list[list[int]]]) -> None:
        """Adds roads to the info layer data.

        Arguments:
            layer (Layer): Layer with textures and tags.
            info_layer_data (dict[list[list[int]]]): Dictionary to store info layer data.
        """
        linestring_infolayers = ["roads", "water"]

        if layer.info_layer in linestring_infolayers:
            if self.osm_pipeline is None:
                raise RuntimeError("OSM pipeline is not initialized. Call process() first.")

            if layer.tags is None:
                return

            for linestring, _ in self.osm_pipeline.linestrings(layer.tags):
                if self.map.size_scale is not None:
                    linestring = [  # type: ignore
                        (int(x * self.map.size_scale), int(y * self.map.size_scale))
                        for x, y in linestring
                    ]
                linestring_entry = {
                    "points": linestring,
                    "tags": str(layer.tags),
                    "width": layer.width,
                    "road_texture": layer.road_texture,
                }
                info_layer_data[f"{layer.info_layer}_polylines"].append(linestring_entry)  # type: ignore

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
        # Check if the image contains any non-zero values, otherwise continue.
        layer_image = cv2.imread(layer_path, cv2.IMREAD_UNCHANGED)
        if layer_image is None:
            self.logger.debug("Layer %s image not found, skipping.", layer.name)
            return

        # Get mask of non-zero pixels. If there are no non-zero pixels, skip the layer.
        mask = layer_image > 0
        if not np.any(mask):
            self.logger.debug(
                "Layer %s does not contain any non-zero values, skipping.", layer.name
            )
            return
        # Save the original image to use it for preview later, without combining the sublayers.
        cv2.imwrite(layer.path_preview(self._weights_dir), layer_image.copy())  # type: ignore

        # Create random assignment array for all pixels
        random_assignment = np.random.randint(0, layer.count, size=layer_image.shape)

        # Create sublayers using vectorized operations.
        sublayers = []
        for i in range(layer.count):
            # Create sublayer: 255 where (mask is True AND random_assignment == i)
            sublayer = np.where((mask) & (random_assignment == i), 255, 0).astype(np.uint8)
            sublayers.append(sublayer)

        # Save sublayers
        for sublayer, sublayer_path in zip(sublayers, layer_paths):
            cv2.imwrite(sublayer_path, sublayer)

        self.logger.debug("Dissolved layer %s.", layer.name)

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

    def np_to_polygon_points(self, np_array: np.ndarray) -> list[tuple[int, int]]:
        """Converts numpy array of polygon points to list of tuples.

        Arguments:
            np_array (np.ndarray): Numpy array of polygon points.

        Returns:
            list[tuple[int, int]]: List of tuples.
        """
        return [
            (int(x * self.map.size_scale), int(y * self.map.size_scale))
            for x, y in np_array.reshape(-1, 2)
        ]

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
            cv2.resize(
                cv2.imread(layer.get_preview_or_path(self._weights_dir), cv2.IMREAD_UNCHANGED),  # type: ignore
                preview_size,
            )
            for layer in active_layers
        ]
        colors = [layer.color for layer in active_layers]
        color_images = []
        for img, color in zip(images, colors):
            color_img = np.zeros((img.shape[0], img.shape[1], 3), dtype=np.uint8)
            color_img[img > 0] = color
            color_images.append(color_img)
        merged = np.sum(color_images, axis=0, dtype=np.uint8)
        self.logger.debug(
            "Merged layers into one image. Shape: %s, dtype: %s.",
            merged.shape,
            merged.dtype,
        )
        preview_path = os.path.join(self.previews_directory, "textures_osm.png")

        cv2.imwrite(preview_path, merged)  # type: ignore
        self.logger.debug("Preview saved to %s.", preview_path)
        return preview_path
