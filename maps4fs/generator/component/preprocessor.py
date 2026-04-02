"""Preprocessor component for generation inputs."""

from __future__ import annotations

import json
import os
import shutil
from typing import Any

from maps4fs.generator.component.base.component import Component
from maps4fs.generator.component.layer import Layer
from maps4fs.generator.osm import (
    OSMTagFilter,
    append_bounds_overlays,
    check_and_fix_osm,
    download_osm_map_by_bbox,
)
from maps4fs.generator.osm import preprocess as preprocess_osm_file
from maps4fs.generator.osm import prune_osm_file
from maps4fs.generator.settings import Parameters


class Preprocessor(Component):
    """Prepare local inputs for later generation components."""

    custom_osm_filename = "custom_osm.osm"
    exclude_cut_tags: OSMTagFilter = {"power": ["line", "minor_line"]}
    merge_distance = 0.35
    split_width = 4.0
    prune_margin = 64
    _smooth_radius_floor = 8.0
    _smooth_radius_span = 22.0
    _extended_info_layers = {
        Parameters.BUILDINGS,
        Parameters.ROADS,
        Parameters.ELECTRICITY_LINES,
        Parameters.ELECTRICITY_POLES,
    }

    def preprocess(self) -> None:
        """Load texture-layer metadata early for schema-driven preprocessing."""
        self.layers = self._load_layers()
        self.map.context.texture_layers = self.layers
        self.auto_download_enabled = self.map.custom_osm is None
        self.download_attempted = False
        self.download_succeeded = False
        self.download_error: str | None = None
        self.preprocessing_reports: list[dict[str, Any]] = []
        self.pruning_report: dict[str, Any] | None = None
        self.bounds_overlay_report: dict[str, Any] | None = None
        self.has_explicit_extended_layers = any(layer.extended for layer in self.layers)
        self.download_map_size = self.map_size + Parameters.BACKGROUND_DISTANCE * 2
        download_size_multiplier = 1.5 if self.rotation else 1.0
        self.download_rotated_size = int(self.download_map_size * download_size_multiplier)
        self.download_bbox = self._download_bbox()
        self.map_prune_bbox = self._bbox_with_margin(int(self.map_rotated_size / 2))
        self.extended_prune_bbox = self._extended_bbox_with_margin()
        self.background_prune_bbox = self._bbox_with_margin(int(self.download_rotated_size / 2))

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

        backup_path = f"{working_osm_path}.preprocessor-backup"
        shutil.copyfile(working_osm_path, backup_path)
        try:
            self._apply_usage_preprocessing(working_osm_path)
            self._prune_local_osm(working_osm_path)
            self._append_bounds_overlays(working_osm_path)
            check_and_fix_osm(working_osm_path)
        except Exception as exc:
            shutil.copyfile(backup_path, working_osm_path)
            self.logger.warning(
                "Failed to finalize local OSM preprocessing. Restored the previous local OSM file: %s",
                exc,
            )
        finally:
            if os.path.isfile(backup_path):
                os.remove(backup_path)

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

    def _download_bbox(self) -> tuple[float, float, float, float]:
        """Return the OSM download bbox covering map, background, and rotation padding."""
        distance = int(self.download_rotated_size / 2)
        north, south, east, west = self.get_bbox(distance=distance)
        return west, south, east, north

    def _bbox_with_margin(self, distance: int) -> tuple[float, float, float, float]:
        """Return a bbox grown by a small prune margin."""
        north, south, east, west = self.get_bbox(distance=distance + self.prune_margin)
        return west, south, east, north

    def _extended_bbox_with_margin(self) -> tuple[float, float, float, float]:
        """Return the extended-pass bbox grown by the prune margin."""
        output_size_multiplier = 1.5 if self.rotation else 1.0
        extended_size = self.map_size + Parameters.EXTENDED_DISTANCE * 2
        extended_rotated_size = int(extended_size * output_size_multiplier)
        return self._bbox_with_margin(int(extended_rotated_size / 2))

    def _ensure_local_osm_path(self) -> str | None:
        """Return a local OSM path, downloading it when needed.

        If a user-supplied custom OSM already exists, prefer the copy in the map directory so
        later preprocessing never mutates the user's original file.
        """
        local_path = self._local_custom_osm_path()
        if self.map.custom_osm:
            if os.path.abspath(self.map.custom_osm) != os.path.abspath(local_path):
                if not os.path.isfile(local_path):
                    shutil.copyfile(self.map.custom_osm, local_path)
                self.map.custom_osm = local_path
            self.logger.debug("Using local OSM source: %s", self.map.custom_osm)
            return self.map.custom_osm

        self.download_attempted = True
        self.logger.info(
            "Downloading raw OSM data for bbox %s (map size: %s, rotated size: %s).",
            self.download_bbox,
            self.download_map_size,
            self.download_rotated_size,
        )
        try:
            download_osm_map_by_bbox(
                self.download_bbox,
                local_path,
                timeout=Parameters.OSM_REQUESTS_TIMEOUT,
            )
        except Exception as exc:
            self.download_error = str(exc)
            self.map.custom_osm = None
            self.map.update_main_settings({"custom_osm": False})
            self.logger.warning(
                "Failed to download raw OSM data, proceeding with the default OSM source: %s",
                exc,
            )
            return None

        self.download_succeeded = True
        self.map.custom_osm = local_path
        self.map.update_main_settings({"custom_osm": True})
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

    def _usage_tag_filters(self, usage: str) -> list[OSMTagFilter]:
        """Return OR-combined preprocess filters for the requested usage.

        Texture schema tag dictionaries are OR-combined by OSMnx across keys. The OSM
        preprocessing path expects each filter to be AND-combined within one dictionary, so we
        expand a layer like {"natural": [...], "landuse": "forest"} into two filters.
        """
        filters: list[OSMTagFilter] = []
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

    def _usage_process_bbox(self, usage: str) -> tuple[float, float, float, float] | None:
        """Return the bbox within which the requested usage must be rewritten."""
        if usage == Parameters.FIELD:
            return self.new_bbox
        if usage == Parameters.FOREST:
            return self.download_bbox
        return None

    @staticmethod
    def _expand_osmnx_filter(filter_tags: OSMTagFilter | None) -> list[OSMTagFilter]:
        """Expand one OSMnx tag dict into one-key OR filters."""
        if not filter_tags:
            return []
        return [{key: value} for key, value in filter_tags.items()]

    def _layer_prune_filters(self, layer: Layer) -> list[OSMTagFilter]:
        """Return conservative prune filters for one layer.

        Keep both base tags and precise tags, and preserve OSMnx OR semantics by splitting each
        tag dictionary into separate one-key filters.
        """
        filters: list[OSMTagFilter] = []
        seen: set[str] = set()

        for filter_tags in (layer.tags, layer.precise_tags):
            for expanded_filter in self._expand_osmnx_filter(filter_tags):
                filter_key = json.dumps(expanded_filter, sort_keys=True, separators=(",", ":"))
                if filter_key in seen:
                    continue
                seen.add(filter_key)
                filters.append(expanded_filter)

        return filters

    def _layer_prune_bbox(self, layer: Layer) -> tuple[float, float, float, float]:
        """Return the spatial retention bbox for one runtime layer."""
        if layer.background:
            return self.background_prune_bbox
        if layer.extended:
            return self.extended_prune_bbox
        if not self.has_explicit_extended_layers and layer.info_layer in self._extended_info_layers:
            return self.extended_prune_bbox
        return self.map_prune_bbox

    def _runtime_prune_rules(
        self,
    ) -> list[tuple[OSMTagFilter, tuple[float, float, float, float] | None]]:
        """Return deduplicated runtime filters with the widest required spatial scope."""
        rules_by_key: dict[
            str,
            tuple[int, OSMTagFilter, tuple[float, float, float, float] | None],
        ] = {}

        for layer in self.layers:
            bbox = self._layer_prune_bbox(layer)
            scope_rank = 3 if layer.background else 2 if bbox == self.extended_prune_bbox else 1
            for filter_tags in self._layer_prune_filters(layer):
                filter_key = json.dumps(filter_tags, sort_keys=True, separators=(",", ":"))
                current_rule = rules_by_key.get(filter_key)
                if current_rule is None or scope_rank > current_rule[0]:
                    rules_by_key[filter_key] = (scope_rank, filter_tags, bbox)

        return [(filter_tags, bbox) for _, filter_tags, bbox in rules_by_key.values()]

    def _prune_local_osm(self, working_osm_path: str) -> None:
        """Drop OSM primitives that will never be queried by the runtime schema."""
        runtime_rules = self._runtime_prune_rules()
        if not runtime_rules:
            self.logger.debug("Skipping local OSM pruning because no runtime filters were found.")
            return

        try:
            self.pruning_report = prune_osm_file(
                working_osm_path,
                working_osm_path,
                [filter_tags for filter_tags, _ in runtime_rules],
                spatial_filters=runtime_rules,
            )
            self.pruning_report["margin"] = self.prune_margin
            self.pruning_report["rule_count"] = len(runtime_rules)
            self.logger.info(
                "Slimmed local OSM file to %d nodes, %d ways and %d relations using %d ROI rules.",
                self.pruning_report.get("kept_nodes", 0),
                self.pruning_report.get("kept_ways", 0),
                self.pruning_report.get("kept_relations", 0),
                len(runtime_rules),
            )
        except Exception as exc:
            self.pruning_report = {"error": str(exc)}
            self.logger.warning(
                "Failed to slim local OSM file. Proceeding with the current local OSM file: %s",
                exc,
            )

    def _append_bounds_overlays(self, working_osm_path: str) -> None:
        """Append synthetic playable and background bounds overlays to the local OSM file."""
        try:
            self.bounds_overlay_report = append_bounds_overlays(
                working_osm_path,
                self.coordinates,
                map_size=self.map_size,
                background_size=self.download_map_size,
                rotation=-self.rotation,
            )
            self.logger.info(
                "Added %d bounds overlays to local OSM file %s.",
                self.bounds_overlay_report.get("created_ways", 0),
                working_osm_path,
            )
        except Exception as exc:
            self.bounds_overlay_report = {"error": str(exc)}
            self.logger.warning(
                "Failed to append bounds overlays to the local OSM file. Continuing without them: %s",
                exc,
            )

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
                self.logger.debug(
                    "No texture-schema filters found for preprocessing usage %s.", usage
                )
                continue

            if not any(
                [
                    usage_settings.smooth_edges,
                    usage_settings.split,
                    usage_settings.merge,
                    usage_settings.collapse,
                    usage_settings.add_holes,
                    usage_settings.padding > 0,
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
            collapse_tags = self._usage_collapse_tags(usage) if usage_settings.collapse else None
            padding = usage_settings.padding
            process_bbox = self._usage_process_bbox(usage)

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
                    process_bbox=process_bbox,
                    validate_input=False,
                    validate_output=False,
                    exclude_cut_tags=self.exclude_cut_tags,
                    smooth_strength=smooth_strength,
                    merge_distance=merge_distance,
                    split_width=split_width,
                    merge_tags=False,
                    collapse_tags=collapse_tags,
                    add_holes=usage_settings.add_holes,
                    shrink_distance=padding,
                )
                self.preprocessing_reports.append(
                    {
                        "usage": usage,
                        "filters": usage_filters,
                        "bbox": process_bbox,
                        "collapse_tags": collapse_tags,
                        "padding": padding,
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
                        "bbox": process_bbox,
                        "collapse_tags": collapse_tags,
                        "padding": padding,
                        "error": str(exc),
                    }
                )

    def info_sequence(self) -> dict[str, Any]:
        """Return preprocessor runtime settings for generation info."""
        return {
            "download_osm": self.auto_download_enabled,
            "download_attempted": self.download_attempted,
            "download_succeeded": self.download_succeeded,
            "download_error": self.download_error,
            "custom_osm": self.map.custom_osm,
            "bbox": self.download_bbox,
            "download_map_size": self.download_map_size,
            "download_rotated_size": self.download_rotated_size,
            "osm_preprocessing": self.preprocessing_reports,
            "osm_pruning": self.pruning_report,
            "osm_bounds_overlays": self.bounds_overlay_report,
        }
