"""OSM file validation and repair utilities."""

from __future__ import annotations

import gzip
import math
import os
import shutil
from copy import deepcopy
from dataclasses import dataclass
from typing import TypeAlias
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET

import osmnx as ox
from osmnx._errors import InsufficientResponseError
from pyproj import Transformer
from shapely.geometry import (
    GeometryCollection,
    LineString,
    MultiPolygon,
    Point,
    Polygon,
)
from shapely.geometry.base import BaseGeometry
from shapely.ops import polygonize, transform, unary_union
from shapely.validation import make_valid

# Representative tags — if the file is fundamentally broken it will fail on any of these.
OSMTagValue: TypeAlias = bool | str | list[str]
OSMTagFilter: TypeAlias = dict[str, OSMTagValue]
OSMTagFilters: TypeAlias = OSMTagFilter | list[OSMTagFilter]

_CHECK_TAGS: list[OSMTagFilter] = [
    {"highway": True},
    {"building": True},
    {"landuse": True},
    {"natural": True},
    {"waterway": True},
]

_LINEAR_TAGS = {
    "highway",
    "railway",
    "waterway",
    "barrier",
    "route",
    "power",
    "aerialway",
}

_CUT_LINEAR_TAGS = {"highway", "railway", "waterway", "barrier", "power", "aerialway"}

_POINT_HOLE_RADII: dict[tuple[str, str], float] = {
    ("natural", "tree"): 3.0,
    ("natural", "rock"): 2.0,
    ("amenity", "hunting_stand"): 1.5,
    ("power", "tower"): 8.0,
    ("power", "portal"): 4.0,
    ("power", "pole"): 1.5,
    ("power", "catenary_mast"): 1.5,
    ("man_made", "tower"): 4.0,
    ("man_made", "mast"): 3.0,
}

_OSM_API_MAP_URL = "https://api.openstreetmap.org/api/0.6/map"
_OSM_TILE_MAX_DEPTH = 10
_OSM_TILE_MIN_SPAN = 1e-6


class _OSMTooManyNodesError(RuntimeError):
    """Internal signal that the OSM API bbox request exceeded the node limit."""


@dataclass
class _WayData:
    """Internal representation of an OSM way."""

    element: ET.Element
    node_refs: list[int]
    tags: dict[str, str]


@dataclass
class _RelationData:
    """Internal representation of an OSM relation."""

    element: ET.Element
    members: list[tuple[str, int, str]]
    tags: dict[str, str]


@dataclass(frozen=True)
class _SplitterData:
    """Internal representation of a linear feature used to cut polygons."""

    geometry: LineString
    tags: dict[str, str]
    round_start: bool = False
    round_end: bool = False


@dataclass(frozen=True)
class _PointHoleData:
    """Internal representation of a point obstacle that should carve a hole."""

    geometry: Point
    radius: float
    tags: dict[str, str]


@dataclass(frozen=True)
class _TargetPolygonData:
    """Target polygon plus the tags that should survive preprocessing."""

    geometry: Polygon
    tags: dict[str, str]
    merge_key: tuple[tuple[str, str], ...]
    target_keys: tuple[str, ...]


@dataclass(frozen=True)
class _ProcessedPolygonData:
    """Processed polygon paired with its output tags."""

    geometry: Polygon
    tags: dict[str, str]


def check_osm_file(file_path: str) -> bool:
    """Try to parse the OSM file with OSMnx using representative tag queries.

    Arguments:
        file_path (str): Path to the OSM file.

    Returns:
        bool: True if the file is valid, False otherwise.
    """
    for tag in _CHECK_TAGS:
        try:
            ox.features_from_xml(file_path, tags=tag)
        except InsufficientResponseError:
            continue
        except Exception:  # pylint: disable=W0718
            return False
    return True


def fix_osm_file(input_file_path: str, output_file_path: str | None = None) -> tuple[bool, int]:
    """Fix an OSM file by removing <relation> nodes and nodes with action='delete'.

    Arguments:
        input_file_path (str): Path to the input OSM file.
        output_file_path (str | None): Path to save the fixed file. Defaults to overwrite input.

    Returns:
        tuple[bool, int]: (file_is_valid_after_fix, number_of_removed_elements)
    """
    broken_entries = ["relation", ".//*[@action='delete']"]
    output_file_path = output_file_path or input_file_path

    tree = ET.parse(input_file_path)
    root = tree.getroot()

    fixed_errors = 0
    for entry in broken_entries:
        for element in root.findall(entry):
            root.remove(element)
            fixed_errors += 1

    tree.write(output_file_path)
    result = check_osm_file(output_file_path)

    return result, fixed_errors


def check_and_fix_osm(
    custom_osm: str | None, save_directory: str | None = None, output_name: str = "custom_osm.osm"
) -> None:
    """Validate and, if necessary, repair a custom OSM file.

    Arguments:
        custom_osm (str | None): Path to the custom OSM file. No-op if None.
        save_directory (str | None): Directory to copy the (fixed) file into.
        output_name (str): Filename for the copy saved to save_directory.

    Raises:
        FileNotFoundError: If the custom OSM file does not exist.
        ValueError: If the file is invalid and cannot be fixed.
    """
    if not custom_osm:
        return None
    if not os.path.isfile(custom_osm):
        raise FileNotFoundError(f"Custom OSM file {custom_osm} does not exist.")

    osm_is_valid = check_osm_file(custom_osm)
    if not osm_is_valid:
        fixed, _ = fix_osm_file(custom_osm)
        if not fixed:
            raise ValueError(f"Custom OSM file {custom_osm} is not valid and cannot be fixed.")

    if save_directory:
        output_path = os.path.join(save_directory, output_name)
        shutil.copyfile(custom_osm, output_path)

    return None


def _normalize_target_filters(tags: OSMTagFilters) -> list[OSMTagFilter]:
    """Return a normalized non-empty list of target filters."""
    if isinstance(tags, dict):
        if not tags:
            raise ValueError("At least one tag must be provided for preprocessing.")
        return [tags]

    normalized_filters = [
        tag_filter for tag_filter in tags if isinstance(tag_filter, dict) and tag_filter
    ]
    if not normalized_filters:
        raise ValueError("At least one tag must be provided for preprocessing.")
    return normalized_filters


def download_osm_map_by_bbox(
    bbox: tuple[float, float, float, float],
    output_file_path: str,
    *,
    timeout: int,
    user_agent: str = "maps4fs OSM downloader",
) -> str:
    """Download raw OSM XML for a bounding box via the main OSM API.

    When the API rejects one large bbox because it exceeds the per-request node limit, the bbox
    is split recursively into smaller tiles and the resulting XML payloads are merged into one
    output file.

    Arguments:
        bbox (tuple[float, float, float, float]): Bounding box in OSMnx order
            ``(left, bottom, right, top)``.
        output_file_path (str): Path where the downloaded ``.osm`` file will be written.
        timeout (int): HTTP request timeout in seconds.
        user_agent (str): User-Agent header value.

    Returns:
        str: The written file path.

    Raises:
        ValueError: If bbox coordinates are invalid or the response is not OSM XML.
        RuntimeError: If the HTTP request fails.
    """
    left, bottom, right, top = bbox
    if left >= right or bottom >= top:
        raise ValueError(f"Invalid bbox for OSM download: {bbox!r}")

    output_directory = os.path.dirname(output_file_path)
    if output_directory:
        os.makedirs(output_directory, exist_ok=True)

    root = _download_osm_root_by_bbox(
        bbox,
        timeout=timeout,
        user_agent=user_agent,
        depth=0,
    )

    tree = ET.ElementTree(root)
    tree.write(output_file_path, encoding="utf-8", xml_declaration=True)

    check_and_fix_osm(output_file_path)
    return output_file_path


def _download_osm_root_by_bbox(
    bbox: tuple[float, float, float, float],
    *,
    timeout: int,
    user_agent: str,
    depth: int,
) -> ET.Element:
    """Download one bbox or recursively merge smaller bbox downloads."""
    try:
        payload = _download_osm_payload_by_bbox(
            bbox,
            timeout=timeout,
            user_agent=user_agent,
        )
    except _OSMTooManyNodesError as exc:
        if depth >= _OSM_TILE_MAX_DEPTH or not _can_split_bbox(bbox):
            raise RuntimeError(
                "Failed to download OSM data: bbox exceeds the OSM API node limit even after "
                f"subdivision ({bbox!r})."
            ) from exc

        child_roots = [
            _download_osm_root_by_bbox(
                child_bbox,
                timeout=timeout,
                user_agent=user_agent,
                depth=depth + 1,
            )
            for child_bbox in _split_bbox(bbox)
        ]
        return _merge_osm_roots(child_roots, bbox)

    return _parse_osm_payload(payload)


def _download_osm_payload_by_bbox(
    bbox: tuple[float, float, float, float],
    *,
    timeout: int,
    user_agent: str,
) -> bytes:
    """Download one raw OSM API bbox payload."""
    left, bottom, right, top = bbox
    query = urlencode({"bbox": f"{left:.7f},{bottom:.7f},{right:.7f},{top:.7f}"})
    request = Request(
        f"{_OSM_API_MAP_URL}?{query}",
        headers={
            "Accept": "application/xml",
            "Accept-Encoding": "gzip",
            "User-Agent": user_agent,
        },
    )

    try:
        with urlopen(request, timeout=timeout) as response:
            payload = response.read()
            if response.headers.get("Content-Encoding", "").lower() == "gzip":
                payload = gzip.decompress(payload)
    except HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace").strip()
        if exc.code == 400 and "too many nodes" in details.lower():
            raise _OSMTooManyNodesError(details or "Too many nodes in bbox request") from exc

        message = f"Failed to download OSM data: HTTP {exc.code}"
        if details:
            message = f"{message}: {details}"
        raise RuntimeError(message) from exc
    except URLError as exc:
        raise RuntimeError(f"Failed to download OSM data: {exc.reason}") from exc

    return payload


def _parse_osm_payload(payload: bytes) -> ET.Element:
    """Parse one downloaded OSM XML payload into its root element."""
    if b"<osm" not in payload:
        raise ValueError("Downloaded response is not valid OSM XML.")
    return ET.fromstring(payload)


def _can_split_bbox(bbox: tuple[float, float, float, float]) -> bool:
    """Return whether the bbox still has enough span to split safely."""
    left, bottom, right, top = bbox
    return (right - left) > _OSM_TILE_MIN_SPAN or (top - bottom) > _OSM_TILE_MIN_SPAN


def _split_bbox(
    bbox: tuple[float, float, float, float],
) -> tuple[tuple[float, float, float, float], tuple[float, float, float, float]]:
    """Split a bbox along its longer axis into two smaller bbox requests."""
    left, bottom, right, top = bbox
    width = right - left
    height = top - bottom

    if width >= height and width > _OSM_TILE_MIN_SPAN:
        middle = (left + right) / 2.0
        return (left, bottom, middle, top), (middle, bottom, right, top)

    middle = (bottom + top) / 2.0
    return (left, bottom, right, middle), (left, middle, right, top)


