"""Component for placing electricity poles from OSM point data using an electricity schema."""

from __future__ import annotations

import json
import math
import os
from typing import Any, NamedTuple
from xml.etree import ElementTree as ET

import numpy as np
import shapely
import trimesh
from tqdm import tqdm

from maps4fs.generator.component.base.component_mesh import MeshComponent
from maps4fs.generator.component.xml_document import XmlDocument
from maps4fs.generator.geo import get_region_by_coordinates
from maps4fs.generator.settings import Parameters


class ElectricityEntry(NamedTuple):
    """Data structure for a single electricity asset entry."""

    file: str
    name: str
    categories: list[str]
    regions: list[str]
    connectors: list["ConnectorEntry"]
    type: str | None = None


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
    entry: ElectricityEntry


class ElectricityEntryCollection:
    """Collection of electricity entries with category lookup."""

    def __init__(self, entries: list[ElectricityEntry], region: str):
        self.region = region
        self.entries = [
            entry
            for entry in entries
            if not entry.regions
            or region in entry.regions
            or Parameters.ALL_REGIONS in entry.regions
        ]
        if not self.entries:
            # Fall back to all entries so generation still works outside tagged regions.
            self.entries = entries

        self.by_category: dict[str, list[ElectricityEntry]] = {}
        for entry in self.entries:
            for category in entry.categories:
                self.by_category.setdefault(category, []).append(entry)

    def find_first(self, category: str) -> ElectricityEntry | None:
        """Return first entry for category, then default category fallback."""
        if category in self.by_category and self.by_category[category]:
            return self.by_category[category][0]
        default_entries = self.by_category.get(Parameters.DEFAULT_ELECTRICITY_CATEGORY, [])
        return default_entries[0] if default_entries else None


