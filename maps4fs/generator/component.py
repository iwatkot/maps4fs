"""This module contains the base class for all map generation components."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import osmnx as ox  # type: ignore

if TYPE_CHECKING:
    from maps4fs.generator.game import Game


# pylint: disable=R0801, R0903, R0902
class Component:
    """Base class for all map generation components.

    Args:
        coordinates (tuple[float, float]): The latitude and longitude of the center of the map.
        map_height (int): The height of the map in pixels.
        map_width (int): The width of the map in pixels.
        map_directory (str): The directory where the map files are stored.
        logger (Any, optional): The logger to use. Must have at least three basic methods: debug,
            info, warning. If not provided, default logging will be used.
    """

    def __init__(
        self,
        game: Game,
        coordinates: tuple[float, float],
        map_height: int,
        map_width: int,
        map_directory: str,
        logger: Any = None,
        **kwargs,  # pylint: disable=W0613, R0913, R0917
    ):
        self.game = game
        self.coordinates = coordinates
        self.map_height = map_height
        self.map_width = map_width
        self.map_directory = map_directory
        self.logger = logger
        self.kwargs = kwargs

        self.save_bbox()
        self.preprocess()

    def preprocess(self) -> None:
        """Prepares the component for processing. Must be implemented in the child class.

        Raises:
            NotImplementedError: If the method is not implemented in the child class.
        """
        raise NotImplementedError

    def process(self) -> None:
        """Launches the component processing. Must be implemented in the child class.

        Raises:
            NotImplementedError: If the method is not implemented in the child class.
        """
        raise NotImplementedError

    def previews(self) -> list[str]:
        """Returns a list of paths to the preview images. Must be implemented in the child class.

        Raises:
            NotImplementedError: If the method is not implemented in the child class.
        """
        raise NotImplementedError

    def get_bbox(self, project_utm: bool = False) -> tuple[int, int, int, int]:
        """Calculates the bounding box of the map from the coordinates and the height and
        width of the map.

        Args:
            project_utm (bool, optional): Whether to project the bounding box to UTM.

        Returns:
            tuple[int, int, int, int]: The bounding box of the map.
        """
        north, south, _, _ = ox.utils_geo.bbox_from_point(
            self.coordinates, dist=self.map_height / 2, project_utm=project_utm
        )
        _, _, east, west = ox.utils_geo.bbox_from_point(
            self.coordinates, dist=self.map_width / 2, project_utm=project_utm
        )
        bbox = north, south, east, west
        self.logger.debug(
            "Calculated bounding box for component: %s: %s, project_utm: %s",
            self.__class__.__name__,
            bbox,
            project_utm,
        )
        return bbox

    def save_bbox(self) -> None:
        """Saves the bounding box of the map to the component instance from the coordinates and the
        height and width of the map.
        """
        self.bbox = self.get_bbox(project_utm=False)
        self.logger.debug("Saved bounding box: %s", self.bbox)
