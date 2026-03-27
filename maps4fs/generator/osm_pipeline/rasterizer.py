"""Geometry rasterization helpers that convert OSM geometries to pixel arrays."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Generator

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely import LineString, MultiLineString, MultiPoint, Point, Polygon
from shapely.geometry import GeometryCollection, MultiPolygon

from maps4fs.generator.osm_pipeline.projector import LatLonProjector


@dataclass
class OSMGeometryRasterizer:
    """Converts OSM geometries to raster-space polygons and polylines."""

    projector: LatLonProjector
    cap_style: str
    fields_padding: int
    logger: Any

    def polygons(
        self,
        objects: gpd.GeoDataFrame,
        width: int | None,
        is_fields: bool,
    ) -> Generator[tuple[np.ndarray, list[np.ndarray], dict[str, Any], str], None, None]:
        """Yield exterior/interior polygon arrays, tags, and original geometry type."""
        for _, obj in objects.iterrows():
            geom_type = obj["geometry"].geom_type
            osm_tags = self._get_tags_from_osm_object(obj)
            try:
                polygons = self._to_polygons(obj, width)
            except Exception as exc:
                self.logger.warning("Error converting object to polygon: %s.", exc)
                continue

            if not polygons:
                continue

            for polygon in polygons:
                polygons_to_emit = [polygon]
                if is_fields and self.fields_padding > 0:
                    padded_polygons = self._extract_polygons(polygon.buffer(-self.fields_padding))
                    if not padded_polygons:
                        self.logger.debug("The padding value is too high, field will not padded.")
                    else:
                        polygons_to_emit = padded_polygons

                for polygon_to_emit in polygons_to_emit:
                    exterior, interiors = self._polygon_to_np(polygon_to_emit)
                    yield exterior, interiors, osm_tags, geom_type

    def linestrings(
        self,
        objects: gpd.GeoDataFrame,
    ) -> Generator[tuple[list[tuple[int, int]], dict[str, Any]], None, None]:
        """Yield pixel-space line point lists and tags."""
        for _, obj in objects.iterrows():
            geometry = obj["geometry"]
            osm_tags = self._get_tags_from_osm_object(obj)
            if isinstance(geometry, LineString):
                points = [self.projector.latlon_to_pixel(lat, lon) for lon, lat in geometry.coords]
                yield points, osm_tags
            elif isinstance(geometry, MultiLineString):
                for linestring in geometry.geoms:
                    points = [
                        self.projector.latlon_to_pixel(lat, lon) for lon, lat in linestring.coords
                    ]
                    yield points, osm_tags

    def points(
        self,
        objects: gpd.GeoDataFrame,
    ) -> Generator[tuple[tuple[int, int], dict[str, Any]], None, None]:
        """Yield pixel-space points and tags."""
        for _, obj in objects.iterrows():
            geometry = obj["geometry"]
            osm_tags = self._get_tags_from_osm_object(obj)
            if isinstance(geometry, Point):
                yield self.projector.latlon_to_pixel(geometry.y, geometry.x), osm_tags
            elif isinstance(geometry, MultiPoint):
                for point in geometry.geoms:
                    yield self.projector.latlon_to_pixel(point.y, point.x), osm_tags

    def _to_polygons(self, obj: pd.core.series.Series, width: int | None) -> list[Polygon]:
        geometry = obj["geometry"]
        if isinstance(geometry, Polygon):
            return [self._polygon_to_pixel_coordinates(geometry)]
        if isinstance(geometry, MultiPolygon):
            return [self._polygon_to_pixel_coordinates(poly) for poly in geometry.geoms]
        if isinstance(geometry, LineString):
            return self._extract_polygons(self._sequence_to_pixel(geometry, width))
        if isinstance(geometry, Point):
            return self._extract_polygons(self._sequence_to_pixel(geometry, width))

        self.logger.debug("Geometry type %s not supported.", geometry.geom_type)
        return []

    def _polygon_to_np(self, polygon: Polygon) -> tuple[np.ndarray, list[np.ndarray]]:
        coords = list(polygon.exterior.coords)
        points = np.array(coords, np.int32).reshape((-1, 1, 2))
        interior_points = [
            np.array(list(interior.coords), np.int32).reshape((-1, 1, 2))
            for interior in polygon.interiors
        ]
        return points, interior_points

    def _polygon_to_pixel_coordinates(self, polygon: Polygon) -> Polygon:
        exterior_coords_pixel = [
            self.projector.latlon_to_pixel(lat, lon) for lon, lat in list(polygon.exterior.coords)
        ]
        interior_coords_pixel = [
            [self.projector.latlon_to_pixel(lat, lon) for lon, lat in list(interior.coords)]
            for interior in polygon.interiors
        ]
        return Polygon(exterior_coords_pixel, holes=interior_coords_pixel)

    def _linestring_to_pixel_coordinates(self, linestring: LineString) -> LineString:
        coords_pixel = [
            self.projector.latlon_to_pixel(lat, lon) for lon, lat in list(linestring.coords)
        ]
        return LineString(coords_pixel)

    def _point_to_pixel_coordinates(self, point: Point) -> Point:
        x, y = self.projector.latlon_to_pixel(point.y, point.x)
        return Point(x, y)

    def _sequence_to_pixel(self, geometry: LineString | Point, width: int | None) -> Any:
        if isinstance(geometry, LineString):
            geometry = self._linestring_to_pixel_coordinates(geometry)
        elif isinstance(geometry, Point):
            geometry = self._point_to_pixel_coordinates(geometry)

        buffered = geometry.buffer(width if width else 0, cap_style=self.cap_style)
        return buffered

    @staticmethod
    def _extract_polygons(geometry: Any) -> list[Polygon]:
        if isinstance(geometry, Polygon):
            return [geometry]
        if isinstance(geometry, MultiPolygon):
            return [poly for poly in geometry.geoms if isinstance(poly, Polygon)]
        if isinstance(geometry, GeometryCollection):
            return [poly for poly in geometry.geoms if isinstance(poly, Polygon)]
        return []

    @staticmethod
    def _get_tags_from_osm_object(obj: pd.core.series.Series) -> dict[str, Any]:
        ignored_keys = {"geometry", "osmid", "element_type", "action", "visible"}
        tags: dict[str, Any] = {}
        for key in obj.index:
            if key in ignored_keys:
                continue
            value = obj[key]
            if pd.isna(value):
                continue
            tags[key] = value
        return tags