def _merge_osm_roots(
    roots: list[ET.Element],
    bbox: tuple[float, float, float, float],
) -> ET.Element:
    """Merge multiple OSM API tile roots into one deduplicated OSM root."""
    merged_root = ET.Element(
        "osm",
        {
            "version": roots[0].get("version", "0.6") if roots else "0.6",
            "generator": (
                roots[0].get("generator", "maps4fs OSM downloader")
                if roots
                else "maps4fs OSM downloader"
            ),
        },
    )

    left, bottom, right, top = bbox
    bounds = ET.SubElement(merged_root, "bounds")
    bounds.set("minlat", f"{bottom:.7f}")
    bounds.set("minlon", f"{left:.7f}")
    bounds.set("maxlat", f"{top:.7f}")
    bounds.set("maxlon", f"{right:.7f}")

    merged_primitives: dict[str, dict[str, ET.Element]] = {
        "node": {},
        "way": {},
        "relation": {},
    }
    append_order: dict[str, list[str]] = {"node": [], "way": [], "relation": []}

    for root in roots:
        for child in root:
            if child.tag not in merged_primitives:
                continue
            element_id = child.get("id")
            if element_id is None or element_id in merged_primitives[child.tag]:
                continue
            merged_primitives[child.tag][element_id] = deepcopy(child)
            append_order[child.tag].append(element_id)

    for primitive_name in ("node", "way", "relation"):
        for element_id in append_order[primitive_name]:
            merged_root.append(merged_primitives[primitive_name][element_id])

    return merged_root


def preprocess(
    input_file_path: str,
    output_file_path: str,
    tags: OSMTagFilters,
    process_bbox: tuple[float, float, float, float] | None = None,
    exclude_cut_tags: dict[str, OSMTagValue] | None = None,
    smooth_strength: float = 0.3,
    merge_distance: float = 0.0,
    split_width: float = 4.0,
    merge_tags: bool = True,
    collapse_tags: dict[str, str] | None = None,
    add_holes: bool = True,
    shrink_distance: float = 0.75,
    narrow_connection_width: float = 3.0,
    min_part_area: float = 40.0,
    min_part_width: float = 2.0,
) -> dict[str, int]:
    """Preprocess matching OSM polygons and save a normalized output file.

    The operation does the following for polygons matching ``tags``:
    1. Split polygons where linear objects (for example roads) pass through them.
    2. Merge touching polygon fragments that remain on the same side of those cuts.
    3. Carve holes where non-matching area objects are inside.
    4. Break very narrow bridge connections into separate polygons.
    5. Smooth resulting geometry boundaries.
    6. Apply a small inward offset so the final polygon sits inside the source.
    7. Drop tiny detached fragments and narrow leftover slivers.

    Arguments:
        input_file_path (str): Path to source OSM XML.
        output_file_path (str): Path to processed OSM XML.
        tags (OSMTagFilters): One tag filter or a list of OR-combined target filters
            for target polygons.
        process_bbox (tuple[float, float, float, float] | None): Optional bbox in
            OSMnx order ``(left, bottom, right, top)``. When provided, only target
            polygons intersecting that bbox are rewritten and only nearby holes and
            splitter features are considered.
        exclude_cut_tags (dict[str, OSMTagValue] | None): Tag filter for linear
            objects that must not split polygons.
        smooth_strength (float): Boundary smoothing strength in the [0, 1] range.
        merge_distance (float): Optional gap-closing distance in meters,
            applied in a local projected coordinate system while merging.
            Defaults to 0 so only touching or overlapping polygons merge.
        split_width (float): Default splitter half-width in meters, applied in
            a local projected coordinate system.
        merge_tags (bool): When True, list-valued target filters are normalized
            to their first configured value before grouping and output tagging.
            For example, {"landuse": ["farmland", "meadow"]} rewrites matched
            meadows as farmland so they can be merged into one output landuse.
        collapse_tags (dict[str, str] | None): Optional canonical output tags for all
            matched target polygons. When provided, any matched target keys are removed
            from the output and replaced by these canonical tags.
        add_holes (bool): If True, carve holes from inner area polygons and supported
            point obstacles.
        shrink_distance (float): Final inward padding in meters applied after
            smoothing so polygons sit inside the original boundary.
        narrow_connection_width (float): Width threshold in meters for breaking
            very narrow polygon bridges into separate polygons. Set to 0 to
            disable this pass.
        min_part_area (float): Minimum area in square meters for keeping a
            resulting polygon fragment after cut/split cleanup.
        min_part_width (float): Minimum effective width in meters for keeping
            narrow leftover polygon slivers after cut/split cleanup. Set to 0
            to disable width-based cleanup.

    Returns:
        dict[str, int]: Processing statistics.
    """
    target_filters = _normalize_target_filters(tags)
    if not os.path.isfile(input_file_path):
        raise FileNotFoundError(f"Input OSM file {input_file_path} does not exist.")

    same_path = os.path.abspath(input_file_path) == os.path.abspath(output_file_path)
    if not same_path:
        output_directory = os.path.dirname(output_file_path)
        if output_directory:
            os.makedirs(output_directory, exist_ok=True)
        shutil.copyfile(input_file_path, output_file_path)

    # Run repository-standard validation/repair flow before geometry edits.
    check_and_fix_osm(output_file_path)

    tree = ET.parse(output_file_path)
    root = tree.getroot()

    nodes = _parse_nodes(root)
    ways = _parse_ways(root)
    relations = _parse_relations(root)
    relation_way_usage = _count_relation_way_usage(relations)

    target_way_ids, target_relation_ids, target_member_way_ids, target_polygons = (
        _collect_target_polygons(
            tags=target_filters,
            nodes=nodes,
            ways=ways,
            relations=relations,
            relation_way_usage=relation_way_usage,
            merge_tags=merge_tags,
            collapse_tags=collapse_tags,
            process_bbox=process_bbox,
        )
    )
    if not target_polygons:
        tree.write(output_file_path, encoding="utf-8", xml_declaration=True)
        return {
            "target_input_polygons": 0,
            "target_output_polygons": 0,
            "splitter_lines": 0,
            "hole_polygons": 0,
            "removed_elements": 0,
            "created_ways": 0,
            "created_relations": 0,
        }

    if add_holes:
        hole_polygons = _collect_hole_polygons(
            tags=target_filters,
            nodes=nodes,
            ways=ways,
            relations=relations,
            excluded_way_ids=target_way_ids | target_member_way_ids,
            excluded_relation_ids=target_relation_ids,
            process_bbox=process_bbox,
        )
        point_holes = _collect_point_holes(
            root=root,
            tags=target_filters,
            nodes=nodes,
            process_bbox=process_bbox,
        )
    else:
        hole_polygons = []
        point_holes = []
    splitter_lines = _collect_splitter_lines(
        nodes=nodes,
        ways=ways,
        excluded_way_ids=target_way_ids,
        exclude_cut_tags=exclude_cut_tags,
        process_bbox=process_bbox,
    )

    processed_polygons = _preprocess_target_polygon_groups(
        target_polygons=target_polygons,
        hole_polygons=hole_polygons,
        point_holes=point_holes,
        splitter_lines=splitter_lines,
        smooth_strength=smooth_strength,
        merge_distance=merge_distance,
        split_width=split_width,
        shrink_distance=shrink_distance,
        narrow_connection_width=narrow_connection_width,
        min_part_area=min_part_area,
        min_part_width=min_part_width,
    )

    removed_elements = _remove_target_elements(
        root=root,
        target_way_ids=target_way_ids | target_member_way_ids,
        target_relation_ids=target_relation_ids,
        ways=ways,
        relations=relations,
    )
    created_ways, created_relations = _append_polygons(root=root, polygons=processed_polygons)
    _remove_orphan_untagged_nodes(root)

    # JOSM expects a version on every persisted primitive.
    _ensure_primitive_versions(root)

    tree.write(output_file_path, encoding="utf-8", xml_declaration=True)
    if not check_osm_file(output_file_path):
        raise ValueError(f"Processed OSM file {output_file_path} is invalid.")

    return {
        "target_input_polygons": len(target_polygons),
        "target_output_polygons": len(processed_polygons),
        "splitter_lines": len(splitter_lines),
        "hole_polygons": len(hole_polygons) + len(point_holes),
        "removed_elements": removed_elements,
        "created_ways": created_ways,
        "created_relations": created_relations,
    }


def prune_osm_file(
    input_file_path: str,
    output_file_path: str,
    tags: OSMTagFilters,
    spatial_filters: list[
        tuple[OSMTagFilter, tuple[float, float, float, float] | None]
    ] | None = None,
) -> dict[str, int]:
    """Remove OSM primitives that are not needed by the runtime tag set.

    Matching nodes, ways, and relations are retained, along with all dependent member ways,
    member relations, and referenced nodes required to keep the remaining OSM XML valid.

    Arguments:
        input_file_path (str): Path to source OSM XML.
        output_file_path (str): Path to the pruned OSM XML.
        tags (OSMTagFilters): Tag filters that define which runtime features must remain.
        spatial_filters (list[tuple[OSMTagFilter, tuple[float, float, float, float] | None]]
            | None): Optional per-filter bbox retention rules in OSMnx order
            ``(left, bottom, right, top)``. Features matching a filter are kept only when they
            intersect that filter's bbox. When omitted, all matching features are kept regardless
            of location.

    Returns:
        dict[str, int]: Pruning statistics.
    """
    retain_filters = _normalize_target_filters(tags)
    retain_rules = spatial_filters or [(target_filter, None) for target_filter in retain_filters]
    if not os.path.isfile(input_file_path):
        raise FileNotFoundError(f"Input OSM file {input_file_path} does not exist.")

    same_path = os.path.abspath(input_file_path) == os.path.abspath(output_file_path)
    if not same_path:
        output_directory = os.path.dirname(output_file_path)
        if output_directory:
            os.makedirs(output_directory, exist_ok=True)
        shutil.copyfile(input_file_path, output_file_path)

    tree = ET.parse(output_file_path)
    root = tree.getroot()
    nodes = _parse_nodes(root)
    ways = _parse_ways(root)
    relations = _parse_relations(root)

    retained_node_ids: set[int] = set()
    retained_way_ids: set[int] = set()
    retained_relation_ids: set[int] = set()
    pending_relation_ids: list[int] = []

    for node_element in root.findall("node"):
        node_id = node_element.get("id")
        if not node_id:
            continue
        try:
            parsed_node_id = int(node_id)
        except ValueError:
            continue

        node_tags = _extract_tags(node_element)
        if node_tags and _matches_spatial_rule_set(
            node_tags,
            (coordinate[0], coordinate[1], coordinate[0], coordinate[1])
            if (coordinate := nodes.get(parsed_node_id)) is not None
            else None,
            retain_rules,
        ):
            retained_node_ids.add(parsed_node_id)

    for way_id, way in ways.items():
        if way.tags and _matches_spatial_rule_set(
            way.tags,
            _way_bounds(way, nodes),
            retain_rules,
        ):
            retained_way_ids.add(way_id)

    for relation_id, relation in relations.items():
        if relation.tags and _matches_spatial_rule_set(
            relation.tags,
            _relation_bounds(relation, ways, relations, nodes),
            retain_rules,
        ):
            retained_relation_ids.add(relation_id)
            pending_relation_ids.append(relation_id)

    while pending_relation_ids:
        relation_id = pending_relation_ids.pop()
        relation = relations.get(relation_id)
        if relation is None:
            continue

        for member_type, member_ref, _ in relation.members:
            if member_type == "node":
                retained_node_ids.add(member_ref)
            elif member_type == "way":
                retained_way_ids.add(member_ref)
            elif member_type == "relation" and member_ref not in retained_relation_ids:
                if member_ref in relations:
                    retained_relation_ids.add(member_ref)
                    pending_relation_ids.append(member_ref)

    for way_id in retained_way_ids:
        way = ways.get(way_id)
        if way is None:
            continue
        retained_node_ids.update(way.node_refs)

    removed_elements = 0
    kept_nodes = 0
    kept_ways = 0
    kept_relations = 0

    for element in list(root):
        if element.tag == "bounds":
            continue

        element_id = element.get("id")
        if element.tag == "node":
            if element_id is None:
                continue
            try:
                keep = int(element_id) in retained_node_ids
            except ValueError:
                continue
            if keep:
                kept_nodes += 1
                continue
            root.remove(element)
            removed_elements += 1
            continue

        if element.tag == "way":
            if element_id is None:
                continue
            try:
                keep = int(element_id) in retained_way_ids
            except ValueError:
                continue
            if keep:
                kept_ways += 1
                continue
            root.remove(element)
            removed_elements += 1
            continue

        if element.tag == "relation":
            if element_id is None:
                continue
            try:
                keep = int(element_id) in retained_relation_ids
            except ValueError:
                continue
            if keep:
                kept_relations += 1
                continue
            root.remove(element)
            removed_elements += 1

    tree.write(output_file_path, encoding="utf-8", xml_declaration=True)
    return {
        "kept_nodes": kept_nodes,
        "kept_ways": kept_ways,
        "kept_relations": kept_relations,
        "removed_elements": removed_elements,
    }


