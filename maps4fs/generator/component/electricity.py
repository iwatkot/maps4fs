"""Component for placing electricity poles from OSM point data using an electricity schema."""

from __future__ import annotations

import json
import math
import os
import shutil
from typing import Any, NamedTuple
from xml.etree import ElementTree as ET

import numpy as np
import shapely
import trimesh
from tqdm import tqdm

from maps4fs.generator.component.base.component_mesh import MeshComponent
from maps4fs.generator.component.xml_document import XmlDocument
from maps4fs.generator.settings import Parameters


class ElectricityEntry(NamedTuple):
    """Data structure for a single electricity asset entry."""

    file: str
    name: str
    categories: list[str]
    connectors: list["ConnectorEntry"]
    rotation_offset_degrees: float
    visual_rotation_offset_degrees: float | None = None
    template_file: str | None = None
    type: str | None = None
    align_to_road: float | None = None
    snap_to_road: float | None = None


class ConnectorEntry(NamedTuple):
    """Connector definition on a pole asset in local pole coordinates."""

    side: float
    height: float


class PolePlacement(NamedTuple):
    """Placed pole record used for connector-based powerline generation."""

    x_pixel: int
    y_pixel: int
    x_world: float
    z_world: float
    ground_height: float
    yaw_degrees: float
    node_id: int
    entry: ElectricityEntry


class RoadSegment(NamedTuple):
    """Fitted road segment with source road width metadata."""

    start: tuple[float, float]
    end: tuple[float, float]
    width: float


class NearestRoadHit(NamedTuple):
    """Nearest road query result used by alignment and snapping."""

    point: tuple[float, float]
    distance: float
    normal: tuple[float, float]
    half_width: float


class ElectricityEntryCollection:
    """Collection of electricity entries with category lookup."""

    def __init__(self, entries: list[ElectricityEntry]) -> None:
        """Build in-memory category index for fast entry lookup.

        Arguments:
            entries (list[ElectricityEntry]): Parsed electricity entries from schema.
        """
        self.entries = entries

        self.by_category: dict[str, list[ElectricityEntry]] = {}
        for entry in self.entries:
            for category in entry.categories:
                self.by_category.setdefault(category, []).append(entry)

    def find_first(self, category: str) -> ElectricityEntry | None:
        """Return first entry for a category with default fallback.

        Arguments:
            category (str): Electricity category to resolve.

        Returns:
            ElectricityEntry | None: Matching entry, default-category entry, or None.
        """
        if category in self.by_category and self.by_category[category]:
            return self.by_category[category][0]
        default_entries = self.by_category.get(Parameters.DEFAULT_ELECTRICITY_CATEGORY, [])
        return default_entries[0] if default_entries else None


