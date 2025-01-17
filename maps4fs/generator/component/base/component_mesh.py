"""Base class for all components that primarily used to work with meshes."""

import cv2
import numpy as np

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
