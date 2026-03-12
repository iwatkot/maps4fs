"""Base class for all components that primarily used to work with meshes."""

import os
import shutil
import subprocess
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import NamedTuple

import cv2
import numpy as np
import shapely
import trimesh
from PIL import Image
from tqdm import tqdm

from maps4fs.generator.component.base.component import Component
from maps4fs.generator.constants import Paths
from maps4fs.generator.settings import Parameters


class LineSurfaceEntry(NamedTuple):
    """Data structure representing a line surface entry with its linestring, width,
    and optional z-offset."""

    linestring: shapely.LineString
    width: int
    z_offset: float = 0.0


class MeshComponent(Component):
    """Base class for all components that primarily used to work with meshes."""

    OBJ_INDEX_OFFSET = 1
    ROAD_MATERIAL_NAME = "RoadMaterial"
    TERRAIN_MATERIAL_NAME = "TerrainMaterial_XZ"
    TEXTURE_TILE_SIZE_METERS = 10.0
    UV_LIMIT = 32.0
    UV_SPLIT_SAFETY_MARGIN = 30.0
    INTERPOLATION_TARGET_SEGMENT_LENGTH = 5.0
    INTERPOLATION_MAX_ANGLE_CHANGE = 30.0
    I3D_ENCODING = "iso-8859-1"
    I3D_VERSION = "1.6"
    I3D_SCHEMA = "http://i3d.giants.ch/schema/i3d-1.6.xsd"
    I3D_XSI_NAMESPACE = "http://www.w3.org/2001/XMLSchema-instance"
    I3D_EXPORT_PROGRAM = "maps4fs"
    I3D_EXPORT_VERSION = "1.0"
    I3D_WATER_SHADER_PATH = "$data/shaders/oceanShader.xml"
    I3D_WATER_SHADER_PATH_BINARY_BROKEN = 'filename="data/shaders/oceanShader.xml"'
    I3D_WATER_SHADER_PATH_BINARY_FIXED = 'filename="$data/shaders/oceanShader.xml"'

    @staticmethod
    def validate_np_for_mesh(image_path: str, map_size: int) -> None:
        """Checks if the given image is a valid for mesh generation.

        Arguments:
            image_path (str): The path to the background image.
            map_size (int): The size of the map.

        Raises:
            FileNotFoundError: If the background image is not found.
            ValueError: If the background image does not meet the requirements.
        """
        if not os.path.isfile(image_path):
            raise FileNotFoundError(f"Can't find the background DEM image at {image_path}.")

        image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
        if image is None:
            raise ValueError(f"Can't read the background DEM image at {image_path}.")

        if image.shape[0] != image.shape[1]:
            raise ValueError("The background image must be a square.")

        if image.shape[0] != map_size + Parameters.BACKGROUND_DISTANCE * 2:
            raise ValueError("The background image must have the size of the map + 4096.")

        if len(image.shape) != 2:
            raise ValueError("The background image must be a grayscale image.")

        if image.dtype != np.uint16:
            raise ValueError("The background image must be a 16-bit grayscale image.")

    @staticmethod
    def mesh_to_stl(mesh: trimesh.Trimesh, save_path: str) -> None:
        """Converts the mesh to an STL file and saves it in the previews directory.
        Uses powerful simplification to reduce the size of the file since it will be used
        only for the preview.

        Arguments:
            mesh (trimesh.Trimesh) -- The mesh to convert to an STL file.
        """
        mesh = mesh.simplify_quadric_decimation(face_count=len(mesh.faces) // 2**6)
        mesh.export(save_path)

    @staticmethod
    def mesh_from_np(
        image: np.ndarray,
        include_zeros: bool,
        z_scaling_factor: float,
        remove_center: bool,
        remove_size: int,
        **kwargs,
    ) -> trimesh.Trimesh:
        """Generates a mesh from the given numpy array.

        Arguments:
            image (np.ndarray): The numpy array to generate the mesh from.
            include_zeros (bool): Whether to include zero values in the mesh.
            z_scaling_factor (float): The scaling factor for the Z-axis.
            remove_center (bool): Whether to remove the center from the mesh.
            remove_size (int): The size of the center to remove.

        Returns:
            trimesh.Trimesh: The generated mesh.
        """
        logger = kwargs.get("logger", None)
        output_x_size, _ = image.shape
        image = image.max() - image

        image = image[:: Parameters.RESIZE_FACTOR, :: Parameters.RESIZE_FACTOR]

        rows, cols = image.shape
        x = np.linspace(0, cols - 1, cols)
        y = np.linspace(0, rows - 1, rows)
        x, y = np.meshgrid(x, y)
        z = image

        ground = z.max()

        vertices = np.column_stack([x.ravel(), y.ravel(), z.ravel()])
        faces = []

        skipped = 0

        for i in tqdm(range(rows - 1), desc="Generating mesh", unit="row"):
            for j in range(cols - 1):
                top_left = i * cols + j
                top_right = top_left + 1
                bottom_left = top_left + cols
                bottom_right = bottom_left + 1

                if (
                    ground in [z[i, j], z[i, j + 1], z[i + 1, j], z[i + 1, j + 1]]
                    and not include_zeros
                ):
                    skipped += 1
                    continue

                faces.append([top_left, bottom_left, bottom_right])
                faces.append([top_left, bottom_right, top_right])

        faces_np = np.array(faces)
        mesh = trimesh.Trimesh(vertices=vertices, faces=faces_np)
        mesh = MeshComponent.rotate_mesh(mesh)

        mesh = MeshComponent.mesh_to_output_size(
            mesh,
            Parameters.RESIZE_FACTOR,
            z_scaling_factor,
            output_x_size,
            skip_resize_to_expected_size=not include_zeros,
        )

        if remove_center:
            try:
                mesh = MeshComponent.remove_center_from_mesh(mesh, remove_size, logger=logger)
            except Exception as e:
                if logger:
                    logger.warning(f"Failed to remove center from mesh: {e}")

        return mesh

    @staticmethod
    def rotate_mesh(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
        """Rotates the given mesh by 180 degrees around the Y-axis and Z-axis.

        Arguments:
            mesh (trimesh.Trimesh): The mesh to rotate.

        Returns:
            trimesh.Trimesh: The rotated mesh.
        """
        mesh_copy = mesh.copy()

        rotation_matrices = [
            trimesh.transformations.rotation_matrix(np.pi, [0, 1, 0]),
            trimesh.transformations.rotation_matrix(np.pi, [0, 0, 1]),
        ]

        for rotation_matrix in tqdm(
            rotation_matrices,
            desc="Rotating mesh",
            unit="rotation",
        ):
            mesh_copy.apply_transform(rotation_matrix)

        return mesh_copy

    @staticmethod
    def fix_mesh(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
        """Fixes the given mesh by filling holes, fixing normals, fixing winding, fixing inversion,
        fixing broken faces, and stitching.

        Arguments:
            mesh (trimesh.Trimesh): The mesh to fix.

        Returns:
            trimesh.Trimesh: The fixed mesh.
        """
        mesh_copy = mesh.copy()

        fix_methods = [
            trimesh.repair.fill_holes,
            trimesh.repair.fix_normals,
            trimesh.repair.fix_winding,
            trimesh.repair.fix_inversion,
            trimesh.repair.broken_faces,
            trimesh.repair.stitch,
        ]

        for method in tqdm(fix_methods, desc="Fixing mesh", unit="method"):
            method(mesh_copy)  # type: ignore

        return mesh_copy

    @staticmethod
    def mesh_to_output_size(
        mesh: trimesh.Trimesh,
        resize_factor: int,
        z_scaling_factor: float,
        expected_size: int,
        skip_resize_to_expected_size: bool = False,
    ) -> trimesh.Trimesh:
        """Resizes the given mesh to the expected size.

        Arguments:
            mesh (trimesh.Trimesh): The mesh to resize.
            resize_factor (int): The resizing factor.
            z_scaling_factor (float): The scaling factor for the Z-axis.
            expected_size (int): The expected size.
            skip_resize_to_expected_size (bool): Whether to skip resizing to the expected size.

        Returns:
            trimesh.Trimesh: The resized mesh.
        """
        mesh_copy = mesh.copy()

        mesh_copy.apply_scale([resize_factor / 1, resize_factor / 1, z_scaling_factor])

        if not skip_resize_to_expected_size:
            x_size, y_size, _ = mesh_copy.extents
            x_resize_factor = expected_size / x_size
            y_resize_factor = expected_size / y_size

            mesh_copy.apply_scale([x_resize_factor, y_resize_factor, 1])
        return mesh_copy

    @staticmethod
    def remove_center_from_mesh(
        mesh: trimesh.Trimesh, remove_size: int, **kwargs
    ) -> trimesh.Trimesh:
        """Removes the center from the given mesh.

        Arguments:
            mesh (trimesh.Trimesh): The mesh to remove the center from.
            remove_size (int): The size of the center to remove.

        Returns:
            trimesh.Trimesh: The mesh with the center removed.
        """
        logger = kwargs.get("logger", None)
        mesh_copy = mesh.copy()

        _, _, z_size = mesh_copy.extents

        try:
            mesh_copy = MeshComponent.mesh_to_origin(mesh_copy)
        except Exception:
            pass
        cube_mesh = trimesh.creation.box([remove_size, remove_size, z_size * 4])

        mesh_copy = MeshComponent.fix_mesh(mesh_copy)

        mesh_copy = trimesh.boolean.difference(
            [mesh_copy, cube_mesh],
            check_volume=False,
            engine="blender",
        )

        if mesh_copy is None:
            if logger:
                logger.warning("Resulting mesh is None after removing center. Using original mesh.")
            return mesh
        if mesh_copy.is_empty:
            if logger:
                logger.warning(
                    "Resulting mesh is empty after removing center. Using original mesh."
                )
            return mesh

        return mesh_copy

    @staticmethod
    def mesh_to_origin(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
        """Moves the mesh to the origin using mesh size.

        Arguments:
            mesh (trimesh.Trimesh): The mesh to move to the origin.

        Returns:
            trimesh.Trimesh: The mesh moved to the origin.
        """
        mesh_copy = mesh.copy()
        x_size, _, _ = mesh_copy.extents
        distance = int(round(x_size) / 2)
        mesh_copy.apply_translation([-distance, distance, 0])
        return mesh_copy

    @staticmethod
    def invert_faces(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
        """
        Inverts the faces (normals) of the mesh by reversing the order of indices in each face.

        Arguments:
            mesh (trimesh.Trimesh): The mesh whose faces are to be inverted.

        Returns:
            trimesh.Trimesh: A new mesh with inverted faces.
        """
        mesh_copy = mesh.copy()
        mesh_copy.faces = mesh_copy.faces[:, ::-1]  # type: ignore
        return mesh_copy

    # @staticmethod
    # def decimate_mesh_by_o3d(mesh: trimesh.Trimesh, reduction_factor: float) -> trimesh.Trimesh:
    #     """Decimate mesh using Open3D's quadric decimation (similar to Blender's approach)

    #     Arguments:
    #         mesh (trimesh.Trimesh): Input trimesh mesh
    #         reduction_factor (float): Reduce to this fraction of original triangles (0.5 = 50%)

    #     Returns:
    #         trimesh.Trimesh: Decimated trimesh mesh
    #     """
    #     import open3d as o3d

    #     # 1. Convert trimesh to Open3D format.
    #     vertices = mesh.vertices
    #     faces = mesh.faces

    #     o3d_mesh = o3d.geometry.TriangleMesh()
    #     o3d_mesh.vertices = o3d.utility.Vector3dVector(vertices)
    #     o3d_mesh.triangles = o3d.utility.Vector3iVector(faces)

    #     # 2. Calculate target number of triangles.
    #     target_triangles = int(len(faces) * reduction_factor)

    #     # 3. Apply quadric decimation.
    #     decimated_o3d = o3d_mesh.simplify_quadric_decimation(target_triangles)

    #     # 4. Convert back to trimesh.
    #     decimated_vertices = np.asarray(decimated_o3d.vertices)
    #     decimated_faces = np.asarray(decimated_o3d.triangles)
    #     decimated_mesh = trimesh.Trimesh(vertices=decimated_vertices, faces=decimated_faces)

    #     return decimated_mesh

    @staticmethod
    def decimate_mesh(mesh: trimesh.Trimesh, reduction_factor: float) -> trimesh.Trimesh:
        """Decimate mesh using available libraries (Open3D preferred, fallback to trimesh).

        Arguments:
            mesh (trimesh.Trimesh): Input trimesh mesh
            reduction_factor (float): Reduce to this fraction of original triangles (0.5 = 50%)

        Returns:
            trimesh.Trimesh: Decimated trimesh mesh
        """
        # try:
        #     return MeshComponent.decimate_mesh_by_o3d(mesh, reduction_factor)
        # except ImportError:
        return MeshComponent.decimate_mesh_by_trimesh(mesh, reduction_factor)

    @staticmethod
    def decimate_mesh_by_trimesh(mesh: trimesh.Trimesh, reduction_factor: float) -> trimesh.Trimesh:
        """Decimate mesh using trimesh's built-in quadric decimation.

        Arguments:
            mesh (trimesh.Trimesh): Input trimesh mesh
            reduction_factor (float): Reduce to this fraction of original triangles (0.5 = 50%)

        Returns:
            trimesh.Trimesh: Decimated trimesh mesh
        """
        target_faces = int(len(mesh.faces) * reduction_factor)
        return mesh.simplify_quadric_decimation(face_count=target_faces)

    def texture_mesh(
        self,
        mesh: trimesh.Trimesh,
        resized_texture_path: str,
        output_directory: str,
        output_name: str,
    ) -> tuple[str, str]:
        """Apply texture to mesh with UV mapping based on X and Z coordinates (ground plane).

        Arguments:
            mesh (trimesh.Trimesh): The mesh to texture
            resized_texture_path (str): Path to resized texture image
            output_directory (str): Directory to save textured OBJ and MTL files and texture.
            output_name (str): Base name for output files (without extension)

        Returns:
            tuple[str, str]: Paths to the saved OBJ and MTL files
        """
        texture_filename, texture_output_path = self._copy_texture_to_output(
            resized_texture_path,
            output_directory,
        )

        rotation_matrix = trimesh.transformations.rotation_matrix(-np.pi / 2, [1, 0, 0])
        mesh.apply_transform(rotation_matrix)
        vertices = mesh.vertices
        uv_coords = self._calculate_ground_plane_uvs(vertices)
        texture_image = Image.open(texture_output_path)
        material = trimesh.visual.material.PBRMaterial(
            baseColorTexture=texture_image,
            metallicFactor=0.0,
            roughnessFactor=1.0,
            emissiveFactor=[0.0, 0.0, 0.0],
        )

        visual = trimesh.visual.TextureVisuals(uv=uv_coords, material=material)
        mesh.visual = visual

        mtl_filename = f"{output_name}.mtl"
        obj_filename = f"{output_name}.obj"
        mtl_filepath = os.path.join(output_directory, mtl_filename)
        obj_filepath = os.path.join(output_directory, obj_filename)

        self._write_terrain_obj(
            obj_filepath=obj_filepath,
            mtl_filename=mtl_filename,
            vertices=vertices,
            uv_coords=uv_coords,
            faces=mesh.faces,
        )
        self._write_terrain_mtl(mtl_filepath, texture_filename)

        return obj_filepath, mtl_filepath

    def _copy_texture_to_output(self, texture_path: str, output_directory: str) -> tuple[str, str]:
        """Copy texture to output directory if needed and return filename/path pair."""
        texture_filename = os.path.basename(texture_path)
        texture_output_path = os.path.join(output_directory, texture_filename)
        if os.path.abspath(texture_path) != os.path.abspath(texture_output_path):
            shutil.copy2(texture_path, texture_output_path)
        return texture_filename, texture_output_path

    def _calculate_ground_plane_uvs(self, vertices: np.ndarray) -> np.ndarray:
        """Calculate UVs from mesh X/Z extents for ground-plane texturing."""
        min_x = np.min(vertices[:, 0])
        max_x = np.max(vertices[:, 0])
        min_z = np.min(vertices[:, 2])
        max_z = np.max(vertices[:, 2])
        width = max_x - min_x
        depth = max_z - min_z

        uv_coords = np.zeros((len(vertices), 2), dtype=np.float32)
        for i, vertex in enumerate(tqdm(vertices, desc="Calculating UVs", unit="vertex")):
            u = (vertex[0] - min_x) / width if width > 0 else 0.5
            v = (vertex[2] - min_z) / depth if depth > 0 else 0.5
            uv_coords[i] = [np.clip(u, 0.0, 1.0), np.clip(1.0 - v, 0.0, 1.0)]
        return uv_coords

    def _write_terrain_obj(
        self,
        obj_filepath: str,
        mtl_filename: str,
        vertices: np.ndarray,
        uv_coords: np.ndarray,
        faces: np.ndarray,
    ) -> None:
        """Write terrain OBJ file with UV and material bindings."""
        with open(obj_filepath, "w", encoding="utf-8") as obj_file:
            obj_file.write("# Terrain mesh generated by maps4fs\n")
            obj_file.write(f"mtllib {os.path.basename(mtl_filename)}\n")

            for vertex in vertices:
                obj_file.write(f"v {vertex[0]:.6f} {vertex[1]:.6f} {vertex[2]:.6f}\n")
            for uv in uv_coords:
                obj_file.write(f"vt {uv[0]:.6f} {uv[1]:.6f}\n")

            obj_file.write(f"usemtl {self.TERRAIN_MATERIAL_NAME}\n")
            for face in faces:
                v1, v2, v3 = [idx + self.OBJ_INDEX_OFFSET for idx in face]
                obj_file.write(f"f {v1}/{v1} {v2}/{v2} {v3}/{v3}\n")

    def _write_terrain_mtl(self, mtl_filepath: str, texture_filename: str) -> None:
        """Write material file for textured terrain mesh."""
        with open(mtl_filepath, "w", encoding="utf-8") as mtl_file:
            mtl_file.write(f"newmtl {self.TERRAIN_MATERIAL_NAME}\n")
            mtl_file.write("Ka 1.0 1.0 1.0\n")
            mtl_file.write("Kd 1.0 1.0 1.0\n")
            mtl_file.write("Ks 0.0 0.0 0.0\n")
            mtl_file.write("illum 1\n")
            mtl_file.write(f"map_Kd {texture_filename}\n")

    def to_i3d_binary(self, raw_i3d_path: str, binary_i3d_path: str, **kwargs) -> None:
        """Convert the raw XML i3d file to the Giants binary i3d format using the i3dConverter.exe tool.

        Generates a raw XML i3d file first, then converts it to the Giants binary i3d
        format in-place by running: i3dConverter.exe -in <file> -out <file>

        Arguments:
            raw_i3d_path (str): Path to the raw XML i3d file
            binary_i3d_path (str): Path to save the converted binary i3d file

        Raises:
            RuntimeError: If the converter executable is not found or returns a non-zero exit code.
        """
        converter_path = Paths.get_i3d_executable_path()
        if converter_path is None:
            raise RuntimeError(
                "i3d_converter executable not found. Cannot convert to binary i3d format."
            )

        # Run the converter: overwrites the XML file with the binary format in-place.
        cmd = [converter_path, "-in", raw_i3d_path, "-out", binary_i3d_path]

        # PyInstaller windowed apps have no console, so we must:
        #   - set stdin=DEVNULL (parent stdin is None in windowed mode, child must not inherit it)
        #   - use CREATE_NO_WINDOW so the converter doesn't try to open a console of its own
        run_kwargs: dict = {
            "stdin": subprocess.DEVNULL,
            "capture_output": True,
            "text": True,
            "creationflags": subprocess.CREATE_NO_WINDOW,  # type: ignore[attr-defined]
        }

        result = subprocess.run(cmd, **run_kwargs)  # pylint: disable=subprocess-run-check

        if result.returncode != 0:
            raise RuntimeError(
                f"i3dConverter.exe failed (exit code {result.returncode}). "
                f"stdout: {result.stdout.strip()} | stderr: {result.stderr.strip()}"
            )

    def mesh_to_i3d(
        self,
        mesh: trimesh.Trimesh,
        output_dir: str,
        name: str,
        texture_path: str | None = None,
        water_mesh: bool = False,
        rotate_mesh: bool = False,
        center_mesh: bool = False,
    ) -> str:
        """Convert a trimesh to i3d format with optional water shader support.

        Arguments:
            mesh (trimesh.Trimesh): trimesh.Trimesh object to convert
            output_dir (str): Directory to save i3d and copy textures to
            name (str): Base name for output files (e.g., "terrain_mesh")
            texture_path (str | None): Optional path to texture file (will be copied to output_dir)
            water_mesh (bool): If True, adds ocean shader material for water rendering
            rotate_mesh (bool): If True, applies 90-degree X-axis rotation fix
            center_mesh (bool): If True, centers the mesh at origin

        Returns:
            str: Full path to the generated i3d file
        """

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        if rotate_mesh:
            # 1. Apply rotation fix (90-degree X-axis correction) - water only
            rotation_matrix = trimesh.transformations.rotation_matrix(-np.pi / 2, [1, 0, 0])
            mesh.apply_transform(rotation_matrix)

        if center_mesh:
            # 2. Center mesh at origin - water only
            vertices = mesh.vertices
            center = vertices.mean(axis=0)
            mesh.vertices = vertices - center

        texture_file = self._copy_i3d_texture_if_needed(texture_path, output_dir)

        output_path = os.path.join(output_dir, f"{name}.i3d")
        self._write_i3d_file(mesh, output_path, name, texture_file, water_mesh)

        try:
            binary_output_path = os.path.join(output_dir, f"{name}_binary.i3d")
            self.to_i3d_binary(output_path, binary_output_path)
            output_path = binary_output_path
            self.fix_binary_paths(output_path)
        except Exception:
            pass

        return output_path

    def _copy_i3d_texture_if_needed(self, texture_path: str | None, output_dir: str) -> str | None:
        """Copy optional i3d texture into output directory and return local filename."""
        if not texture_path or not os.path.exists(texture_path):
            return None

        texture_filename = os.path.basename(texture_path)
        texture_dest = os.path.join(output_dir, texture_filename)
        if os.path.abspath(texture_path) != os.path.abspath(texture_dest):
            shutil.copy2(texture_path, texture_dest)
        return texture_filename

    def fix_binary_paths(self, binary_i3d_path: str) -> None:
        """The binary i3d converter replaces $data with data in file paths, which causes issues with
        loading shaders.

        Arguments:
            binary_i3d_path (str): Path to the binary i3d file to fix
        """

        if not os.path.isfile(binary_i3d_path):
            return

        with open(binary_i3d_path, "r", encoding="utf-8") as f:
            content = f.read()
            content = content.replace(
                self.I3D_WATER_SHADER_PATH_BINARY_BROKEN,
                self.I3D_WATER_SHADER_PATH_BINARY_FIXED,
            )
        with open(binary_i3d_path, "w", encoding="utf-8") as f:
            f.write(content)

    def _write_i3d_file(
        self,
        mesh: trimesh.Trimesh,
        output_path: str,
        name: str,
        texture_file: str | None,
        is_water: bool,
    ) -> None:
        """Write the actual i3d XML file.

        Arguments:
            mesh  (trimesh.Trimesh): object containing the geometry
            output_path (str): Full path where to save the i3d file
            name (str): Name for the mesh in i3d file
            texture_file (str | None): Optional texture filename (if copied to output dir)
            is_water (bool): If True, generates water mesh with ocean shader
        """

        i3d = self._create_i3d_root(name)
        self._append_i3d_asset(i3d)

        vertices = mesh.vertices
        faces = mesh.faces

        has_normals = mesh.vertex_normals is not None and len(mesh.vertex_normals) == len(vertices)
        has_uv = (
            hasattr(mesh.visual, "uv")
            and mesh.visual.uv is not None
            and len(mesh.visual.uv) == len(vertices)
        )

        self._append_i3d_files(i3d, is_water, texture_file)
        self._append_i3d_material(i3d, name, is_water, texture_file)

        shape = self._append_i3d_shape(i3d, name, vertices)

        self._append_i3d_vertices(shape, vertices, has_normals, has_uv, mesh)
        self._append_i3d_triangles(shape, faces, len(vertices))
        self._append_i3d_scene(i3d, name, is_water)

        tree = ET.ElementTree(i3d)
        ET.indent(tree, space="  ")
        tree.write(output_path, encoding=self.I3D_ENCODING, xml_declaration=True)

    def _create_i3d_root(self, name: str) -> ET.Element:
        return ET.Element(
            "i3D",
            attrib={
                "name": name,
                "version": self.I3D_VERSION,
                "xmlns:xsi": self.I3D_XSI_NAMESPACE,
                "xsi:noNamespaceSchemaLocation": self.I3D_SCHEMA,
            },
        )

    def _append_i3d_asset(self, i3d: ET.Element) -> None:
        asset = ET.SubElement(i3d, "Asset")
        export = ET.SubElement(asset, "Export")
        export.set("program", self.I3D_EXPORT_PROGRAM)
        export.set("version", self.I3D_EXPORT_VERSION)
        export.set("date", datetime.now().strftime("%Y-%m-%d"))

    def _append_i3d_files(
        self,
        i3d: ET.Element,
        is_water: bool,
        texture_file: str | None,
    ) -> None:
        if not is_water and not texture_file:
            return

        files_section = ET.SubElement(i3d, "Files")
        file_node = ET.SubElement(files_section, "File")
        if is_water:
            file_node.set("fileId", "4")
            file_node.set("filename", self.I3D_WATER_SHADER_PATH)
        else:
            file_node.set("fileId", "1")
            file_node.set("filename", texture_file or "")
            file_node.set("relativePath", "true")

    def _append_i3d_material(
        self,
        i3d: ET.Element,
        name: str,
        is_water: bool,
        texture_file: str | None,
    ) -> None:
        materials = ET.SubElement(i3d, "Materials")
        material = ET.SubElement(materials, "Material")
        material.set("materialId", "1")

        if is_water:
            material.set("name", "OceanShader")
            material.set("diffuseColor", "0.8 0.8 0.8 1")
            material.set("specularColor", "0.501961 1 0")
            material.set("customShaderId", "4")
            material.set("customShaderVariation", "simple")
            ET.SubElement(material, "Normalmap", {"fileId": "2"})
            ET.SubElement(
                material,
                "Refractionmap",
                {"coeff": "1", "bumpScale": "0.01", "withSSRData": "true"},
            )
            return

        material.set("name", f"{name}_material")
        material.set("diffuseColor", "1 1 1 1")
        material.set("specularColor", "0.5 0.5 0.5")
        if texture_file:
            ET.SubElement(material, "Texture", {"fileId": "1"})

    def _append_i3d_shape(self, i3d: ET.Element, name: str, vertices: np.ndarray) -> ET.Element:
        shapes = ET.SubElement(i3d, "Shapes")
        shape = ET.SubElement(shapes, "IndexedTriangleSet")
        shape.set("name", name)
        shape.set("shapeId", "1")
        if len(vertices) == 0:
            return shape

        center = vertices.mean(axis=0)
        max_dist = ((vertices - center) ** 2).sum(axis=1).max() ** 0.5
        shape.set("bvCenter", f"{center[0]:.6f} {center[1]:.6f} {center[2]:.6f}")
        shape.set("bvRadius", f"{max_dist:.6f}")
        return shape

    def _append_i3d_vertices(
        self,
        shape: ET.Element,
        vertices: np.ndarray,
        has_normals: bool,
        has_uv: bool,
        mesh: trimesh.Trimesh,
    ) -> None:
        xml_vertices = ET.SubElement(shape, "Vertices", {"count": str(len(vertices))})
        if has_normals:
            xml_vertices.set("normal", "true")
        if has_uv:
            xml_vertices.set("uv0", "true")

        normals = mesh.vertex_normals if has_normals else None
        uvs = mesh.visual.uv if has_uv else None
        for idx, vertex in enumerate(tqdm(vertices, desc="Writing vertices", unit="vertex")):
            vertex_node = ET.SubElement(xml_vertices, "v")
            vertex_node.set("p", f"{vertex[0]:.6f} {vertex[1]:.6f} {vertex[2]:.6f}")
            if normals is not None:
                normal = normals[idx]
                vertex_node.set("n", f"{normal[0]:.6f} {normal[1]:.6f} {normal[2]:.6f}")
            if uvs is not None:
                uv = uvs[idx]
                vertex_node.set("t0", f"{uv[0]:.6f} {uv[1]:.6f}")

    def _append_i3d_triangles(
        self, shape: ET.Element, faces: np.ndarray, vertex_count: int
    ) -> None:
        xml_tris = ET.SubElement(shape, "Triangles", {"count": str(len(faces))})
        for face in tqdm(faces, desc="Writing triangles", unit="triangle"):
            ET.SubElement(xml_tris, "t", {"vi": f"{face[0]} {face[1]} {face[2]}"})

        subsets = ET.SubElement(shape, "Subsets", {"count": "1"})
        ET.SubElement(
            subsets,
            "Subset",
            {
                "firstVertex": "0",
                "numVertices": str(vertex_count),
                "firstIndex": "0",
                "numIndices": str(len(faces) * 3),
            },
        )

    def _append_i3d_scene(self, i3d: ET.Element, name: str, is_water: bool) -> None:
        scene = ET.SubElement(i3d, "Scene")
        if is_water:
            ET.SubElement(
                scene,
                "Shape",
                {
                    "name": name,
                    "shapeId": "1",
                    "nodeId": "4",
                    "castsShadows": "true",
                    "receiveShadows": "true",
                    "materialIds": "1",
                },
            )
            return

        transform_group = ET.SubElement(scene, "TransformGroup", {"name": name, "nodeId": "1"})
        ET.SubElement(
            transform_group,
            "Shape",
            {
                "name": f"{name}_shape",
                "nodeId": "2",
                "shapeId": "1",
                "static": "true",
                "compound": "false",
                "collision": "true",
                "materialIds": "1",
            },
        )

    def create_textured_linestrings_mesh(
        self,
        road_entries: list[LineSurfaceEntry],
        obj_output_path: str,
        mtl_output_path: str | None = None,
        texture_path: str | None = None,
        dem_override: np.ndarray | None = None,
    ) -> None:
        """Creates a textured mesh from linestrings with varying widths.

        This method generates a 3D mesh for roads by:
        1. Creating rectangular strips along each linestring based on its width
        2. Applying proper UV mapping for tiled texture along the road length
        3. Exporting the mesh to OBJ format with corresponding MTL material file

        Arguments:
            road_entries (list[LineSurfaceEntry]): List of LineSurfaceEntry objects to generate the mesh from.
            obj_output_path: Output path for the OBJ mesh file
            mtl_output_path: Output path for the MTL material file. If None, MTL file is not created.
            texture_path: Path to the texture image file to apply. If None, texture is not applied.
            dem_override (np.ndarray | None): Optional DEM to use for Z values instead of default.
        """
        not_resized_dem = self._resolve_linestring_dem(dem_override)
        if not_resized_dem is None:
            return

        vertices, faces, uvs = self._build_linestring_mesh_data(road_entries, not_resized_dem)
        if not vertices:
            self.logger.warning("No vertices generated for road mesh.")
            return

        if mtl_output_path and texture_path:
            self._write_road_mtl(mtl_output_path, texture_path)

        mtl_filename = os.path.basename(mtl_output_path) if mtl_output_path else None
        with open(obj_output_path, "w", encoding="utf-8") as obj_file:
            obj_file.write("# Road mesh generated by maps4fs\n")
            if mtl_filename:
                obj_file.write(f"mtllib {mtl_filename}\n\n")

            obj_file.write(f"# {len(vertices)} vertices\n")
            for v in vertices:
                obj_file.write(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n")

            obj_file.write(f"\n# {len(uvs)} texture coordinates\n")
            for uv in uvs:
                obj_file.write(f"vt {uv[0]:.6f} {uv[1]:.6f}\n")

            obj_file.write(f"\n# {len(faces)} faces\n")
            if mtl_output_path:
                obj_file.write(f"usemtl {self.ROAD_MATERIAL_NAME}\n")
            for face in faces:
                v1, v2, v3 = [idx + self.OBJ_INDEX_OFFSET for idx in face]
                obj_file.write(f"f {v1}/{v1} " f"{v2}/{v2} " f"{v3}/{v3}\n")

        self.logger.debug(
            "OBJ file written to %s with %d vertices and %d faces",
            obj_output_path,
            len(vertices),
            len(faces),
        )

    def _resolve_linestring_dem(self, dem_override: np.ndarray | None) -> np.ndarray | None:
        """Resolve DEM source for linestring-based mesh generation."""
        if dem_override is not None:
            return dem_override
        not_resized_dem = self.get_dem_image_with_fallback()  # type: ignore
        if not_resized_dem is None:
            self.logger.warning(
                "Not resized DEM with flattened roads is not available. Cannot generate road mesh."
            )
            return None
        return not_resized_dem

    def _build_linestring_mesh_data(
        self,
        road_entries: list[LineSurfaceEntry],
        dem_image: np.ndarray,
    ) -> tuple[
        list[tuple[float, float, float]], list[tuple[int, int, int]], list[tuple[float, float]]
    ]:
        """Build vertex/face/uv lists for linestring surfaces."""
        vertices: list[tuple[float, float, float]] = []
        faces: list[tuple[int, int, int]] = []
        uvs: list[tuple[float, float]] = []
        vertex_offset = 0

        patches_count = sum(1 for entry in road_entries if entry.z_offset > 0)
        self.logger.debug(
            "Creating mesh for %d roads (%d patches with z-offset)",
            len(road_entries),
            patches_count,
        )

        for linestring, width, z_offset in road_entries:
            strip_vertices, strip_uvs = self._build_linestring_strip(
                linestring,
                width,
                z_offset,
                dem_image,
            )
            if not strip_vertices:
                continue

            vertices.extend(strip_vertices)
            uvs.extend(strip_uvs)

            num_segments = len(strip_vertices) // 2 - 1
            for i in range(num_segments):
                v0 = vertex_offset + i * 2
                v1 = vertex_offset + i * 2 + 1
                v2 = vertex_offset + (i + 1) * 2
                v3 = vertex_offset + (i + 1) * 2 + 1
                faces.append((v0, v2, v1))
                faces.append((v1, v2, v3))

            vertex_offset += len(strip_vertices)

        return vertices, faces, uvs

    def _build_linestring_strip(
        self,
        linestring: shapely.LineString,
        width: int,
        z_offset: float,
        dem_image: np.ndarray,
    ) -> tuple[list[tuple[float, float, float]], list[tuple[float, float]]]:
        """Build one linestring strip as paired left/right vertices plus UVs."""
        coords = list(linestring.coords)
        if len(coords) < 2:
            return [], []

        strip_vertices: list[tuple[float, float, float]] = []
        strip_uvs: list[tuple[float, float]] = []
        accumulated_distance = 0.0
        prev_center_3d: tuple[float, float, float] | None = None

        for i, (x, y) in enumerate(coords):
            perp_x, perp_y = self._perpendicular_direction(coords, i)
            exact_z_value = self.get_z_coordinate_from_dem(dem_image, x, y)
            offsetted_z = -exact_z_value + z_offset

            left_vertex = (x + perp_x * width, y + perp_y * width, offsetted_z)
            right_vertex = (x - perp_x * width, y - perp_y * width, offsetted_z)
            strip_vertices.extend([left_vertex, right_vertex])

            current_center_3d = (x, y, offsetted_z)
            if prev_center_3d is not None:
                accumulated_distance += np.sqrt(
                    (current_center_3d[0] - prev_center_3d[0]) ** 2
                    + (current_center_3d[1] - prev_center_3d[1]) ** 2
                    + (current_center_3d[2] - prev_center_3d[2]) ** 2
                )
            prev_center_3d = current_center_3d

            v_coord_raw = accumulated_distance / self.TEXTURE_TILE_SIZE_METERS
            strip_uvs.extend([(0.0, v_coord_raw), (1.0, v_coord_raw)])

        return strip_vertices, strip_uvs

    def _perpendicular_direction(
        self,
        coords: list[tuple[float, float]],
        index: int,
    ) -> tuple[float, float]:
        """Return normalized perpendicular direction for a point on a polyline."""
        if index == 0:
            dx = coords[index + 1][0] - coords[index][0]
            dy = coords[index + 1][1] - coords[index][1]
        elif index == len(coords) - 1:
            dx = coords[index][0] - coords[index - 1][0]
            dy = coords[index][1] - coords[index - 1][1]
        else:
            dx = (coords[index][0] - coords[index - 1][0]) + (
                coords[index + 1][0] - coords[index][0]
            )
            dy = (coords[index][1] - coords[index - 1][1]) + (
                coords[index + 1][1] - coords[index][1]
            )

        length = np.sqrt(dx * dx + dy * dy)
        if length <= 0:
            return 0.0, 0.0

        dx /= length
        dy /= length
        return -dy, dx

    def _write_road_mtl(self, mtl_output_path: str, texture_path: str) -> None:
        """Write MTL file for road/line surface mesh."""
        texture_filename = os.path.basename(texture_path)
        with open(mtl_output_path, "w", encoding="utf-8") as mtl_file:
            mtl_file.write(f"newmtl {self.ROAD_MATERIAL_NAME}\n")
            mtl_file.write("Ka 1.0 1.0 1.0\n")
            mtl_file.write("Kd 1.0 1.0 1.0\n")
            mtl_file.write("Ks 0.3 0.3 0.3\n")
            mtl_file.write("Ns 10.0\n")
            mtl_file.write("illum 2\n")
            mtl_file.write(f"map_Kd {texture_filename}\n")

    def split_long_line_surfaces(
        self, road_entries: list[LineSurfaceEntry], texture_tile_size: float = 10.0
    ) -> list[LineSurfaceEntry]:
        """Split line surfaces that exceed Giants Engine's UV coordinate limits.

        Giants Engine requires UV coordinates to be in [-32, 32] range.
        Line surfaces longer than 32 * texture_tile_size meters need to be split.

        Arguments:
            road_entries (list[LineSurfaceEntry]): List of LineSurfaceEntry objects
            texture_tile_size (float): Size of texture tile in meters

        Returns:
            (list[LineSurfaceEntry]): List of LineSurfaceEntry objects with long roads split.
        """
        max_road_length = self.UV_SPLIT_SAFETY_MARGIN * texture_tile_size
        split_entries = []

        for linestring, width, z_offset in road_entries:
            split_entries.extend(
                self._split_line_surface_entry(
                    linestring,
                    width,
                    z_offset,
                    max_road_length,
                )
            )

        self.logger.debug(
            "Line surface splitting complete: %d line surfaces -> %d segments",
            len(road_entries),
            len(split_entries),
        )
        return split_entries

    def _split_line_surface_entry(
        self,
        linestring: shapely.LineString,
        width: int,
        z_offset: float,
        max_road_length: float,
    ) -> list[LineSurfaceEntry]:
        """Split a single line surface entry into UV-safe segments."""
        road_length = linestring.length
        if road_length <= max_road_length:
            return [LineSurfaceEntry(linestring, width, z_offset)]

        num_segments = int(np.ceil(road_length / max_road_length))
        segment_length = road_length / num_segments

        segments: list[LineSurfaceEntry] = []
        for i in range(num_segments):
            start_distance = i * segment_length
            end_distance = min((i + 1) * segment_length, road_length)
            try:
                segment_linestring = shapely.ops.substring(
                    linestring,
                    start_distance,
                    end_distance,
                    normalized=False,
                )
                segments.append(LineSurfaceEntry(segment_linestring, width, z_offset))
            except Exception as e:
                self.logger.warning("Failed to split line surface segment %d: %s", i, e)

        return segments

    def smart_interpolation(self, road_entries: list[LineSurfaceEntry]) -> list[LineSurfaceEntry]:
        """Apply smart interpolation to road linestrings.
        Making sure that result polylines do not have points too close to each other.

        Arguments:
            road_entries (list[LineSurfaceEntry]): List of LineSurfaceEntry objects

        Returns:
            (list[LineSurfaceEntry]): List of LineSurfaceEntry objects with interpolated linestrings.
        """
        interpolated_entries = []
        target_segment_length = self.INTERPOLATION_TARGET_SEGMENT_LENGTH
        max_angle_change = self.INTERPOLATION_MAX_ANGLE_CHANGE

        for linestring, width, z_offset in road_entries:
            coords = list(linestring.coords)
            if len(coords) < 2:
                interpolated_entries.append(LineSurfaceEntry(linestring, width, z_offset))
                continue

            if self._has_sharp_curve(coords, max_angle_change):
                interpolated_entries.append(LineSurfaceEntry(linestring, width, z_offset))
                continue

            if not self._needs_interpolation(coords, target_segment_length):
                interpolated_entries.append(LineSurfaceEntry(linestring, width, z_offset))
                continue

            try:
                interpolated_linestring = self._interpolate_linestring(
                    linestring,
                    coords,
                    target_segment_length,
                )
                interpolated_entries.append(
                    LineSurfaceEntry(interpolated_linestring, width, z_offset)
                )
            except Exception as e:
                self.logger.warning(
                    "Failed to create interpolated linestring: %s. Using original.", e
                )
                interpolated_entries.append(LineSurfaceEntry(linestring, width, z_offset))

        self.logger.debug(
            "Smart interpolation complete. Processed %d roads.", len(interpolated_entries)
        )
        return interpolated_entries

    def _has_sharp_curve(
        self,
        coords: list[tuple[float, float]],
        max_angle_change: float,
    ) -> bool:
        """Detect whether polyline has sharp turns exceeding the threshold."""
        if len(coords) < 3:
            return False

        for i in range(1, len(coords) - 1):
            v1_x = coords[i][0] - coords[i - 1][0]
            v1_y = coords[i][1] - coords[i - 1][1]
            v2_x = coords[i + 1][0] - coords[i][0]
            v2_y = coords[i + 1][1] - coords[i][1]

            len1 = np.sqrt(v1_x**2 + v1_y**2)
            len2 = np.sqrt(v2_x**2 + v2_y**2)
            if len1 <= 0 or len2 <= 0:
                continue

            dot = v1_x * v2_x + v1_y * v2_y
            cos_angle = np.clip(dot / (len1 * len2), -1.0, 1.0)
            angle_deg = np.degrees(np.arccos(cos_angle))
            if angle_deg > max_angle_change:
                return True

        return False

    def _needs_interpolation(
        self,
        coords: list[tuple[float, float]],
        target_segment_length: float,
    ) -> bool:
        """Check whether any segment is sparse enough to require interpolation."""
        threshold = target_segment_length * 1.5
        for i in range(len(coords) - 1):
            segment_length = np.sqrt(
                (coords[i + 1][0] - coords[i][0]) ** 2 + (coords[i + 1][1] - coords[i][1]) ** 2
            )
            if segment_length > threshold:
                return True
        return False

    def _interpolate_linestring(
        self,
        linestring: shapely.LineString,
        original_coords: list[tuple[float, float]],
        target_segment_length: float,
    ) -> shapely.LineString:
        """Interpolate linestring points at roughly fixed segment length."""
        road_length = linestring.length
        num_points = int(np.ceil(road_length / target_segment_length)) + 1

        new_coords = []
        for i in range(num_points):
            distance = min(i * target_segment_length, road_length)
            point = linestring.interpolate(distance)
            new_coords.append((point.x, point.y))

        if new_coords[-1] != original_coords[-1]:
            new_coords.append(original_coords[-1])

        return shapely.LineString(new_coords)
