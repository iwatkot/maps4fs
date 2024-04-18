import logging
from typing import Any


class Component:
    """Base class for all map generation components.

    Args:
        coordinates (tuple[float, float]): The latitude and longitude of the center of the map.
        distance (int): The distance from the center to the edge of the map.
        map_directory (str): The directory where the map files are stored.
        logger (Any, optional): The logger to use. Must have at least three basic methods: debug,
            info, warning. If not provided, default logging will be used.
    """

    def __init__(
        self,
        coordinates: tuple[float, float],
        distance: int,
        map_directory: str,
        logger: Any = None,
    ):
        self._coordinates = coordinates
        self._distance = distance
        self._map_directory = map_directory

        if not logger:
            logger = logging.getLogger(__name__)
        self.logger = logger

    def process(self):
        raise NotImplementedError