def _matches_spatial_rule_set(
    feature_tags: dict[str, str],
    bounds: tuple[float, float, float, float] | None,
    retain_rules: list[tuple[OSMTagFilter, tuple[float, float, float, float] | None]],
) -> bool:
    """Return whether feature tags match any retention rule and intersect its bbox."""
    if bounds is None:
        return False

    for target_filter, bbox in retain_rules:
        if _matching_target_filter(feature_tags, [target_filter]) is None:
            continue
        if _bounds_intersect_bbox(bounds, bbox):
            return True
    return False


def _way_bounds(
    way: _WayData,
    nodes: dict[int, tuple[float, float]],
) -> tuple[float, float, float, float] | None:
    """Return the bounds of a way from its referenced coordinates."""
    coordinates = [nodes[node_id] for node_id in way.node_refs if node_id in nodes]
    if not coordinates:
        return None

    xs = [coordinate[0] for coordinate in coordinates]
    ys = [coordinate[1] for coordinate in coordinates]
    return min(xs), min(ys), max(xs), max(ys)


def _relation_bounds(
    relation: _RelationData,
    ways: dict[int, _WayData],
    relations: dict[int, _RelationData],
    nodes: dict[int, tuple[float, float]],
) -> tuple[float, float, float, float] | None:
    """Return approximate bounds of a relation from all reachable member coordinates."""
    xs: list[float] = []
    ys: list[float] = []
    relation_id = relation.element.get("id")
    if relation_id is None:
        return None

    try:
        pending_relation_ids = [int(relation_id)]
    except ValueError:
        return None

    seen_relation_ids: set[int] = set()

    while pending_relation_ids:
        current_relation_id = pending_relation_ids.pop()
        if current_relation_id in seen_relation_ids:
            continue
        seen_relation_ids.add(current_relation_id)

        current_relation = relations.get(current_relation_id)
        if current_relation is None:
            continue

        for member_type, member_ref, _ in current_relation.members:
            if member_type == "node":
                coordinate = nodes.get(member_ref)
                if coordinate is None:
                    continue
                xs.append(coordinate[0])
                ys.append(coordinate[1])
                continue

            if member_type == "way":
                way = ways.get(member_ref)
                if way is None:
                    continue
                way_bounds = _way_bounds(way, nodes)
                if way_bounds is None:
                    continue
                minx, miny, maxx, maxy = way_bounds
                xs.extend((minx, maxx))
                ys.extend((miny, maxy))
                continue

            if member_type == "relation":
                nested_relation = relations.get(member_ref)
                if nested_relation is not None:
                    pending_relation_ids.append(member_ref)

    if not xs or not ys:
        return None
    return min(xs), min(ys), max(xs), max(ys)


def _parse_nodes(root: ET.Element) -> dict[int, tuple[float, float]]:
    """Read all node coordinates from OSM XML.

    Arguments:
        root (ET.Element): Root OSM XML element.

    Returns:
        dict[int, tuple[float, float]]: Mapping of node ids to
            ``(longitude, latitude)`` coordinates.
    """
    nodes: dict[int, tuple[float, float]] = {}
    for element in root.findall("node"):
        element_id = element.get("id")
        lat = element.get("lat")
        lon = element.get("lon")
        if not element_id or lat is None or lon is None:
            continue
        try:
            nodes[int(element_id)] = (float(lon), float(lat))
        except ValueError:
            continue
    return nodes


def _parse_ways(root: ET.Element) -> dict[int, _WayData]:
    """Read all ways from OSM XML.

    Arguments:
        root (ET.Element): Root OSM XML element.

    Returns:
        dict[int, _WayData]: Mapping of way ids to parsed way data.
    """
    ways: dict[int, _WayData] = {}
    for way_element in root.findall("way"):
        way_id = way_element.get("id")
        if not way_id:
            continue

        refs: list[int] = []
        for node_ref in way_element.findall("nd"):
            ref_value = node_ref.get("ref")
            if ref_value is None:
                continue
            try:
                refs.append(int(ref_value))
            except ValueError:
                continue

        way_tags = _extract_tags(way_element)
        ways[int(way_id)] = _WayData(element=way_element, node_refs=refs, tags=way_tags)
    return ways


def _parse_relations(root: ET.Element) -> dict[int, _RelationData]:
    """Read all relations from OSM XML.

    Arguments:
        root (ET.Element): Root OSM XML element.

    Returns:
        dict[int, _RelationData]: Mapping of relation ids to parsed
            relation data.
    """
    relations: dict[int, _RelationData] = {}
    for relation_element in root.findall("relation"):
        relation_id = relation_element.get("id")
        if not relation_id:
            continue

        members: list[tuple[str, int, str]] = []
        for member in relation_element.findall("member"):
            member_type = member.get("type")
            member_ref = member.get("ref")
            role = member.get("role") or ""
            if not member_type or member_ref is None:
                continue
            try:
                members.append((member_type, int(member_ref), role))
            except ValueError:
                continue

        relation_tags = _extract_tags(relation_element)
        relations[int(relation_id)] = _RelationData(
            element=relation_element,
            members=members,
            tags=relation_tags,
        )
    return relations


def _extract_tags(element: ET.Element) -> dict[str, str]:
    """Extract the tag dictionary from an OSM XML element.

    Arguments:
        element (ET.Element): XML element that may contain ``tag``
            children.

    Returns:
        dict[str, str]: Mapping of tag keys to tag values.
    """
    tags: dict[str, str] = {}
    for tag in element.findall("tag"):
        key = tag.get("k")
        value = tag.get("v")
        if key and value is not None:
            tags[key] = value
    return tags


def _bounds_intersect_bbox(
    bounds: tuple[float, float, float, float],
    bbox: tuple[float, float, float, float] | None,
) -> bool:
    """Return whether geometry bounds intersect an optional bbox."""
    if bbox is None:
        return True

    minx, miny, maxx, maxy = bounds
    left, bottom, right, top = bbox
    return not (maxx < left or right < minx or maxy < bottom or top < miny)


def _coordinates_intersect_bbox(
    coordinates: list[tuple[float, float]],
    bbox: tuple[float, float, float, float] | None,
) -> bool:
    """Return whether a coordinate sequence intersects an optional bbox."""
    if bbox is None:
        return True
    if not coordinates:
        return False

    xs = [coordinate[0] for coordinate in coordinates]
    ys = [coordinate[1] for coordinate in coordinates]
    return _bounds_intersect_bbox((min(xs), min(ys), max(xs), max(ys)), bbox)


def _way_intersects_bbox(
    way: _WayData,
    nodes: dict[int, tuple[float, float]],
    bbox: tuple[float, float, float, float] | None,
) -> bool:
    """Return whether a way's referenced coordinates intersect an optional bbox."""
    if bbox is None:
        return True

    coordinates = [nodes[node_id] for node_id in way.node_refs if node_id in nodes]
    return _coordinates_intersect_bbox(coordinates, bbox)


def _count_relation_way_usage(relations: dict[int, _RelationData]) -> dict[int, int]:
    """Count how many relations reference each way id.

    Arguments:
        relations (dict[int, _RelationData]): Parsed relation data by
            relation id.

    Returns:
        dict[int, int]: Mapping of way ids to relation reference count.
    """
    usage: dict[int, int] = {}
    for relation in relations.values():
        for member_type, member_ref, _ in relation.members:
            if member_type != "way":
                continue
            usage[member_ref] = usage.get(member_ref, 0) + 1
    return usage


def _target_merge_key(
    feature_tags: dict[str, str],
    target_tags: dict[str, OSMTagValue],
    merge_tags: bool,
) -> tuple[tuple[str, str], ...]:
    """Build the merge key for a matched target feature.

    Arguments:
        feature_tags (dict[str, str]): Actual tags from the matched OSM
            feature.
        target_tags (dict[str, OSMTagValue]): Requested target tag filter.
        merge_tags (bool): Whether list-valued target tags should be
            normalized to their first configured value.

    Returns:
        tuple[tuple[str, str], ...]: Normalized merge key used to group
            compatible target polygons.
    """
    return tuple(
        (
            key,
            _normalized_target_tag_value(
                actual_value=feature_tags[key],
                expected_value=target_tags[key],
                merge_tags=merge_tags,
            ),
        )
        for key in target_tags
        if key in feature_tags and feature_tags[key] is not None
    )


def _normalized_target_tag_value(
    actual_value: str,
    expected_value: OSMTagValue,
    merge_tags: bool,
) -> str:
    """Return the canonical value for a matched target tag.

    Arguments:
        actual_value (str): Tag value found on the source feature.
        expected_value (OSMTagValue): Requested value from the target
            filter.
        merge_tags (bool): Whether compatible values should collapse to
            the first configured target value.

    Returns:
        str: Canonical value used for merge grouping and output tags.
    """
    if not merge_tags:
        return actual_value
    if isinstance(expected_value, list) and expected_value and actual_value in expected_value:
        return expected_value[0]
    return actual_value


def _output_feature_tags(feature_tags: dict[str, str]) -> dict[str, str]:
    """Return source tags that should survive rewritten output.

    Arguments:
        feature_tags (dict[str, str]): Source feature tags.

    Returns:
        dict[str, str]: Output tag mapping with relation-only helper tags
            removed.
    """
    return {key: value for key, value in feature_tags.items() if key != "type"}


