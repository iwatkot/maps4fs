"""Preprocessor component for generation inputs."""

from __future__ import annotations

import json
import os
from typing import Any

from maps4fs.generator.component.base.component import Component
from maps4fs.generator.component.layer import Layer
from maps4fs.generator.osm import download_osm_map_by_bbox, preprocess as preprocess_osm_file
from maps4fs.generator.settings import Parameters


class Preprocessor(Component):
    """Prepare local inputs for later generation components."""

    custom_osm_filename = "custom_osm.osm"
    exclude_cut_tags = {"power": ["line", "minor_line"]}
    merge_distance = 0.35
    split_width = 4.0
    _smooth_radius_floor = 8.0
    _smooth_radius_span = 22.0

    def preprocess(self) -> None:
        """Load texture-layer metadata early for schema-driven preprocessing."""
        self.layers = self._load_layers()
        self.map.context.texture_layers = self.layers
        self.download_attempted = False
        self.download_succeeded = False
        self.download_error: str | None = None
        self.preprocessing_reports: list[dict[str, Any]] = []

    def process(self) -> None:
        """Prepare local OSM input and optionally preprocess field and forest polygons."""
        working_osm_path = self._ensure_local_osm_path()
        if working_osm_path is None:
            if self._has_enabled_usage_preprocessing():
                self.logger.warning(
                    "OSM preprocessing is enabled but no local OSM file is available. "
                    "Proceeding with the default OSM source."
                )
            return

        self._apply_usage_preprocessing(working_osm_path)

    def _load_layers(self) -> list[Layer]:
        """Load texture layers from schema without instantiating Texture."""
        custom_schema = self.map.texture_custom_schema
        if custom_schema:
            layers_schema = custom_schema
        else:
            with open(self.game.texture_schema, "r", encoding="utf-8") as file:
                layers_schema = json.load(file)

        if not isinstance(layers_schema, list):
            raise ValueError("Texture layers schema must be a list of dictionaries.")
        return [Layer.from_json(layer) for layer in layers_schema]

    def _local_custom_osm_path(self) -> str:
        """Return the working OSM path inside the map directory."""
        return os.path.join(self.map_directory, self.custom_osm_filename)

    def _ensure_local_osm_path(self) -> str | None:
        """Return a local OSM path, downloading it when configured.

        If a user-supplied custom OSM already exists, prefer the copy in the map directory so
        later preprocessing never mutates the user's original file.
        """
        local_path = self._local_custom_osm_path()
        if self.map.custom_osm:
            if os.path.isfile(local_path):
                self.map.custom_osm = local_path
            self.logger.debug("Using local OSM source: %s", self.map.custom_osm)
            return self.map.custom_osm

        if not self.map.preprocessor_settings.download_osm:
            self.logger.debug("Skipping OSM download because download_osm is disabled.")
            return None

        self.download_attempted = True
        self.logger.info("Downloading raw OSM data for bbox %s.", self.new_bbox)
        try:
            download_osm_map_by_bbox(
                self.new_bbox,
                local_path,
                timeout=Parameters.OSM_REQUESTS_TIMEOUT,
            )
        except Exception as exc:
            self.download_error = str(exc)
            self.logger.warning(
                "Failed to download raw OSM data, proceeding with the default OSM source: %s",
                exc,
            )
            return None

        self.download_succeeded = True
        self.map.custom_osm = local_path
        self.map._update_main_settings({"custom_osm": True})
        self.logger.info("Saved downloaded OSM data to %s.", local_path)
        return local_path

    def _has_enabled_usage_preprocessing(self) -> bool:
        """Return whether any usage-specific preprocessing is enabled."""
        return any(
            settings.enabled
            for settings in (
                self.map.preprocessor_settings.fields,
                self.map.preprocessor_settings.forests,
            )
        )

    def _usage_settings(self) -> dict[str, Any]:
        """Return preprocessing settings keyed by texture usage."""
        return {
            Parameters.FIELD: self.map.preprocessor_settings.fields,
            Parameters.FOREST: self.map.preprocessor_settings.forests,
        }

    def _usage_tag_filters(self, usage: str) -> list[dict[str, str | list[str] | bool]]:
        """Return OR-combined preprocess filters for the requested usage.

        Texture schema tag dictionaries are OR-combined by OSMnx across keys. The OSM
        preprocessing path expects each filter to be AND-combined within one dictionary, so we
        expand a layer like {"natural": [...], "landuse": "forest"} into two filters.
        """
        filters: list[dict[str, str | list[str] | bool]] = []
        seen: set[str] = set()

        for layer in self.layers:
            if layer.usage != usage or not layer.tags:
                continue

            for key, value in layer.tags.items():
                filter_tags = {key: value}
                filter_key = json.dumps(filter_tags, sort_keys=True, separators=(",", ":"))
                if filter_key in seen:
                    continue
                seen.add(filter_key)
                filters.append(filter_tags)

        return filters

    def _usage_collapse_tags(self, usage: str) -> dict[str, str] | None:
        """Return canonical tags for collapsed output using the first schema tag entry."""
        for layer in self.layers:
            if layer.usage != usage or not layer.tags:
                continue

            first_key, first_value = next(iter(layer.tags.items()))
            if isinstance(first_value, list):
                if not first_value:
                    return None
                return {first_key: first_value[0]}
            if isinstance(first_value, str):
                return {first_key: first_value}
            return None

        return None

    def _smooth_strength_from_radius(self, radius: float) -> float:
        """Convert the user-facing smooth radius to the internal strength scale."""
        if radius <= 0:
            return 0.0
        return max(
            0.0,
            min(1.0, (radius - self._smooth_radius_floor) / self._smooth_radius_span),
        )

    def _apply_usage_preprocessing(self, working_osm_path: str) -> None:
        """Apply usage-specific OSM preprocessing to the local OSM file."""
        for usage, usage_settings in self._usage_settings().items():
            if not usage_settings.enabled:
                continue

            usage_filters = self._usage_tag_filters(usage)
            if not usage_filters:
                self.logger.debug("No texture-schema filters found for preprocessing usage %s.", usage)
                continue

            if not any(
                [
                    usage_settings.smooth_edges,
                    usage_settings.split,
                    usage_settings.merge,
                    usage_settings.collapse,
                    usage_settings.add_holes,
                ]
            ):
                self.logger.debug(
                    "Skipping preprocessing for usage %s because all operations are disabled.",
                    usage,
                )
                continue

            smooth_strength = (
                self._smooth_strength_from_radius(usage_settings.smooth_radius)
                if usage_settings.smooth_edges
                else 0.0
            )
            split_width = self.split_width if usage_settings.split else 0.0
            merge_distance = self.merge_distance if usage_settings.merge else 0.0
            collapse_tags = (
                self._usage_collapse_tags(usage) if usage_settings.collapse else None
            )

            self.logger.info(
                "Preprocessing OSM usage %s with %d schema-derived filters.",
                usage,
                len(usage_filters),
            )
            try:
                stats = preprocess_osm_file(
                    working_osm_path,
                    working_osm_path,
                    usage_filters,
                    exclude_cut_tags=self.exclude_cut_tags,
                    smooth_strength=smooth_strength,
                    merge_distance=merge_distance,
                    split_width=split_width,
                    merge_tags=False,
                    collapse_tags=collapse_tags,
                    add_holes=usage_settings.add_holes,
                )
                self.preprocessing_reports.append(
                    {
                        "usage": usage,
                        "filters": usage_filters,
                        "collapse_tags": collapse_tags,
                        "stats": stats,
                    }
                )
            except Exception as exc:
                self.logger.warning(
                    "Failed to preprocess usage %s. Proceeding with the current local OSM file: %s",
                    usage,
                    exc,
                )
                self.preprocessing_reports.append(
                    {
                        "usage": usage,
                        "filters": usage_filters,
                        "collapse_tags": collapse_tags,
                        "error": str(exc),
                    }
                )

    def info_sequence(self) -> dict[str, Any]:
        """Return preprocessor runtime settings for generation info."""
        return {
            "download_osm": self.map.preprocessor_settings.download_osm,
            "download_attempted": self.download_attempted,
            "download_succeeded": self.download_succeeded,
            "download_error": self.download_error,
            "custom_osm": self.map.custom_osm,
            "bbox": self.new_bbox,
            "osm_preprocessing": self.preprocessing_reports,
        }