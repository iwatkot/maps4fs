"""Base class for all components that primarily used to work with meshes."""

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
            image_path (str): The path to the custom background image.
            map_size (int): The size of the map.

        Raises:
            ValueError: If the custom background image does not meet the requirements.
        """
        image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
        if image.shape[0] != image.shape[1]:
            raise ValueError("The custom background image must be a square.")

        if image.shape[0] != map_size + Parameters.BACKGROUND_DISTANCE * 2:
            raise ValueError("The custom background image must have the size of the map + 4096.")

        if len(image.shape) != 2:
            raise ValueError("The custom background image must be a grayscale image.")

        if image.dtype != np.uint16:
            raise ValueError("The custom background image must be a 16-bit grayscale image.")

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
        resize_factor: int,
        apply_decimation: bool,
        decimation_percent: int,
        decimation_agression: int,
        remove_center: bool,
        remove_size: int,
        disable_tqdm: bool = False,
    ) -> trimesh.Trimesh:
        """Generates a mesh from the given numpy array.

        Arguments:
            image (np.ndarray): The numpy array to generate the mesh from.
            include_zeros (bool): Whether to include zero values in the mesh.
            z_scaling_factor (float): The scaling factor for the Z-axis.
            resize_factor (int): The resizing factor.
            apply_decimation (bool): Whether to apply decimation to the mesh.
            decimation_percent (int): The percent of the decimation.
            decimation_agression (int): The agression of the decimation.
            remove_center (bool): Whether to remove the center from the mesh.
            remove_size (int): The size of the center to remove.
            disable_tqdm (bool): Whether to disable the tqdm progress bar.

        Returns:
            trimesh.Trimesh: The generated mesh.
        """
        output_x_size, _ = image.shape
        image = image.max() - image

        image = image[::resize_factor, ::resize_factor]

        rows, cols = image.shape
        x = np.linspace(0, cols - 1, cols)
        y = np.linspace(0, rows - 1, rows)
        x, y = np.meshgrid(x, y)
        z = image

        ground = z.max()

        vertices = np.column_stack([x.ravel(), y.ravel(), z.ravel()])
        faces = []

        skipped = 0

        for i in tqdm(range(rows - 1), desc="Generating mesh", unit="row", disable=disable_tqdm):
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
        mesh = MeshComponent.rotate_mesh(mesh, disable_tqdm=disable_tqdm)

        if apply_decimation:
            percent = decimation_percent / 100
            mesh = mesh.simplify_quadric_decimation(
                percent=percent, aggression=decimation_agression
            )

        try:
            if not mesh.is_watertight:
                mesh = MeshComponent.fix_mesh(mesh, disable_tqdm=disable_tqdm)
        except Exception:
            pass

        mesh = MeshComponent.mesh_to_output_size(
            mesh,
            resize_factor,
            z_scaling_factor,
            output_x_size,
            skip_resize_to_expected_size=not include_zeros,
        )

        if remove_center:
            mesh = MeshComponent.remove_center_from_mesh(mesh, remove_size)

        return mesh

    @staticmethod
    def rotate_mesh(mesh: trimesh.Trimesh, disable_tqdm: bool = False) -> trimesh.Trimesh:
        """Rotates the given mesh by 180 degrees around the Y-axis and Z-axis.

        Arguments:
            mesh (trimesh.Trimesh): The mesh to rotate.
            disable_tqdm (bool): Whether to disable the tqdm progress bar.

        Returns:
            trimesh.Trimesh: The rotated mesh.
        """
        mesh_copy = mesh.copy()

        rotation_matrices = [
            trimesh.transformations.rotation_matrix(np.pi, [0, 1, 0]),
            trimesh.transformations.rotation_matrix(np.pi, [0, 0, 1]),
        ]

        for rotation_matrix in tqdm(
            rotation_matrices, desc="Rotating mesh", unit="rotation", disable=disable_tqdm
        ):
            mesh_copy.apply_transform(rotation_matrix)

        return mesh_copy

    @staticmethod
    def fix_mesh(mesh: trimesh.Trimesh, disable_tqdm: bool = False) -> trimesh.Trimesh:
        """Fixes the given mesh by filling holes, fixing normals, fixing winding, fixing inversion,
        fixing broken faces, and stitching.

        Arguments:
            mesh (trimesh.Trimesh): The mesh to fix.
            disable_tqdm (bool): Whether to disable the tqdm progress bar.

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

        for method in tqdm(fix_methods, desc="Fixing mesh", unit="method", disable=disable_tqdm):
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

        cube_mesh = trimesh.creation.box([remove_size, remove_size, z_size * 4])
        cube_mesh.apply_translation(mesh_copy.centroid - cube_mesh.centroid)

        return trimesh.boolean.difference([mesh_copy, cube_mesh], check_volume=False)