def _common_output_tags(
    tag_sets: list[dict[str, str]],
    merge_key: tuple[tuple[str, str], ...],
    remove_keys: set[str] | None = None,
) -> dict[str, str]:
    """Return stable output tags for a processed polygon group.

    Arguments:
        tag_sets (list[dict[str, str]]): Source tag dictionaries from all
            polygons in the merge group.
        merge_key (tuple[tuple[str, str], ...]): Normalized tags that must
            be preserved on the merged output.
        remove_keys (set[str] | None): Tag keys to strip from the common source tags
            before merge-key tags are applied.

    Returns:
        dict[str, str]: Tag mapping common across the group with merge-key
            values forced to remain.
    """
    if not tag_sets:
        return dict(merge_key)

    common_tags = dict(tag_sets[0])
    for tag_set in tag_sets[1:]:
        common_tags = {
            key: value for key, value in common_tags.items() if tag_set.get(key) == value
        }

    if remove_keys:
        common_tags = {key: value for key, value in common_tags.items() if key not in remove_keys}

    for key, value in merge_key:
        common_tags[key] = value
    return common_tags


def _matches_tags(feature_tags: dict[str, str], target_tags: dict[str, OSMTagValue]) -> bool:
    """Return whether feature tags satisfy a target filter.

    Arguments:
        feature_tags (dict[str, str]): Tags from the source OSM feature.
        target_tags (dict[str, OSMTagValue]): Tag filter to evaluate.

    Returns:
        bool: True when the feature matches the requested filter.
    """
    for key, expected_value in target_tags.items():
        actual_value = feature_tags.get(key)
        if actual_value is None:
            return False
        if isinstance(expected_value, bool):
            if expected_value and not actual_value:
                return False
            if not expected_value and actual_value not in {"0", "false", "no"}:
                return False
            continue
        if isinstance(expected_value, str):
            if actual_value != expected_value:
                return False
            continue
        if actual_value not in expected_value:
            return False
    return True


def _matching_target_filter(
    feature_tags: dict[str, str],
    target_filters: list[OSMTagFilter],
) -> OSMTagFilter | None:
    """Return the first target filter matched by a feature."""
    for target_filter in target_filters:
        if _matches_tags(feature_tags, target_filter):
            return target_filter
    return None


def _is_area_way(way: _WayData) -> bool:
    """Heuristically classify whether a way should be treated as an area.

    Arguments:
        way (_WayData): Parsed OSM way.

    Returns:
        bool: True when the way should be treated as a polygon.
    """
    if len(way.node_refs) < 4 or way.node_refs[0] != way.node_refs[-1]:
        return False

    area_value = way.tags.get("area")
    if area_value == "no":
        return False
    if area_value == "yes":
        return True

    return not any(tag in _LINEAR_TAGS for tag in way.tags)


def _way_to_polygon(way: _WayData, nodes: dict[int, tuple[float, float]]) -> Polygon | None:
    """Build a polygon from an OSM way when possible.

    Arguments:
        way (_WayData): Parsed OSM way.
        nodes (dict[int, tuple[float, float]]): Node coordinate mapping.

    Returns:
        Polygon | None: Polygon geometry for the way, or None when the
            way cannot be converted into a valid area.
    """
    if not _is_area_way(way):
        return None
    coordinates = [nodes[node_id] for node_id in way.node_refs if node_id in nodes]
    if len(coordinates) < 4:
        return None
    polygon = Polygon(coordinates)
    if polygon.is_empty:
        return None
    if not polygon.is_valid:
        polygon = make_valid(polygon)
        polygons = _geometry_to_polygons(polygon)
        return polygons[0] if polygons else None
    return polygon


def _way_to_line_string(
    way: _WayData,
    nodes: dict[int, tuple[float, float]],
) -> LineString | None:
    """Build a line string from an OSM way when possible.

    Arguments:
        way (_WayData): Parsed OSM way.
        nodes (dict[int, tuple[float, float]]): Node coordinate mapping.

    Returns:
        LineString | None: Line geometry for the way, or None when the way cannot be
            converted into a valid line.
    """
    coordinates = [nodes[node_id] for node_id in way.node_refs if node_id in nodes]
    if len(coordinates) < 2:
        return None
    if len(set(coordinates)) < 2:
        return None

    line = LineString(coordinates)
    return None if line.is_empty else line


def _assemble_relation_member_polygons(
    member_way_ids: list[int],
    ways: dict[int, _WayData],
    nodes: dict[int, tuple[float, float]],
) -> tuple[list[Polygon], set[int]]:
    """Assemble polygon geometry from relation member ways.

    OSM multipolygon relations often split one boundary ring across several way members. This
    helper merges those way lines and polygonizes the result so preprocessing can still operate on
    relations whose outers or inners are not individually closed ways.

    Arguments:
        member_way_ids (list[int]): Relation member way ids for one role.
        ways (dict[int, _WayData]): Parsed OSM ways by id.
        nodes (dict[int, tuple[float, float]]): Node coordinate mapping.

    Returns:
        tuple[list[Polygon], set[int]]: Assembled polygons and the subset of member way ids that
            contributed geometry.
    """
    member_lines: list[LineString] = []
    used_way_ids: set[int] = set()

    for member_way_id in member_way_ids:
        member_way = ways.get(member_way_id)
        if not member_way:
            continue
        member_line = _way_to_line_string(member_way, nodes)
        if member_line is None:
            continue
        member_lines.append(member_line)
        used_way_ids.add(member_way_id)

    if not member_lines:
        return [], set()

    merged_geometry = make_valid(unary_union(member_lines))
    assembled_polygons = [
        polygon
        for polygon in polygonize(merged_geometry)
        if not polygon.is_empty and polygon.area > 0
    ]
    return assembled_polygons, used_way_ids


def _relation_to_polygons(
    relation: _RelationData,
    ways: dict[int, _WayData],
    nodes: dict[int, tuple[float, float]],
) -> tuple[list[Polygon], set[int]]:
    """Build polygons from a multipolygon relation.

    Arguments:
        relation (_RelationData): Parsed OSM relation.
        ways (dict[int, _WayData]): Parsed OSM ways by id.
        nodes (dict[int, tuple[float, float]]): Node coordinate mapping.

    Returns:
        tuple[list[Polygon], set[int]]: Polygon geometry extracted from the
            relation and the set of referenced member way ids.
    """
    if relation.tags.get("type") != "multipolygon":
        return [], set()

    outer_way_ids: list[int] = []
    inner_way_ids: list[int] = []
    member_way_ids: set[int] = set()

    for member_type, member_ref, role in relation.members:
        if member_type != "way":
            continue
        if role == "inner":
            inner_way_ids.append(member_ref)
        else:
            outer_way_ids.append(member_ref)

    outer_polygons, outer_member_way_ids = _assemble_relation_member_polygons(
        outer_way_ids,
        ways,
        nodes,
    )
    inner_polygons, inner_member_way_ids = _assemble_relation_member_polygons(
        inner_way_ids,
        ways,
        nodes,
    )
    member_way_ids.update(outer_member_way_ids)
    member_way_ids.update(inner_member_way_ids)

    if not outer_polygons:
        return [], member_way_ids

    inner_union = unary_union(inner_polygons) if inner_polygons else None
    result: list[Polygon] = []
    for outer in outer_polygons:
        polygon = outer
        if inner_union is not None and polygon.intersects(inner_union):
            polygon = make_valid(polygon.difference(inner_union))
        result.extend(_geometry_to_polygons(polygon))

    return result, member_way_ids


def _collect_target_polygons(
    tags: list[OSMTagFilter],
    nodes: dict[int, tuple[float, float]],
    ways: dict[int, _WayData],
    relations: dict[int, _RelationData],
    relation_way_usage: dict[int, int],
    merge_tags: bool,
    collapse_tags: dict[str, str] | None,
    process_bbox: tuple[float, float, float, float] | None = None,
) -> tuple[set[int], set[int], set[int], list[_TargetPolygonData]]:
    """Collect target polygons and the source elements they replace.

    Arguments:
        tags (list[OSMTagFilter]): OR-combined target polygon tag filters.
        nodes (dict[int, tuple[float, float]]): Node coordinate mapping.
        ways (dict[int, _WayData]): Parsed OSM ways by id.
        relations (dict[int, _RelationData]): Parsed OSM relations by id.
        relation_way_usage (dict[int, int]): Count of how many relations use
            each way.
        merge_tags (bool): Whether compatible target tag values should be
            normalized before grouping.
        collapse_tags (dict[str, str] | None): Optional canonical tags that replace
            matched target keys on output.

    Returns:
        tuple[set[int], set[int], set[int], list[_TargetPolygonData]]:
            Target way ids, target relation ids, orphaned relation-member way
            ids to remove, and collected target polygons.
    """
    target_way_ids: set[int] = set()
    target_relation_ids: set[int] = set()
    target_member_way_ids: set[int] = set()
    target_polygons: list[_TargetPolygonData] = []

    for way_id, way in ways.items():
        if not way.tags:
            continue
        matching_filter = _matching_target_filter(way.tags, tags)
        if matching_filter is None:
            continue
        if not _way_intersects_bbox(way, nodes, process_bbox):
            continue
        polygon = _way_to_polygon(way, nodes)
        if polygon is None:
            continue
        if not _bounds_intersect_bbox(polygon.bounds, process_bbox):
            continue
        target_way_ids.add(way_id)
        target_keys = tuple(matching_filter.keys())
        target_polygons.append(
            _TargetPolygonData(
                geometry=polygon,
                tags=_output_feature_tags(way.tags),
                merge_key=(
                    tuple(collapse_tags.items())
                    if collapse_tags is not None
                    else _target_merge_key(way.tags, matching_filter, merge_tags)
                ),
                target_keys=target_keys,
            )
        )

    for relation_id, relation in relations.items():
        matching_filter = _matching_target_filter(relation.tags, tags)
        if matching_filter is None:
            continue
        relation_polygons, member_way_ids = _relation_to_polygons(relation, ways, nodes)
        if process_bbox is not None:
            relation_polygons = [
                polygon
                for polygon in relation_polygons
                if _bounds_intersect_bbox(polygon.bounds, process_bbox)
            ]
        if not relation_polygons:
            continue
        target_relation_ids.add(relation_id)
        relation_output_tags = _output_feature_tags(relation.tags)
        relation_merge_key = (
            tuple(collapse_tags.items())
            if collapse_tags is not None
            else _target_merge_key(relation.tags, matching_filter, merge_tags)
        )
        relation_target_keys = tuple(matching_filter.keys())
        target_polygons.extend(
            _TargetPolygonData(
                geometry=polygon,
                tags=relation_output_tags,
                merge_key=relation_merge_key,
                target_keys=relation_target_keys,
            )
            for polygon in relation_polygons
        )

        for member_way_id in member_way_ids:
            member_way = ways.get(member_way_id)
            if not member_way or member_way.tags:
                continue
            if relation_way_usage.get(member_way_id, 0) == 1:
                target_member_way_ids.add(member_way_id)

    return target_way_ids, target_relation_ids, target_member_way_ids, target_polygons


