"""OSM file validation and repair utilities."""

from __future__ import annotations

import math
import os
import shutil
from dataclasses import dataclass
from typing import TypeAlias
from xml.etree import ElementTree as ET

import osmnx as ox
from osmnx._errors import InsufficientResponseError
from pyproj import Transformer
from shapely.geometry import GeometryCollection, LineString, MultiPolygon, Point, Polygon
from shapely.geometry.base import BaseGeometry
from shapely.ops import transform, unary_union
from shapely.validation import make_valid

# Representative tags — if the file is fundamentally broken it will fail on any of these.
OSMTagValue: TypeAlias = bool | str | list[str]

_CHECK_TAGS: list[dict[str, OSMTagValue]] = [
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
    ("power", "tower"): 4.0,
    ("power", "portal"): 4.0,
    ("power", "pole"): 1.5,
    ("power", "catenary_mast"): 1.5,
    ("man_made", "tower"): 4.0,
    ("man_made", "mast"): 3.0,
}


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


def preprocess(
    input_file_path: str,
    output_file_path: str,
    tags: dict[str, OSMTagValue],
    exclude_cut_tags: dict[str, OSMTagValue] | None = None,
    smooth_strength: float = 0.3,
    merge_distance: float = 0.0,
    split_width: float = 4.0,
    merge_tags: bool = True,
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
        tags (dict[str, OSMTagValue]): Tag filter for target polygons.
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
        shrink_distance (float): Final inward offset in meters applied after
            smoothing so polygons sit slightly inside the original boundary.
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
    if not tags:
        raise ValueError("At least one tag must be provided for preprocessing.")
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
            tags=tags,
            nodes=nodes,
            ways=ways,
            relations=relations,
            relation_way_usage=relation_way_usage,
            merge_tags=merge_tags,
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

    hole_polygons = _collect_hole_polygons(
        tags=tags,
        nodes=nodes,
        ways=ways,
        relations=relations,
        excluded_way_ids=target_way_ids | target_member_way_ids,
        excluded_relation_ids=target_relation_ids,
    )
    point_holes = _collect_point_holes(root=root, tags=tags, nodes=nodes)
    splitter_lines = _collect_splitter_lines(
        nodes=nodes,
        ways=ways,
        excluded_way_ids=target_way_ids,
        exclude_cut_tags=exclude_cut_tags,
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


def _parse_nodes(root: ET.Element) -> dict[int, tuple[float, float]]:
    """Read all node coordinates from OSM XML."""
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
    """Read all ways from OSM XML."""
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
    """Read all relations from OSM XML."""
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
    """Extract OSM tag dictionary from an element."""
    tags: dict[str, str] = {}
    for tag in element.findall("tag"):
        key = tag.get("k")
        value = tag.get("v")
        if key and value is not None:
            tags[key] = value
    return tags


def _count_relation_way_usage(relations: dict[int, _RelationData]) -> dict[int, int]:
    """Count how many relations reference each way id."""
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
    """Build a merge key from the actual matched tag values."""
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
    """Return the canonical merge/output value for a matched target tag."""
    if not merge_tags:
        return actual_value
    if isinstance(expected_value, list) and expected_value and actual_value in expected_value:
        return expected_value[0]
    return actual_value


def _output_feature_tags(feature_tags: dict[str, str]) -> dict[str, str]:
    """Return the source tags that should be preserved on rewritten output."""
    return {key: value for key, value in feature_tags.items() if key != "type"}


def _common_output_tags(
    tag_sets: list[dict[str, str]], merge_key: tuple[tuple[str, str], ...]
) -> dict[str, str]:
    """Return tags common to the group, forcing the merge-key tags to survive."""
    if not tag_sets:
        return dict(merge_key)

    common_tags = dict(tag_sets[0])
    for tag_set in tag_sets[1:]:
        common_tags = {
            key: value for key, value in common_tags.items() if tag_set.get(key) == value
        }

    for key, value in merge_key:
        common_tags[key] = value
    return common_tags


def _matches_tags(feature_tags: dict[str, str], target_tags: dict[str, OSMTagValue]) -> bool:
    """Return True when feature tags satisfy the provided filter."""
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


def _is_area_way(way: _WayData) -> bool:
    """Heuristically classify whether a way is an area polygon."""
    if len(way.node_refs) < 4 or way.node_refs[0] != way.node_refs[-1]:
        return False

    area_value = way.tags.get("area")
    if area_value == "no":
        return False
    if area_value == "yes":
        return True

    return not any(tag in _LINEAR_TAGS for tag in way.tags)


def _way_to_polygon(way: _WayData, nodes: dict[int, tuple[float, float]]) -> Polygon | None:
    """Build a polygon from a way when possible."""
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


def _relation_to_polygons(
    relation: _RelationData,
    ways: dict[int, _WayData],
    nodes: dict[int, tuple[float, float]],
) -> tuple[list[Polygon], set[int]]:
    """Build polygons from a multipolygon relation.

    Returns:
        tuple[list[Polygon], set[int]]: Relation polygons and all way ids referenced by the relation.
    """
    if relation.tags.get("type") != "multipolygon":
        return [], set()

    outer_polygons: list[Polygon] = []
    inner_polygons: list[Polygon] = []
    member_way_ids: set[int] = set()

    for member_type, member_ref, role in relation.members:
        if member_type != "way":
            continue
        member_way = ways.get(member_ref)
        if not member_way:
            continue
        polygon = _way_to_polygon(member_way, nodes)
        if polygon is None:
            continue
        member_way_ids.add(member_ref)
        if role == "inner":
            inner_polygons.append(polygon)
        else:
            outer_polygons.append(polygon)

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
    tags: dict[str, OSMTagValue],
    nodes: dict[int, tuple[float, float]],
    ways: dict[int, _WayData],
    relations: dict[int, _RelationData],
    relation_way_usage: dict[int, int],
    merge_tags: bool,
) -> tuple[set[int], set[int], set[int], list[_TargetPolygonData]]:
    """Collect all target polygons plus element ids that should be replaced."""
    target_way_ids: set[int] = set()
    target_relation_ids: set[int] = set()
    target_member_way_ids: set[int] = set()
    target_polygons: list[_TargetPolygonData] = []

    for way_id, way in ways.items():
        if not way.tags or not _matches_tags(way.tags, tags):
            continue
        polygon = _way_to_polygon(way, nodes)
        if polygon is None:
            continue
        target_way_ids.add(way_id)
        target_polygons.append(
            _TargetPolygonData(
                geometry=polygon,
                tags=_output_feature_tags(way.tags),
                merge_key=_target_merge_key(way.tags, tags, merge_tags),
            )
        )

    for relation_id, relation in relations.items():
        if not _matches_tags(relation.tags, tags):
            continue
        relation_polygons, member_way_ids = _relation_to_polygons(relation, ways, nodes)
        if not relation_polygons:
            continue
        target_relation_ids.add(relation_id)
        relation_output_tags = _output_feature_tags(relation.tags)
        relation_merge_key = _target_merge_key(relation.tags, tags, merge_tags)
        target_polygons.extend(
            _TargetPolygonData(
                geometry=polygon,
                tags=relation_output_tags,
                merge_key=relation_merge_key,
            )
            for polygon in relation_polygons
        )

        for member_way_id in member_way_ids:
            way = ways.get(member_way_id)
            if not way or way.tags:
                continue
            if relation_way_usage.get(member_way_id, 0) == 1:
                target_member_way_ids.add(member_way_id)

    return target_way_ids, target_relation_ids, target_member_way_ids, target_polygons


def _collect_hole_polygons(
    tags: dict[str, OSMTagValue],
    nodes: dict[int, tuple[float, float]],
    ways: dict[int, _WayData],
    relations: dict[int, _RelationData],
    excluded_way_ids: set[int],
    excluded_relation_ids: set[int],
) -> list[Polygon]:
    """Collect area polygons that should be subtracted from target polygons."""
    hole_polygons: list[Polygon] = []

    for way_id, way in ways.items():
        if way_id in excluded_way_ids or not way.tags:
            continue
        if _matches_tags(way.tags, tags):
            continue
        polygon = _way_to_polygon(way, nodes)
        if polygon is not None:
            hole_polygons.append(polygon)

    for relation_id, relation in relations.items():
        if relation_id in excluded_relation_ids:
            continue
        if relation.tags.get("type") != "multipolygon":
            continue
        if _matches_tags(relation.tags, tags):
            continue
        relation_polygons, _ = _relation_to_polygons(relation, ways, nodes)
        hole_polygons.extend(relation_polygons)

    return hole_polygons


def _collect_point_holes(
    root: ET.Element,
    tags: dict[str, OSMTagValue],
    nodes: dict[int, tuple[float, float]],
) -> list[_PointHoleData]:
    """Collect point obstacles that should carve circular holes in target polygons."""
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

        node_tags = _extract_tags(node_element)
        if not node_tags or _matches_tags(node_tags, tags):
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
    """Return the projected-meter hole radius for tagged point obstacles."""
    best_radius = 0.0
    for key, value in tags.items():
        best_radius = max(best_radius, _POINT_HOLE_RADII.get((key, value), 0.0))
    return best_radius


def _collect_splitter_lines(
    nodes: dict[int, tuple[float, float]],
    ways: dict[int, _WayData],
    excluded_way_ids: set[int],
    exclude_cut_tags: dict[str, OSMTagValue] | None,
) -> list[_SplitterData]:
    """Collect linear objects that may split target polygons."""
    lines: list[_SplitterData] = []

    for way_id, way in ways.items():
        if way_id in excluded_way_ids:
            continue
        if not way.tags:
            continue
        if exclude_cut_tags and _matches_tags(way.tags, exclude_cut_tags):
            continue
        if _is_area_way(way):
            continue
        if not any(tag in _CUT_LINEAR_TAGS for tag in way.tags):
            continue
        if len(way.node_refs) < 2:
            continue

        coordinates = [nodes[node_id] for node_id in way.node_refs if node_id in nodes]
        if len(coordinates) < 2:
            continue
        if len(set(coordinates)) < 2:
            continue

        line = LineString(coordinates)
        if line.is_empty:
            continue
        lines.append(_SplitterData(geometry=line, tags=way.tags))

    return lines


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
    """Apply split/merge/hole cleanup, then smooth, inset and remove artifacts."""
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
            split_buffers.append(projected_line.buffer(buffer_width, cap_style=2, join_style=2))

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
    """Merge touching polygons and optionally close tiny gaps when requested."""
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
    """Process targets per matched tag group so tags and merges stay correct."""
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
    """Smooth polygons by rounding corners without densifying straight edges."""
    bounded_strength = max(0.0, min(1.0, strength))
    if bounded_strength <= 0:
        return polygons
    if not polygons:
        return []

    base_radius = 8.0 + (22.0 * bounded_strength)
    min_corner_deviation = math.radians(12.0 - (6.0 * bounded_strength))
    segment_count = 5 + int(7.0 * bounded_strength)

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
    """Split polygons where a very narrow bridge is the only connection."""
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
    """Break a polygon into lobes when a thin connector falls below the threshold."""
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
    """Apply a small inward offset while keeping tiny polygons from disappearing."""
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
    """Remove tiny detached fragments and narrow slivers in projected meters."""
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
    """Smooth a single polygon ring-by-ring by rounding only actual corners."""
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
    """Round only meaningful corners while leaving straight edges untouched."""
    if len(coordinates) < 4 or radius <= 0:
        return coordinates

    points = coordinates[:-1]
    if len(points) < 3:
        return coordinates

    rounded_points: list[tuple[float, float]] = []
    rounded_corner_count = 0
    for index, point in enumerate(points):
        previous_point = points[index - 1]
        next_point = points[(index + 1) % len(points)]

        to_previous = (previous_point[0] - point[0], previous_point[1] - point[1])
        to_next = (next_point[0] - point[0], next_point[1] - point[1])
        previous_length = math.hypot(*to_previous)
        next_length = math.hypot(*to_next)
        if previous_length <= 1e-6 or next_length <= 1e-6:
            if not rounded_points or rounded_points[-1] != point:
                rounded_points.append(point)
            continue

        cosine = ((to_previous[0] * to_next[0]) + (to_previous[1] * to_next[1])) / (
            previous_length * next_length
        )
        cosine = max(-1.0, min(1.0, cosine))
        angle = math.acos(cosine)
        deviation = math.pi - angle
        if deviation <= min_corner_deviation:
            if not rounded_points or rounded_points[-1] != point:
                rounded_points.append(point)
            continue

        local_radius = min(
            radius * min(1.0, deviation / (math.pi / 2.0)),
            previous_length * 0.4,
            next_length * 0.4,
        )
        if local_radius <= 0.25:
            if not rounded_points or rounded_points[-1] != point:
                rounded_points.append(point)
            continue

        start_point = (
            point[0] + ((to_previous[0] / previous_length) * local_radius),
            point[1] + ((to_previous[1] / previous_length) * local_radius),
        )
        end_point = (
            point[0] + ((to_next[0] / next_length) * local_radius),
            point[1] + ((to_next[1] / next_length) * local_radius),
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


def _quadratic_bezier_points(
    start_point: tuple[float, float],
    control_point: tuple[float, float],
    end_point: tuple[float, float],
    segment_count: int,
) -> list[tuple[float, float]]:
    """Create interpolated points for a rounded corner curve."""
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
    """Build forward/backward transformers for a local UTM zone."""
    centroid = reference_geometry.centroid
    epsg_code = _utm_epsg_for_coordinate(centroid.x, centroid.y)
    forward = Transformer.from_crs("EPSG:4326", f"EPSG:{epsg_code}", always_xy=True)
    backward = Transformer.from_crs(f"EPSG:{epsg_code}", "EPSG:4326", always_xy=True)
    return forward, backward


def _utm_epsg_for_coordinate(longitude: float, latitude: float) -> int:
    """Return the UTM EPSG code for a lon/lat coordinate."""
    zone = min(max(int((longitude + 180.0) // 6.0) + 1, 1), 60)
    return (32600 if latitude >= 0 else 32700) + zone


def _transform_geometry(geometry: BaseGeometry, transformer: Transformer) -> BaseGeometry:
    """Transform geometry coordinates using the provided CRS transformer."""
    return transform(transformer.transform, geometry)


def _transform_polygons(polygons: list[Polygon], transformer: Transformer) -> list[Polygon]:
    """Transform polygon coordinates and flatten valid polygonal output."""
    transformed_polygons: list[Polygon] = []
    for polygon in polygons:
        transformed = make_valid(_transform_geometry(polygon, transformer))
        transformed_polygons.extend(_geometry_to_polygons(transformed))
    return transformed_polygons


def _splitter_buffer_width(tags: dict[str, str], default_split_width: float) -> float:
    """Return a road-aware splitter half-width in projected meters."""
    if default_split_width <= 0:
        return 0.0

    highway_value = tags.get("highway")
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
        return max(default_split_width, highway_widths.get(highway_value, 4.0))

    if "railway" in tags:
        return max(default_split_width, 5.0)
    if "waterway" in tags:
        return max(default_split_width, 3.0)
    if "barrier" in tags:
        return max(default_split_width, 1.5)
    if "aerialway" in tags:
        return max(default_split_width, 1.5)
    if "power" in tags:
        return max(default_split_width, 2.0)
    return default_split_width


def _geometry_to_polygons(geometry: BaseGeometry) -> list[Polygon]:
    """Extract polygons from arbitrary geometry output."""
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
    """Remove target polygons from XML tree before appending processed geometry."""
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
    """Append polygons as OSM ways/relations and return creation counters."""
    node_ids = [int(node.get("id")) for node in root.findall("node") if node.get("id")]
    way_ids = [int(way.get("id")) for way in root.findall("way") if way.get("id")]
    relation_ids = [
        int(relation.get("id")) for relation in root.findall("relation") if relation.get("id")
    ]

    next_node_id = max([0, *node_ids]) + 1
    next_way_id = max([0, *way_ids]) + 1
    next_relation_id = max([0, *relation_ids]) + 1

    node_cache: dict[tuple[float, float], int] = {}
    created_ways = 0
    created_relations = 0

    def append_node(coordinate: tuple[float, float]) -> int:
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


def _ensure_primitive_versions(root: ET.Element) -> None:
    """Ensure all OSM primitives have a version attribute for JOSM compatibility."""
    for primitive_name in ("node", "way", "relation"):
        for element in root.findall(primitive_name):
            if not element.get("version"):
                element.set("version", "1")