class Electricity(MeshComponent):
    """Component for placing electricity poles in map.i3d based on OSM point data."""

    def preprocess(self) -> None:
        """Load schema and prepare electricity component state."""
        self.info: dict[str, Any] = {}
        self._extended_border = int(round(Parameters.EXTENDED_DISTANCE * self.map.size_scale))
        self.xml_path = self.game.i3d_file_path
        self.electricity_collection: ElectricityEntryCollection | None = None
        self._schema_base_dir: str | None = None
        self._resolved_template_assets: dict[tuple[str, str], str] = {}

        entries = self._load_electricity_schema()
        if not entries:
            return

        self.electricity_collection = ElectricityEntryCollection(entries)
        self.logger.debug(
            "Electricity collection created with %d entries.",
            len(self.electricity_collection.entries),
        )

    def process(self) -> None:
        """Place electricity poles from context point data into map.i3d."""
        if self.electricity_collection is None:
            self.logger.debug("Electricity schema is not loaded; skipping electricity placement.")
            return

        try:
            self.add_electricity()
        except Exception as e:  # pylint: disable=broad-except
            self.logger.warning("An error occurred during electricity processing: %s", e)

    def add_electricity(self) -> None:
        """Read electricity point data from context and append reference nodes to I3D."""
        points_data = self.get_infolayer_data(
            Parameters.EXTENDED, Parameters.ELECTRICITY_POLES_POINTS
        )
        if not points_data:
            points_data = self.get_infolayer_data(
                Parameters.TEXTURES, Parameters.ELECTRICITY_POLES_POINTS
            )
        if not points_data:
            self.logger.warning("No electricity pole points found in context; skipping.")
            return

        if self.electricity_collection is None:
            return

        not_resized_dem = self.get_dem_image_with_fallback(start_at=1)
        if not_resized_dem is None:
            self.logger.warning("Not resized DEM not found. Electricity placement is skipped.")
            return

        prepared_document = self._prepare_i3d_targets()
        if prepared_document is None:
            return

        doc, files_section, scene_node, electricity_group = prepared_document

        used_files: dict[str, int] = {}
        used_file_ids = self._collect_used_file_ids(files_section)
        used_node_ids = self._collect_used_node_ids(scene_node)
        file_id_counter = self._next_free_id(
            Parameters.ELECTRICITY_STARTING_FILE_ID,
            used_file_ids,
        )
        node_id_counter = self._next_free_id(
            Parameters.ELECTRICITY_STARTING_NODE_ID,
            used_node_ids,
        )

        electricity_group.set(self.game.config.i3d_attr_node_id, str(node_id_counter))
        used_node_ids.add(node_id_counter)
        node_id_counter = self._next_free_id(node_id_counter + 1, used_node_ids)

        placed_count = 0
        placed_poles: list[PolePlacement] = []
        roads_data = self.get_infolayer_data(Parameters.EXTENDED, Parameters.ROADS_POLYLINES)
        if not roads_data:
            roads_data = self.get_infolayer_data(Parameters.TEXTURES, Parameters.ROADS_POLYLINES)
        fitted_road_segments = self._build_fitted_road_segments(
            roads_data if isinstance(roads_data, list) else []
        )

        for point_data in tqdm(points_data, desc="Placing electricity poles", unit="pole"):
            placed, file_id_counter, node_id_counter, placement = self._place_single_pole(
                point_data,
                not_resized_dem,
                files_section,
                electricity_group,
                used_files,
                used_file_ids,
                used_node_ids,
                file_id_counter,
                node_id_counter,
                fitted_road_segments,
            )
            if placed:
                placed_count += 1
            if placement is not None:
                placed_poles.append(placement)

        network_lines_data = self.get_infolayer_data(
            Parameters.EXTENDED, Parameters.ELECTRICITY_LINES_POLYLINES
        )
        if not network_lines_data:
            network_lines_data = self.get_infolayer_data(
                Parameters.TEXTURES, Parameters.ELECTRICITY_LINES_POLYLINES
            )
        network_segments = self._create_and_attach_powerline_network(
            placed_poles,
            network_lines_data if isinstance(network_lines_data, list) else [],
            files_section,
            electricity_group,
            used_file_ids,
            used_node_ids,
            file_id_counter,
            node_id_counter,
        )

        self.info["total_poles_placed"] = placed_count
        self.info["total_poles_attempted"] = len(points_data)
        self.info["total_line_segments_created"] = network_segments

        doc.save()
        self.logger.debug("Electricity placement completed and saved to map.i3d")

    def _load_electricity_schema(self) -> list[ElectricityEntry] | None:
        """Load electricity schema from custom map config or default game schema.

        Returns:
            list[ElectricityEntry] | None: Parsed entries, or None when no valid schema is available.
        """
        custom_schema = getattr(self.map, "electricity_custom_schema", None)
        if custom_schema:
            raw_schema = custom_schema
        else:
            schema_path = getattr(self.game, "electricity_schema", "")
            if not schema_path or not os.path.isfile(schema_path):
                self.logger.warning("Electricity schema not found: %s", schema_path)
                return None
            self._schema_base_dir = os.path.dirname(schema_path)
            try:
                with open(schema_path, "r", encoding="utf-8") as schema_file:
                    raw_schema = json.load(schema_file)
            except Exception as e:  # pylint: disable=broad-except
                self.logger.warning("Could not load electricity schema from %s: %s", schema_path, e)
                return None

        entries: list[ElectricityEntry] = []
        for row in raw_schema:
            try:
                file = str(row["file"])
                name = str(row["name"])
            except KeyError:
                continue

            categories = row.get("categories") or [Parameters.DEFAULT_ELECTRICITY_CATEGORY]
            connectors = self._parse_connectors(row.get("connectors"))
            entry_type = row.get("type")
            template_file = row.get("template_file")
            rotation_offset_degrees = float(row.get("rotation_offset_degrees", 0.0))
            raw_visual_rotation = row.get("visual_rotation_offset_degrees")
            visual_rotation_offset_degrees = (
                float(raw_visual_rotation) if raw_visual_rotation is not None else None
            )
            align_to_road = self._parse_optional_distance(row.get("align_to_road"))
            snap_to_road = self._parse_optional_distance(
                row.get("snap_to_road"),
                allow_zero=True,
            )

            entries.append(
                ElectricityEntry(
                    file=file,
                    name=name,
                    categories=list(categories),
                    connectors=connectors,
                    rotation_offset_degrees=rotation_offset_degrees,
                    visual_rotation_offset_degrees=visual_rotation_offset_degrees,
                    template_file=str(template_file) if template_file else None,
                    type=str(entry_type) if entry_type is not None else None,
                    align_to_road=align_to_road,
                    snap_to_road=snap_to_road,
                )
            )

        if not entries:
            self.logger.warning("Electricity schema is empty. Electricity placement is skipped.")
            return None

        return entries

    def _parse_connectors(self, raw_connectors: Any) -> list[ConnectorEntry]:
        """Parse connector definitions from schema with sane defaults.

        Arguments:
            raw_connectors (Any): Raw schema value for connector definitions.

        Returns:
            list[ConnectorEntry]: Parsed connectors, or default two-wire connectors.
        """
        if not isinstance(raw_connectors, list):
            return [ConnectorEntry(side=2.0, height=10.0), ConnectorEntry(side=-2.0, height=10.0)]

        connectors: list[ConnectorEntry] = []
        for connector in raw_connectors:
            if not isinstance(connector, dict):
                continue
            try:
                side = float(connector.get("side", 0.0))
                height = float(connector.get("height", 10.0))
            except (TypeError, ValueError):
                continue
            connectors.append(ConnectorEntry(side=side, height=height))

        if not connectors:
            return [ConnectorEntry(side=2.0, height=10.0), ConnectorEntry(side=-2.0, height=10.0)]
        return connectors

    def _prepare_i3d_targets(
        self,
    ) -> tuple[XmlDocument, ET.Element, ET.Element, ET.Element] | None:
        """Open map I3D XML and resolve sections needed for electricity placement.

        Returns:
            tuple[XmlDocument, ET.Element, ET.Element, ET.Element] | None:
                Loaded XML document, Files section, Scene node, and electricity group,
                or None when the Scene element is missing.
        """
        doc = XmlDocument(self.xml_path)
        scene_node = doc.get(self.game.config.i3d_scene_xpath)
        if scene_node is None:
            self.logger.warning("Scene element not found in I3D file.")
            return None

        files_section = doc.get(self.game.config.i3d_files_xpath)
        if files_section is None:
            files_section = doc.append_child(".", self.game.config.i3d_files_section_tag)

        electricity_group = self._find_or_create_electricity_group(scene_node)
        return doc, files_section, scene_node, electricity_group

    def _find_or_create_electricity_group(self, scene_node: ET.Element) -> ET.Element:
        """Find or create electricity transform group in scene.

        Arguments:
            scene_node (ET.Element): Root scene node where transform groups are stored.

        Returns:
            ET.Element: Existing or newly created electricity transform group element.
        """
        cfg = self.game.config
        for transform_group in scene_node.iter(cfg.i3d_transform_group_tag):
            if transform_group.get(cfg.i3d_attr_name) == Parameters.ELECTRICITY_GROUP_NAME:
                return transform_group

        electricity_group = XmlDocument.create_element(
            cfg.i3d_transform_group_tag,
            {
                cfg.i3d_attr_name: Parameters.ELECTRICITY_GROUP_NAME,
                cfg.i3d_attr_translation: cfg.i3d_zero_translation,
                cfg.i3d_attr_node_id: "0",
            },
        )
        scene_node.append(electricity_group)
        return electricity_group

    def _place_single_pole(
        self,
        point_data: dict[str, Any],
        not_resized_dem: np.ndarray,
        files_section: ET.Element,
        electricity_group: ET.Element,
        used_files: dict[str, int],
        used_file_ids: set[int],
        used_node_ids: set[int],
        file_id_counter: int,
        node_id_counter: int,
        fitted_road_segments: list[RoadSegment],
    ) -> tuple[bool, int, int, PolePlacement | None]:
        """Attempt to place a single pole from one point record.

        Arguments:
            point_data (dict[str, Any]): Infolayer point record with pixel point and tags.
            not_resized_dem (np.ndarray): Source DEM used to sample ground elevation.
            files_section (ET.Element): I3D Files section for registering referenced assets.
            electricity_group (ET.Element): I3D group where pole reference nodes are appended.
            used_files (dict[str, int]): Cache from asset path to assigned fileId.
            used_file_ids (set[int]): Set of already used file IDs.
            used_node_ids (set[int]): Set of already used node IDs.
            file_id_counter (int): Candidate file ID for new assets.
            node_id_counter (int): Candidate node ID for new reference nodes.
            fitted_road_segments (list[tuple[tuple[float, float], tuple[float, float]]]):
            fitted_road_segments (list[RoadSegment]):
                Pre-fitted road segments for optional road-facing light orientation.

        Returns:
            tuple[bool, int, int, PolePlacement | None]:
                Placement flag, next file ID candidate, next node ID candidate,
                and created pole placement metadata when successful.
        """
        point_raw = point_data.get(Parameters.POINT) if isinstance(point_data, dict) else None
        if not point_raw or len(point_raw) < 2:
            return False, file_id_counter, node_id_counter, None

        x, y = int(point_raw[0]), int(point_raw[1])
        fitted_point = self._fit_point_into_bounds((x, y))
        if fitted_point is None:
            return False, file_id_counter, node_id_counter, None

        osm_tags = point_data.get(Parameters.TAGS, {}) if isinstance(point_data, dict) else {}
        category = self._resolve_electricity_category(
            osm_tags if isinstance(osm_tags, dict) else {}
        )

        if self.electricity_collection is None:
            return False, file_id_counter, node_id_counter, None

        best_match = self.electricity_collection.find_first(category)
        if best_match is None:
            return False, file_id_counter, node_id_counter, None

        resolved_asset_file = self._resolve_entry_asset_file(best_match)

        file_id, next_file_id = self._ensure_file_id(
            files_section,
            used_files,
            used_file_ids,
            resolved_asset_file,
            file_id_counter,
        )

        node_id_counter = self._next_free_id(node_id_counter, used_node_ids)

        fitted_point = self._snap_point_to_road(fitted_point, best_match, fitted_road_segments)

        x_center, y_center = self.top_left_coordinates_to_center(fitted_point)
        try:
            z = self.get_z_coordinate_from_dem(not_resized_dem, fitted_point[0], fitted_point[1])
        except Exception:
            z = Parameters.DEFAULT_HEIGHT

        yaw_degrees = self._initial_pole_yaw(
            fitted_point,
            best_match,
            fitted_road_segments,
        )

        placement = PolePlacement(
            x_pixel=fitted_point[0],
            y_pixel=fitted_point[1],
            x_world=float(x_center),
            z_world=float(y_center),
            ground_height=float(z),
            yaw_degrees=yaw_degrees,
            node_id=node_id_counter,
            entry=best_match,
        )

        cfg = self.game.config
        pole_node = XmlDocument.create_element(
            cfg.i3d_reference_node_tag,
            {
                cfg.i3d_attr_name: f"{best_match.name}_{node_id_counter}",
                cfg.i3d_attr_translation: f"{x_center:.3f} {z:.3f} {y_center:.3f}",
                cfg.i3d_attr_rotation: f"0 {self._visual_pole_yaw(placement):.3f} 0",
                cfg.i3d_attr_reference_id: str(file_id),
                cfg.i3d_attr_node_id: str(node_id_counter),
            },
        )
        electricity_group.append(pole_node)

        used_node_ids.add(node_id_counter)

        return (
            True,
            next_file_id,
            self._next_free_id(node_id_counter + 1, used_node_ids),
            placement,
        )

    def _create_and_attach_powerline_network(
        self,
        poles: list[PolePlacement],
        line_records: list[dict[str, Any]],
        files_section: ET.Element,
        electricity_group: ET.Element,
        used_file_ids: set[int],
        used_node_ids: set[int],
        next_file_id: int,
        next_node_id: int,
    ) -> int:
        """Build one mesh network from line topology and attach it as one I3D reference.

        Arguments:
            poles (list[PolePlacement]): Placed poles participating in the network.
            line_records (list[dict[str, Any]]): Electricity line records from texture context.
            files_section (ET.Element): I3D Files section where the generated asset is registered.
            electricity_group (ET.Element): I3D group where the network reference node is added.
            used_file_ids (set[int]): Set of already used file IDs.
            used_node_ids (set[int]): Set of already used node IDs.
            next_file_id (int): Candidate file ID for the generated network asset.
            next_node_id (int): Candidate node ID for the generated network node.

        Returns:
            int: Number of generated connector-to-connector line segments.
        """
        if len(poles) < 2 or not line_records:
            return 0

        segments, oriented_poles = self._build_powerline_segments(poles, line_records)
        if not segments:
            return 0

        self._apply_pole_rotations(electricity_group, oriented_poles)

        mesh = self._build_powerline_mesh(segments)
        if mesh is None:
            return 0

        output_dir = os.path.join(
            self.map_directory,
            Parameters.ASSETS_DIRECTORY,
            Parameters.ELECTRICITY_GROUP_NAME,
        )
        os.makedirs(output_dir, exist_ok=True)

        asset_name = "powerline_network"
        network_i3d_path = self.mesh_to_i3d(mesh, output_dir, asset_name)
        self._set_network_material_black(network_i3d_path)

        relative_asset_path = os.path.relpath(
            network_i3d_path, os.path.dirname(self.xml_path)
        ).replace("\\", "/")

        file_id = self._next_free_id(next_file_id, used_file_ids)
        used_file_ids.add(file_id)
        next_node_id = self._next_free_id(next_node_id, used_node_ids)
        used_node_ids.add(next_node_id)

        cfg = self.game.config
        files_section.append(
            XmlDocument.create_element(
                cfg.i3d_file_tag,
                {
                    cfg.i3d_attr_file_id: str(file_id),
                    cfg.i3d_attr_filename: relative_asset_path,
                },
            )
        )
        electricity_group.append(
            XmlDocument.create_element(
                cfg.i3d_reference_node_tag,
                {
                    cfg.i3d_attr_name: asset_name,
                    cfg.i3d_attr_translation: cfg.i3d_zero_translation,
                    cfg.i3d_attr_rotation: "0 0 0",
                    cfg.i3d_attr_reference_id: str(file_id),
                    cfg.i3d_attr_node_id: str(next_node_id),
                },
            )
        )

        return len(segments)

    def _set_network_material_black(self, i3d_path: str) -> None:
        """Set generated network material color to black.

        Arguments:
            i3d_path (str): Path to generated powerline network i3d file.

        Works for XML i3d and text-readable converted i3d outputs.
        """
        try:
            doc = XmlDocument(i3d_path)
            material = doc.root.find(".//Materials/Material")
            if material is not None:
                material.set("diffuseColor", "0.03 0.03 0.03 1")
                material.set("specularColor", "0.02 0.02 0.02")
            for shape in doc.root.findall(".//Scene//Shape"):
                shape.set(
                    self.game.config.i3d_attr_casts_shadows,
                    Parameters.I3D_TRUE,
                )
            doc.save()
            return
        except Exception:
            pass

        try:
            with open(i3d_path, "r", encoding="utf-8") as file:
                content = file.read()
            content = content.replace('diffuseColor="1 1 1 1"', 'diffuseColor="0.03 0.03 0.03 1"')
            content = content.replace(
                'specularColor="0.5 0.5 0.5"',
                'specularColor="0.02 0.02 0.02"',
            )
            with open(i3d_path, "w", encoding="utf-8") as file:
                file.write(content)
        except Exception:
            # Leave default material if file is not text-editable.
            return

    def _build_powerline_segments(
        self,
        poles: list[PolePlacement],
        line_records: list[dict[str, Any]],
    ) -> tuple[list[tuple[list[tuple[float, float, float]], float]], list[PolePlacement]]:
        """Build sagging connector polylines and oriented poles from topology.

        Arguments:
            poles (list[PolePlacement]): Placed poles available for linking.
            line_records (list[dict[str, Any]]): Fitted electricity lines with metadata.

        Returns:
            tuple[list[tuple[list[tuple[float, float, float]], float]], list[PolePlacement]]:
                Segment polylines paired with radius and poles with resolved yaws.
        """
        segments: list[tuple[list[tuple[float, float, float]], float]] = []
        links_with_radius = self._extract_pole_links(poles, line_records)
        if not links_with_radius:
            return segments, poles

        links = [pair for pair, _ in links_with_radius]
        pole_yaws = self._compute_pole_yaws(poles, links)
        pole_yaws = self._force_endpoint_quarter_turn(pole_yaws, len(poles), links)
        oriented_poles = self._with_updated_pole_yaws(poles, pole_yaws)

        for (idx_a, idx_b), line_radius in links_with_radius:
            pole_a = oriented_poles[idx_a]
            pole_b = oriented_poles[idx_b]

            connectors_a_world = self._connector_world_positions(pole_a)
            connectors_b_world = self._connector_world_positions(pole_b)
            if not connectors_a_world or not connectors_b_world:
                continue

            _, _, right_x, right_z = self._pair_directions(pole_a, pole_b)
            if right_x == 0.0 and right_z == 0.0:
                continue

            for connector_a, connector_b in self._match_connectors_non_overlapping(
                connectors_a_world,
                connectors_b_world,
                right_x,
                right_z,
            ):
                segments.append(
                    (self._build_sagging_polyline(connector_a, connector_b), line_radius)
                )

        return segments, oriented_poles

    def _extract_pole_links(
        self,
        poles: list[PolePlacement],
        line_records: list[dict[str, Any]],
    ) -> list[tuple[tuple[int, int], float]]:
        """Extract unique pole-to-pole links and resolved radius per link.

        Arguments:
            poles (list[PolePlacement]): Candidate poles mapped in output pixel space.
            line_records (list[dict[str, Any]]): Raw line records from texture info layer.

        Returns:
            list[tuple[tuple[int, int], float]]: Sorted unique pole index pairs and line radius.
        """
        unique_pairs: dict[tuple[int, int], float] = {}
        wire_indices = {idx for idx, pole in enumerate(poles) if self._is_wire_capable(pole)}
        if len(wire_indices) < 2:
            return []

        for record in line_records:
            line_radius = self._line_radius(record)
            points = record.get(Parameters.POINTS) if isinstance(record, dict) else None
            if not isinstance(points, list) or len(points) < 2:
                continue

            try:
                fitted_line = self.fit_object_into_bounds(
                    linestring_points=points,
                    angle=self.rotation,
                    border=-self._extended_border,
                )
            except ValueError:
                continue

            if len(fitted_line) < 2:
                continue

            line_pole_sequence = self._line_pole_sequence(poles, fitted_line, wire_indices)
            if len(line_pole_sequence) < 2:
                continue

            for start_idx, end_idx in zip(line_pole_sequence[:-1], line_pole_sequence[1:]):
                if start_idx == end_idx:
                    continue

                pair = (min(start_idx, end_idx), max(start_idx, end_idx))
                existing = unique_pairs.get(pair, 0.0)
                unique_pairs[pair] = max(existing, line_radius)

        return sorted(unique_pairs.items(), key=lambda item: item[0])

    def _line_radius(self, record: dict[str, Any]) -> float:
        """Resolve line radius from line record metadata with safe fallback.

        Arguments:
            record (dict[str, Any]): One electricity line record.

        Returns:
            float: Positive radius value, defaulting to 0.01 when invalid or missing.
        """
        raw = record.get(Parameters.ELECTRICITY_RADIUS) if isinstance(record, dict) else None
        if isinstance(raw, (int, float)):
            radius = float(raw)
        elif isinstance(raw, str):
            try:
                radius = float(raw)
            except ValueError:
                radius = 0.01
        else:
            radius = 0.01
        if radius <= 0:
            return 0.01
        return radius

    def _compute_pole_yaws(
        self,
        poles: list[PolePlacement],
        links: list[tuple[int, int]],
    ) -> dict[int, float]:
        """Compute yaw for each pole from connected neighbor vectors in XZ plane.

        Arguments:
            poles (list[PolePlacement]): Pole placements with world positions.
            links (list[tuple[int, int]]): Connected pole index pairs.

        Returns:
            dict[int, float]: Pole index to computed yaw angle in degrees.
        """
        vectors: dict[int, list[tuple[float, float]]] = {idx: [] for idx in range(len(poles))}

        for idx_a, idx_b in links:
            pole_a = poles[idx_a]
            pole_b = poles[idx_b]
            dx = pole_b.x_world - pole_a.x_world
            dz = pole_b.z_world - pole_a.z_world
            length = math.hypot(dx, dz)
            if length <= 1e-6:
                continue
            vx = dx / length
            vz = dz / length
            vectors[idx_a].append((vx, vz))
            vectors[idx_b].append((-vx, -vz))

        result: dict[int, float] = {}
        for idx, vecs in vectors.items():
            if not vecs:
                result[idx] = 0.0
                continue
            yaw: float
            is_near_straight_internal = False
            if len(vecs) == 2:
                v1x, v1z = vecs[0]
                v2x, v2z = vecs[1]
                dot = v1x * v2x + v1z * v2z
                # Near-opposite vectors indicate a straight-through chain segment.
                # Use one axis direction directly to avoid unstable perpendicular bisectors.
                if dot < -0.85:
                    yaw = math.degrees(math.atan2(v1z, v1x))
                    is_near_straight_internal = True
                else:
                    avg_x = sum(v[0] for v in vecs)
                    avg_z = sum(v[1] for v in vecs)
                    if math.hypot(avg_x, avg_z) <= 1e-6:
                        first_x, first_z = vecs[0]
                        yaw = math.degrees(math.atan2(first_z, first_x))
                    else:
                        yaw = math.degrees(math.atan2(avg_z, avg_x))
            else:
                avg_x = sum(v[0] for v in vecs)
                avg_z = sum(v[1] for v in vecs)
                if math.hypot(avg_x, avg_z) <= 1e-6:
                    first_x, first_z = vecs[0]
                    yaw = math.degrees(math.atan2(first_z, first_x))
                else:
                    yaw = math.degrees(math.atan2(avg_z, avg_x))

            # Apply this asset-axis correction only for straight-through poles.
            if is_near_straight_internal:
                yaw -= 90.0
            result[idx] = yaw

        return result

    def _with_updated_pole_yaws(
        self,
        poles: list[PolePlacement],
        yaws: dict[int, float],
    ) -> list[PolePlacement]:
        """Return new pole placements with topology-derived yaw values.

        Arguments:
            poles (list[PolePlacement]): Source pole placements.
            yaws (dict[int, float]): Yaw overrides keyed by pole index.

        Returns:
            list[PolePlacement]: New pole placement list with updated yaw values.
        """
        result: list[PolePlacement] = []
        for idx, pole in enumerate(poles):
            result.append(
                PolePlacement(
                    x_pixel=pole.x_pixel,
                    y_pixel=pole.y_pixel,
                    x_world=pole.x_world,
                    z_world=pole.z_world,
                    ground_height=pole.ground_height,
                    yaw_degrees=float(yaws.get(idx, pole.yaw_degrees)),
                    node_id=pole.node_id,
                    entry=pole.entry,
                )
            )
        return result

    def _force_endpoint_quarter_turn(
        self,
        yaws: dict[int, float],
        pole_count: int,
        links: list[tuple[int, int]],
    ) -> dict[int, float]:
        """Apply deterministic +90 degree turn to chain endpoints (degree == 1).

        Arguments:
            yaws (dict[int, float]): Current pole yaw mapping.
            pole_count (int): Total number of poles.
            links (list[tuple[int, int]]): Connected pole index pairs.

        Returns:
            dict[int, float]: Adjusted yaw mapping with endpoint quarter-turn applied.
        """
        degrees: dict[int, int] = {idx: 0 for idx in range(pole_count)}
        for idx_a, idx_b in links:
            degrees[idx_a] += 1
            degrees[idx_b] += 1

        result = dict(yaws)
        for idx, degree in degrees.items():
            if degree == 1:
                result[idx] = float(result.get(idx, 0.0) + 90.0)
        return result

    def _apply_pole_rotations(
        self,
        electricity_group: ET.Element,
        poles: list[PolePlacement],
    ) -> None:
        """Apply computed yaw values to already placed pole reference nodes.

        Arguments:
            electricity_group (ET.Element): XML group containing pole ReferenceNode elements.
            poles (list[PolePlacement]): Pole placements with resolved visual yaw values.
        """
        cfg = self.game.config
        nodes_by_id: dict[int, ET.Element] = {}
        for group_node in electricity_group.findall(cfg.i3d_reference_node_tag):
            if group_node is None:
                continue
            node_id = group_node.get(cfg.i3d_attr_node_id)
            if node_id is None or not node_id.isdigit():
                continue
            nodes_by_id[int(node_id)] = group_node

        for pole in poles:
            if not self._is_wire_capable(pole):
                continue
            pole_node = nodes_by_id.get(pole.node_id)
            if pole_node is None:
                continue
            pole_node.set(cfg.i3d_attr_rotation, f"0 {self._visual_pole_yaw(pole):.3f} 0")

    def _line_pole_sequence(
        self,
        poles: list[PolePlacement],
        fitted_line: list[tuple[int, int]],
        allowed_indices: set[int] | None = None,
    ) -> list[int]:
        """Map a fitted line to an ordered sequence of nearby pole indices.

        Arguments:
            poles (list[PolePlacement]): Available pole placements.
            fitted_line (list[tuple[int, int]]): In-bounds fitted polyline in pixel coordinates.
            allowed_indices (set[int] | None, optional): Restrict matching to these pole indices.

        Returns:
            list[int]: Ordered pole index sequence without immediate duplicates.
        """
        sequence: list[int] = []
        # Use stricter matching on line endpoints to avoid creating synthetic
        # links when a line exits map bounds and no actual endpoint pole exists.
        endpoint_max_distance = 24.0
        interior_max_distance = 64.0
        last_index = len(fitted_line) - 1

        for i, point in enumerate(fitted_line):
            max_distance = interior_max_distance
            if i in (0, last_index):
                max_distance = endpoint_max_distance

            idx = self._nearest_pole_index(
                poles,
                point,
                max_distance=max_distance,
                allowed_indices=allowed_indices,
            )
            if idx is None:
                continue
            if not sequence or sequence[-1] != idx:
                sequence.append(idx)
        return sequence

    def _pair_directions(
        self,
        pole_a: PolePlacement,
        pole_b: PolePlacement,
    ) -> tuple[float, float, float, float]:
        """Return normalized forward/right vectors in XZ plane for a pole pair.

        Arguments:
            pole_a (PolePlacement): Start pole.
            pole_b (PolePlacement): End pole.

        Returns:
            tuple[float, float, float, float]: (dir_x, dir_z, right_x, right_z).
        """
        dx = pole_b.x_world - pole_a.x_world
        dz = pole_b.z_world - pole_a.z_world
        length = math.hypot(dx, dz)
        if length <= 1e-6:
            return 0.0, 0.0, 0.0, 0.0

        dir_x = dx / length
        dir_z = dz / length
        right_x = -dir_z
        right_z = dir_x
        return dir_x, dir_z, right_x, right_z

    def _nearest_pole_index(
        self,
        poles: list[PolePlacement],
        point: tuple[int, int],
        max_distance: float = 96.0,
        allowed_indices: set[int] | None = None,
    ) -> int | None:
        """Return index of nearest pole in fitted pixel space within max distance.

        Arguments:
            poles (list[PolePlacement]): Candidate pole placements.
            point (tuple[int, int]): Pixel-space point to match.
            max_distance (float, optional): Maximum allowed pixel distance.
            allowed_indices (set[int] | None, optional): Restrict matching to these indices.

        Returns:
            int | None: Nearest pole index or None when no pole is close enough.
        """
        px, py = point
        best_idx: int | None = None
        best_distance = float("inf")

        for idx, pole in enumerate(poles):
            if allowed_indices is not None and idx not in allowed_indices:
                continue
            dx = pole.x_pixel - px
            dy = pole.y_pixel - py
            distance = math.hypot(dx, dy)
            if distance < best_distance:
                best_distance = distance
                best_idx = idx

        if best_idx is None or best_distance > max_distance:
            return None
        return best_idx

    def _connector_world_position(
        self,
        pole: PolePlacement,
        connector: ConnectorEntry,
    ) -> tuple[float, float, float]:
        """Convert connector local pole coordinates to world XYZ coordinates.

        The connector side offset is applied in the pole-local right direction
        derived from its yaw.

        Arguments:
            pole (PolePlacement): Pole placement record.
            connector (ConnectorEntry): Local connector coordinates on the pole asset.

        Returns:
            tuple[float, float, float]: Connector world-space XYZ position.
        """
        yaw_rad = math.radians(self._effective_pole_yaw(pole))
        right_x = -math.sin(yaw_rad)
        right_z = math.cos(yaw_rad)

        x = pole.x_world + connector.side * right_x
        y = pole.ground_height + connector.height
        z = pole.z_world + connector.side * right_z
        return (x, y, z)

    def _connector_world_positions(self, pole: PolePlacement) -> list[tuple[float, float, float]]:
        """Return connector world positions for one pole in schema order.

        Arguments:
            pole (PolePlacement): Pole placement record.

        Returns:
            list[tuple[float, float, float]]: World positions for all pole connectors.
        """
        return [
            self._connector_world_position(pole, connector) for connector in pole.entry.connectors
        ]

    @staticmethod
    def _distance3(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
        """Return Euclidean distance between two 3D points.

        Arguments:
            a (tuple[float, float, float]): First point.
            b (tuple[float, float, float]): Second point.

        Returns:
            float: 3D distance between points.
        """
        return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2)

    @staticmethod
    def _project_on_right(
        pos: tuple[float, float, float],
        right_x: float,
        right_z: float,
    ) -> float:
        """Project an XZ position onto the local right-axis scalar.

        Arguments:
            pos (tuple[float, float, float]): 3D position to project.
            right_x (float): Right-axis X component.
            right_z (float): Right-axis Z component.

        Returns:
            float: Signed scalar projection along the right axis.
        """
        return pos[0] * right_x + pos[2] * right_z

    def _match_connectors_non_overlapping(
        self,
        connectors_a: list[tuple[float, float, float]],
        connectors_b: list[tuple[float, float, float]],
        right_x: float,
        right_z: float,
    ) -> list[tuple[tuple[float, float, float], tuple[float, float, float]]]:
        """Match connectors by sorted right-axis order to avoid crossing spans.

        Tries both same-order and reversed-order pairings and picks the lower total length.

        Arguments:
            connectors_a (list[tuple[float, float, float]]): Connectors on first pole.
            connectors_b (list[tuple[float, float, float]]): Connectors on second pole.
            right_x (float): Right-axis X component for ordering.
            right_z (float): Right-axis Z component for ordering.

        Returns:
            list[tuple[tuple[float, float, float], tuple[float, float, float]]]:
                Paired connectors between poles.
        """
        if not connectors_a or not connectors_b:
            return []

        a_sorted = sorted(connectors_a, key=lambda p: self._project_on_right(p, right_x, right_z))
        b_sorted = sorted(connectors_b, key=lambda p: self._project_on_right(p, right_x, right_z))

        limit = min(len(a_sorted), len(b_sorted))
        pairs_normal = list(zip(a_sorted[:limit], b_sorted[:limit]))
        pairs_reversed = list(zip(a_sorted[:limit], list(reversed(b_sorted))[:limit]))

        cost_normal = sum(self._distance3(a, b) for a, b in pairs_normal)
        cost_reversed = sum(self._distance3(a, b) for a, b in pairs_reversed)

        return pairs_normal if cost_normal <= cost_reversed else pairs_reversed

    def _match_connectors_by_distance(
        self,
        connectors_a: list[tuple[float, float, float]],
        connectors_b: list[tuple[float, float, float]],
    ) -> list[tuple[tuple[float, float, float], tuple[float, float, float]]]:
        """Match connectors by shortest pairwise distance.

        Arguments:
            connectors_a (list[tuple[float, float, float]]): Connectors on first pole.
            connectors_b (list[tuple[float, float, float]]): Connectors on second pole.

        Returns:
            list[tuple[tuple[float, float, float], tuple[float, float, float]]]:
                Greedy minimum-distance connector pairs.
        """
        candidates: list[tuple[float, int, int]] = []
        for idx_a, pos_a in enumerate(connectors_a):
            for idx_b, pos_b in enumerate(connectors_b):
                distance = math.sqrt(
                    (pos_a[0] - pos_b[0]) ** 2
                    + (pos_a[1] - pos_b[1]) ** 2
                    + (pos_a[2] - pos_b[2]) ** 2
                )
                candidates.append((distance, idx_a, idx_b))

        candidates.sort(key=lambda item: item[0])
        used_a: set[int] = set()
        used_b: set[int] = set()
        limit = min(len(connectors_a), len(connectors_b))
        pairs: list[tuple[tuple[float, float, float], tuple[float, float, float]]] = []

        for _, idx_a, idx_b in candidates:
            if idx_a in used_a or idx_b in used_b:
                continue
            used_a.add(idx_a)
            used_b.add(idx_b)
            pairs.append((connectors_a[idx_a], connectors_b[idx_b]))
            if len(pairs) >= limit:
                break

        return pairs

    def _effective_pole_yaw(self, pole: PolePlacement) -> float:
        """Return connector yaw with schema offset applied.

        Arguments:
            pole (PolePlacement): Pole placement and schema entry.

        Returns:
            float: Effective connector yaw in degrees.
        """
        return pole.yaw_degrees + pole.entry.rotation_offset_degrees

    def _effective_visual_pole_yaw(self, pole: PolePlacement) -> float:
        """Return visual yaw source angle before axis folding/sign mapping.

        Arguments:
            pole (PolePlacement): Pole placement and schema entry.

        Returns:
            float: Visual source yaw in degrees.
        """
        visual_offset = pole.entry.visual_rotation_offset_degrees
        if visual_offset is None:
            visual_offset = pole.entry.rotation_offset_degrees
        return pole.yaw_degrees + visual_offset

    def _visual_pole_yaw(self, pole: PolePlacement) -> float:
        """Return display yaw for poles without affecting connector/wire geometry.

        We fold to a direction-agnostic axis (mod 180) and flip sign to match
        current pole asset orientation in GE.

        Arguments:
            pole (PolePlacement): Pole placement with computed topology yaw.

        Returns:
            float: Visual yaw in degrees used in i3d node rotation.
        """
        if pole.entry.align_to_road and (pole.entry.type or "").lower() == "light":
            # Light assets are directional, so keep full heading (no axis folding).
            return -self._effective_visual_pole_yaw(pole)

        axis_yaw = self._fold_axis_degrees(self._effective_visual_pole_yaw(pole))
        return -axis_yaw

    @staticmethod
    def _fold_axis_degrees(value: float) -> float:
        """Fold angle to [-90, 90] so direction flips map to the same axis.

        Arguments:
            value (float): Input angle in degrees.

        Returns:
            float: Folded axis angle in degrees.
        """
        return (value + 90.0) % 180.0 - 90.0

    def _build_sagging_polyline(
        self,
        p1: tuple[float, float, float],
        p2: tuple[float, float, float],
        steps: int = 10,
    ) -> list[tuple[float, float, float]]:
        """Build a sagging polyline between connector points using a parabola.

        Arguments:
            p1 (tuple[float, float, float]): Start connector position.
            p2 (tuple[float, float, float]): End connector position.
            steps (int, optional): Number of interpolation segments.

        Returns:
            list[tuple[float, float, float]]: Polyline points from start to end.
        """
        dx = p2[0] - p1[0]
        dz = p2[2] - p1[2]
        horizontal_length = math.hypot(dx, dz)
        sag = max(0.35, min(2.0, horizontal_length * 0.03))

        points: list[tuple[float, float, float]] = []
        for i in range(steps + 1):
            t = i / steps
            x = p1[0] + dx * t
            z = p1[2] + dz * t
            y_linear = p1[1] + (p2[1] - p1[1]) * t
            y = y_linear - sag * 4.0 * t * (1.0 - t)
            points.append((x, y, z))

        return points

    def _build_powerline_mesh(
        self,
        segments: list[tuple[list[tuple[float, float, float]], float]],
    ) -> trimesh.Trimesh | None:
        """Build one trimesh mesh from cylinder strips representing powerlines.

        Arguments:
            segments (list[tuple[list[tuple[float, float, float]], float]]):
                Segment polylines paired with radius.

        Returns:
            trimesh.Trimesh | None: Combined mesh, or None when no geometry is generated.
        """
        cylinders: list[trimesh.Trimesh] = []
        for segment, radius in segments:
            if len(segment) < 2:
                continue
            for p1, p2 in zip(segment[:-1], segment[1:]):
                if shapely.LineString([(p1[0], p1[2]), (p2[0], p2[2])]).length < 0.01:
                    continue
                cylinder = trimesh.creation.cylinder(
                    radius=radius,
                    segment=np.array([p1, p2], dtype=float),
                    sections=8,
                )
                cylinders.append(cylinder)

        if not cylinders:
            return None

        return trimesh.util.concatenate(cylinders)

    def _ensure_file_id(
        self,
        files_section: ET.Element,
        used_files: dict[str, int],
        used_file_ids: set[int],
        asset_file: str,
        next_file_id: int,
    ) -> tuple[int, int]:
        """Return file ID for an electricity asset, appending File on first use.

        Arguments:
            files_section (ET.Element): I3D Files section.
            used_files (dict[str, int]): Cache of registered assets by path.
            used_file_ids (set[int]): Set of already used file IDs.
            asset_file (str): Asset file path to register.
            next_file_id (int): Candidate file ID.

        Returns:
            tuple[int, int]: Assigned file ID and next file ID candidate.
        """
        if asset_file in used_files:
            return used_files[asset_file], next_file_id

        cfg = self.game.config
        file_id = self._next_free_id(next_file_id, used_file_ids)
        file_element = XmlDocument.create_element(
            cfg.i3d_file_tag,
            {
                cfg.i3d_attr_file_id: str(file_id),
                cfg.i3d_attr_filename: asset_file,
            },
        )
        files_section.append(file_element)
        used_files[asset_file] = file_id
        used_file_ids.add(file_id)

        return file_id, self._next_free_id(file_id + 1, used_file_ids)

    def _resolve_entry_asset_file(self, entry: ElectricityEntry) -> str:
        """Resolve final i3d asset path for an entry.

        Copies template_file to its target location when requested.

        Arguments:
            entry (ElectricityEntry): Electricity schema entry.

        Returns:
            str: Asset path relative to map.i3d directory.
        """
        if not entry.template_file:
            return entry.file

        cache_key = (entry.file, entry.template_file)
        cached = self._resolved_template_assets.get(cache_key)
        if cached:
            return cached

        source_path = self._resolve_template_source_path(entry.template_file)
        if source_path is None:
            self.logger.warning(
                "template_file not found for electricity entry '%s': %s",
                entry.name,
                entry.template_file,
            )
            return entry.file

        target_relative = entry.file.replace("\\", "/")
        mod_root = self._mod_root_directory()
        target_path = os.path.normpath(os.path.join(mod_root, target_relative))
        os.makedirs(os.path.dirname(target_path), exist_ok=True)

        if os.path.abspath(source_path) != os.path.abspath(target_path):
            shutil.copy2(source_path, target_path)
        self._copy_optional_shapes_file(source_path, target_path)

        target_reference = os.path.relpath(
            target_path,
            os.path.dirname(self.xml_path),
        ).replace("\\", "/")

        self._resolved_template_assets[cache_key] = target_reference
        return target_reference

    def _mod_root_directory(self) -> str:
        """Return mod root directory (the folder containing modDesc.xml).

        Returns:
            str: Best-effort mod root path.
        """
        candidates = [self.map_directory, os.path.dirname(self.xml_path)]
        for start in candidates:
            current = os.path.abspath(start)
            for _ in range(4):
                if os.path.isfile(os.path.join(current, "modDesc.xml")):
                    return current
                parent = os.path.dirname(current)
                if parent == current:
                    break
                current = parent
        return self.map_directory

    @staticmethod
    def _copy_optional_shapes_file(source_i3d_path: str, target_i3d_path: str) -> None:
        """Copy companion .i3d.shapes file next to target i3d when present.

        Arguments:
            source_i3d_path (str): Source i3d path.
            target_i3d_path (str): Destination i3d path.
        """
        source_shapes = f"{source_i3d_path}.shapes"
        target_shapes = f"{target_i3d_path}.shapes"
        if not os.path.isfile(source_shapes):
            return
        if os.path.abspath(source_shapes) == os.path.abspath(target_shapes):
            return
        shutil.copy2(source_shapes, target_shapes)

    def _resolve_template_source_path(self, template_file: str) -> str | None:
        """Resolve template file to an existing source path.

        Arguments:
            template_file (str): Raw template path from schema entry.

        Returns:
            str | None: Resolved existing file path, or None if no candidate exists.
        """
        candidates: list[str] = []
        mod_root = self._mod_root_directory()
        if os.path.isabs(template_file):
            candidates.append(template_file)
        else:
            candidates.append(template_file)
            candidates.append(os.path.join(self.map_directory, template_file))
            candidates.append(os.path.join(mod_root, template_file))
            if self._schema_base_dir:
                candidates.append(os.path.join(self._schema_base_dir, template_file))
                candidates.append(
                    os.path.join(os.path.dirname(self._schema_base_dir), template_file)
                )

        for candidate in candidates:
            normalized = os.path.normpath(candidate)
            if os.path.isfile(normalized):
                return normalized
        return None

    def _collect_used_file_ids(self, files_section: ET.Element) -> set[int]:
        """Collect numeric file IDs already present in I3D Files section.

        Arguments:
            files_section (ET.Element): I3D Files element.

        Returns:
            set[int]: Used file IDs parsed from existing File elements.
        """
        used: set[int] = set()
        attr = self.game.config.i3d_attr_file_id
        for file_elem in files_section.iter(self.game.config.i3d_file_tag):
            file_id = file_elem.get(attr)
            if file_id is None:
                continue
            try:
                used.add(int(file_id))
            except ValueError:
                continue
        return used

    def _collect_used_node_ids(self, scene_node: ET.Element) -> set[int]:
        """Collect numeric node IDs already present in I3D Scene subtree.

        Arguments:
            scene_node (ET.Element): Root Scene element.

        Returns:
            set[int]: Used node IDs parsed from scene descendants.
        """
        used: set[int] = set()
        attr = self.game.config.i3d_attr_node_id
        for elem in scene_node.iter():
            node_id = elem.get(attr)
            if node_id is None:
                continue
            try:
                used.add(int(node_id))
            except ValueError:
                continue
        return used

    @staticmethod
    def _next_free_id(start_id: int, used_ids: set[int]) -> int:
        """Return first free numeric ID starting from start_id.

        Arguments:
            start_id (int): Starting candidate ID.
            used_ids (set[int]): IDs already taken.

        Returns:
            int: First available ID not in used_ids.
        """
        candidate = start_id
        while candidate in used_ids:
            candidate += 1
        return candidate

    def _fit_point_into_bounds(self, point: tuple[int, int]) -> tuple[int, int] | None:
        """Fit point into output bounds by using a tiny line through the point.

        Arguments:
            point (tuple[int, int]): Source point in pixel coordinates.

        Returns:
            tuple[int, int] | None: Fitted in-bounds point or None if fitting fails.
        """
        x, y = point
        try:
            fitted = self.fit_object_into_bounds(
                linestring_points=[(x, y), (x + 1, y)],
                angle=self.rotation,
                border=-self._extended_border,
            )
            if not fitted:
                return None
            fx, fy = fitted[0]
            return int(fx), int(fy)
        except ValueError:
            return None

    def _resolve_electricity_category(self, osm_tags: dict[str, Any]) -> str:
        """Resolve electricity category from texture layer tag rules.

        Arguments:
            osm_tags (dict[str, Any]): OSM tags for the current point feature.

        Returns:
            str: Matched electricity category or default fallback category.
        """
        if osm_tags:
            for layer in self.map.context.texture_layers:
                electricity_category = getattr(layer, "electricity_category", None)
                if electricity_category is None or not layer.tags:
                    continue

                for tag_key, tag_values in layer.tags.items():
                    if tag_key not in osm_tags:
                        continue

                    value = osm_tags[tag_key]
                    matched = False
                    if isinstance(tag_values, list):
                        matched = value in tag_values
                    elif isinstance(tag_values, bool):
                        matched = bool(value) is tag_values
                    else:
                        matched = value == tag_values

                    if matched:
                        return electricity_category

        return Parameters.DEFAULT_ELECTRICITY_CATEGORY

    @staticmethod
    def _is_wire_capable(pole: PolePlacement) -> bool:
        """Return whether pole entry should participate in wire topology and yaw updates.

        Arguments:
            pole (PolePlacement): Pole placement to check.

        Returns:
            bool: True when the entry can carry wires, False for light-only assets.
        """
        entry_type = (pole.entry.type or "").lower()
        if entry_type == "light":
            return False
        return bool(pole.entry.connectors)

    def _build_fitted_road_segments(
        self,
        road_records: list[dict[str, Any]],
    ) -> list[RoadSegment]:
        """Build fitted road segment list in output pixel space.

        Arguments:
            road_records (list[dict[str, Any]]): Road polyline records from texture info layer.

        Returns:
            list[RoadSegment]: Fitted road segment endpoints with source width metadata.
        """
        segments: list[RoadSegment] = []
        for road in road_records:
            points = road.get(Parameters.POINTS) if isinstance(road, dict) else None
            if not isinstance(points, list) or len(points) < 2:
                continue
            road_width = 0.0
            if isinstance(road, dict):
                raw_road_width = road.get(Parameters.WIDTH)
                if isinstance(raw_road_width, (int, float)):
                    road_width = max(0.0, float(raw_road_width))
                elif isinstance(raw_road_width, str):
                    try:
                        road_width = max(0.0, float(raw_road_width))
                    except ValueError:
                        road_width = 0.0
            try:
                fitted_line = self.fit_object_into_bounds(
                    linestring_points=points,
                    angle=self.rotation,
                    border=-self._extended_border,
                )
            except ValueError:
                continue
            if len(fitted_line) < 2:
                continue
            for start, end in zip(fitted_line[:-1], fitted_line[1:]):
                dx = float(end[0] - start[0])
                dy = float(end[1] - start[1])
                if math.hypot(dx, dy) <= 1e-6:
                    continue
                segments.append(
                    RoadSegment(
                        start=(float(start[0]), float(start[1])),
                        end=(float(end[0]), float(end[1])),
                        width=road_width,
                    )
                )
        return segments

    def _snap_point_to_road(
        self,
        fitted_point: tuple[int, int],
        entry: ElectricityEntry,
        fitted_road_segments: list[RoadSegment],
    ) -> tuple[int, int]:
        """Snap fitted point to nearest road edge with configured offset.

        Arguments:
            fitted_point (tuple[int, int]): Original fitted point coordinates.
            entry (ElectricityEntry): Matched electricity entry.
            fitted_road_segments (list[RoadSegment]): Fitted road segments in output space.

        Returns:
            tuple[int, int]: Snapped fitted point when configured, otherwise original point.
        """
        if entry.snap_to_road is None:
            return fitted_point

        point_x = float(fitted_point[0])
        point_y = float(fitted_point[1])
        nearest_road = self._nearest_road_point(point_x, point_y, fitted_road_segments)
        if nearest_road is None:
            return fitted_point

        road_point = nearest_road.point
        normal_x, normal_y = nearest_road.normal
        from_center_x = point_x - road_point[0]
        from_center_y = point_y - road_point[1]
        side_projection = from_center_x * normal_x + from_center_y * normal_y
        side_sign = 1.0 if side_projection >= 0.0 else -1.0

        edge_offset = nearest_road.half_width + entry.snap_to_road
        snapped_x = road_point[0] + normal_x * side_sign * edge_offset
        snapped_y = road_point[1] + normal_y * side_sign * edge_offset
        return self._clamp_fitted_point(snapped_x, snapped_y)

    def _clamp_fitted_point(self, x: float, y: float) -> tuple[int, int]:
        """Clamp floating fitted coordinates to valid map pixel bounds.

        Arguments:
            x (float): Fitted X coordinate.
            y (float): Fitted Y coordinate.

        Returns:
            tuple[int, int]: In-bounds integer pixel coordinates.
        """
        max_index = max(0, int(self.scaled_size) - 1)
        min_index = -self._extended_border
        max_extended = max_index + self._extended_border
        clamped_x = max(min_index, min(max_extended, int(round(x))))
        clamped_y = max(min_index, min(max_extended, int(round(y))))
        return clamped_x, clamped_y

    def _initial_pole_yaw(
        self,
        fitted_point: tuple[int, int],
        entry: ElectricityEntry,
        fitted_road_segments: list[RoadSegment],
    ) -> float:
        """Resolve initial pole yaw, optionally orienting light assets toward nearby roads.

        Arguments:
            fitted_point (tuple[int, int]): Pole point in fitted output pixel space.
            entry (ElectricityEntry): Matched electricity asset entry.
            fitted_road_segments (list[RoadSegment]):
                Pre-fitted road segment endpoints.

        Returns:
            float: Initial yaw in degrees.
        """
        if entry.align_to_road is None:
            return 0.0

        point_x = float(fitted_point[0])
        point_y = float(fitted_point[1])
        nearest_road = self._nearest_road_point(point_x, point_y, fitted_road_segments)
        if nearest_road is None:
            return 0.0

        road_target = nearest_road.point
        road_distance = nearest_road.distance
        if road_distance > entry.align_to_road:
            return 0.0

        dx = road_target[0] - point_x
        dy = road_target[1] - point_y
        if math.hypot(dx, dy) <= 1e-6:
            return 0.0

        return math.degrees(math.atan2(dy, dx))

    @staticmethod
    def _nearest_road_point(
        point_x: float,
        point_y: float,
        fitted_road_segments: list[RoadSegment],
    ) -> NearestRoadHit | None:
        """Return nearest projected point on fitted road segments.

        Arguments:
            point_x (float): Query point X coordinate.
            point_y (float): Query point Y coordinate.
            fitted_road_segments (list[RoadSegment]):
                Road segment endpoints in fitted pixel space.

        Returns:
            NearestRoadHit | None: Closest road projection details, or None if unavailable.
        """
        best_point: tuple[float, float] | None = None
        best_distance_sq = float("inf")
        best_normal: tuple[float, float] | None = None
        best_half_width = 0.0

        for segment in fitted_road_segments:
            x1, y1 = segment.start
            x2, y2 = segment.end
            seg_dx = x2 - x1
            seg_dy = y2 - y1
            seg_len_sq = seg_dx * seg_dx + seg_dy * seg_dy
            if seg_len_sq <= 1e-12:
                continue
            seg_len = math.sqrt(seg_len_sq)
            normal_x = -seg_dy / seg_len
            normal_y = seg_dx / seg_len

            t = ((point_x - x1) * seg_dx + (point_y - y1) * seg_dy) / seg_len_sq
            t = max(0.0, min(1.0, t))
            proj_x = x1 + t * seg_dx
            proj_y = y1 + t * seg_dy
            dist_sq = (point_x - proj_x) ** 2 + (point_y - proj_y) ** 2

            if dist_sq < best_distance_sq:
                best_distance_sq = dist_sq
                best_point = (proj_x, proj_y)
                best_normal = (normal_x, normal_y)
                best_half_width = max(0.0, segment.width * 0.5)

        if best_point is None or best_normal is None:
            return None
        return NearestRoadHit(
            point=best_point,
            distance=math.sqrt(best_distance_sq),
            normal=best_normal,
            half_width=best_half_width,
        )

    @staticmethod
    def _parse_optional_distance(value: Any, allow_zero: bool = False) -> float | None:
        """Parse optional numeric distance from schema values.

        Arguments:
            value (Any): Raw schema value.
            allow_zero (bool, optional): Whether zero is considered valid.

        Returns:
            float | None: Parsed distance when valid, otherwise None.
        """
        if value is None or isinstance(value, bool):
            return None

        try:
            distance = float(value)
        except (TypeError, ValueError):
            return None

        if allow_zero and distance >= 0:
            return distance
        if distance > 0:
            return distance
        return None

    def info_sequence(self) -> dict[str, Any]:
        """Return electricity placement info for generation report.

        Returns:
            dict[str, Any]: Aggregated runtime counters for generation reporting.
        """
        return self.info