def _collect_hole_polygons(
    tags: list[OSMTagFilter],
    nodes: dict[int, tuple[float, float]],
    ways: dict[int, _WayData],
    relations: dict[int, _RelationData],
    excluded_way_ids: set[int],
    excluded_relation_ids: set[int],
    process_bbox: tuple[float, float, float, float] | None = None,
) -> list[Polygon]:
    """Collect non-target area polygons that should carve holes.

    Arguments:
        tags (list[OSMTagFilter]): OR-combined target polygon tag filters.
        nodes (dict[int, tuple[float, float]]): Node coordinate mapping.
        ways (dict[int, _WayData]): Parsed OSM ways by id.
        relations (dict[int, _RelationData]): Parsed OSM relations by id.
        excluded_way_ids (set[int]): Way ids that belong to target polygons.
        excluded_relation_ids (set[int]): Relation ids that belong to target
            polygons.

    Returns:
        list[Polygon]: Area polygons that should be subtracted from targets.
    """
    hole_polygons: list[Polygon] = []

    for way_id, way in ways.items():
        if way_id in excluded_way_ids or not way.tags:
            continue
        if _matching_target_filter(way.tags, tags) is not None:
            continue
        if not _way_intersects_bbox(way, nodes, process_bbox):
            continue
        polygon = _way_to_polygon(way, nodes)
        if polygon is not None and _bounds_intersect_bbox(polygon.bounds, process_bbox):
            hole_polygons.append(polygon)

    for relation_id, relation in relations.items():
        if relation_id in excluded_relation_ids:
            continue
        if relation.tags.get("type") != "multipolygon":
            continue
        if _matching_target_filter(relation.tags, tags) is not None:
            continue
        relation_polygons, _ = _relation_to_polygons(relation, ways, nodes)
        if process_bbox is not None:
            relation_polygons = [
                polygon
                for polygon in relation_polygons
                if _bounds_intersect_bbox(polygon.bounds, process_bbox)
            ]
        hole_polygons.extend(relation_polygons)

    return hole_polygons


def _collect_point_holes(
    root: ET.Element,
    tags: list[OSMTagFilter],
    nodes: dict[int, tuple[float, float]],
    process_bbox: tuple[float, float, float, float] | None = None,
) -> list[_PointHoleData]:
    """Collect point obstacles that should carve circular holes.

    Arguments:
        root (ET.Element): Root OSM XML element.
        tags (list[OSMTagFilter]): OR-combined target polygon tag filters.
        nodes (dict[int, tuple[float, float]]): Node coordinate mapping.

    Returns:
        list[_PointHoleData]: Tagged point obstacles with projected hole
            radii.
    """
    point_holes: list[_PointHoleData] = []

    for node_element in root.findall("node"):
        node_id = node_element.get("id")
        if not node_id:
            continue

        try:
            parsed_node_id = int(node_id)
        except ValueError:
            continue

        coordinate = nodes.get(parsed_node_id)
        if coordinate is None:
            continue
        if not _coordinates_intersect_bbox([coordinate], process_bbox):
            continue

        node_tags = _extract_tags(node_element)
        if not node_tags or _matching_target_filter(node_tags, tags) is not None:
            continue

        hole_radius = _point_hole_radius(node_tags)
        if hole_radius <= 0:
            continue

        point_holes.append(
            _PointHoleData(
                geometry=Point(coordinate),
                radius=hole_radius,
                tags=node_tags,
            )
        )

    return point_holes


def _point_hole_radius(tags: dict[str, str]) -> float:
    """Return the hole radius for a tagged point obstacle.

    Arguments:
        tags (dict[str, str]): Tags from a point feature.

    Returns:
        float: Hole radius in projected meters.
    """
    best_radius = 0.0
    for key, value in tags.items():
        best_radius = max(best_radius, _POINT_HOLE_RADII.get((key, value), 0.0))
    return best_radius


def _collect_splitter_lines(
    nodes: dict[int, tuple[float, float]],
    ways: dict[int, _WayData],
    excluded_way_ids: set[int],
    exclude_cut_tags: dict[str, OSMTagValue] | None,
    process_bbox: tuple[float, float, float, float] | None = None,
) -> list[_SplitterData]:
    """Collect linear objects that may split target polygons.

    Arguments:
        nodes (dict[int, tuple[float, float]]): Node coordinate mapping.
        ways (dict[int, _WayData]): Parsed OSM ways by id.
        excluded_way_ids (set[int]): Way ids that should never be treated as
            splitters.
        exclude_cut_tags (dict[str, OSMTagValue] | None): Optional tag filter
            for linear features that must not cut polygons.

    Returns:
        list[_SplitterData]: Linear features eligible to cut target polygons.
    """
    splitter_candidates: list[tuple[dict[str, str], list[int], list[tuple[float, float]]]] = []
    endpoint_counts: dict[int, int] = {}

    for way_id, way in ways.items():
        if way_id in excluded_way_ids:
            continue
        if not way.tags:
            continue
        if exclude_cut_tags and _matches_tags(way.tags, exclude_cut_tags):
            continue
        if _is_area_way(way):
            continue
        if not _is_splitter_feature(way.tags):
            continue
        if not _way_intersects_bbox(way, nodes, process_bbox):
            continue

        available_node_refs = [node_id for node_id in way.node_refs if node_id in nodes]
        if len(available_node_refs) < 2:
            continue

        coordinates = [nodes[node_id] for node_id in available_node_refs]
        if len(set(coordinates)) < 2:
            continue

        splitter_candidates.append((way.tags, available_node_refs, coordinates))
        endpoint_counts[available_node_refs[0]] = endpoint_counts.get(available_node_refs[0], 0) + 1
        endpoint_counts[available_node_refs[-1]] = (
            endpoint_counts.get(available_node_refs[-1], 0) + 1
        )

    lines: list[_SplitterData] = []

    for tags, available_node_refs, coordinates in splitter_candidates:
        line = LineString(coordinates)
        if line.is_empty:
            continue
        if not _bounds_intersect_bbox(line.bounds, process_bbox):
            continue
        lines.append(
            _SplitterData(
                geometry=line,
                tags=tags,
                round_start=endpoint_counts.get(available_node_refs[0], 0) == 1,
                round_end=endpoint_counts.get(available_node_refs[-1], 0) == 1,
            )
        )

    return lines


def _is_splitter_feature(tags: dict[str, str]) -> bool:
    """Return whether a tagged linear feature should cut target polygons."""
    if any(tag in _CUT_LINEAR_TAGS for tag in tags):
        return True
    return tags.get("natural") == "tree_row"


def _preprocess_polygons(
    target_polygons: list[Polygon],
    hole_polygons: list[Polygon],
    point_holes: list[_PointHoleData],
    splitter_lines: list[_SplitterData],
    smooth_strength: float,
    merge_distance: float,
    split_width: float,
    shrink_distance: float,
    narrow_connection_width: float,
    min_part_area: float,
    min_part_width: float,
) -> list[Polygon]:
    """Apply projected geometry cleanup to one polygon group.

    Arguments:
        target_polygons (list[Polygon]): Source polygons for one merge group.
        hole_polygons (list[Polygon]): Area polygons that should be
            subtracted from the targets.
        point_holes (list[_PointHoleData]): Point obstacles that should carve
            circular holes.
        splitter_lines (list[_SplitterData]): Linear features that may split
            the targets.
        smooth_strength (float): Corner-rounding strength in the [0, 1]
            range.
        merge_distance (float): Optional gap-closing merge distance in
            projected meters.
        split_width (float): Default splitter half-width in projected meters.
        shrink_distance (float): Final inward offset in projected meters.
        narrow_connection_width (float): Width threshold in projected meters
            for breaking thin bridges.
        min_part_area (float): Minimum fragment area in square meters.
        min_part_width (float): Minimum effective fragment width in meters.

    Returns:
        list[Polygon]: Cleaned output polygons in geographic coordinates.
    """
    if not target_polygons:
        return []

    target_union = unary_union(target_polygons)
    forward_transformer, backward_transformer = _build_local_transformers(target_union)

    projected_targets = _transform_polygons(target_polygons, forward_transformer)
    working_geometry = make_valid(unary_union(projected_targets))

    if splitter_lines and split_width > 0:
        split_buffers: list[BaseGeometry] = []
        for splitter in splitter_lines:
            projected_line = make_valid(_transform_geometry(splitter.geometry, forward_transformer))
            if projected_line.is_empty or not projected_line.intersects(working_geometry):
                continue

            buffer_width = _splitter_buffer_width(splitter.tags, split_width)
            if buffer_width <= 0:
                continue
            split_buffers.append(
                _buffer_splitter_geometry(
                    splitter,
                    projected_line,
                    buffer_width,
                )
            )

        if split_buffers:
            split_mask = make_valid(unary_union(split_buffers))
            working_geometry = make_valid(working_geometry.difference(split_mask))

    working_polygons = _geometry_to_polygons(working_geometry)
    if not working_polygons:
        return []

    post_split_merge_distance = merge_distance
    if splitter_lines and split_width > 0:
        # Keep post-cut merging conservative so roads are not bridged back together.
        post_split_merge_distance = min(merge_distance, max(0.25, split_width * 0.2))

    merged = _merge_connected_polygons(working_polygons, post_split_merge_distance)

    hole_geometries: list[BaseGeometry] = []
    if hole_polygons:
        hole_geometries.extend(
            polygon
            for polygon in _transform_polygons(hole_polygons, forward_transformer)
            if polygon.intersects(merged)
        )
    if point_holes:
        for point_hole in point_holes:
            projected_point = _transform_geometry(point_hole.geometry, forward_transformer)
            if projected_point.is_empty:
                continue
            buffered_point = projected_point.buffer(point_hole.radius)
            if buffered_point.is_empty or not buffered_point.intersects(merged):
                continue
            hole_geometries.append(buffered_point)
    if hole_geometries:
        hole_mask = make_valid(unary_union(hole_geometries))
        merged = make_valid(merged.difference(hole_mask))

    merged_polygons = _geometry_to_polygons(merged)
    if not merged_polygons:
        return []

    split_polygons = _split_polygons_at_narrow_connections(
        merged_polygons,
        narrow_connection_width,
    )
    smoothed_polygons = _smooth_polygons(split_polygons, smooth_strength)
    inset_polygons = _inset_polygons(smoothed_polygons, shrink_distance)
    cleaned_polygons = _cleanup_cut_artifacts(
        inset_polygons,
        min_part_area,
        min_part_width,
    )
    polygons: list[Polygon] = []
    for polygon in cleaned_polygons:
        transformed_polygon = make_valid(_transform_geometry(polygon, backward_transformer))
        polygons.extend(_geometry_to_polygons(transformed_polygon))
    if not polygons:
        return []

    minx, miny, maxx, maxy = target_union.bounds
    bbox_area = max((maxx - minx) * (maxy - miny), 1e-16)
    min_area = bbox_area * 1e-8
    return [polygon for polygon in polygons if polygon.area > min_area]


def _merge_connected_polygons(polygons: list[Polygon], merge_distance: float) -> BaseGeometry:
    """Merge touching polygons and optionally bridge tiny gaps.

    Arguments:
        polygons (list[Polygon]): Polygon geometries in projected meters.
        merge_distance (float): Optional gap-closing distance in projected
            meters.

    Returns:
        BaseGeometry: Merged polygonal geometry.
    """
    merged = make_valid(unary_union(polygons))
    if merge_distance <= 0:
        return merged

    # A small buffer-in/buffer-out pass bridges precision gaps so contiguous
    # landuse fragments become a single polygon.
    bridged = make_valid(
        merged.buffer(merge_distance, join_style=1, cap_style=1).buffer(
            -merge_distance,
            join_style=1,
            cap_style=1,
        )
    )
    return merged if bridged.is_empty else bridged


