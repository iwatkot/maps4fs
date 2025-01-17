"""Base class for all components that primarily used to work with images."""

import numpy as np

from maps4fs.generator.component.base.component import Component


class ImageComponent(Component):
    """Base class for all components that primarily used to work with images."""

    @staticmethod
    def polygon_points_to_np(
        polygon_points: list[tuple[int, int]], divide: int | None = None
    ) -> np.ndarray:
        """Converts the polygon points to a NumPy array.

        Arguments:
            polygon_points (list[tuple[int, int]]): The polygon points.
            divide (int, optional): The number to divide the points by. Defaults to None.

        Returns:
            np.array: The NumPy array of the polygon points.
        """
        array = np.array(polygon_points, dtype=np.int32).reshape((-1, 1, 2))
        if divide:
            return array // divide
        return array

    @staticmethod
    def cut_out_np(
        image: np.ndarray, half_size: int, set_zeros: bool = False, return_cutout: bool = False
    ) -> np.ndarray:
        """Cuts out a square from the center of the image.

        Arguments:
            image (np.ndarray): The image.
            half_size (int): The half size of the square.
            set_zeros (bool, optional): Whether to set the cutout to zeros. Defaults to False.
            return_cutout (bool, optional): Whether to return the cutout. Defaults to False.

        Returns:
            np.ndarray: The image with the cutout or the cutout itself.
        """
        center = (image.shape[0] // 2, image.shape[1] // 2)
        x1 = center[0] - half_size
        x2 = center[0] + half_size
        y1 = center[1] - half_size
        y2 = center[1] + half_size

        if return_cutout:
            return image[x1:x2, y1:y2]

        if set_zeros:
            image[x1:x2, y1:y2] = 0

        return image
