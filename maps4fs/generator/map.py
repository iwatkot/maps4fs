"""This module contains Map class, which is used to generate map using all components."""

import os
import shutil
from typing import Any

from tqdm import tqdm

from maps4fs.generator.component import Component
from maps4fs.generator.game import Game
from maps4fs.logger import Logger


# pylint: disable=R0913, R0902
class Map:
    """Class used to generate map using all components.

    Args:
        game (Type[Game]): Game for which the map is generated.
        coordinates (tuple[float, float]): Coordinates of the center of the map.
        height (int): Height of the map in pixels.
        width (int): Width of the map in pixels.
        map_directory (str): Path to the directory where map files will be stored.
        logger (Any): Logger instance
    """

    def __init__(  # pylint: disable=R0917
        self,
        game: Game,
        coordinates: tuple[float, float],
        height: int,
        width: int,
        map_directory: str,
        logger: Any = None,
        **kwargs,
    ):
        self.game = game
        self.components: list[Component] = []
        self.coordinates = coordinates
        self.height = height
        self.width = width
        self.map_directory = map_directory

        if not logger:
            logger = Logger(__name__, to_stdout=True, to_file=False)
        self.logger = logger
        self.logger.debug("Game was set to %s", game.code)

        self.kwargs = kwargs

        os.makedirs(self.map_directory, exist_ok=True)
        self.logger.debug("Map directory created: %s", self.map_directory)

        try:
            shutil.unpack_archive(game.template_path, self.map_directory)
            self.logger.info("Map template unpacked to %s", self.map_directory)
        except Exception as e:
            raise RuntimeError(f"Can not unpack map template due to error: {e}") from e

    def generate(self) -> None:
        """Launch map generation using all components."""
        with tqdm(total=len(self.game.components), desc="Generating map...") as pbar:
            for game_component in self.game.components:
                component = game_component(
                    self.game,
                    self.coordinates,
                    self.height,
                    self.width,
                    self.map_directory,
                    self.logger,
                    **self.kwargs,
                )
                try:
                    component.process()
                except Exception as e:  # pylint: disable=W0718
                    self.logger.error(
                        "Error processing component %s: %s",
                        component.__class__.__name__,
                        e,
                    )
                    raise e
                self.components.append(component)

                pbar.update(1)

    def previews(self) -> list[str]:
        """Get list of preview images.

        Returns:
            list[str]: List of preview images.
        """
        previews = []
        for component in self.components:
            previews.extend(component.previews())
        return previews

    def pack(self, archive_name: str) -> str:
        """Pack map directory to zip archive.

        Args:
            archive_name (str): Name of the archive.

        Returns:
            str: Path to the archive.
        """
        archive_path = shutil.make_archive(archive_name, "zip", self.map_directory)
        self.logger.info("Map packed to %s.zip", archive_name)
        return archive_path