def _preprocess_target_polygon_groups(
    target_polygons: list[_TargetPolygonData],
    hole_polygons: list[Polygon],
    point_holes: list[_PointHoleData],
    splitter_lines: list[_SplitterData],
    smooth_strength: float,
    merge_distance: float,
    split_width: float,
    shrink_distance: float,
    narrow_connection_width: float,
    min_part_area: float,
    min_part_width: float,
) -> list[_ProcessedPolygonData]:
    """Process target polygons per normalized tag group.

    Arguments:
        target_polygons (list[_TargetPolygonData]): Target polygons paired
            with output tag metadata.
        hole_polygons (list[Polygon]): Area polygons that should carve holes.
        point_holes (list[_PointHoleData]): Point obstacles that should carve
            holes.
        splitter_lines (list[_SplitterData]): Linear features that may split
            polygons.
        smooth_strength (float): Corner-rounding strength in the [0, 1]
            range.
        merge_distance (float): Optional gap-closing merge distance in
            projected meters.
        split_width (float): Default splitter half-width in projected meters.
        shrink_distance (float): Final inward offset in projected meters.
        narrow_connection_width (float): Width threshold in projected meters
            for breaking thin bridges.
        min_part_area (float): Minimum fragment area in square meters.
        min_part_width (float): Minimum effective fragment width in meters.

    Returns:
        list[_ProcessedPolygonData]: Processed polygons paired with their
            surviving output tags.
    """
    if not target_polygons:
        return []

    grouped_targets: dict[tuple[tuple[str, str], ...], list[_TargetPolygonData]] = {}
    for target_polygon in target_polygons:
        grouped_targets.setdefault(target_polygon.merge_key, []).append(target_polygon)

    group_geometries = {
        merge_key: [target.geometry for target in group_targets]
        for merge_key, group_targets in grouped_targets.items()
    }

    processed_polygons: list[_ProcessedPolygonData] = []
    for merge_key, group_targets in grouped_targets.items():
        group_holes = list(hole_polygons)
        for other_merge_key, other_geometries in group_geometries.items():
            if other_merge_key == merge_key:
                continue
            group_holes.extend(other_geometries)

        group_target_keys = {
            key for target_polygon in group_targets for key in target_polygon.target_keys
        }

        group_output_polygons = _preprocess_polygons(
            target_polygons=group_geometries[merge_key],
            hole_polygons=group_holes,
            point_holes=point_holes,
            splitter_lines=splitter_lines,
            smooth_strength=smooth_strength,
            merge_distance=merge_distance,
            split_width=split_width,
            shrink_distance=shrink_distance,
            narrow_connection_width=narrow_connection_width,
            min_part_area=min_part_area,
            min_part_width=min_part_width,
        )
        if not group_output_polygons:
            continue

        group_tags = _common_output_tags(
            [target_polygon.tags for target_polygon in group_targets],
            merge_key,
            remove_keys=group_target_keys,
        )
        processed_polygons.extend(
            _ProcessedPolygonData(geometry=polygon, tags=group_tags)
            for polygon in group_output_polygons
        )

    return processed_polygons


def _smooth_polygons(
    polygons: list[Polygon],
    strength: float,
) -> list[Polygon]:
    """Round polygon corners without densifying straight edges.

    Arguments:
        polygons (list[Polygon]): Projected polygon geometries.
        strength (float): Corner-rounding strength in the [0, 1] range.

    Returns:
        list[Polygon]: Smoothed polygon geometries.
    """
    bounded_strength = max(0.0, min(1.0, strength))
    if bounded_strength <= 0:
        return polygons
    if not polygons:
        return []

    base_radius = 8.0 + (22.0 * bounded_strength)
    min_corner_deviation = math.radians(10.0 - (6.0 * bounded_strength))
    segment_count = 6 + int(8.0 * bounded_strength)

    smoothed_polygons: list[Polygon] = []
    for polygon in polygons:
        smoothed_polygon = _smooth_polygon(
            polygon,
            base_radius,
            min_corner_deviation,
            segment_count,
        )
        smoothed_polygons.extend(_geometry_to_polygons(make_valid(smoothed_polygon)) or [polygon])

    if not smoothed_polygons:
        return polygons

    return smoothed_polygons


def _split_polygons_at_narrow_connections(
    polygons: list[Polygon],
    connection_width: float,
) -> list[Polygon]:
    """Split polygons where a narrow bridge is the only connection.

    Arguments:
        polygons (list[Polygon]): Projected polygon geometries.
        connection_width (float): Width threshold in projected meters.

    Returns:
        list[Polygon]: Original polygons or the split lobes when a narrow
            connector is detected.
    """
    if connection_width <= 0 or not polygons:
        return polygons

    working_polygons = list(polygons)
    for _ in range(3):
        next_polygons: list[Polygon] = []
        split_any = False
        for polygon in working_polygons:
            split_polygons = _split_polygon_at_narrow_connection(
                polygon,
                connection_width,
            )
            if len(split_polygons) > 1:
                split_any = True
            next_polygons.extend(split_polygons)
        working_polygons = next_polygons
        if not split_any:
            break

    return working_polygons


def _split_polygon_at_narrow_connection(
    polygon: Polygon,
    connection_width: float,
) -> list[Polygon]:
    """Break one polygon into lobes when a thin connector is detected.

    Arguments:
        polygon (Polygon): Projected polygon geometry.
        connection_width (float): Width threshold in projected meters.

    Returns:
        list[Polygon]: Split polygon lobes, or the original polygon when no
            narrow connector is found.
    """
    if polygon.is_empty or connection_width <= 0:
        return [polygon]

    erosion_distance = connection_width / 2.0
    if erosion_distance <= 0:
        return [polygon]

    eroded_geometry = make_valid(polygon.buffer(-erosion_distance, join_style=1, cap_style=1))
    eroded_polygons = _geometry_to_polygons(eroded_geometry)
    if len(eroded_polygons) < 2:
        return [polygon]

    min_seed_area = max((erosion_distance * erosion_distance) * 2.0, polygon.area * 0.01)
    seed_polygons = [seed for seed in eroded_polygons if seed.area > min_seed_area]
    if len(seed_polygons) < 2:
        return [polygon]

    seed_polygons.sort(key=lambda seed: seed.area, reverse=True)
    assigned_geometries: list[BaseGeometry] = []
    split_polygons: list[Polygon] = []
    min_output_area = max(erosion_distance * erosion_distance, polygon.area * 0.005)

    for seed_polygon in seed_polygons:
        expanded_seed = make_valid(seed_polygon.buffer(erosion_distance, join_style=1, cap_style=1))
        candidate_geometry = make_valid(expanded_seed.intersection(polygon))
        if candidate_geometry.is_empty:
            continue
        if assigned_geometries:
            candidate_geometry = make_valid(
                candidate_geometry.difference(unary_union(assigned_geometries))
            )
        candidate_polygons = [
            candidate_polygon
            for candidate_polygon in _geometry_to_polygons(candidate_geometry)
            if candidate_polygon.area > min_output_area
        ]
        if not candidate_polygons:
            continue
        split_polygons.extend(candidate_polygons)
        assigned_geometries.extend(candidate_polygons)

    return split_polygons if len(split_polygons) >= 2 else [polygon]


def _inset_polygons(polygons: list[Polygon], shrink_distance: float) -> list[Polygon]:
    """Apply a small inward offset while preserving meaningful polygons.

    Arguments:
        polygons (list[Polygon]): Projected polygon geometries.
        shrink_distance (float): Inward offset distance in projected meters.

    Returns:
        list[Polygon]: Inset polygons, with originals retained when the inset
            would collapse the geometry.
    """
    if shrink_distance <= 0 or not polygons:
        return polygons

    inset_polygons: list[Polygon] = []
    for polygon in polygons:
        inset_geometry = make_valid(polygon.buffer(-shrink_distance, join_style=1, cap_style=1))
        min_output_area = max((shrink_distance * shrink_distance) * 0.25, polygon.area * 0.001)
        inset_parts = [
            inset_polygon
            for inset_polygon in _geometry_to_polygons(inset_geometry)
            if inset_polygon.area > min_output_area
        ]
        if inset_parts:
            inset_polygons.extend(inset_parts)
            continue
        inset_polygons.append(polygon)

    return inset_polygons


def _cleanup_cut_artifacts(
    polygons: list[Polygon],
    min_part_area: float,
    min_part_width: float,
) -> list[Polygon]:
    """Remove tiny detached fragments and narrow slivers.

    Arguments:
        polygons (list[Polygon]): Projected polygon geometries.
        min_part_area (float): Minimum fragment area in square meters.
        min_part_width (float): Minimum effective width in projected meters.

    Returns:
        list[Polygon]: Cleaned polygon fragments that satisfy the thresholds.
    """
    if not polygons:
        return []

    effective_min_area = max(0.0, min_part_area)
    opening_radius = max(0.0, min_part_width / 2.0)
    if effective_min_area <= 0 and opening_radius <= 0:
        return polygons

    cleaned_polygons: list[Polygon] = []
    for polygon in polygons:
        candidate_geometry: BaseGeometry = polygon
        if opening_radius > 0:
            candidate_geometry = make_valid(
                polygon.buffer(-opening_radius, join_style=1, cap_style=1).buffer(
                    opening_radius,
                    join_style=1,
                    cap_style=1,
                )
            )
            if candidate_geometry.is_empty:
                continue
            candidate_geometry = make_valid(candidate_geometry.intersection(polygon))

        for candidate_polygon in _geometry_to_polygons(candidate_geometry):
            if candidate_polygon.is_empty:
                continue
            if effective_min_area > 0 and candidate_polygon.area < effective_min_area:
                continue
            cleaned_polygons.append(candidate_polygon)

    return cleaned_polygons


def _smooth_polygon(
    polygon: Polygon,
    radius: float,
    min_corner_deviation: float,
    segment_count: int,
) -> Polygon:
    """Smooth one polygon ring-by-ring by rounding actual corners.

    Arguments:
        polygon (Polygon): Projected polygon geometry.
        radius (float): Maximum rounding radius in projected meters.
        min_corner_deviation (float): Minimum angular deviation in radians
            required before a corner is rounded.
        segment_count (int): Base number of segments used to interpolate the
            rounded corner arc.

    Returns:
        Polygon: Smoothed polygon geometry.
    """
    if polygon.is_empty:
        return polygon

    exterior = _smooth_ring(
        list(polygon.exterior.coords),
        radius,
        min_corner_deviation,
        segment_count,
    )
    if len(exterior) < 4:
        return polygon

    interiors: list[list[tuple[float, float]]] = []
    for interior in polygon.interiors:
        smoothed_interior = _smooth_ring(
            list(interior.coords),
            radius,
            min_corner_deviation,
            segment_count,
        )
        if len(smoothed_interior) >= 4:
            interiors.append(smoothed_interior)

    candidate = Polygon(exterior, interiors)
    return polygon if candidate.is_empty else candidate


