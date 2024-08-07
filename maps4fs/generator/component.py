"""This module contains the base class for all map generation components."""

from typing import Any


# pylint: disable=R0801, R0903
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
        **kwargs,  # pylint: disable=W0613
    ):
        self.coordinates = coordinates
        self.distance = distance
        self.map_directory = map_directory
        self.logger = logger

    def process(self) -> None:
        """Launches the component processing. Must be implemented in the child class.

        Raises:
            NotImplementedError: If the method is not implemented in the child class.
        """
        raise NotImplementedError
