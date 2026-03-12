"""MapContext — in-memory store for data shared between components during generation.

Replaces both SharedSettings (DEM→I3d height scale channel) and the
info_layers/*.json files (Texture→Background/GRLE/I3d/Road/Building data channel).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class MapContext:
    """In-memory store for data shared between pipeline components.

    Populated incrementally as each component runs; later components read
    what earlier components have written.
    """

    # ---- Populated by Texture component ----
    # Polygon point lists (pixel coordinates on the scaled canvas)
    fields: list[list[tuple[int, int]]] = field(default_factory=list)
    buildings: list[list[tuple[int, int]]] = field(default_factory=list)
    farmyards: list[list[tuple[int, int]]] = field(default_factory=list)
    forest: list[list[tuple[int, int]]] = field(default_factory=list)
    water: list[list[tuple[int, int]]] = field(default_factory=list)

    # Polyline dicts: {"points": [...], "tags": "...", "width": N, "road_texture": "..."}
    roads_polylines: list[dict[str, Any]] = field(default_factory=list)
    water_polylines: list[dict[str, Any]] = field(default_factory=list)

    # Layer objects from Texture component — used by later components to query layer metadata
    # (e.g. usage, area_type, building_category).  Typed as Any to avoid circular imports.
    texture_layers: list[Any] = field(default_factory=list)

    # ---- Populated by Background component (written to context after background.json) ----
    background_water: list[list[tuple[int, int]]] = field(default_factory=list)
    background_water_polylines: list[dict[str, Any]] = field(default_factory=list)

    # ---- Populated by DEM/Background (replaces SharedSettings) ----
    height_scale_value: float | None = None
    height_scale_multiplier: float | None = None
    mesh_z_scaling_factor: float | None = None
    change_height_scale: bool = False

    # ---- Populated by DEM component ----
    dem_path: str | None = None

    # ---- Populated by Satellite component ----
    satellite_overview_path: str | None = None
    satellite_background_path: str | None = None

    # ---- Layer query helpers (mirror Texture component methods) ----

    def get_layer_by_usage(self, usage: str) -> Any | None:
        """Return the first texture layer whose usage matches *usage*."""
        for layer in self.texture_layers:
            if layer.usage == usage:
                return layer
        return None

    def get_layers_by_usage(self, usage: str) -> list[Any]:
        """Return all texture layers whose usage matches *usage*."""
        return [layer for layer in self.texture_layers if layer.usage == usage]

    def get_building_category_layers(self) -> list[Any]:
        """Return all texture layers that have a building_category set."""
        return [layer for layer in self.texture_layers if layer.building_category is not None]

    def get_area_type_layers(self) -> list[Any]:
        """Return all texture layers that have an area_type set."""
        return [layer for layer in self.texture_layers if layer.area_type is not None]

    def get_water_area_layers(self) -> list[Any]:
        """Return all texture layers marked as water areas."""
        return [layer for layer in self.texture_layers if layer.area_water]

    def get_indoor_layers(self) -> list[Any]:
        """Return all texture layers marked as indoor areas."""
        return [layer for layer in self.texture_layers if layer.indoor]
