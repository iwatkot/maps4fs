"""This module contains the base class for all map generation components."""

from __future__ import annotations

import json
import os
from copy import deepcopy
from typing import TYPE_CHECKING, Any

import osmnx as ox  # type: ignore
from pyproj import Transformer

if TYPE_CHECKING:
    from maps4fs.generator.game import Game


# pylint: disable=R0801, R0903, R0902
class Component:
    """Base class for all map generation components.

    Args:
        game (Game): The game instance for which the map is generated.
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

        os.makedirs(self.previews_directory, exist_ok=True)

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

    @property
    def previews_directory(self) -> str:
        """The directory where the preview images are stored.

        Returns:
            str: The directory where the preview images are stored.
        """
        return os.path.join(self.map_directory, "previews")

    @property
    def generation_info_path(self) -> str:
        """The path to the generation info JSON file.

        Returns:
            str: The path to the generation info JSON file.
        """
        return os.path.join(self.map_directory, "generation_info.json")

    def info_sequence(self) -> dict[Any, Any]:
        """Returns the information sequence for the component. Must be implemented in the child
        class. If the component does not have an information sequence, an empty dictionary must be
        returned.

        Returns:
            dict[Any, Any]: The information sequence for the component.
        """
        return {}

    def commit_generation_info(self) -> None:
        """Commits the generation info to the generation info JSON file."""
        self.update_generation_info(self.info_sequence())

    def update_generation_info(self, data: dict[Any, Any]) -> None:
        """Updates the generation info with the provided data.
        If the generation info file does not exist, it will be created.

        Args:
            data (dict[Any, Any]): The data to update the generation info with.
        """
        if os.path.isfile(self.generation_info_path):
            with open(self.generation_info_path, "r", encoding="utf-8") as file:
                generation_info = json.load(file)
                self.logger.debug("Loaded generation info from %s", self.generation_info_path)
        else:
            self.logger.debug(
                "Generation info file does not exist, creating a new one in %s",
                self.generation_info_path,
            )
            generation_info = {}

        updated_generation_info = deepcopy(generation_info)
        updated_generation_info[self.__class__.__name__] = data

        self.logger.debug("Updated generation info, now contains %s fields", len(data))

        with open(self.generation_info_path, "w", encoding="utf-8") as file:
            json.dump(updated_generation_info, file, indent=4)

        self.logger.debug("Saved updated generation info to %s", self.generation_info_path)

    def get_bbox(
        self,
        coordinates: tuple[float, float] | None = None,
        distance: int | None = None,
        project_utm: bool = False,
    ) -> tuple[int, int, int, int]:
        """Calculates the bounding box of the map from the coordinates and the height and
        width of the map.
        If coordinates and distance are not provided, the instance variables are used.

        Args:
            coordinates (tuple[float, float], optional): The latitude and longitude of the center of
                the map. Defaults to None.
            distance (int, optional): The distance from the center of the map to the edge of the
                map. Defaults to None.
            project_utm (bool, optional): Whether to project the bounding box to UTM.

        Returns:
            tuple[int, int, int, int]: The bounding box of the map.
        """
        coordinates = coordinates or self.coordinates
        distance = distance or int(self.map_height / 2)

        north, south, _, _ = ox.utils_geo.bbox_from_point(
            coordinates, dist=distance, project_utm=project_utm
        )
        _, _, east, west = ox.utils_geo.bbox_from_point(
            coordinates, dist=distance, project_utm=project_utm
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

    def get_epsg3857_string(self, bbox: tuple[int, int, int, int] | None = None) -> str:
        """Converts the bounding box to EPSG:3857 string.
        If the bounding box is not provided, the instance variable is used.

        Args:
            bbox (tuple[int, int, int, int], optional): The bounding box to convert.

        Returns:
            str: The bounding box in EPSG:3857 string.
        """
        bbox = bbox or self.bbox
        north, south, east, west = bbox
        transformer = Transformer.from_crs("epsg:4326", "epsg:3857")
        epsg3857_north, epsg3857_west = transformer.transform(north, west)
        epsg3857_south, epsg3857_east = transformer.transform(south, east)

        return f"{epsg3857_north},{epsg3857_south},{epsg3857_east},{epsg3857_west} [EPSG:3857]"
