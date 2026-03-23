"""High-level OSM extraction pipeline for texture generation."""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from threading import Lock
from typing import Any, Generator

import geopandas as gpd
import numpy as np
from tqdm import tqdm

from maps4fs.generator.constants import Paths
from maps4fs.generator.osm_pipeline.rasterizer import OSMGeometryRasterizer


@dataclass
class OSMRasterPipeline:
    """Coordinates feature fetching and geometry rasterization."""

    source: Any
    rasterizer: OSMGeometryRasterizer
    logger: Any

    def __post_init__(self) -> None:
        self._cache: dict[str, gpd.GeoDataFrame | None] = {}
        self._cache_lock = Lock()

    @staticmethod
    def _tags_key(tags: dict[str, str | list[str] | bool]) -> str:
        """Build a stable cache key for tag dictionary values."""
        return json.dumps(tags, sort_keys=True, separators=(",", ":"), ensure_ascii=True)

    def _get_or_fetch_objects(
        self, tags: dict[str, str | list[str] | bool]
    ) -> gpd.GeoDataFrame | None:
        """Get objects from cache or fetch from source and store result."""
        key = self._tags_key(tags)
        with self._cache_lock:
            if key in self._cache:
                return self._cache[key]

        objects = self.source.fetch(tags)
        with self._cache_lock:
            self._cache[key] = objects
        return objects

    def prefetch(
        self,
        tags_list: list[dict[str, str | list[str] | bool]],
        max_workers: int,
    ) -> None:
        """Fetch unique tag filters in parallel and populate cache."""
        if not tags_list:
            return

        pending_by_key: dict[str, dict[str, str | list[str] | bool]] = {}
        with self._cache_lock:
            for tags in tags_list:
                key = self._tags_key(tags)
                if key in self._cache or key in pending_by_key:
                    continue
                pending_by_key[key] = tags

        if not pending_by_key:
            return

        workers = max(1, min(max_workers, len(pending_by_key)))
        self.logger.debug(
            "Prefetching OSM data: %d unique queries with %d workers.",
            len(pending_by_key),
            workers,
        )

        with ThreadPoolExecutor(max_workers=workers) as executor:
            future_to_key = {
                executor.submit(self.source.fetch, tags): key
                for key, tags in pending_by_key.items()
            }
            with tqdm(
                total=len(future_to_key),
                desc="Prefetching OSM",
                unit="query",
                disable=Paths.TQDM_DISABLE,
            ) as progress:
                for future in as_completed(future_to_key):
                    key = future_to_key[future]
                    try:
                        objects = future.result()
                    except Exception as exc:
                        self.logger.debug("OSM prefetch failed for key %s: %s", key, exc)
                        objects = None
                    with self._cache_lock:
                        self._cache[key] = objects
                    progress.update(1)

        self.logger.debug(
            "OSM prefetch completed: %d unique tag queries with %d workers.",
            len(pending_by_key),
            workers,
        )

    def polygons(
        self,
        tags: dict[str, str | list[str] | bool],
        width: int | None,
        is_fields: bool,
    ) -> Generator[tuple[np.ndarray, dict[str, Any], str], None, None]:
        """Yield rasterized polygons for a tag filter."""
        objects = self._get_or_fetch_objects(tags)
        if objects is None or objects.empty:
            self.logger.debug("No objects found for tags: %s.", tags)
            return

        self.logger.debug("Fetched %s elements for tags: %s.", len(objects), tags)
        yield from self.rasterizer.polygons(objects, width, is_fields)

    def linestrings(
        self,
        tags: dict[str, str | list[str] | bool],
    ) -> Generator[tuple[list[tuple[int, int]], dict[str, Any]], None, None]:
        """Yield rasterized linestrings for a tag filter."""
        objects = self._get_or_fetch_objects(tags)
        if objects is None or objects.empty:
            self.logger.debug("No objects found for tags: %s.", tags)
            return

        self.logger.debug("Fetched %s elements for tags: %s.", len(objects), tags)
        yield from self.rasterizer.linestrings(objects)

    def points(
        self,
        tags: dict[str, str | list[str] | bool],
    ) -> Generator[tuple[tuple[int, int], dict[str, Any]], None, None]:
        """Yield rasterized points for a tag filter."""
        objects = self._get_or_fetch_objects(tags)
        if objects is None or objects.empty:
            self.logger.debug("No objects found for tags: %s.", tags)
            return

        self.logger.debug("Fetched %s elements for tags: %s.", len(objects), tags)
        yield from self.rasterizer.points(objects)
