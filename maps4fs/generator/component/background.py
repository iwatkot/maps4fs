"""This module contains the Background component, which generates 3D obj files based on DEM data
around the map."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from typing import Any, Sequence

import cv2
import numpy as np
import shapely
import trimesh
from tqdm import tqdm
from trimesh import Trimesh

from maps4fs.generator.component.base.component_image import ImageComponent
from maps4fs.generator.component.base.component_mesh import MeshComponent
from maps4fs.generator.component.texture import Texture, TextureOptions
from maps4fs.generator.constants import Paths
from maps4fs.generator.monitor import monitor_performance
from maps4fs.generator.settings import Parameters


class Background(MeshComponent, ImageComponent):
    """Component for creating 3D obj files based on DEM data around the map.

    Arguments:
        game (Game): The game instance for which the map is generated.
        coordinates (tuple[float, float]): The latitude and longitude of the center of the map.
        map_size (int): The size of the map in pixels (it's a square).
        rotated_map_size (int): The size of the map in pixels after rotation.
        rotation (int): The rotation angle of the map.
        map_directory (str): The directory where the map files are stored.
        logger (Any, optional): The logger to use. Must have at least three basic methods: debug,
            info, warning. If not provided, default logging will be used.
    """

    @monitor_performance
    def preprocess(self) -> None:
        """Registers the DEMs for the background terrain."""
        self.stl_preview_path = os.path.join(self.previews_directory, "background_dem.stl")

        if self.rotation:
            self.logger.debug("Rotation is enabled: %s.", self.rotation)
            output_size_multiplier = 1.5
        else:
            output_size_multiplier = 1

        self.background_size = self.map_size + Parameters.BACKGROUND_DISTANCE * 2
        self.rotated_size = int(self.background_size * output_size_multiplier)
        self.mesh_info: list[dict[str, Any]] = []

        self.background_directory = os.path.join(
            self.map_directory, Parameters.BACKGROUND_DIRECTORY
        )
        os.makedirs(self.background_directory, exist_ok=True)

        self.textured_mesh_directory = os.path.join(
            self.background_directory,
            Parameters.TEXTURED_MESH_DIRECTORY,
        )
        os.makedirs(self.textured_mesh_directory, exist_ok=True)

        self.assets_background_directory = os.path.join(
            self.map.assets_directory,
            Parameters.BACKGROUND_DIRECTORY,
        )
        os.makedirs(self.assets_background_directory, exist_ok=True)

        self.output_path = self.map.context.dem_path or os.path.join(
            self.background_directory,
            f"{Parameters.FULL}.png",
        )
        self.not_substracted_path: str = self.map.context.dem_not_subtracted_path or os.path.join(
            self.background_directory, "not_substracted.png"
        )

    def process(self) -> None:
        """Launches the component processing. Iterates over all tiles and processes them
        as a result the DEM files will be saved, then based on them the obj files will be
        generated."""
        cutted_dem_path = self._prepare_main_dem()

        if self.game.additional_dem_name is not None:
            self.make_copy(cutted_dem_path, self.game.additional_dem_name)

        self._generate_optional_assets()
        self.process_road_masks()

    def _prepare_main_dem(self) -> str:
        """Prepare and save DEM outputs used by downstream generation steps."""
        if not os.path.isfile(self.output_path):
            raise FileNotFoundError(
                f"Background DEM not found. Expected DEM component output: {self.output_path}"
            )

        self.validate_np_for_mesh(self.output_path, self.map_size)

        if not os.path.isfile(self.not_substracted_path):
            shutil.copyfile(self.output_path, self.not_substracted_path)

        cutted_dem_path = self.save_map_dem(self.output_path)
        self.save_map_dem(
            self.output_path, save_path=self.not_resized_path(Parameters.NOT_RESIZED_DEM)
        )

        if self.map.background_settings.flatten_roads:
            self.flatten_roads()

        return cutted_dem_path

    def _generate_optional_assets(self) -> None:
        """Generate optional background terrain assets based on settings."""
        if self.map.background_settings.generate_background:
            self.generate_obj_files()
            self.decimate_background_mesh()
            self.texture_background_mesh()
            self.convert_background_mesh_to_i3d()
            self.generate_background_trees()

    def _read_background_tree_schema(self) -> list[dict[str, Any]]:
        """Read and validate minimal background tree schema entries.

        Returns:
            list[dict[str, Any]]: Normalized tree entries containing safe name,
                resolved texture path, and dimensions.
        """
        schema_path = getattr(self.game, "background_schema", "")
        if not schema_path:
            return []

        if not os.path.isfile(schema_path):
            self.logger.debug("Background tree schema not found: %s", schema_path)
            return []

        try:
            with open(schema_path, "r", encoding="utf-8") as schema_file:
                raw_schema = json.load(schema_file)
        except Exception as e:
            self.logger.warning("Could not load background tree schema %s: %s", schema_path, e)
            return []

        if not isinstance(raw_schema, list):
            self.logger.warning("Background tree schema must be a list: %s", schema_path)
            return []

        entries: list[dict[str, Any]] = []
        for idx, raw_entry in enumerate(raw_schema, start=1):
            if not isinstance(raw_entry, dict):
                continue

            category = str(raw_entry.get("category", "")).strip().lower()
            if category != Parameters.BACKGROUND_TREES_CATEGORY:
                continue

            name = str(raw_entry.get("name", "")).strip()
            path = str(raw_entry.get("path", "")).strip()
            if not name or not path:
                self.logger.warning(
                    "Skipping background tree entry #%s: missing name/path.",
                    idx,
                )
                continue

            raw_width = raw_entry.get("width")
            raw_height = raw_entry.get("height")
            if raw_width is None or raw_height is None:
                self.logger.warning(
                    "Skipping background tree '%s': width/height must be numbers.",
                    name,
                )
                continue

            try:
                width = float(raw_width)
                height = float(raw_height)
            except (TypeError, ValueError):
                self.logger.warning(
                    "Skipping background tree '%s': width/height must be numbers.",
                    name,
                )
                continue

            if width <= 0 or height <= 0:
                self.logger.warning(
                    "Skipping background tree '%s': width/height must be positive.",
                    name,
                )
                continue

            texture_path = self._resolve_background_tree_texture_path(path)
            if not texture_path:
                self.logger.warning(
                    "Skipping background tree '%s': texture file not found for path '%s'.",
                    name,
                    path,
                )
                continue

            safe_name = "".join(ch if ch.isalnum() or ch in {"_", "-"} else "_" for ch in name)
            safe_name = safe_name.strip("_").lower() or f"tree_{idx}"

            entries.append(
                {
                    "name": name,
                    "safe_name": safe_name,
                    "texture_path": texture_path,
                    "width": width,
                    "height": height,
                }
            )

        return entries

    @staticmethod
    def _resolve_background_tree_texture_path(path_value: str) -> str | None:
        """Resolve a schema texture path against templates and map directories.

        Arguments:
            path_value (str): Relative or absolute path from the schema entry.

        Returns:
            str | None: Absolute path to existing texture file, otherwise None.
        """
        normalized = path_value.replace("/", os.sep).replace("\\", os.sep).strip()
        if not normalized:
            return None

        candidates = []
        if os.path.isabs(normalized):
            candidates.append(normalized)
        else:
            candidates.append(os.path.join(Paths.TEMPLATES_DIR, normalized))
            candidates.append(os.path.join(os.getcwd(), normalized))

        for candidate in candidates:
            if os.path.isfile(candidate):
                return candidate
        return None

    def _collect_background_forest_layers(self) -> list[dict[str, Any]]:
        """Collect and normalize forest layers for background mask rasterization.

        Returns:
            list[dict[str, Any]]: Forest layer definitions suitable for background
                texture processing.
        """
        layers_schema = self.map.texture_schema or []
        forest_layers = [
            layer
            for layer in layers_schema
            if isinstance(layer, dict) and layer.get("usage") == "forest"
        ]
        if not forest_layers:
            return []

        background_forest_layers = [
            layer for layer in forest_layers if layer.get("background") is True
        ]
        source_layers = background_forest_layers if background_forest_layers else forest_layers

        normalized_layers: list[dict[str, Any]] = []
        for idx, layer in enumerate(source_layers, start=1):
            if not layer.get("name"):
                continue
            normalized = dict(layer)
            normalized["name"] = f"{layer['name']}_bgforest_{idx}"
            normalized["count"] = 1
            normalized["background"] = True
            normalized_layers.append(normalized)
        return normalized_layers

    def _render_background_forest_mask(self) -> np.ndarray | None:
        """Rasterize OSM forest layers on a background-sized canvas.

        Returns:
            np.ndarray | None: Merged grayscale forest mask, or None when source
                layers are unavailable.
        """
        background_forest_layers = self._collect_background_forest_layers()
        if not background_forest_layers:
            self.logger.warning(
                "No forest layers found for background trees. "
                "Set usage='forest' in texture schema (and optionally background=true)."
            )
            return None

        background_texture = Texture(
            self.game,
            self.map,
            map_size=self.background_size,
            map_rotated_size=self.rotated_size,
            options=TextureOptions(
                texture_custom_schema=background_forest_layers,
                skip_scaling=True,
                channel="background",
                cap_style="round",
            ),
        )
        background_texture.preprocess()
        background_texture.process()

        processed_layers = background_texture.get_background_layers()
        if not processed_layers:
            self.logger.warning("No processed background forest layers available.")
            return None

        weights_directory = self.game.weights_dir_path
        mask: np.ndarray = np.zeros((self.background_size, self.background_size), dtype=np.uint8)
        for layer in processed_layers:
            layer_image_path = layer.get_preview_or_path(weights_directory)
            layer_image = cv2.imread(layer_image_path, cv2.IMREAD_GRAYSCALE)
            if layer_image is None:
                continue
            if layer_image.shape != mask.shape:
                resized_layer_image = cv2.resize(
                    layer_image,
                    (mask.shape[1], mask.shape[0]),
                    interpolation=cv2.INTER_NEAREST,
                )
                mask = cv2.max(mask, np.asarray(resized_layer_image, dtype=np.uint8))
                continue
            mask = cv2.max(mask, layer_image)

        return mask

    def _background_tree_candidate_points(
        self,
        forest_mask: np.ndarray,
    ) -> tuple[list[tuple[int, int]], int]:
        """Sample deterministic sparse points from the background forest mask.

        Arguments:
            forest_mask (np.ndarray): Grayscale forest mask on the background canvas.

        Returns:
            tuple[list[tuple[int, int]], int]: Candidate points and sampling step.
        """
        height, width = forest_mask.shape[:2]
        center_x = width // 2
        center_y = height // 2

        expected_full_size = max(1, self.background_size)
        scale = min(width, height) / expected_full_size

        step = max(8, int(Parameters.BACKGROUND_TREES_FOREST_STEP * scale))
        inner_buffer = max(0, int(Parameters.BACKGROUND_TREES_RING_BUFFER * scale))
        playable_half = max(1, int((self.map_size / 2) * scale))

        points: list[tuple[int, int]] = []
        for y in range(0, height, step):
            for x in range(0, width, step):
                if forest_mask[y, x] == 0:
                    continue

                dx = abs(x - center_x)
                dy = abs(y - center_y)

                if dx <= playable_half + inner_buffer and dy <= playable_half + inner_buffer:
                    continue

                points.append((x, y))

        return points, step

    def _cleanup_previous_background_tree_assets(self) -> None:
        """Remove previously generated background tree meshes and textures.

        Returns:
            None
        """
        if not os.path.isdir(self.assets_background_directory):
            return

        for entry in os.scandir(self.assets_background_directory):
            if not entry.is_file():
                continue

            filename = entry.name
            is_tree_mesh = filename.startswith(Parameters.BACKGROUND_TREES_ASSET_PREFIX)
            is_tree_texture = filename.startswith("bg_") and filename.lower().endswith(".dds")
            if is_tree_mesh or is_tree_texture:
                try:
                    os.remove(entry.path)
                except OSError:
                    self.logger.debug(
                        "Could not remove stale background tree asset: %s", entry.path
                    )

    def _is_background_ring_point(
        self,
        x: int,
        y: int,
        shape: tuple[int, int],
    ) -> bool:
        """Check whether point is outside playable center on the background canvas.

        Arguments:
            x (int): X coordinate in mask space.
            y (int): Y coordinate in mask space.
            shape (tuple[int, int]): Mask shape as (height, width).

        Returns:
            bool: True when point belongs to the background ring.
        """
        height, width = shape
        center_x = width // 2
        center_y = height // 2

        expected_full_size = max(1, self.background_size)
        scale = min(width, height) / expected_full_size
        inner_buffer = max(0, int(Parameters.BACKGROUND_TREES_RING_BUFFER * scale))
        playable_half = max(1, int((self.map_size / 2) * scale))

        dx = abs(x - center_x)
        dy = abs(y - center_y)
        return not (dx <= playable_half + inner_buffer and dy <= playable_half + inner_buffer)

    def _randomize_background_tree_points(
        self,
        points: list[tuple[int, int]],
        forest_mask: np.ndarray,
        jitter_range: int,
        seed: int,
    ) -> list[tuple[int, int]]:
        """Apply deterministic jitter while keeping points in valid forest ring area.

        Arguments:
            points (list[tuple[int, int]]): Input candidate points.
            forest_mask (np.ndarray): Forest mask for validity checks.
            jitter_range (int): Max random offset in pixels for both axes.
            seed (int): Seed used to keep randomization deterministic.

        Returns:
            list[tuple[int, int]]: Jittered points constrained to valid locations.
        """
        if jitter_range <= 0 or not points:
            return points

        height, width = forest_mask.shape[:2]
        rng = np.random.default_rng(seed)
        randomized: list[tuple[int, int]] = []

        for x, y in points:
            chosen_x, chosen_y = x, y
            for _ in range(4):
                offset_x = int(rng.integers(-jitter_range, jitter_range + 1))
                offset_y = int(rng.integers(-jitter_range, jitter_range + 1))

                nx = max(0, min(width - 1, x + offset_x))
                ny = max(0, min(height - 1, y + offset_y))

                if forest_mask[ny, nx] == 0:
                    continue
                if not self._is_background_ring_point(nx, ny, (height, width)):
                    continue

                chosen_x, chosen_y = nx, ny
                break

            randomized.append((chosen_x, chosen_y))

        return randomized

    @staticmethod
    def _append_billboard_quad(
        vertices: list[tuple[float, float, float]],
        faces: list[tuple[int, int, int]],
        uvs: list[tuple[float, float]],
        p0: tuple[float, float, float],
        p1: tuple[float, float, float],
        p2: tuple[float, float, float],
        p3: tuple[float, float, float],
    ) -> None:
        """Append one textured billboard quad to mesh buffers.

        Arguments:
            vertices (list[tuple[float, float, float]]): Vertex buffer to extend.
            faces (list[tuple[int, int, int]]): Face index buffer to extend.
            uvs (list[tuple[float, float]]): UV buffer to extend.
            p0 (tuple[float, float, float]): Bottom-left vertex.
            p1 (tuple[float, float, float]): Bottom-right vertex.
            p2 (tuple[float, float, float]): Top-right vertex.
            p3 (tuple[float, float, float]): Top-left vertex.

        Returns:
            None
        """
        base = len(vertices)
        vertices.extend([p0, p1, p2, p3])
        # FS uses top-left texture origin; keep UV V increasing downwards to avoid upside-down billboards.
        uvs.extend([(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)])
        faces.append((base, base + 1, base + 2))
        faces.append((base, base + 2, base + 3))

    @staticmethod
    def _has_texture_reference(i3d_path: str) -> bool:
        """Check whether i3d contains texture references for fileId=1.

        Arguments:
            i3d_path (str): Path to i3d file to inspect.

        Returns:
            bool: True when both file and texture entries for fileId=1 exist.
        """
        if not os.path.isfile(i3d_path):
            return False
        try:
            with open(i3d_path, "r", encoding="utf-8") as i3d_file:
                content = i3d_file.read()
        except Exception:
            return False
        return ('<File fileId="1"' in content) and ('<Texture fileId="1"' in content)

    def _export_background_tree_i3d(
        self,
        mesh: trimesh.Trimesh,
        output_dir: str,
        name: str,
        texture_path: str,
    ) -> str:
        """Export background tree mesh and preserve raw payload as fallback.

        Arguments:
            mesh (trimesh.Trimesh): Generated billboard mesh.
            output_dir (str): Destination directory for exported files.
            name (str): Asset base name.
            texture_path (str): Source texture path.

        Returns:
            str: Path to binary i3d output, or raw i3d path on conversion failure.
        """
        os.makedirs(output_dir, exist_ok=True)

        texture_file = self._prepare_background_tree_texture(texture_path, output_dir)
        raw_i3d_path = os.path.join(output_dir, f"{name}.i3d")
        binary_i3d_path = os.path.join(output_dir, f"{name}{Parameters.BINARY_I3D_SUFFIX}")

        self._write_i3d_file(mesh, raw_i3d_path, name, texture_file, is_water=False)

        try:
            self.to_i3d_binary(raw_i3d_path, binary_i3d_path, remove_raw_i3d=True)
            self.fix_binary_paths(binary_i3d_path)
        except Exception:
            return raw_i3d_path

        if self._has_texture_reference(binary_i3d_path):
            return binary_i3d_path

        # If converter dropped texture links, keep binary filename but raw XML payload.
        shutil.copyfile(raw_i3d_path, binary_i3d_path)

        raw_shapes_path = f"{raw_i3d_path}.shapes"
        binary_shapes_path = f"{binary_i3d_path}.shapes"
        if os.path.isfile(raw_shapes_path):
            shutil.copyfile(raw_shapes_path, binary_shapes_path)

        self.logger.warning(
            "Background tree binary lacked texture reference for %s; "
            "replaced with raw i3d payload.",
            name,
        )
        return binary_i3d_path

    def _prepare_background_tree_texture(self, texture_path: str, output_dir: str) -> str:
        """Copy and optionally normalize texture used by background trees.

        Arguments:
            texture_path (str): Source texture path.
            output_dir (str): Destination directory for copied/converted texture.

        Returns:
            str: Destination texture filename used in exported i3d.
        """
        source_path = texture_path
        dest_path = os.path.join(output_dir, os.path.basename(source_path))

        ext = os.path.splitext(source_path)[1].lower()
        texconv_path = Paths.get_texconv_executable_path()

        if ext == ".dds" and texconv_path is not None:
            output_dir_abs = os.path.abspath(output_dir)
            cmd = [
                texconv_path,
                "-f",
                "BC3_UNORM",
                "-m",
                "1",
                "-y",
                "-o",
                output_dir_abs,
                os.path.abspath(source_path),
            ]

            run_kwargs: dict[str, Any] = {
                "stdin": subprocess.DEVNULL,
                "capture_output": True,
                "text": True,
            }
            if os.name == "nt":
                run_kwargs["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)

            try:
                result = subprocess.run(cmd, **run_kwargs)  # pylint: disable=subprocess-run-check
                if result.returncode == 0:
                    produced_path = os.path.join(
                        output_dir_abs,
                        os.path.splitext(os.path.basename(source_path))[0] + ".dds",
                    )
                    if os.path.abspath(produced_path) != os.path.abspath(dest_path):
                        os.replace(produced_path, dest_path)
                    return os.path.basename(dest_path)

                self.logger.warning(
                    "texconv DDS normalization failed for %s (exit %s). "
                    "Falling back to raw copy. stderr: %s",
                    source_path,
                    result.returncode,
                    result.stderr.strip(),
                )
            except Exception as e:
                self.logger.warning(
                    "texconv DDS normalization failed for %s: %s. Falling back to raw copy.",
                    source_path,
                    e,
                )

        if os.path.abspath(source_path) != os.path.abspath(dest_path):
            shutil.copy2(source_path, dest_path)
        return os.path.basename(dest_path)

    def _build_background_tree_mesh(
        self,
        points: list[tuple[int, int]],
        width_m: float,
        height_m: float,
        dem_image: np.ndarray,
        size_rng: np.random.Generator,
        size_variation: float = 0.2,
    ) -> Trimesh:
        """Build crossed-billboard mesh geometry for tree points.

        Arguments:
            points (list[tuple[int, int]]): Placement points in DEM pixel space.
            width_m (float): Base billboard width in meters.
            height_m (float): Base billboard height in meters.
            dem_image (np.ndarray): DEM image for base elevation sampling.
            size_rng (np.random.Generator): RNG used for per-instance size jitter.
            size_variation (float): Max relative size variation, e.g. 0.2 for +/-20%.

        Returns:
            Trimesh: Mesh containing crossed quads for all provided points.
        """
        if not points:
            return trimesh.Trimesh()

        vertices: list[tuple[float, float, float]] = []
        faces: list[tuple[int, int, int]] = []
        uvs: list[tuple[float, float]] = []

        image_height, image_width = dem_image.shape[:2]
        center_x = image_width / 2.0
        center_y = image_height / 2.0
        for px, py in points:
            scale_factor = 1.0
            if size_variation > 0:
                scale_factor = float(size_rng.uniform(1.0 - size_variation, 1.0 + size_variation))

            tree_width = width_m * scale_factor
            tree_height = height_m * scale_factor
            half_width = tree_width / 2.0

            base_y = float(self.get_z_coordinate_from_dem(dem_image, px, py))
            top_y = base_y + tree_height
            world_x = float(px - center_x)
            world_z = float(py - center_y)

            # First quad: facing +Z/-Z directions.
            self._append_billboard_quad(
                vertices,
                faces,
                uvs,
                (world_x - half_width, base_y, world_z),
                (world_x + half_width, base_y, world_z),
                (world_x + half_width, top_y, world_z),
                (world_x - half_width, top_y, world_z),
            )

            # Second quad: rotated 90 degrees, facing +X/-X directions.
            self._append_billboard_quad(
                vertices,
                faces,
                uvs,
                (world_x, base_y, world_z - half_width),
                (world_x, base_y, world_z + half_width),
                (world_x, top_y, world_z + half_width),
                (world_x, top_y, world_z - half_width),
            )

        mesh = trimesh.Trimesh(
            vertices=np.asarray(vertices, dtype=np.float64),
            faces=np.asarray(faces, dtype=np.int64),
            process=False,
        )
        mesh.visual = trimesh.visual.texture.TextureVisuals(uv=np.asarray(uvs, dtype=np.float64))
        return mesh

    @monitor_performance
    def generate_background_trees(self) -> None:
        """Generate sparse background tree billboard assets from schema textures.

        Returns:
            None
        """
        tree_entries = self._read_background_tree_schema()
        if not tree_entries:
            self.logger.debug("No valid background tree entries found; skipping generation.")
            return

        self._cleanup_previous_background_tree_assets()

        if not os.path.isfile(self.output_path):
            self.logger.warning(
                "Background DEM not found for background trees: %s", self.output_path
            )
            return

        dem_image = cv2.imread(self.output_path, cv2.IMREAD_UNCHANGED)
        if dem_image is None:
            self.logger.warning(
                "Could not read background DEM for background trees: %s",
                self.output_path,
            )
            return

        forest_mask = self._render_background_forest_mask()
        if forest_mask is None:
            return

        if forest_mask.shape[:2] != dem_image.shape[:2]:
            forest_mask = cv2.resize(
                forest_mask,
                (dem_image.shape[1], dem_image.shape[0]),
                interpolation=cv2.INTER_NEAREST,
            )

        candidate_points, step = self._background_tree_candidate_points(forest_mask)
        if not candidate_points:
            self.logger.warning("No candidate points for background tree generation.")
            return

        generated_assets = 0
        entry_count = len(tree_entries)
        seed_base = (
            int(abs(self.coordinates[0]) * 1_000_000)
            + int(abs(self.coordinates[1]) * 1_000_000)
            + self.map_size
        )

        for idx, tree_entry in enumerate(tree_entries):
            assigned_points = candidate_points[idx::entry_count]
            if not assigned_points:
                continue

            jitter_range = max(1, step // 3)
            assigned_points = self._randomize_background_tree_points(
                assigned_points,
                forest_mask,
                jitter_range=jitter_range,
                seed=seed_base + (idx + 1) * 7919,
            )

            size_rng = np.random.default_rng(seed_base + (idx + 1) * 1543)

            tree_mesh = self._build_background_tree_mesh(
                assigned_points,
                float(tree_entry["width"]),
                float(tree_entry["height"]),
                dem_image,
                size_rng=size_rng,
                size_variation=0.2,
            )
            if len(tree_mesh.faces) == 0:
                continue

            asset_name = (
                f"{Parameters.BACKGROUND_TREES_ASSET_PREFIX}"
                f"{tree_entry['safe_name']}_{idx + 1:02d}"
            )
            i3d_path = self._export_background_tree_i3d(
                tree_mesh,
                output_dir=self.assets_background_directory,
                name=asset_name,
                texture_path=str(tree_entry["texture_path"]),
            )
            self.logger.debug(
                "Background trees asset generated: %s using %s points (%s).",
                i3d_path,
                len(assigned_points),
                tree_entry["name"],
            )
            generated_assets += 1

        self.logger.debug("Generated %s background tree assets.", generated_assets)

    def not_resized_paths(self) -> list[str]:
        """Returns the list of paths to all not resized DEM files.

        Returns:
            list[str] : The list of paths to all not resized DEM files.
        """
        return [self.not_resized_path(dem_type) for dem_type in Parameters.SUPPORTED_DEM_TYPES]

    def not_resized_path(self, dem_type: str) -> str:
        """Returns the path to the specified not resized DEM file.

        Arguments:
            dem_type (str): The type of the DEM file. Must be one of the SUPPORTED_DEM_TYPES.

        Raises:
            ValueError: If the dem_type is not supported.

        Returns:
            str: The path to the specified not resized DEM file.
        """
        if not dem_type.endswith(".png"):
            dem_type += ".png"
        if dem_type not in Parameters.SUPPORTED_DEM_TYPES:
            raise ValueError(f"Unsupported dem_type: {dem_type}")

        return os.path.join(self.background_directory, dem_type)

    @monitor_performance
    def create_foundations(self, dem_image: np.ndarray) -> np.ndarray:
        """Creates foundations for buildings based on the DEM data.

        Arguments:
            dem_image (np.ndarray): The DEM data as a numpy array.

        Returns:
            np.ndarray: The DEM data with the foundations added.
        """
        buildings = self.get_infolayer_data(Parameters.TEXTURES, Parameters.BUILDINGS)
        if not buildings:
            self.logger.warning("Buildings data not found in textures info layer.")
            return dem_image

        self.logger.debug("Found %s buildings in textures info layer.", len(buildings))

        for building in tqdm(buildings, desc="Creating foundations", unit="building"):
            mask = self._get_building_mask(building, dem_image.shape)
            if mask is None:
                continue

            mean = cv2.mean(dem_image, mask=mask)
            mean_scalar = float(mean[0]) if isinstance(mean, Sequence) else float(mean)
            mean_value = np.array(round(mean_scalar), dtype=dem_image.dtype).item()
            dem_image[mask == 255] = mean_value

        return dem_image

    def _get_building_mask(
        self,
        building: list[tuple[int, int]],
        dem_shape: tuple[int, ...],
    ) -> np.ndarray | None:
        """Create a raster mask for one building footprint in DEM coordinates."""
        try:
            fitted_building = self.fit_object_into_bounds(
                polygon_points=building,
                angle=self.rotation,
            )
        except ValueError as e:
            self.logger.debug("Building could not be fitted into the map bounds: %s", e)
            return None

        building_np = self.polygon_points_to_np(fitted_building)
        mask = np.zeros(dem_shape, dtype=np.uint8)
        try:
            cv2.fillPoly(mask, [building_np], 255)
            return mask
        except Exception as e:
            self.logger.debug("Could not create building mask: %s", e)
            return None

    def make_copy(self, dem_path: str, dem_name: str) -> None:
        """Copies DEM data to additional DEM file.

        Arguments:
            dem_path (str): Path to the DEM file.
            dem_name (str): Name of the additional DEM file.
        """
        dem_directory = os.path.dirname(dem_path)

        additional_dem_path = os.path.join(dem_directory, dem_name)

        shutil.copyfile(dem_path, additional_dem_path)
        self.logger.debug("Additional DEM data was copied to %s.", additional_dem_path)

    def info_sequence(self) -> dict[str, Any]:
        """Returns a dictionary with information about the background terrain.
        Adds the EPSG:3857 string to the data for convenient usage in QGIS.

        Returns:
            dict[str, str, float | int] -- A dictionary with information about the background
                terrain.
        """
        north, south, east, west = self.bbox

        data: dict[str, Any] = {
            "center_latitude": self.coordinates[0],
            "center_longitude": self.coordinates[1],
            "height": self.map_size,
            "width": self.map_size,
            "north": north,
            "south": south,
            "east": east,
            "west": west,
        }
        data["Mesh"] = self.mesh_info
        return data

    @monitor_performance
    def generate_obj_files(self) -> None:
        """Iterates over all dems and generates 3D obj files based on DEM data.
        If at least one DEM file is missing, the generation will be stopped at all.
        """
        if not os.path.isfile(self.output_path):
            self.logger.error(
                "DEM file not found, generation will be stopped: %s", self.output_path
            )
            return

        self.logger.debug("DEM file for found: %s", self.output_path)

        filename = os.path.splitext(os.path.basename(self.output_path))[0]
        save_path = os.path.join(self.background_directory, f"{filename}.obj")
        self.logger.debug("Generating obj file in path: %s", save_path)

        self.assets.background_mesh = save_path

        dem_data = cv2.imread(self.output_path, cv2.IMREAD_UNCHANGED)
        if dem_data is None:
            self.logger.warning("Failed to read DEM file for OBJ generation: %s", self.output_path)
            return

        if self.map.output_size is not None:
            scaled_background_size = int(self.background_size * self.map.size_scale)
            dem_data = cv2.resize(
                dem_data,
                (scaled_background_size, scaled_background_size),
                interpolation=cv2.INTER_NEAREST,
            )

        self.plane_from_np(
            dem_data,
            save_path,
            create_preview=True,
            remove_center=False,
        )

    @staticmethod
    def get_decimate_factor(map_size: int) -> float:
        """Returns the decimation factor based on the map size.

        Arguments:
            map_size (int): The size of the map in pixels.

        Raises:
            ValueError: If the map size is too large for decimation.

        Returns:
            float -- The decimation factor.
        """
        thresholds = {
            2048: 0.1,
            4096: 0.05,
            8192: 0.025,
            16384: 0.0125,
        }
        for threshold, factor in thresholds.items():
            if map_size <= threshold:
                return min(1.0, factor * Parameters.BACKGROUND_TERRAIN_PARTS)
        raise ValueError(
            "Map size is too large for decimation, perform manual decimation in Blender."
        )

    @staticmethod
    def get_background_texture_resolution(map_size: int) -> int:
        """Returns the background texture resolution based on the map size.

        Arguments:
            map_size (int): The size of the map in pixels.

        Returns:
            int -- The background texture resolution.
        """
        resolutions = {
            2048: 2048,
            4096: Parameters.MAXIMUM_BACKGROUND_TEXTURE_SIZE,
            8192: Parameters.MAXIMUM_BACKGROUND_TEXTURE_SIZE,
            16384: Parameters.MAXIMUM_BACKGROUND_TEXTURE_SIZE,
        }
        for threshold, resolution in resolutions.items():
            if map_size <= threshold:
                return resolution
        return Parameters.MAXIMUM_BACKGROUND_TEXTURE_SIZE

    @staticmethod
    def _background_terrain_chunk_name(chunk_index: int) -> str:
        """Build deterministic chunk name for split background terrain mesh."""
        return f"{Parameters.BACKGROUND_TERRAIN_PART_PREFIX}{chunk_index + 1:02d}"

    def _cleanup_previous_background_terrain_assets(self) -> None:
        """Remove stale background terrain i3d assets before writing new chunks."""
        if not os.path.isdir(self.assets_background_directory):
            return

        for entry in os.scandir(self.assets_background_directory):
            if not entry.is_file():
                continue
            if not entry.name.startswith(Parameters.BACKGROUND_TERRAIN):
                continue
            try:
                os.remove(entry.path)
            except OSError:
                self.logger.debug("Could not remove stale background terrain asset: %s", entry.path)

    def _split_background_terrain_mesh(self, mesh: Trimesh) -> list[tuple[str, Trimesh]]:
        """Split textured background mesh into four aligned center-based quadrants."""
        if len(mesh.faces) == 0 or len(mesh.vertices) == 0:
            return []

        vertices = np.asarray(mesh.vertices)
        faces = np.asarray(mesh.faces)
        face_centroids = vertices[faces].mean(axis=1)

        x_coords = face_centroids[:, 0]
        z_coords = face_centroids[:, 2]
        quadrant_masks = [
            (x_coords <= 0) & (z_coords <= 0),
            (x_coords > 0) & (z_coords <= 0),
            (x_coords <= 0) & (z_coords > 0),
            (x_coords > 0) & (z_coords > 0),
        ]

        chunks: list[tuple[str, Trimesh]] = []
        for quadrant_index, mask in enumerate(quadrant_masks):
            face_indices = np.flatnonzero(mask)
            if len(face_indices) == 0:
                continue

            chunk_mesh_result = mesh.submesh([face_indices], append=True, repair=False)
            if isinstance(chunk_mesh_result, list):
                if not chunk_mesh_result:
                    continue
                chunk_mesh = chunk_mesh_result[0]
            else:
                chunk_mesh = chunk_mesh_result

            if len(chunk_mesh.faces) == 0:
                continue

            chunks.append((self._background_terrain_chunk_name(quadrant_index), chunk_mesh))

        return chunks

    @monitor_performance
    def decimate_background_mesh(self) -> None:
        """Decimates the background mesh based on the map size."""
        if not self.assets.background_mesh or not os.path.isfile(self.assets.background_mesh):
            self.logger.warning("Background mesh not found, cannot generate i3d background.")
            return

        try:
            mesh = trimesh.load_mesh(self.assets.background_mesh, force="mesh")
        except Exception as e:
            self.logger.error("Could not load background mesh: %s", e)
            return

        try:
            decimate_factor = self.get_decimate_factor(self.map_size)
        except ValueError as e:
            self.logger.error("Could not determine decimation factor: %s", e)
            return

        decimated_save_path = os.path.join(
            self.background_directory, f"{Parameters.DECIMATED_BACKGROUND}.obj"
        )
        try:
            self.logger.debug("Decimating background mesh with factor %s.", decimate_factor)
            decimated_mesh = self.decimate_mesh(mesh, decimate_factor)
            self.logger.debug("Decimation completed.")
        except Exception as e:
            self.logger.error("Could not decimate background mesh: %s", e)
            return

        if self.map.background_settings.remove_center:
            try:
                self.logger.debug("Removing center from decimated background mesh.")
                decimated_mesh = self.remove_center_from_mesh(
                    decimated_mesh,
                    self.scaled_size,
                    logger=self.logger,
                )
                self.logger.debug("Center removal from decimated background mesh completed.")
            except Exception as e:
                self.logger.error("Could not remove center from decimated background mesh: %s", e)
                return

        decimated_mesh.export(decimated_save_path)
        self.logger.debug("Decimated background mesh saved: %s", decimated_save_path)

        self.assets.decimated_background_mesh = decimated_save_path

    @monitor_performance
    def texture_background_mesh(self) -> None:
        """Textures the background mesh using satellite imagery."""
        decimated_background_mesh_path = self.assets.decimated_background_mesh
        if not decimated_background_mesh_path or not os.path.isfile(decimated_background_mesh_path):
            self.logger.warning(
                "Decimated background mesh not found, cannot texture background mesh."
            )
            return

        texture_bundle = self._prepare_background_texture_bundle()
        if texture_bundle is None:
            return
        resized_texture_save_path, texture_for_i3d = texture_bundle

        try:
            decimated_mesh = trimesh.load_mesh(decimated_background_mesh_path, force="mesh")
        except Exception as e:
            self.logger.error("Could not load decimated background mesh: %s", e)
            return

        try:
            obj_save_path, mtl_save_path = self.texture_mesh(
                decimated_mesh,
                resized_texture_save_path,
                output_directory=self.textured_mesh_directory,
                output_name="background_textured_mesh",
            )

            self.assets.textured_background_mesh = obj_save_path
            self.assets.textured_background_mtl = mtl_save_path
            self.assets.resized_background_texture = texture_for_i3d
            self.logger.debug("Textured background mesh saved: %s", obj_save_path)
        except Exception as e:
            self.logger.error("Could not texture background mesh: %s", e)
            return

    def _prepare_background_texture_bundle(self) -> tuple[str, str] | None:
        """Load, resize, and optionally convert the background texture to DDS."""
        background_texture_path = self.map.context.satellite_background_path
        if not background_texture_path or not os.path.isfile(background_texture_path):
            self.logger.warning("Background texture not found, cannot texture background mesh.")
            return None

        resolution = self.get_background_texture_resolution(self.map_size)
        source_image = cv2.imread(background_texture_path, cv2.IMREAD_UNCHANGED)
        if source_image is None:
            self.logger.error(
                "Failed to read background texture image: %s", background_texture_path
            )
            return None

        resized_texture_image = cv2.resize(
            source_image,
            (resolution, resolution),
            interpolation=cv2.INTER_AREA,
        )
        resized_texture_save_path = os.path.join(
            self.textured_mesh_directory, "background_texture.jpg"
        )
        cv2.imwrite(resized_texture_save_path, resized_texture_image)

        dds_texture_save_path = os.path.join(self.textured_mesh_directory, "background_texture.dds")
        texture_for_i3d = resized_texture_save_path
        try:
            self.convert_png_to_dds(resized_texture_save_path, dds_texture_save_path)
            texture_for_i3d = dds_texture_save_path
        except Exception as e:
            self.logger.warning("Could not convert background texture to DDS: %s", e)

        return resized_texture_save_path, texture_for_i3d

    @monitor_performance
    def convert_background_mesh_to_i3d(self) -> bool:
        """Converts the textured background mesh to i3d format.

        Returns:
            bool -- True if the conversion was successful, False otherwise.
        """
        if not self.assets.textured_background_mesh or not os.path.isfile(
            self.assets.textured_background_mesh
        ):
            self.logger.warning("Textured background mesh not found, cannot convert to i3d.")
            return False

        if not self.assets.resized_background_texture or not os.path.isfile(
            self.assets.resized_background_texture
        ):
            self.logger.warning("Resized background texture not found, cannot convert to i3d.")
            return False

        try:
            mesh = trimesh.load_mesh(self.assets.textured_background_mesh, force="mesh")
        except Exception as e:
            self.logger.error("Could not load textured background mesh: %s", e)
            return False

        self._cleanup_previous_background_terrain_assets()

        # Compute terrain max elevation and save for GE positioning.
        # The mesh is built with z_vertex = (pixel - max_pixel) * z_factor (inverted),
        # so T_y = max_pixel * z_factor maps every vertex back to its real elevation.
        try:
            background_dem = cv2.imread(self.not_substracted_path, cv2.IMREAD_UNCHANGED)
            if background_dem is not None:
                z_factor = self.get_z_scaling_factor(ignore_height_scale_multiplier=True)
                max_elevation = float(np.max(background_dem) * z_factor)
                for asset_name in [
                    Parameters.BACKGROUND_TERRAIN,
                    *[
                        self._background_terrain_chunk_name(chunk_index)
                        for chunk_index in range(Parameters.BACKGROUND_TERRAIN_PARTS)
                    ],
                ]:
                    self.map.context.set_mesh_position(
                        asset_name,
                        mesh_centroid_y=max_elevation,
                    )
                self.logger.debug("Background terrain T_y (max elevation): %.4f m", max_elevation)
        except Exception as e:
            self.logger.warning("Could not save background terrain elevation: %s", e)

        terrain_chunks = self._split_background_terrain_mesh(mesh)
        if not terrain_chunks:
            self.logger.warning(
                "No terrain chunks created from textured background mesh; "
                "falling back to single terrain mesh export."
            )
            terrain_chunks = [(Parameters.BACKGROUND_TERRAIN, mesh)]
        elif len(terrain_chunks) < Parameters.BACKGROUND_TERRAIN_PARTS:
            self.logger.warning(
                "Generated %s/%s background terrain chunks.",
                len(terrain_chunks),
                Parameters.BACKGROUND_TERRAIN_PARTS,
            )

        try:
            i3d_background_terrains: list[str] = []
            for chunk_name, chunk_mesh in terrain_chunks:
                i3d_background_terrain = self.mesh_to_i3d(
                    chunk_mesh,
                    output_dir=self.assets_background_directory,
                    name=chunk_name,
                    texture_path=self.assets.resized_background_texture,
                    water_mesh=False,
                )
                i3d_background_terrains.append(i3d_background_terrain)
                self.logger.debug(
                    "Background mesh chunk converted to i3d successfully: %s",
                    i3d_background_terrain,
                )

            self.assets.background_terrain_parts_i3d = i3d_background_terrains
            self.assets.background_terrain_i3d = i3d_background_terrains[0]
            return True
        except Exception as e:
            self.logger.error("Could not convert background mesh to i3d: %s", e)
            return False

    def map_dem_size(self) -> int:
        """Returns the size of the map DEM.

        Returns:
            int -- The size of the map DEM.
        """
        return self.scaled_size + 1

    def save_map_dem(self, dem_path: str, save_path: str | None = None) -> str:
        """Cuts out the center of the DEM (the actual map) and saves it as a separate file.

        Arguments:
            dem_path (str): The path to the DEM file.
            save_path (str, optional): The path where the cutout DEM file will be saved.

        Returns:
            str -- The path to the cutout DEM file.
        """
        dem_data = cv2.imread(dem_path, cv2.IMREAD_UNCHANGED)
        if dem_data is None:
            raise ValueError(f"Could not load DEM image: {dem_path}")
        half_size = self.map_size // 2
        dem_data = self.cut_out_np(dem_data, half_size, return_cutout=True)

        if save_path:
            cv2.imwrite(save_path, dem_data)
            self.logger.debug("Not resized DEM saved: %s", save_path)
            return save_path

        if self.map.dem_settings.add_foundations:
            dem_data = self.create_foundations(dem_data)
            cv2.imwrite(self.not_resized_path(Parameters.NOT_RESIZED_DEM_FOUNDATIONS), dem_data)
            self.logger.debug(
                "Not resized DEM with foundations saved: %s",
                self.not_resized_path(Parameters.NOT_RESIZED_DEM_FOUNDATIONS),
            )

        output_size = self.map_dem_size()

        main_dem_path = self.game.dem_file_path

        try:
            os.remove(main_dem_path)
        except FileNotFoundError:
            pass

        resized_dem_data = cv2.resize(
            dem_data, (output_size, output_size), interpolation=cv2.INTER_NEAREST
        )

        cv2.imwrite(main_dem_path, resized_dem_data)
        self.logger.debug("DEM cutout saved: %s", main_dem_path)

        self.assets.dem = main_dem_path

        return main_dem_path

    def plane_from_np(
        self,
        dem_data: np.ndarray,
        save_path: str,
        include_zeros: bool = True,
        create_preview: bool = False,
        remove_center: bool = False,
    ) -> None:
        """Generates a 3D obj file based on DEM data.

        Arguments:
            dem_data (np.ndarray) -- The DEM data as a numpy array.
            save_path (str) -- The path where the obj file will be saved.
            include_zeros (bool, optional) -- If True, the mesh will include the zero height values.
            create_preview (bool, optional) -- If True, a simplified mesh will be saved as an STL.
            remove_center (bool, optional) -- If True, the center of the mesh will be removed.
                This setting is used for a Background Terrain, where the center part where the
                playable area is will be cut out.
        """
        mesh = self.mesh_from_np(
            dem_data,
            include_zeros=include_zeros,
            z_scaling_factor=self.get_z_scaling_factor(ignore_height_scale_multiplier=True),
            remove_center=remove_center,
            remove_size=self.scaled_size,
            logger=self.logger,
        )

        try:
            self.update_mesh_info(save_path, mesh)
        except Exception as e:
            self.logger.error("Could not update mesh info: %s", e)

        mesh.export(save_path)
        self.logger.debug("Obj file saved: %s", save_path)

        if create_preview:
            try:
                mesh.apply_scale([0.5, 0.5, 0.5])
                self.mesh_to_stl(mesh, save_path=self.stl_preview_path)
            except Exception as e:
                self.logger.error("Could not create STL preview: %s", e)

    def update_mesh_info(self, save_path: str, mesh: Trimesh) -> None:
        """Updates the mesh info with the data from the mesh.

        Arguments:
            save_path (str): The path where the mesh is saved.
            mesh (Trimesh): The mesh to get the data from.
        """
        filename = os.path.splitext(os.path.basename(save_path))[0]
        x_size, y_size, z_size = mesh.extents
        x_center, y_center, z_center = mesh.centroid

        entry = {
            "name": filename,
            "x_size": round(x_size, 4),
            "y_size": round(y_size, 4),
            "z_size": round(z_size, 4),
            "x_center": round(x_center, 4),
            "y_center": round(y_center, 4),
            "z_center": round(z_center, 4),
        }

        self.mesh_info.append(entry)

    def previews(self) -> list[str]:
        """Returns the path to the image previews paths and the path to the STL preview file.

        Returns:
            list[str] -- A list of paths to the previews.
        """
        preview_paths = self.dem_previews(self.game.dem_file_path)

        background_dem_preview_path = os.path.join(self.previews_directory, "background_dem.png")

        if not os.path.isfile(self.output_path):
            self.logger.warning("DEM file not found for preview generation: %s", self.output_path)
            return []

        background_dem_preview_image = cv2.imread(self.output_path, cv2.IMREAD_UNCHANGED)
        if background_dem_preview_image is None:
            self.logger.warning("Could not read DEM preview source: %s", self.output_path)
            return preview_paths

        background_dem_preview_image = cv2.resize(
            background_dem_preview_image, (0, 0), fx=1 / 4, fy=1 / 4
        )
        background_dem_preview_image = cv2.normalize(
            background_dem_preview_image,
            dst=np.empty_like(background_dem_preview_image),
            alpha=0,
            beta=255,
            norm_type=cv2.NORM_MINMAX,
            dtype=cv2.CV_8U,
        )
        background_dem_preview_image = cv2.cvtColor(
            background_dem_preview_image, cv2.COLOR_GRAY2BGR
        )

        cv2.imwrite(background_dem_preview_path, background_dem_preview_image)
        preview_paths.append(background_dem_preview_path)

        if os.path.isfile(self.stl_preview_path):
            preview_paths.append(self.stl_preview_path)

        return preview_paths

    def dem_previews(self, image_path: str) -> list[str]:
        """Get list of preview images.

        Arguments:
            image_path (str): Path to the DEM file.

        Returns:
            list[str]: List of preview images.
        """
        self.logger.debug("Starting DEM previews generation.")
        return [self.grayscale_preview(image_path), self.colored_preview(image_path)]

    def grayscale_preview(self, image_path: str) -> str:
        """Converts DEM image to grayscale RGB image and saves it to the map directory.
        Returns path to the preview image.

        Arguments:
            image_path (str): Path to the DEM file.

        Returns:
            str: Path to the preview image.
        """
        grayscale_dem_path = os.path.join(self.previews_directory, "dem_grayscale.png")

        self.logger.debug("Creating grayscale preview of DEM data in %s.", grayscale_dem_path)

        dem_data = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if dem_data is None:
            raise ValueError(f"Could not read DEM image for grayscale preview: {image_path}")
        dem_data_rgb = cv2.cvtColor(dem_data, cv2.COLOR_GRAY2RGB)
        cv2.imwrite(grayscale_dem_path, dem_data_rgb)
        return grayscale_dem_path

    def colored_preview(self, image_path: str) -> str:
        """Converts DEM image to colored RGB image and saves it to the map directory.
        Returns path to the preview image.

        Arguments:
            image_path (str): Path to the DEM file.

        Returns:
            list[str]: List with a single path to the DEM file
        """
        colored_dem_path = os.path.join(self.previews_directory, "dem_colored.png")

        self.logger.debug("Creating colored preview of DEM data in %s.", colored_dem_path)

        dem_data = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if dem_data is None:
            raise ValueError(f"Could not read DEM image for colored preview: {image_path}")

        # Create an empty array with the same shape and type as dem_data.
        dem_data_normalized = np.empty_like(dem_data)

        # Normalize the DEM data to the range [0, 255]
        cv2.normalize(dem_data, dem_data_normalized, 0, 255, cv2.NORM_MINMAX)
        dem_data_colored = cv2.applyColorMap(dem_data_normalized, cv2.COLORMAP_JET)

        cv2.imwrite(colored_dem_path, dem_data_colored)
        return colored_dem_path

    @monitor_performance
    def flatten_roads(self) -> None:
        """Flattens the roads in the DEM data by averaging the height values along the road polylines."""
        dem_image = self._load_roads_base_dem()
        if dem_image is None:
            return

        roads_polylines = self.get_infolayer_data(Parameters.TEXTURES, Parameters.ROADS_POLYLINES)
        if not roads_polylines:
            self.logger.warning("No roads polylines found in textures info layer.")
            return

        self.logger.debug("Found %s roads polylines in textures info layer.", len(roads_polylines))

        full_mask = np.zeros(dem_image.shape, dtype=np.uint8)

        for road_polyline in tqdm(roads_polylines, desc="Flattening roads", unit="road"):
            road_result = self._flatten_single_road(road_polyline, dem_image)
            if road_result is None:
                continue

            road_y, road_x, interpolated_elevations = road_result
            dem_image[road_y, road_x] = interpolated_elevations
            full_mask[road_y, road_x] = 255

        main_dem_path = self.game.dem_file_path
        dem_image = self.blur_by_mask(dem_image, full_mask, blur_radius=5)
        dem_image = self.blur_edges_by_mask(dem_image, full_mask)

        # Save the not resized DEM with flattened roads.
        cv2.imwrite(self.not_resized_path(Parameters.NOT_RESIZED_DEM_ROADS), dem_image)
        self.logger.debug(
            "Not resized DEM with flattened roads saved to: %s",
            self.not_resized_path(Parameters.NOT_RESIZED_DEM_ROADS),
        )

        output_size = self.map_dem_size()
        resized_dem = cv2.resize(
            dem_image, (output_size, output_size), interpolation=cv2.INTER_NEAREST
        )

        cv2.imwrite(main_dem_path, resized_dem)
        self.logger.debug("Flattened roads saved to DEM file: %s", main_dem_path)

    def _load_roads_base_dem(self) -> np.ndarray | None:
        """Load the highest-priority DEM available for road flattening."""
        candidate_paths = [
            self.not_resized_path(Parameters.NOT_RESIZED_DEM_FOUNDATIONS),
            self.not_resized_path(Parameters.NOT_RESIZED_DEM),
        ]
        for candidate_path in candidate_paths:
            if not os.path.isfile(candidate_path):
                continue

            dem_image = cv2.imread(candidate_path, cv2.IMREAD_UNCHANGED)
            if dem_image is not None:
                return dem_image

        self.logger.warning("No DEM data found for flattening roads.")
        return None

    def _flatten_single_road(
        self,
        road_polyline: dict[str, Any],
        dem_image: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray] | None:
        """Return target pixels and interpolated elevations for one road polyline."""
        points = road_polyline.get("points")
        width = road_polyline.get("width")
        if not points or not width:
            self.logger.warning("Skipping road with insufficient data: %s", road_polyline)
            return None

        try:
            fitted_road = self.fit_object_into_bounds(linestring_points=points, angle=self.rotation)
        except ValueError as e:
            self.logger.debug("Road polyline could not be fitted into bounds: %s", e)
            return None

        polyline = shapely.LineString(fitted_road)
        total_length = polyline.length
        if total_length <= 0:
            return None

        line_thickness = int(width * 4)
        road_mask = np.zeros(dem_image.shape, dtype=np.uint8)
        dense_sample_distance = min(Parameters.SEGMENT_LENGTH, total_length / 100)
        num_dense_points = max(100, int(total_length / dense_sample_distance))
        dense_distances = np.linspace(0, total_length, num_dense_points)
        dense_points = [polyline.interpolate(d) for d in dense_distances]
        dense_coords = np.array([(int(p.x), int(p.y)) for p in dense_points], dtype=np.int32)
        if len(dense_coords) > 1:
            cv2.polylines(road_mask, [dense_coords], False, 255, thickness=line_thickness)

        road_pixels = np.where(road_mask == 255)
        if len(road_pixels[0]) == 0:
            return None
        road_y, road_x = road_pixels

        large_segment_length = Parameters.SEGMENT_LENGTH * 15
        num_large_segments = max(1, int(np.ceil(total_length / large_segment_length)))
        large_distances = np.linspace(0, total_length, num_large_segments + 1)

        segment_elevations = []
        for dist in large_distances:
            sample_point = polyline.interpolate(dist)
            sample_x, sample_y = int(sample_point.x), int(sample_point.y)
            sample_radius = max(5, line_thickness // 4)
            y_min = max(0, sample_y - sample_radius)
            y_max = min(dem_image.shape[0], sample_y + sample_radius)
            x_min = max(0, sample_x - sample_radius)
            x_max = min(dem_image.shape[1], sample_x + sample_radius)

            if y_max > y_min and x_max > x_min:
                sample_elevation = np.mean(dem_image[y_min:y_max, x_min:x_max])
            elif 0 <= sample_y < dem_image.shape[0] and 0 <= sample_x < dem_image.shape[1]:
                sample_elevation = dem_image[sample_y, sample_x]
            else:
                sample_elevation = 0
            segment_elevations.append(sample_elevation)

        road_distances_from_start = np.array(
            [
                polyline.project(polyline.interpolate(polyline.project(shapely.Point(px, py))))
                for px, py in zip(road_x, road_y)
            ]
        )
        interpolated_elevations = np.interp(
            road_distances_from_start,
            large_distances,
            segment_elevations,
        )
        return road_y, road_x, interpolated_elevations

    def process_road_masks(self) -> None:
        """Reads road mask images from the roads directory and saves bounding-box position
        data for each mask so the GE can position the road meshes correctly."""
        roads_directory = os.path.join(self.map_directory, "roads")
        if not os.path.isdir(roads_directory):
            self.logger.warning("Roads directory not found, skipping road mask processing.")
            return

        dem_image = self.get_dem_image_with_fallback()
        if dem_image is None:
            self.logger.warning("DEM image not found, skipping road mask processing.")
            return

        # Get all files in directory ending with _mask.png
        mask_files = [f for f in os.listdir(roads_directory) if f.endswith("_mask.png")]

        for mask_file in mask_files:
            mask_path = os.path.join(roads_directory, mask_file)
            mask = cv2.imread(mask_path, cv2.IMREAD_UNCHANGED)
            if mask is None:
                self.logger.warning("Could not read mask file: %s, skipping.", mask_path)
                continue
            if not np.any(mask):
                self.logger.warning(
                    "No non-zero pixels found in rotated mask, skipping road mask processing."
                )
                continue

            extremes = self.get_dem_extremes_by_mask(dem_image, mask)
            if extremes is None:
                self.logger.warning("No valid pixels found in DEM image for road mask, skipping.")
                continue

            (min_x, min_y, _), (max_x, max_y, _) = extremes

            min_z = self.get_z_coordinate_from_dem(dem_image, min_x, min_y)
            max_z = self.get_z_coordinate_from_dem(dem_image, max_x, max_y)

            # Compute the true pixel centroid of the mask (mean of all non-zero pixel coords).
            # This matches where mesh.vertices -= center places the mesh origin.
            ys, xs = np.where(mask > 0)
            centroid_x = int(np.mean(xs))
            centroid_y = int(np.mean(ys))

            base_filename = os.path.splitext(mask_file)[0].replace("_mask", "")
            self.map.context.set_mesh_position(
                base_filename,
                mesh_centroid_x=float(centroid_x),
                mesh_centroid_y=float((min_z + max_z) / 2),
                mesh_centroid_z=float(centroid_y),
            )

            try:
                os.remove(mask_path)
                self.logger.debug("Temporary road mask %s removed.", mask_path)
            except Exception as e:
                self.logger.warning(
                    "Error removing temporary road mask %s: %s.", mask_path, repr(e)
                )
