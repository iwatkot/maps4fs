"""High-level OSM extraction pipeline for texture generation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Generator

import numpy as np

from maps4fs.generator.osm_pipeline.rasterizer import OSMGeometryRasterizer
from maps4fs.generator.osm_pipeline.source import OSMFeatureSource


@dataclass
class OSMRasterPipeline:
    """Coordinates feature fetching and geometry rasterization."""

    source: OSMFeatureSource
    rasterizer: OSMGeometryRasterizer
    logger: Any

    def polygons(
        self,
        tags: dict[str, str | list[str] | bool],
        width: int | None,
        is_fields: bool,
    ) -> Generator[tuple[np.ndarray, dict[str, Any], str], None, None]:
        """Yield rasterized polygons for a tag filter."""
        objects = self.source.fetch(tags)
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
        objects = self.source.fetch(tags)
        if objects is None or objects.empty:
            self.logger.debug("No objects found for tags: %s.", tags)
            return

        self.logger.debug("Fetched %s elements for tags: %s.", len(objects), tags)
        yield from self.rasterizer.linestrings(objects)