class Electricity(MeshComponent):
    """Component for placing electricity poles in map.i3d based on OSM point data."""

    def preprocess(self) -> None:
        """Load schema and prepare electricity component state."""
        self.info: dict[str, Any] = {}
        self.xml_path = self.game.i3d_file_path
        self.electricity_collection: ElectricityEntryCollection | None = None

        entries = self._load_electricity_schema()
        if not entries:
            return

        region = get_region_by_coordinates(self.coordinates)
        self.electricity_collection = ElectricityEntryCollection(entries, region)
        self.logger.info(
            "Electricity collection created with %d entries for region '%s'.",
            len(self.electricity_collection.entries),
            region,
        )

    def process(self) -> None:
        """Place electricity poles from context point data into map.i3d."""
        if self.electricity_collection is None:
            self.logger.info("Electricity schema is not loaded; skipping electricity placement.")
            return

        try:
            self.add_electricity()
        except Exception as e:  # pylint: disable=broad-except
            self.logger.warning("An error occurred during electricity processing: %s", e)

    def add_electricity(self) -> None:
        """Read electricity point data from context and append reference nodes to I3D."""
        points_data = self.get_infolayer_data(
            Parameters.TEXTURES, Parameters.ELECTRICITY_POLES_POINTS
        )
        if not points_data:
            self.logger.info("No electricity pole points found in context; skipping.")
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
            )
            if placed:
                placed_count += 1
            if placement is not None:
                placed_poles.append(placement)

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
        self.logger.info("Electricity placement completed and saved to map.i3d")

    def _load_electricity_schema(self) -> list[ElectricityEntry] | None:
        """Load electricity schema from custom map config or default game schema."""
        custom_schema = getattr(self.map, "electricity_custom_schema", None)
        if custom_schema:
            raw_schema = custom_schema
        else:
            schema_path = getattr(self.game, "electricity_schema", "")
            if not schema_path or not os.path.isfile(schema_path):
                self.logger.info("Electricity schema not found: %s", schema_path)
                return None
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
            regions = row.get("regions") or [Parameters.ALL_REGIONS]
            connectors = self._parse_connectors(row.get("connectors"))
            entry_type = row.get("type")

            entries.append(
                ElectricityEntry(
                    file=file,
                    name=name,
                    categories=list(categories),
                    regions=list(regions),
                    connectors=connectors,
                    type=str(entry_type) if entry_type is not None else None,
                )
            )

        if not entries:
            self.logger.warning("Electricity schema is empty. Electricity placement is skipped.")
            return None

        return entries

    def _parse_connectors(self, raw_connectors: Any) -> list[ConnectorEntry]:
        """Parse connectors from schema with sane defaults."""
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
        """Open map I3D XML and return required sections for electricity placement."""
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
        """Find or create electricity transform group in scene."""
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
        not_resized_dem,
        files_section: ET.Element,
        electricity_group: ET.Element,
        used_files: dict[str, int],
        used_file_ids: set[int],
        used_node_ids: set[int],
        file_id_counter: int,
        node_id_counter: int,
    ) -> tuple[bool, int, int, PolePlacement | None]:
        """Attempt to place one pole and return (placed, next_file_id, next_node_id)."""
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

        file_id, next_file_id = self._ensure_file_id(
            files_section,
            used_files,
            used_file_ids,
            best_match.file,
            file_id_counter,
        )

        node_id_counter = self._next_free_id(node_id_counter, used_node_ids)

        x_center, y_center = self.top_left_coordinates_to_center(fitted_point)
        try:
            z = self.get_z_coordinate_from_dem(not_resized_dem, fitted_point[0], fitted_point[1])
        except Exception:
            z = Parameters.DEFAULT_HEIGHT

        cfg = self.game.config
        pole_node = XmlDocument.create_element(
            cfg.i3d_reference_node_tag,
            {
                cfg.i3d_attr_name: f"{best_match.name}_{node_id_counter}",
                cfg.i3d_attr_translation: f"{x_center:.3f} {z:.3f} {y_center:.3f}",
                cfg.i3d_attr_rotation: "0 0 0",
                cfg.i3d_attr_reference_id: str(file_id),
                cfg.i3d_attr_node_id: str(node_id_counter),
            },
        )
        electricity_group.append(pole_node)

        used_node_ids.add(node_id_counter)

        placement = PolePlacement(
            x_pixel=fitted_point[0],
            y_pixel=fitted_point[1],
            x_world=float(x_center),
            z_world=float(y_center),
            ground_height=float(z),
            yaw_degrees=0.0,
            entry=best_match,
        )

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
        """Build one mesh network from line topology and attach as one referenced I3D asset."""
        if len(poles) < 2 or not line_records:
            return 0

        segments = self._build_powerline_segments(poles, line_records)
        if not segments:
            return 0

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

        Works for XML i3d and text-readable converted i3d outputs.
        """
        try:
            doc = XmlDocument(i3d_path)
            material = doc.root.find(".//Materials/Material")
            if material is not None:
                material.set("diffuseColor", "0.03 0.03 0.03 1")
                material.set("specularColor", "0.02 0.02 0.02")
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
    ) -> list[list[tuple[float, float, float]]]:
        """Build connector-to-connector sagging 3D polylines following OSM electricity lines."""
        segments: list[list[tuple[float, float, float]]] = []
        used_pairs: set[tuple[int, int]] = set()

        for record in line_records:
            points = record.get(Parameters.POINTS) if isinstance(record, dict) else None
            if not isinstance(points, list) or len(points) < 2:
                continue

            try:
                fitted_line = self.fit_object_into_bounds(
                    linestring_points=points, angle=self.rotation
                )
            except ValueError:
                continue

            if len(fitted_line) < 2:
                continue

            line_pole_sequence = self._line_pole_sequence(poles, fitted_line)
            if len(line_pole_sequence) < 2:
                continue

            for start_idx, end_idx in zip(line_pole_sequence[:-1], line_pole_sequence[1:]):
                if start_idx == end_idx:
                    continue

                pair = (min(start_idx, end_idx), max(start_idx, end_idx))
                if pair in used_pairs:
                    continue
                used_pairs.add(pair)

                pole_a = poles[start_idx]
                pole_b = poles[end_idx]

                dir_x, dir_z, right_x, right_z = self._pair_directions(pole_a, pole_b)
                if dir_x == 0.0 and dir_z == 0.0:
                    continue

                connectors_a = sorted(pole_a.entry.connectors, key=lambda c: c.side)
                connectors_b = sorted(pole_b.entry.connectors, key=lambda c: c.side)

                connectors_count = min(len(connectors_a), len(connectors_b))
                for idx in range(connectors_count):
                    p1 = self._connector_world_position(
                        pole_a,
                        connectors_a[idx],
                        right_x,
                        right_z,
                    )
                    p2 = self._connector_world_position(
                        pole_b,
                        connectors_b[idx],
                        right_x,
                        right_z,
                    )
                    segments.append(self._build_sagging_polyline(p1, p2))

        return segments

    def _line_pole_sequence(
        self,
        poles: list[PolePlacement],
        fitted_line: list[tuple[int, int]],
    ) -> list[int]:
        """Map a fitted OSM line to an ordered sequence of nearby pole indices."""
        sequence: list[int] = []
        for point in fitted_line:
            idx = self._nearest_pole_index(poles, point)
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
        """Return normalized forward and right vectors in XZ plane for a pole pair."""
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
    ) -> int | None:
        """Return index of nearest pole in fitted pixel space within max distance."""
        px, py = point
        best_idx: int | None = None
        best_distance = float("inf")

        for idx, pole in enumerate(poles):
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
        right_x: float,
        right_z: float,
    ) -> tuple[float, float, float]:
        """Convert connector local pole coordinates to world XYZ coordinates.

        The connector side offset is applied along the pair-right vector so wires stay
        parallel regardless of map orientation.
        """

        x = pole.x_world + connector.side * right_x
        y = pole.ground_height + connector.height
        z = pole.z_world + connector.side * right_z
        return (x, y, z)

    def _build_sagging_polyline(
        self,
        p1: tuple[float, float, float],
        p2: tuple[float, float, float],
        steps: int = 10,
    ) -> list[tuple[float, float, float]]:
        """Build a sagging polyline between two connector points using a parabola."""
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
        segments: list[list[tuple[float, float, float]]],
    ) -> trimesh.Trimesh | None:
        """Build a single mesh from cylinder strips representing powerlines."""
        cylinders: list[trimesh.Trimesh] = []
        for segment in segments:
            if len(segment) < 2:
                continue
            for p1, p2 in zip(segment[:-1], segment[1:]):
                if shapely.LineString([(p1[0], p1[2]), (p2[0], p2[2])]).length < 0.01:
                    continue
                cylinder = trimesh.creation.cylinder(
                    radius=0.04,
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
        """Return file ID for an electricity asset, appending <File> on first use."""
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

    def _collect_used_file_ids(self, files_section: ET.Element) -> set[int]:
        """Collect numeric file IDs already present in I3D <Files>."""
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
        """Collect numeric node IDs already present in I3D <Scene> subtree."""
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
        """Return first free numeric ID starting from start_id."""
        candidate = start_id
        while candidate in used_ids:
            candidate += 1
        return candidate

    def _fit_point_into_bounds(self, point: tuple[int, int]) -> tuple[int, int] | None:
        """Fit point into output bounds by using a tiny line through the point."""
        x, y = point
        try:
            fitted = self.fit_object_into_bounds(
                linestring_points=[(x, y), (x + 1, y)],
                angle=self.rotation,
            )
            if not fitted:
                return None
            fx, fy = fitted[0]
            return int(fx), int(fy)
        except ValueError:
            return None

    def _resolve_electricity_category(self, osm_tags: dict[str, Any]) -> str:
        """Resolve electricity category from texture layer tag rules."""
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

    def info_sequence(self) -> dict[str, Any]:
        """Return electricity placement info for generation report."""
        return self.info
