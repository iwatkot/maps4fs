"""This module contains functions and clas for generating path steps."""

from typing import NamedTuple

from geopy.distance import distance  # type: ignore

DEFAULT_DISTANCE = 2048


class PathStep(NamedTuple):
    """Represents parameters of one step in the path.

    Attributes:
        code {str} -- Tile code (N, NE, E, SE, S, SW, W, NW).
        angle {int} -- Angle in degrees (for example 0 for North, 90 for East).
        distance {int} -- Distance in meters from previous step.
        size {tuple[int, int]} -- Size of the tile in pixels (width, height).
    """

    code: str
    angle: int
    distance: int
    size: tuple[int, int]

    def get_destination(self, origin: tuple[float, float]) -> tuple[float, float]:
        """Calculate destination coordinates based on origin and step parameters.

        Arguments:
            origin {tuple[float, float]} -- Origin coordinates (latitude, longitude)

        Returns:
            tuple[float, float] -- Destination coordinates (latitude, longitude)
        """
        destination = distance(meters=self.distance).destination(origin, self.angle)
        return destination.latitude, destination.longitude


def get_steps(map_height: int, map_width: int) -> list[PathStep]:
    """Return a list of PathStep objects for each tile, which represent a step in the path.
    Moving from the center of the map to North, then clockwise.

    Arguments:
        map_height {int} -- Height of the map in pixels
        map_width {int} -- Width of the map in pixels

    Returns:
        list[PathStep] -- List of PathStep objects
    """
    # Move clockwise from N and calculate coordinates and sizes for each tile.
    half_width = int(map_width / 2)
    half_height = int(map_height / 2)

    half_default_distance = int(DEFAULT_DISTANCE / 2)

    return [
        PathStep("N", 0, half_height + half_default_distance, (map_width, DEFAULT_DISTANCE)),
        PathStep(
            "NE", 90, half_width + half_default_distance, (DEFAULT_DISTANCE, DEFAULT_DISTANCE)
        ),
        PathStep("E", 180, half_height + half_default_distance, (DEFAULT_DISTANCE, map_height)),
        PathStep(
            "SE", 180, half_height + half_default_distance, (DEFAULT_DISTANCE, DEFAULT_DISTANCE)
        ),
        PathStep("S", 270, half_width + half_default_distance, (map_width, DEFAULT_DISTANCE)),
        PathStep(
            "SW", 270, half_width + half_default_distance, (DEFAULT_DISTANCE, DEFAULT_DISTANCE)
        ),
        PathStep("W", 0, half_height + half_default_distance, (DEFAULT_DISTANCE, map_height)),
        PathStep(
            "NW", 0, half_height + half_default_distance, (DEFAULT_DISTANCE, DEFAULT_DISTANCE)
        ),
    ]
