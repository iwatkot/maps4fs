from typing import Any

import maps4fs as mfs


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
        **kwargs,
    ):
        self.coordinates = coordinates
        self.distance = distance
        self.map_directory = map_directory

        if not logger:
            logger = mfs.Logger(__name__, to_stdout=True, to_file=False)
        self.logger = logger

    def process(self):
        raise NotImplementedError