def _smooth_ring(
    coordinates: list[tuple[float, float]],
    radius: float,
    min_corner_deviation: float,
    segment_count: int,
) -> list[tuple[float, float]]:
    """Round meaningful corners on a ring while leaving straight edges alone.

    Arguments:
        coordinates (list[tuple[float, float]]): Closed ring coordinates in
            projected meters.
        radius (float): Maximum rounding radius in projected meters.
        min_corner_deviation (float): Minimum angular deviation in radians
            required before a corner is rounded.
        segment_count (int): Base number of interpolation segments per corner.

    Returns:
        list[tuple[float, float]]: Smoothed closed ring coordinates.
    """
    if len(coordinates) < 4 or radius <= 0:
        return coordinates

    control_coordinates = _build_smoothing_control_ring(coordinates, radius)
    points = control_coordinates[:-1]
    if len(points) < 3:
        return coordinates

    rounded_points: list[tuple[float, float]] = []
    rounded_corner_count = 0
    alignment_tolerance = max(math.radians(35.0), min_corner_deviation * 3.0)
    max_corner_search_distance = max(radius / 0.45, radius * 1.5)
    probe_distance = max(radius, 2.0)

    for index, point in enumerate(points):
        previous_probe = _point_along_ring_side(points, index, -1, probe_distance)
        next_probe = _point_along_ring_side(points, index, 1, probe_distance)

        to_previous_probe = (
            previous_probe[0] - point[0],
            previous_probe[1] - point[1],
        )
        to_next_probe = (next_probe[0] - point[0], next_probe[1] - point[1])
        previous_probe_length = math.hypot(*to_previous_probe)
        next_probe_length = math.hypot(*to_next_probe)
        if previous_probe_length <= 1e-6 or next_probe_length <= 1e-6:
            if not rounded_points or rounded_points[-1] != point:
                rounded_points.append(point)
            continue

        cosine = (
            (to_previous_probe[0] * to_next_probe[0]) + (to_previous_probe[1] * to_next_probe[1])
        ) / (previous_probe_length * next_probe_length)
        cosine = max(-1.0, min(1.0, cosine))
        angle = math.acos(cosine)
        deviation = math.pi - angle
        if deviation <= min_corner_deviation:
            if not rounded_points or rounded_points[-1] != point:
                rounded_points.append(point)
            continue

        previous_run_length = _available_ring_side_length(
            points,
            index,
            -1,
            (
                to_previous_probe[0] / previous_probe_length,
                to_previous_probe[1] / previous_probe_length,
            ),
            alignment_tolerance,
            max_corner_search_distance,
        )
        next_run_length = _available_ring_side_length(
            points,
            index,
            1,
            (to_next_probe[0] / next_probe_length, to_next_probe[1] / next_probe_length),
            alignment_tolerance,
            max_corner_search_distance,
        )

        local_radius = min(
            radius * min(1.0, deviation / (math.pi / 2.0)),
            previous_run_length * 0.45,
            next_run_length * 0.45,
        )
        if local_radius <= 0.25:
            if not rounded_points or rounded_points[-1] != point:
                rounded_points.append(point)
            continue

        start_point = _point_along_ring_side(
            points,
            index,
            -1,
            local_radius,
        )
        end_point = _point_along_ring_side(
            points,
            index,
            1,
            local_radius,
        )

        corner_segments = max(
            3,
            segment_count + int((deviation / (math.pi / 2.0)) * 2.0),
        )
        corner_points = _quadratic_bezier_points(
            start_point,
            point,
            end_point,
            corner_segments,
        )
        if not rounded_points or rounded_points[-1] != corner_points[0]:
            rounded_points.append(corner_points[0])
        rounded_points.extend(corner_points[1:])
        rounded_corner_count += 1

    if len(rounded_points) < 3 or rounded_corner_count == 0:
        return coordinates

    deduped_points: list[tuple[float, float]] = []
    for rounded_point in rounded_points:
        if (
            deduped_points
            and math.isclose(deduped_points[-1][0], rounded_point[0], abs_tol=1e-6)
            and math.isclose(
                deduped_points[-1][1],
                rounded_point[1],
                abs_tol=1e-6,
            )
        ):
            continue
        deduped_points.append(rounded_point)

    if len(deduped_points) < 3:
        return coordinates

    return [*deduped_points, deduped_points[0]]


def _build_smoothing_control_ring(
    coordinates: list[tuple[float, float]],
    radius: float,
) -> list[tuple[float, float]]:
    """Return a simplified control ring for stable corner detection.

    The geometric cleanup steps can introduce many tiny segments around what is still
    visually one corner. This helper lightly simplifies the ring only for smoothing so the
    radius is applied to the effective corner rather than to each micro-segment.

    Arguments:
        coordinates (list[tuple[float, float]]): Closed ring coordinates.
        radius (float): Requested corner radius in projected meters.

    Returns:
        list[tuple[float, float]]: Closed control ring coordinates.
    """
    simplify_tolerance = max(0.75, radius * 0.18)
    control_line = LineString(coordinates).simplify(simplify_tolerance, preserve_topology=False)
    control_coordinates = list(control_line.coords)
    if not control_coordinates:
        return coordinates
    if control_coordinates[0] != control_coordinates[-1]:
        control_coordinates.append(control_coordinates[0])

    deduped_coordinates: list[tuple[float, float]] = []
    for coordinate in control_coordinates:
        if (
            deduped_coordinates
            and math.isclose(deduped_coordinates[-1][0], coordinate[0], abs_tol=1e-6)
            and math.isclose(deduped_coordinates[-1][1], coordinate[1], abs_tol=1e-6)
        ):
            continue
        deduped_coordinates.append(coordinate)

    return deduped_coordinates if len(deduped_coordinates) >= 4 else coordinates


def _available_ring_side_length(
    points: list[tuple[float, float]],
    corner_index: int,
    step: int,
    reference_direction: tuple[float, float],
    alignment_tolerance: float,
    max_distance: float,
) -> float:
    """Measure usable path length on one side of a corner.

    The walk stops once the ring bends too far away from the initial edge direction.

    Arguments:
        points (list[tuple[float, float]]): Open ring point sequence.
        corner_index (int): Index of the corner point.
        step (int): Ring traversal direction, either -1 or 1.
        reference_direction (tuple[float, float]): Unit direction vector for the
            first segment leaving the corner on this side.
        alignment_tolerance (float): Maximum angular drift in radians allowed while
            extending the side length.
        max_distance (float): Hard cap on the measured distance.

    Returns:
        float: Usable path length along the requested side.
    """
    total_length = 0.0
    current_index = corner_index

    for _ in range(len(points) - 1):
        next_index = (current_index + step) % len(points)
        segment = (
            points[next_index][0] - points[current_index][0],
            points[next_index][1] - points[current_index][1],
        )
        segment_length = math.hypot(*segment)
        if segment_length <= 1e-6:
            current_index = next_index
            continue

        segment_direction = (segment[0] / segment_length, segment[1] / segment_length)
        if (
            _angle_between_unit_vectors(segment_direction, reference_direction)
            > alignment_tolerance
        ):
            break

        total_length += segment_length
        if total_length >= max_distance:
            return max_distance

        current_index = next_index

    return total_length


def _point_along_ring_side(
    points: list[tuple[float, float]],
    corner_index: int,
    step: int,
    distance: float,
) -> tuple[float, float]:
    """Return a point at a path distance from the corner along one ring side.

    Arguments:
        points (list[tuple[float, float]]): Open ring point sequence.
        corner_index (int): Index of the corner point.
        step (int): Ring traversal direction, either -1 or 1.
        distance (float): Path distance to travel from the corner.

    Returns:
        tuple[float, float]: Coordinate located on the ring path.
    """
    if distance <= 0:
        return points[corner_index]

    remaining_distance = distance
    current_index = corner_index
    current_point = points[corner_index]

    for _ in range(len(points) - 1):
        next_index = (current_index + step) % len(points)
        next_point = points[next_index]
        segment = (
            next_point[0] - current_point[0],
            next_point[1] - current_point[1],
        )
        segment_length = math.hypot(*segment)
        if segment_length <= 1e-6:
            current_index = next_index
            current_point = next_point
            continue

        if remaining_distance <= segment_length:
            ratio = remaining_distance / segment_length
            return (
                current_point[0] + (segment[0] * ratio),
                current_point[1] + (segment[1] * ratio),
            )

        remaining_distance -= segment_length
        current_index = next_index
        current_point = next_point

    return current_point


def _angle_between_unit_vectors(
    first: tuple[float, float],
    second: tuple[float, float],
) -> float:
    """Return the angle between two unit vectors in radians."""
    cosine = max(-1.0, min(1.0, (first[0] * second[0]) + (first[1] * second[1])))
    return math.acos(cosine)


def _quadratic_bezier_points(
    start_point: tuple[float, float],
    control_point: tuple[float, float],
    end_point: tuple[float, float],
    segment_count: int,
) -> list[tuple[float, float]]:
    """Create interpolated points for a rounded corner curve.

    Arguments:
        start_point (tuple[float, float]): Curve start coordinate.
        control_point (tuple[float, float]): Quadratic Bezier control point.
        end_point (tuple[float, float]): Curve end coordinate.
        segment_count (int): Number of interpolation segments.

    Returns:
        list[tuple[float, float]]: Interpolated curve coordinates including
            the start and end points.
    """
    point_count = max(2, segment_count)
    curve_points: list[tuple[float, float]] = []
    for index in range(point_count + 1):
        t = index / point_count
        one_minus_t = 1.0 - t
        curve_points.append(
            (
                (one_minus_t * one_minus_t * start_point[0])
                + (2.0 * one_minus_t * t * control_point[0])
                + (t * t * end_point[0]),
                (one_minus_t * one_minus_t * start_point[1])
                + (2.0 * one_minus_t * t * control_point[1])
                + (t * t * end_point[1]),
            )
        )

    return curve_points


def _build_local_transformers(reference_geometry: BaseGeometry) -> tuple[Transformer, Transformer]:
    """Build forward and backward transformers for a local UTM zone.

    Arguments:
        reference_geometry (BaseGeometry): Geometry used to choose the local
            projected CRS.

    Returns:
        tuple[Transformer, Transformer]: Forward and backward CRS
            transformers.
    """
    centroid = reference_geometry.centroid
    epsg_code = _utm_epsg_for_coordinate(centroid.x, centroid.y)
    forward = Transformer.from_crs("EPSG:4326", f"EPSG:{epsg_code}", always_xy=True)
    backward = Transformer.from_crs(f"EPSG:{epsg_code}", "EPSG:4326", always_xy=True)
    return forward, backward


