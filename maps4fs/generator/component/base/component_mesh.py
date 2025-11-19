"""Base class for all components that primarily used to work with meshes."""

import os
import shutil
import xml.etree.ElementTree as ET
from datetime import datetime

import cv2
import numpy as np
import trimesh
from PIL import Image
from tqdm import tqdm

from maps4fs.generator.component.base.component import Component
from maps4fs.generator.settings import Parameters


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
    ) -> str:
        """Convert a trimesh to i3d format with optional water shader support.

        Arguments:
            mesh (trimesh.Trimesh): trimesh.Trimesh object to convert
            output_dir (str): Directory to save i3d and copy textures to
            name (str): Base name for output files (e.g., "terrain_mesh")
            texture_path (str | None): Optional path to texture file (will be copied to output_dir)
            water_mesh (bool): If True, adds ocean shader material for water rendering

        Returns:
            str: Full path to the generated i3d file
        """

        # Ensure output directory exists
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Apply transformations (only for water meshes)
        if water_mesh:
            # 1. Apply rotation fix (90-degree X-axis correction) - water only
            rotation_matrix = trimesh.transformations.rotation_matrix(-np.pi / 2, [1, 0, 0])
            mesh.apply_transform(rotation_matrix)

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
