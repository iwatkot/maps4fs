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
