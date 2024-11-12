"""This module contains Map class, which is used to generate map using all components."""

import os
import shutil
from typing import Any

from tqdm import tqdm

from maps4fs.generator.game import Game
from maps4fs.logger import Logger


# pylint: disable=R0913
class Map:
    """Class used to generate map using all components.

    Args:
        game (Type[Game]): Game for which the map is generated.
        coordinates (tuple[float, float]): Coordinates of the center of the map.
        distance (int): Distance from the center of the map.
        map_directory (str): Path to the directory where map files will be stored.
        blur_seed (int): Seed used for blur effect.
        max_height (int): Maximum height of the map.
        logger (Any): Logger instance
    """

    def __init__(  # pylint: disable=R0917
        self,
        game: Game,
        coordinates: tuple[float, float],
        distance: int,
        map_directory: str,
        blur_seed: int,
        max_height: int,
        logger: Any = None,
    ):
        self.game = game
        self.coordinates = coordinates
        self.distance = distance
        self.map_directory = map_directory

        if not logger:
            logger = Logger(__name__, to_stdout=True, to_file=False)
        self.logger = logger
        self.logger.debug("Game was set to %s", game.code)

        os.makedirs(self.map_directory, exist_ok=True)
        self.logger.debug("Map directory created: %s", self.map_directory)

        try:
            shutil.unpack_archive(game.template_path, self.map_directory)
            self.logger.info("Map template unpacked to %s", self.map_directory)
        except Exception as e:
            raise RuntimeError(f"Can not unpack map template due to error: {e}") from e

        # Blur seed should be positive and odd.
        if blur_seed <= 0:
            raise ValueError("Blur seed should be positive.")
        if blur_seed % 2 == 0:
            blur_seed += 1

        self.blur_seed = blur_seed
        self.max_height = max_height

    def generate(self) -> None:
        """Launch map generation using all components."""
        with tqdm(total=len(self.game.components), desc="Generating map...") as pbar:
            for game_component in self.game.components:
                component = game_component(
                    self.game,
                    self.coordinates,
                    self.distance,
                    self.map_directory,
                    self.logger,
                    blur_seed=self.blur_seed,
                    max_height=self.max_height,
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
                setattr(self, game_component.__name__.lower(), component)

                pbar.update(1)

    def previews(self) -> list[str]:
        """Get list of preview images.

        Returns:
            list[str]: List of preview images.
        """
        return self.texture.previews()  # type: ignore # pylint: disable=no-member

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
