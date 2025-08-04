"""Base class for all components that primarily used to work with meshes."""

import os

import cv2
import numpy as np
import trimesh
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
            mesh = MeshComponent.remove_center_from_mesh(mesh, remove_size)

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
    def remove_center_from_mesh(mesh: trimesh.Trimesh, remove_size: int) -> trimesh.Trimesh:
        """Removes the center from the given mesh.

        Arguments:
            mesh (trimesh.Trimesh): The mesh to remove the center from.
            remove_size (int): The size of the center to remove.

        Returns:
            trimesh.Trimesh: The mesh with the center removed.
        """
        mesh_copy = mesh.copy()

        _, _, z_size = mesh_copy.extents

        try:
            mesh_copy = MeshComponent.mesh_to_origin(mesh_copy)
        except Exception:
            pass
        cube_mesh = trimesh.creation.box([remove_size, remove_size, z_size * 4])

        return trimesh.boolean.difference(
            [mesh_copy, cube_mesh], check_volume=False, engine="blender"
        )

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
