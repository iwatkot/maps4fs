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
        resize_factor: float,
        apply_decimation: bool,
        decimation_percent: int,
        decimation_agression: int,
    ) -> trimesh.Trimesh:
        """Generates a mesh from the given numpy array.

        Arguments:
            image (np.ndarray): The numpy array to generate the mesh from.
            include_zeros (bool): Whether to include zero values in the mesh.
            z_scaling_factor (float): The scaling factor for the Z-axis.
            resize_factor (float): The resizing factor.
            apply_decimation (bool): Whether to apply decimation to the mesh.
            decimation_percent (int): The percent of the decimation.
            decimation_agression (int): The agression of the decimation.

        Returns:
            trimesh.Trimesh: The generated mesh.
        """
        image = image.max() - image

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

        # Apply rotation: 180 degrees around Y-axis and Z-axis
        rotation_matrix_y = trimesh.transformations.rotation_matrix(np.pi, [0, 1, 0])
        rotation_matrix_z = trimesh.transformations.rotation_matrix(np.pi, [0, 0, 1])
        mesh.apply_transform(rotation_matrix_y)
        mesh.apply_transform(rotation_matrix_z)

        # if not include_zeros:
        mesh.apply_scale([1 / resize_factor, 1 / resize_factor, z_scaling_factor])

        if apply_decimation:
            percent = decimation_percent / 100
            mesh = mesh.simplify_quadric_decimation(
                percent=percent, aggression=decimation_agression
            )

        return mesh
