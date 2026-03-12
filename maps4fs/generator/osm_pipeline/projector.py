"""Coordinate projection helpers for mapping lat/lon geometries onto raster space."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LatLonProjector:
    """Project WGS84 coordinates into a square pixel raster."""

    minimum_x: float
    minimum_y: float
    maximum_x: float
    maximum_y: float
    raster_size: int

    @classmethod
    def from_bbox(
        cls, bbox: tuple[float, float, float, float], raster_size: int
    ) -> "LatLonProjector":
        """Build projector from osmnx bbox tuple (west, south, east, north)."""
        minimum_x, minimum_y, maximum_x, maximum_y = bbox
        return cls(
            minimum_x=minimum_x,
            minimum_y=minimum_y,
            maximum_x=maximum_x,
            maximum_y=maximum_y,
            raster_size=raster_size,
        )

    def latlon_to_pixel(self, lat: float, lon: float) -> tuple[int, int]:
        """Convert latitude/longitude point to pixel coordinates."""
        x = int((lon - self.minimum_x) / (self.maximum_x - self.minimum_x) * self.raster_size)
        y = int((lat - self.maximum_y) / (self.minimum_y - self.maximum_y) * self.raster_size)
        return x, y
