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
