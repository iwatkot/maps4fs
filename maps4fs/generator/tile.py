"""This module contains the Tile component, which is used to generate a tile of DEM data around
the map."""

import os

from maps4fs.generator.dem import DEM


class Tile(DEM):
    """Component for creating a tile of DEM data around the map.

    Arguments:
        coordinates (tuple[float, float]): The latitude and longitude of the center of the map.
        map_height (int): The height of the map in pixels.
        map_width (int): The width of the map in pixels.
        map_directory (str): The directory where the map files are stored.
        logger (Any, optional): The logger to use. Must have at least three basic methods: debug,
            info, warning. If not provided, default logging will be used.

    Keyword Arguments:
        tile_code (str): The code of the tile (N, NE, E, SE, S, SW, W, NW).

    Public Methods:
        get_output_resolution: Return the resolution of the output image.
        process: Launch the component processing.
        make_copy: Override the method to prevent copying the tile.
    """

    def preprocess(self) -> None:
        """Prepares the component for processing. Reads the tile code from the kwargs and sets the
        DEM path for the tile."""
        super().preprocess()
        self.code = self.kwargs.get("tile_code")
        if not self.code:
            raise ValueError("Tile code was not provided")

        self.logger.debug(f"Generating tile {self.code}")

        tiles_directory = os.path.join(self.map_directory, "objects", "tiles")
        os.makedirs(tiles_directory, exist_ok=True)

        self._dem_path = os.path.join(tiles_directory, f"{self.code}.png")
        self.logger.debug(f"DEM path for tile {self.code} is {self._dem_path}")

    def get_output_resolution(self) -> tuple[int, int]:
        """Return the resolution of the output image.

        Returns:
            tuple[int, int]: The width and height of the output image.
        """
        return self.map_width, self.map_height

    def make_copy(self, *args, **kwargs) -> None:
        """Override the method to prevent copying the tile."""
        pass  # pylint: disable=unnecessary-pass