def _utm_epsg_for_coordinate(longitude: float, latitude: float) -> int:
    """Return the UTM EPSG code for a geographic coordinate.

    Arguments:
        longitude (float): Longitude in degrees.
        latitude (float): Latitude in degrees.

    Returns:
        int: EPSG code for the local UTM zone.
    """
    zone = min(max(int((longitude + 180.0) // 6.0) + 1, 1), 60)
    return (32600 if latitude >= 0 else 32700) + zone


def _transform_geometry(geometry: BaseGeometry, transformer: Transformer) -> BaseGeometry:
    """Transform geometry coordinates using a CRS transformer.

    Arguments:
        geometry (BaseGeometry): Geometry to transform.
        transformer (Transformer): Coordinate transformer to apply.

    Returns:
        BaseGeometry: Transformed geometry.
    """
    return transform(transformer.transform, geometry)


def _transform_polygons(polygons: list[Polygon], transformer: Transformer) -> list[Polygon]:
    """Transform polygons and flatten the resulting polygonal geometry.

    Arguments:
        polygons (list[Polygon]): Polygon geometries to transform.
        transformer (Transformer): Coordinate transformer to apply.

    Returns:
        list[Polygon]: Valid transformed polygons.
    """
    transformed_polygons: list[Polygon] = []
    for polygon in polygons:
        transformed = make_valid(_transform_geometry(polygon, transformer))
        transformed_polygons.extend(_geometry_to_polygons(transformed))
    return transformed_polygons


def _splitter_buffer_width(tags: dict[str, str], default_split_width: float) -> float:
    """Return a feature-aware splitter half-width in projected meters.

    Arguments:
        tags (dict[str, str]): Tags from the linear splitter feature.
        default_split_width (float): Default half-width in projected meters.

    Returns:
        float: Splitter half-width in projected meters.
    """
    if default_split_width <= 0:
        return 0.0

    if tags.get("natural") == "tree_row":
        return 1.0

    highway_value = tags.get("highway")
    width = default_split_width
    if highway_value:
        highway_widths = {
            "path": 1.5,
            "footway": 1.5,
            "cycleway": 1.5,
            "bridleway": 2.0,
            "track": 3.0,
            "service": 3.5,
            "residential": 4.0,
            "unclassified": 4.0,
            "tertiary": 4.5,
            "secondary": 5.0,
            "primary": 6.0,
            "trunk": 7.0,
            "motorway": 8.0,
        }
        width = max(width, highway_widths.get(highway_value, 4.0))
    elif "railway" in tags:
        width = max(width, 5.0)
    elif "waterway" in tags:
        width = max(width, 3.0)
    elif "barrier" in tags:
        width = max(width, 1.5)
    elif "aerialway" in tags:
        width = max(width, 1.5)
    elif "power" in tags:
        width = max(width, 2.0)

    return width


def _buffer_splitter_geometry(
    splitter: _SplitterData,
    projected_line: LineString,
    buffer_width: float,
) -> BaseGeometry:
    """Return splitter cut geometry with rounded terminal endpoints.

    Continuous roads should keep flat joins at shared way endpoints so field cuts do not bulge at
    every OSM way break. True dead-end endpoints, however, look artificial with a flat cap, so
    they receive a local round cap.

    Arguments:
        splitter (_SplitterData): Splitter metadata, including terminal-end flags.
        projected_line (LineString): Splitter geometry in projected meters.
        buffer_width (float): Splitter half-width in projected meters.

    Returns:
        BaseGeometry: Polygonal cut geometry for the splitter.
    """
    base_buffer = projected_line.buffer(buffer_width, cap_style=2, join_style=2)
    coordinates = list(projected_line.coords)
    if len(coordinates) < 2:
        return base_buffer

    cap_geometries: list[BaseGeometry] = [base_buffer]
    if splitter.round_start:
        cap_geometries.append(Point(coordinates[0]).buffer(buffer_width))
    if splitter.round_end:
        cap_geometries.append(Point(coordinates[-1]).buffer(buffer_width))

    return base_buffer if len(cap_geometries) == 1 else make_valid(unary_union(cap_geometries))


def _geometry_to_polygons(geometry: BaseGeometry) -> list[Polygon]:
    """Extract polygon members from arbitrary geometry output.

    Arguments:
        geometry (BaseGeometry): Geometry that may contain polygonal parts.

    Returns:
        list[Polygon]: Polygon members extracted from the input geometry.
    """
    if geometry.is_empty:
        return []
    if isinstance(geometry, Polygon):
        return [geometry]
    if isinstance(geometry, MultiPolygon):
        return [polygon for polygon in geometry.geoms if not polygon.is_empty]
    if isinstance(geometry, GeometryCollection):
        polygons: list[Polygon] = []
        for member in geometry.geoms:
            polygons.extend(_geometry_to_polygons(member))
        return polygons
    return []


def _remove_target_elements(
    root: ET.Element,
    target_way_ids: set[int],
    target_relation_ids: set[int],
    ways: dict[int, _WayData],
    relations: dict[int, _RelationData],
) -> int:
    """Remove replaced target elements from the XML tree.

    Arguments:
        root (ET.Element): Root OSM XML element.
        target_way_ids (set[int]): Way ids to remove.
        target_relation_ids (set[int]): Relation ids to remove.
        ways (dict[int, _WayData]): Parsed OSM ways by id.
        relations (dict[int, _RelationData]): Parsed OSM relations by id.

    Returns:
        int: Number of removed way and relation elements.
    """
    removed_elements = 0

    for way_id in target_way_ids:
        way = ways.get(way_id)
        if not way:
            continue
        root.remove(way.element)
        removed_elements += 1

    for relation_id in target_relation_ids:
        relation = relations.get(relation_id)
        if not relation:
            continue
        root.remove(relation.element)
        removed_elements += 1

    return removed_elements


def _append_polygons(root: ET.Element, polygons: list[_ProcessedPolygonData]) -> tuple[int, int]:
    """Append processed polygons as OSM ways and relations.

    Arguments:
        root (ET.Element): Root OSM XML element.
        polygons (list[_ProcessedPolygonData]): Processed polygons paired with
            output tags.

    Returns:
        tuple[int, int]: Number of created ways and created relations.
    """
    node_ids = [
        int(existing_node_id)
        for node in root.findall("node")
        if (existing_node_id := node.get("id")) is not None
    ]
    way_ids = [
        int(existing_way_id)
        for way in root.findall("way")
        if (existing_way_id := way.get("id")) is not None
    ]
    relation_ids = [
        int(existing_relation_id)
        for relation in root.findall("relation")
        if (existing_relation_id := relation.get("id")) is not None
    ]

    next_node_id = max([0, *node_ids]) + 1
    next_way_id = max([0, *way_ids]) + 1
    next_relation_id = max([0, *relation_ids]) + 1

    node_cache: dict[tuple[float, float], int] = {}
    created_ways = 0
    created_relations = 0

    def append_node(coordinate: tuple[float, float]) -> int:
        """Append or reuse a node for one coordinate.

        Arguments:
            coordinate (tuple[float, float]): ``(longitude, latitude)`` pair.

        Returns:
            int: Node id for the rounded coordinate.
        """
        nonlocal next_node_id
        rounded = (round(coordinate[0], 10), round(coordinate[1], 10))
        cached = node_cache.get(rounded)
        if cached is not None:
            return cached

        node_id = next_node_id
        next_node_id += 1
        node_cache[rounded] = node_id

        node_element = ET.SubElement(root, "node")
        node_element.set("id", str(node_id))
        node_element.set("lat", f"{rounded[1]:.10f}")
        node_element.set("lon", f"{rounded[0]:.10f}")
        node_element.set("version", "1")
        return node_id

    def append_way(
        coordinates: list[tuple[float, float]], way_tags: dict[str, str] | None = None
    ) -> int:
        """Append one OSM way built from coordinates and optional tags.

        Arguments:
            coordinates (list[tuple[float, float]]): Way coordinates in
                geographic order.
            way_tags (dict[str, str] | None): Optional tags to attach to the
                way element.

        Returns:
            int: Newly created way id.
        """
        nonlocal next_way_id, created_ways
        way_id = next_way_id
        next_way_id += 1
        created_ways += 1

        way_element = ET.SubElement(root, "way")
        way_element.set("id", str(way_id))
        way_element.set("version", "1")
        for coordinate in coordinates:
            nd_element = ET.SubElement(way_element, "nd")
            nd_element.set("ref", str(append_node(coordinate)))

        for key, value in (way_tags or {}).items():
            tag_element = ET.SubElement(way_element, "tag")
            tag_element.set("k", key)
            tag_element.set("v", value)

        return way_id

    for polygon_data in polygons:
        polygon = polygon_data.geometry
        polygon_tags = polygon_data.tags
        exterior_coordinates = list(polygon.exterior.coords)
        interior_coordinates = [list(interior.coords) for interior in polygon.interiors]
        if not exterior_coordinates:
            continue

        if not interior_coordinates:
            append_way(exterior_coordinates, polygon_tags)
            continue

        outer_way_id = append_way(exterior_coordinates)
        inner_way_ids = [append_way(interior) for interior in interior_coordinates if interior]

        relation_id = next_relation_id
        next_relation_id += 1
        created_relations += 1

        relation_element = ET.SubElement(root, "relation")
        relation_element.set("id", str(relation_id))
        relation_element.set("version", "1")

        outer_member = ET.SubElement(relation_element, "member")
        outer_member.set("type", "way")
        outer_member.set("ref", str(outer_way_id))
        outer_member.set("role", "outer")

        for inner_way_id in inner_way_ids:
            inner_member = ET.SubElement(relation_element, "member")
            inner_member.set("type", "way")
            inner_member.set("ref", str(inner_way_id))
            inner_member.set("role", "inner")

        type_tag = ET.SubElement(relation_element, "tag")
        type_tag.set("k", "type")
        type_tag.set("v", "multipolygon")

        for key, value in polygon_tags.items():
            tag_element = ET.SubElement(relation_element, "tag")
            tag_element.set("k", key)
            tag_element.set("v", value)

    return created_ways, created_relations


def _remove_orphan_untagged_nodes(root: ET.Element) -> int:
    """Remove nodes that have no tags and are not referenced by any way or relation.

    Arguments:
        root (ET.Element): Root OSM XML element.

    Returns:
        int: Number of removed orphan nodes.
    """
    referenced_node_ids: set[int] = set()

    for way_element in root.findall("way"):
        for nd_element in way_element.findall("nd"):
            ref_value = nd_element.get("ref")
            if ref_value is None:
                continue
            try:
                referenced_node_ids.add(int(ref_value))
            except ValueError:
                continue

    for relation_element in root.findall("relation"):
        for member_element in relation_element.findall("member"):
            if member_element.get("type") != "node":
                continue
            ref_value = member_element.get("ref")
            if ref_value is None:
                continue
            try:
                referenced_node_ids.add(int(ref_value))
            except ValueError:
                continue

    removed_nodes = 0
    for node_element in list(root.findall("node")):
        node_id = node_element.get("id")
        if node_id is None:
            continue
        try:
            parsed_node_id = int(node_id)
        except ValueError:
            continue
        if parsed_node_id in referenced_node_ids:
            continue
        if node_element.findall("tag"):
            continue

        root.remove(node_element)
        removed_nodes += 1

    return removed_nodes


def _ensure_primitive_versions(root: ET.Element) -> None:
    """Ensure all OSM primitives have a version attribute.

    Arguments:
        root (ET.Element): Root OSM XML element.
    """
    for primitive_name in ("node", "way", "relation"):
        for element in root.findall(primitive_name):
            if not element.get("version"):
                element.set("version", "1")
