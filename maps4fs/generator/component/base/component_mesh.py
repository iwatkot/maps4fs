"""Base class for all components that primarily used to work with meshes."""

import os
import shutil
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
from maps4fs.generator.settings import Parameters


class LineSurfaceEntry(NamedTuple):
    """Data structure representing a line surface entry with its linestring, width,
    and optional z-offset."""

    linestring: shapely.LineString
    width: int
    z_offset: float = 0.0


class MeshComponent(Component):
    """Base class for all components that primarily used to work with meshes."""

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

    @staticmethod
    def texture_mesh(
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
        # 1. Copy texture to output directory (only if not already there).
        texture_filename = os.path.basename(resized_texture_path)
        texture_output_path = os.path.join(output_directory, texture_filename)

        # Check if source and destination are the same file to avoid copy conflicts
        if os.path.abspath(resized_texture_path) != os.path.abspath(texture_output_path):
            shutil.copy2(resized_texture_path, texture_output_path)

        # 2. Apply rotation to fix 90-degree X-axis rotation.
        rotation_matrix = trimesh.transformations.rotation_matrix(-np.pi / 2, [1, 0, 0])
        mesh.apply_transform(rotation_matrix)

        # 3. Get mesh bounds: using X and Z for ground plane.
        vertices = mesh.vertices

        # 4. Ground plane coordinates (X, Z)
        min_x = np.min(vertices[:, 0])  # X coordinate
        max_x = np.max(vertices[:, 0])
        min_z = np.min(vertices[:, 2])  # Z coordinate
        max_z = np.max(vertices[:, 2])

        width = max_x - min_x  # X dimension
        depth = max_z - min_z  # Z dimension

        # 5. Load texture.
        texture_image = Image.open(texture_output_path)

        # 6. Calculate UV coordinates based on X and Z positions.
        uv_coords = np.zeros((len(vertices), 2), dtype=np.float32)
        for i in tqdm(range(len(vertices)), desc="Calculating UVs", unit="vertex"):
            vertex = vertices[i]

            # Map X coordinate to U
            u = (vertex[0] - min_x) / width if width > 0 else 0.5

            # Map Z coordinate to V (NOT Y!)
            v = (vertex[2] - min_z) / depth if depth > 0 else 0.5

            # Flip V coordinate for correct orientation
            v = 1.0 - v

            # Clamp to valid range
            u = np.clip(u, 0.0, 1.0)
            v = np.clip(v, 0.0, 1.0)

            uv_coords[i] = [u, v]

        # 7. Create material.
        material = trimesh.visual.material.PBRMaterial(
            baseColorTexture=texture_image,
            metallicFactor=0.0,
            roughnessFactor=1.0,
            emissiveFactor=[0.0, 0.0, 0.0],
        )

        # 8. Apply UV and material to mesh.
        visual = trimesh.visual.TextureVisuals(uv=uv_coords, material=material)
        mesh.visual = visual

        mtl_filename = f"{output_name}.mtl"
        obj_filename = f"{output_name}.obj"
        mtl_filepath = os.path.join(output_directory, mtl_filename)
        obj_filepath = os.path.join(output_directory, obj_filename)

        faces = mesh.faces

        # 9. Write OBJ file with correct UV mapping.
        with open(obj_filepath, "w") as f:  # pylint: disable=unspecified-encoding
            f.write("# Corrected UV mapping using X,Z coordinates (ground plane)\n")
            f.write("# Y coordinate represents elevation\n")
            f.write(f"mtllib {os.path.basename(mtl_filename)}\n")

            # Write vertices
            for vertex in vertices:
                f.write(f"v {vertex[0]:.6f} {vertex[1]:.6f} {vertex[2]:.6f}\n")

            # Write UV coordinates
            for uv in uv_coords:
                f.write(f"vt {uv[0]:.6f} {uv[1]:.6f}\n")

            # Write faces
            f.write("usemtl TerrainMaterial_XZ\n")
            for face in faces:
                v1, v2, v3 = face[0] + 1, face[1] + 1, face[2] + 1
                f.write(f"f {v1}/{v1} {v2}/{v2} {v3}/{v3}\n")

        # 10. Write MTL file.
        with open(mtl_filepath, "w") as f:  # pylint: disable=unspecified-encoding
            f.write("# Material with X,Z UV mapping\n")
            f.write("newmtl TerrainMaterial_XZ\n")
            f.write("Ka 1.0 1.0 1.0\n")
            f.write("Kd 1.0 1.0 1.0\n")
            f.write("Ks 0.0 0.0 0.0\n")
            f.write("illum 1\n")
            f.write(f"map_Kd {texture_filename}\n")

        return obj_filepath, mtl_filepath

    @staticmethod
    def mesh_to_i3d(
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

        # Ensure output directory exists
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

        # 3. Handle texture copying if provided
        texture_file = None
        if texture_path and os.path.exists(texture_path):
            texture_filename = os.path.basename(texture_path)
            texture_dest = os.path.join(output_dir, texture_filename)

            # Copy texture if it's not already in output_dir
            if os.path.abspath(texture_path) != os.path.abspath(texture_dest):
                shutil.copy2(texture_path, texture_dest)

            texture_file = texture_filename

        # 4. Generate i3d file
        output_path = os.path.join(output_dir, f"{name}.i3d")
        MeshComponent._write_i3d_file(mesh, output_path, name, texture_file, water_mesh)

        return output_path

    @staticmethod
    def _write_i3d_file(
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

        # Root element
        i3d = ET.Element(
            "i3D",
            attrib={
                "name": name,
                "version": "1.6",
                "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
                "xsi:noNamespaceSchemaLocation": "http://i3d.giants.ch/schema/i3d-1.6.xsd",
            },
        )

        # Asset section
        asset = ET.SubElement(i3d, "Asset")
        exp = ET.SubElement(asset, "Export")
        exp.set("program", "maps4fs")
        exp.set("version", "1.0")
        exp.set("date", datetime.now().strftime("%Y-%m-%d"))

        vertices = mesh.vertices
        faces = mesh.faces

        has_normals = mesh.vertex_normals is not None and len(mesh.vertex_normals) == len(vertices)
        has_uv = (
            hasattr(mesh.visual, "uv")
            and mesh.visual.uv is not None
            and len(mesh.visual.uv) == len(vertices)
        )

        # Files section
        files_section = None
        if is_water:
            # Water mesh: add ocean shader
            files_section = ET.SubElement(i3d, "Files")
            shader_file = ET.SubElement(files_section, "File")
            shader_file.set("fileId", "4")
            shader_file.set("filename", "$data/shaders/oceanShader.xml")
        elif texture_file:
            # Terrain mesh: add texture file
            files_section = ET.SubElement(i3d, "Files")
            file_entry = ET.SubElement(files_section, "File")
            file_entry.set("fileId", "1")
            file_entry.set("filename", texture_file)
            file_entry.set("relativePath", "true")

        # Materials section
        materials_section = ET.SubElement(i3d, "Materials")
        material = ET.SubElement(materials_section, "Material")

        if is_water:
            # Water material with ocean shader
            material.set("name", "OceanShader")
            material.set("materialId", "1")
            material.set("diffuseColor", "0.8 0.8 0.8 1")
            material.set("specularColor", "0.501961 1 0")
            material.set("customShaderId", "4")
            material.set("customShaderVariation", "simple")

            # Required for ocean shader
            normalmap = ET.SubElement(material, "Normalmap")
            normalmap.set("fileId", "2")

            refractionmap = ET.SubElement(material, "Refractionmap")
            refractionmap.set("coeff", "1")
            refractionmap.set("bumpScale", "0.01")
            refractionmap.set("withSSRData", "true")
        else:
            # Standard terrain material
            material.set("name", f"{name}_material")
            material.set("materialId", "1")
            material.set("diffuseColor", "1 1 1 1")
            material.set("specularColor", "0.5 0.5 0.5")

            if texture_file:
                texture = ET.SubElement(material, "Texture")
                texture.set("fileId", "1")

        # Shapes section
        shapes = ET.SubElement(i3d, "Shapes")
        shape = ET.SubElement(shapes, "IndexedTriangleSet")
        shape.set("name", name)
        shape.set("shapeId", "1")

        # Calculate bounding sphere
        if len(vertices) > 0:
            center = vertices.mean(axis=0)
            max_dist = ((vertices - center) ** 2).sum(axis=1).max() ** 0.5
            shape.set("bvCenter", f"{center[0]:.6f} {center[1]:.6f} {center[2]:.6f}")
            shape.set("bvRadius", f"{max_dist:.6f}")

        # Vertices block
        xml_vertices = ET.SubElement(shape, "Vertices")
        xml_vertices.set("count", str(len(vertices)))

        if has_normals:
            xml_vertices.set("normal", "true")
        if has_uv:
            xml_vertices.set("uv0", "true")

        # Pre-format ALL strings using vectorized operations
        pos_strings = np.array([f"{v[0]:.6f} {v[1]:.6f} {v[2]:.6f}" for v in vertices])

        normal_strings = None
        if has_normals:
            normal_strings = np.array(
                [f"{n[0]:.6f} {n[1]:.6f} {n[2]:.6f}" for n in mesh.vertex_normals]
            )

        uv_strings = None
        if has_uv:
            uv_strings = np.array([f"{uv[0]:.6f} {uv[1]:.6f}" for uv in mesh.visual.uv])

        # Batch process vertices for memory efficiency
        batch_size = 2000
        vertex_elements = []

        for batch_start in tqdm(
            range(0, len(vertices), batch_size), desc="Writing vertices", unit="batch"
        ):
            batch_end = min(batch_start + batch_size, len(vertices))
            batch_elements = []

            for idx in range(batch_start, batch_end):
                v_el = ET.Element("v")
                v_el.set("p", pos_strings[idx])

                if has_normals:
                    v_el.set("n", normal_strings[idx])  # type: ignore

                if has_uv:
                    v_el.set("t0", uv_strings[idx])  # type: ignore

                batch_elements.append(v_el)

            vertex_elements.extend(batch_elements)

        # Add all vertex elements at once
        xml_vertices.extend(vertex_elements)

        # Triangles block
        xml_tris = ET.SubElement(shape, "Triangles")
        xml_tris.set("count", str(len(faces)))
        for f in tqdm(faces, desc="Writing triangles", unit="triangle"):
            t = ET.SubElement(xml_tris, "t")
            t.set("vi", f"{f[0]} {f[1]} {f[2]}")

        # Subsets block
        xml_subs = ET.SubElement(shape, "Subsets")
        xml_subs.set("count", "1")
        subset = ET.SubElement(xml_subs, "Subset")
        subset.set("firstVertex", "0")
        subset.set("numVertices", str(len(vertices)))
        subset.set("firstIndex", "0")
        subset.set("numIndices", str(len(faces) * 3))

        # Scene section
        scene = ET.SubElement(i3d, "Scene")

        if is_water:
            # Water: direct shape node
            shape_node = ET.SubElement(scene, "Shape")
            shape_node.set("name", name)
            shape_node.set("shapeId", "1")
            shape_node.set("nodeId", "4")
            shape_node.set("castsShadows", "true")
            shape_node.set("receiveShadows", "true")
            shape_node.set("materialIds", "1")
        else:
            # Terrain: transform group with shape
            transform_group = ET.SubElement(scene, "TransformGroup")
            transform_group.set("name", name)
            transform_group.set("nodeId", "1")

            shape_node = ET.SubElement(transform_group, "Shape")
            shape_node.set("name", f"{name}_shape")
            shape_node.set("nodeId", "2")
            shape_node.set("shapeId", "1")
            shape_node.set("static", "true")
            shape_node.set("compound", "false")
            shape_node.set("collision", "true")
            shape_node.set("materialIds", "1")

        # Pretty print and write
        MeshComponent._indent(i3d)
        tree = ET.ElementTree(i3d)
        tree.write(output_path, encoding="iso-8859-1", xml_declaration=True)

    @staticmethod
    def _indent(elem: ET.Element, level: int = 0) -> None:
        """Pretty print XML formatting. Modifies the element in place.

        Arguments:
            elem (ET.Element): The XML element to indent
            level (int): Current indentation level
        """
        i = "\n" + level * "  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for e in elem:
                MeshComponent._indent(e, level + 1)
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i

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
        # Use the not resized DEM with flattened roads to get accurate Z values
        # for the road mesh vertices.
        if dem_override is not None:
            not_resized_dem = dem_override
        else:
            not_resized_dem = self.get_dem_image_with_fallback()  # type: ignore
            if not_resized_dem is None:
                self.logger.warning(
                    "Not resized DEM with flattened roads is not available. "
                    "Cannot generate road mesh."
                )
                return

        vertices = []
        faces = []
        uvs = []
        vertex_offset = 0

        texture_tile_size = 10.0  # meters - how many meters before texture repeats

        patches_count = sum(1 for entry in road_entries if entry.z_offset > 0)
        self.logger.debug(
            "Creating mesh for %d roads (%d patches with z-offset)",
            len(road_entries),
            patches_count,
        )

        for _, (linestring, width, z_offset) in enumerate(road_entries):
            coords = list(linestring.coords)
            if len(coords) < 2:
                continue

            # Generate road strip vertices
            segment_vertices = []
            segment_uvs = []
            accumulated_distance = 0.0
            prev_center_3d: tuple[float, float, float] | None = (
                None  # Track previous center point in 3D
            )

            for i in range(len(coords)):  # pylint: disable=consider-using-enumerate
                x, y = coords[i]

                # Calculate direction vector for perpendicular offset
                if i == 0:
                    # First point: use direction to next point
                    dx = coords[i + 1][0] - coords[i][0]
                    dy = coords[i + 1][1] - coords[i][1]
                elif i == len(coords) - 1:
                    # Last point: use direction from previous point
                    dx = coords[i][0] - coords[i - 1][0]
                    dy = coords[i][1] - coords[i - 1][1]
                else:
                    # Middle points: average direction
                    dx1 = coords[i][0] - coords[i - 1][0]
                    dy1 = coords[i][1] - coords[i - 1][1]
                    dx2 = coords[i + 1][0] - coords[i][0]
                    dy2 = coords[i + 1][1] - coords[i][1]
                    dx = (dx1 + dx2) / 2.0
                    dy = (dy1 + dy2) / 2.0

                # Normalize direction and get perpendicular
                length = np.sqrt(dx * dx + dy * dy)
                if length > 0:
                    dx /= length
                    dy /= length

                # Perpendicular vector (rotated 90 degrees)
                perp_x = -dy
                perp_y = dx

                exact_z_value = self.get_z_coordinate_from_dem(not_resized_dem, x, y)
                offsetted_z = -exact_z_value + z_offset

                # Create left and right vertices with z-offset
                left_vertex = (x + perp_x * width, y + perp_y * width, offsetted_z)
                right_vertex = (x - perp_x * width, y - perp_y * width, offsetted_z)

                segment_vertices.append(left_vertex)
                segment_vertices.append(right_vertex)

                # Calculate UV coordinates based on 3D distance (including Z changes)
                # U coordinate: 0 for left edge, 1 for right edge
                # V coordinate: based on accumulated 3D distance along the road
                segment_distance_3d = 0.0
                current_center_3d = (x, y, offsetted_z)

                # pylint: disable=unsubscriptable-object
                if i > 0 and prev_center_3d is not None:
                    # Calculate both 2D and 3D distances for comparison
                    segment_distance_3d = np.sqrt(
                        (current_center_3d[0] - prev_center_3d[0]) ** 2
                        + (current_center_3d[1] - prev_center_3d[1]) ** 2
                        + (current_center_3d[2] - prev_center_3d[2]) ** 2
                    )
                    accumulated_distance += segment_distance_3d

                prev_center_3d = current_center_3d

                # Calculate V coordinate - divide by texture tile size
                v_coord_raw = accumulated_distance / texture_tile_size

                # Store raw V coordinate for now - we'll apply modulo to the entire road later
                segment_uvs.append((0.0, v_coord_raw))  # Left edge
                segment_uvs.append((1.0, v_coord_raw))  # Right edge

            # Add vertices and UVs to global lists
            vertices.extend(segment_vertices)
            uvs.extend(segment_uvs)

            # Create faces (triangles) for the road strip
            num_segments = len(coords) - 1
            for i in range(num_segments):
                # Each segment creates 2 triangles (a quad)
                # Vertex indices for this segment
                v0 = vertex_offset + i * 2  # Left vertex of current segment
                v1 = vertex_offset + i * 2 + 1  # Right vertex of current segment
                v2 = vertex_offset + (i + 1) * 2  # Left vertex of next segment
                v3 = vertex_offset + (i + 1) * 2 + 1  # Right vertex of next segment

                # First triangle (counter-clockwise winding)
                faces.append((v0, v2, v1))
                # Second triangle
                faces.append((v1, v2, v3))

            vertex_offset += len(segment_vertices)

        if not vertices:
            self.logger.warning("No vertices generated for road mesh.")
            return

        # Write MTL file
        if mtl_output_path and texture_path:
            mtl_filename = os.path.basename(mtl_output_path)
            texture_filename = os.path.basename(texture_path)

            with open(mtl_output_path, "w", encoding="utf-8") as mtl_file:
                mtl_file.write("# Road material\n")
                mtl_file.write("newmtl RoadMaterial\n")
                mtl_file.write("Ka 1.0 1.0 1.0\n")  # Ambient color
                mtl_file.write("Kd 1.0 1.0 1.0\n")  # Diffuse color
                mtl_file.write("Ks 0.3 0.3 0.3\n")  # Specular color
                mtl_file.write("Ns 10.0\n")  # Specular exponent
                mtl_file.write("illum 2\n")  # Illumination model
                mtl_file.write(f"map_Kd {texture_filename}\n")  # Diffuse texture map

            self.logger.debug("MTL file written to %s", mtl_output_path)

        # Write OBJ file
        with open(obj_output_path, "w", encoding="utf-8") as obj_file:
            obj_file.write("# Road mesh generated by maps4fs\n")
            if mtl_output_path:
                # pylint: disable=possibly-used-before-assignment
                obj_file.write(f"mtllib {mtl_filename}\n\n")

            # Write vertices
            obj_file.write(f"# {len(vertices)} vertices\n")
            for v in vertices:
                obj_file.write(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n")

            # Write UV coordinates
            obj_file.write(f"\n# {len(uvs)} texture coordinates\n")
            for uv in uvs:
                obj_file.write(f"vt {uv[0]:.6f} {uv[1]:.6f}\n")

            # Write faces with material
            obj_file.write(f"\n# {len(faces)} faces\n")
            if mtl_output_path:
                obj_file.write("usemtl RoadMaterial\n")
            for face in faces:
                # OBJ format uses 1-based indexing
                # Format: f v1/vt1 v2/vt2 v3/vt3
                obj_file.write(
                    f"f {face[0] + 1}/{face[0] + 1} "
                    f"{face[1] + 1}/{face[1] + 1} "
                    f"{face[2] + 1}/{face[2] + 1}\n"
                )

        self.logger.debug(
            "OBJ file written to %s with %d vertices and %d faces",
            obj_output_path,
            len(vertices),
            len(faces),
        )

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
        max_road_length = 30.0 * texture_tile_size  # Use 30 instead of 32 for safety margin
        split_entries = []

        for linestring, width, z_offset in road_entries:
            road_length = linestring.length

            if road_length <= max_road_length:
                # Road is short enough, keep as is
                split_entries.append(LineSurfaceEntry(linestring, width, z_offset))
                continue

            # Road is too long, split it into segments
            num_segments = int(np.ceil(road_length / max_road_length))
            segment_length = road_length / num_segments

            self.logger.debug(
                "Splitting line surface (%.2fm) into %d segments of ~%.2fm each",
                road_length,
                num_segments,
                segment_length,
            )

            for i in range(num_segments):
                start_distance = i * segment_length
                end_distance = min((i + 1) * segment_length, road_length)

                # Extract segment using shapely's substring
                try:
                    segment_linestring = shapely.ops.substring(
                        linestring, start_distance, end_distance, normalized=False
                    )
                    split_entries.append(LineSurfaceEntry(segment_linestring, width, z_offset))
                    self.logger.debug(
                        "  Segment %d: %.2fm to %.2fm (length: %.2fm)",
                        i,
                        start_distance,
                        end_distance,
                        segment_linestring.length,
                    )
                except Exception as e:
                    self.logger.warning("Failed to split line surface segment %d: %s", i, e)

        self.logger.debug(
            "Line surface splitting complete: %d line surfaces -> %d segments",
            len(road_entries),
            len(split_entries),
        )
        return split_entries

    def smart_interpolation(self, road_entries: list[LineSurfaceEntry]) -> list[LineSurfaceEntry]:
        """Apply smart interpolation to road linestrings.
        Making sure that result polylines do not have points too close to each other.

        Arguments:
            road_entries (list[LineSurfaceEntry]): List of LineSurfaceEntry objects

        Returns:
            (list[LineSurfaceEntry]): List of LineSurfaceEntry objects with interpolated linestrings.
        """
        interpolated_entries = []
        target_segment_length = 5  # Target distance between points in meters (denser)
        max_angle_change = 30.0  # Maximum angle change in degrees to allow interpolation

        for linestring, width, z_offset in road_entries:
            coords = list(linestring.coords)
            if len(coords) < 2:
                interpolated_entries.append(LineSurfaceEntry(linestring, width, z_offset))
                continue

            # Check if road has sharp curves - if so, skip interpolation
            has_sharp_curves = False
            if len(coords) >= 3:
                for i in range(1, len(coords) - 1):
                    # Calculate angle change at this point
                    v1_x = coords[i][0] - coords[i - 1][0]
                    v1_y = coords[i][1] - coords[i - 1][1]
                    v2_x = coords[i + 1][0] - coords[i][0]
                    v2_y = coords[i + 1][1] - coords[i][1]

                    # Calculate angle between vectors
                    dot = v1_x * v2_x + v1_y * v2_y
                    len1 = np.sqrt(v1_x**2 + v1_y**2)
                    len2 = np.sqrt(v2_x**2 + v2_y**2)

                    if len1 > 0 and len2 > 0:
                        cos_angle = np.clip(dot / (len1 * len2), -1.0, 1.0)
                        angle_deg = np.degrees(np.arccos(cos_angle))

                        if angle_deg > max_angle_change:
                            has_sharp_curves = True
                            break

            if has_sharp_curves:
                # Skip interpolation for curved roads
                interpolated_entries.append(LineSurfaceEntry(linestring, width, z_offset))
                continue

            # Check if interpolation is needed
            needs_interpolation = False
            for i in range(len(coords) - 1):
                segment_length = np.sqrt(
                    (coords[i + 1][0] - coords[i][0]) ** 2 + (coords[i + 1][1] - coords[i][1]) ** 2
                )
                if segment_length > target_segment_length * 1.5:
                    needs_interpolation = True
                    break

            if not needs_interpolation:
                # Road is already dense enough
                interpolated_entries.append(LineSurfaceEntry(linestring, width, z_offset))
                continue

            # Perform interpolation using shapely's interpolate (follows curves)
            road_length = linestring.length
            num_points = int(np.ceil(road_length / target_segment_length)) + 1

            new_coords = []
            for i in range(num_points):
                distance = min(i * target_segment_length, road_length)
                point = linestring.interpolate(distance)
                new_coords.append((point.x, point.y))

            # Ensure last point is exact
            if new_coords[-1] != coords[-1]:
                new_coords.append(coords[-1])

            # Create new linestring with interpolated coordinates
            # No cleanup needed - interpolation already creates evenly spaced points
            try:
                interpolated_linestring = shapely.LineString(new_coords)
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
