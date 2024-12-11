"""This module contains functions to work with the background terrain of the map."""

import cv2
import numpy as np
import trimesh  # type: ignore


# pylint: disable=R0801, R0914
def plane_from_np(
    dem_data: np.ndarray,
    resize_factor: float,
    simplify_factor: int,
    save_path: str,
) -> None:
    """Generates a 3D obj file based on DEM data.

    Arguments:
        dem_data (np.ndarray) -- The DEM data as a numpy array.
        resize_factor (float) -- The factor by which the DEM data will be resized. Bigger values
            will result in a bigger mesh.
        simplify_factor (int) -- The factor by which the mesh will be simplified. Bigger values
            will result in a simpler mesh.
        save_path (str) -- The path to save the obj file.
    """
    dem_data = cv2.resize(  # pylint: disable=no-member
        dem_data, (0, 0), fx=resize_factor, fy=resize_factor
    )

    # Invert the height values.
    dem_data = dem_data.max() - dem_data

    rows, cols = dem_data.shape
    x = np.linspace(0, cols - 1, cols)
    y = np.linspace(0, rows - 1, rows)
    x, y = np.meshgrid(x, y)
    z = dem_data

    vertices = np.column_stack([x.ravel(), y.ravel(), z.ravel()])
    faces = []

    for i in range(rows - 1):
        for j in range(cols - 1):
            top_left = i * cols + j
            top_right = top_left + 1
            bottom_left = top_left + cols
            bottom_right = bottom_left + 1

            faces.append([top_left, bottom_left, bottom_right])
            faces.append([top_left, bottom_right, top_right])

    faces = np.array(faces)  # type: ignore
    mesh = trimesh.Trimesh(vertices=vertices, faces=faces)

    # Apply rotation: 180 degrees around Y-axis and Z-axis
    rotation_matrix_y = trimesh.transformations.rotation_matrix(np.pi, [0, 1, 0])
    rotation_matrix_z = trimesh.transformations.rotation_matrix(np.pi, [0, 0, 1])
    mesh.apply_transform(rotation_matrix_y)
    mesh.apply_transform(rotation_matrix_z)

    # Simplify the mesh to reduce the number of faces.
    mesh = mesh.simplify_quadric_decimation(face_count=len(faces) // simplify_factor)

    mesh.export(save_path)
