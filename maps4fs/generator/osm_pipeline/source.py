"""Data source abstractions for OSM feature retrieval."""

from __future__ import annotations

import warnings
from dataclasses import dataclass
from typing import Any, Protocol

import geopandas as gpd
import osmnx as ox
from osmnx import settings as ox_settings


class OSMFeatureSource(Protocol):
    """Source contract for fetching OSM features by tag filter."""

    def fetch(self, tags: dict[str, str | list[str] | bool]) -> gpd.GeoDataFrame | None:
        """Fetch features for provided tag filter."""


@dataclass
class OSMNXFeatureSource:
    """OSM source backed by osmnx."""

    bbox: tuple[float, float, float, float]
    custom_osm_path: str | None
    use_cache: bool
    requests_timeout: int
    logger: Any

    def fetch(self, tags: dict[str, str | list[str] | bool]) -> gpd.GeoDataFrame | None:
        """Fetch matching features either from custom OSM XML or overpass."""
        ox_settings.use_cache = self.use_cache
        ox_settings.requests_timeout = self.requests_timeout

        try:
            if self.custom_osm_path is not None:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", FutureWarning)
                    return ox.features_from_xml(self.custom_osm_path, tags=tags)
            return ox.features_from_bbox(bbox=self.bbox, tags=tags)
        except Exception as exc:
            self.logger.debug("Error fetching objects for tags: %s. Error: %s.", tags, exc)
            return None
