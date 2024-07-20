"""This module contains Map class, which is used to generate map using all components."""

import os
import shutil
from typing import Any

from tqdm import tqdm

from maps4fs.generator.component import Component
from maps4fs.generator.config import Config
from maps4fs.generator.dem import DEM
from maps4fs.generator.texture import Texture
from maps4fs.logger import Logger

BaseComponents = [Config, Texture, DEM]


# pylint: disable=R0913
class Map:
    """Class used to generate map using all components.

    Args:
        coordinates (tuple[float, float]): Coordinates of the center of the map.
        distance (int): Distance from the center of the map.
        map_directory (str): Path to the directory where map files will be stored.
        blur_seed (int): Seed used for blur effect.
        max_height (int): Maximum height of the map.
        map_template (str | None): Path to the map template. If not provided, default will be used.
        logger (Any): Logger instance
    """

    def __init__(
        self,
        coordinates: tuple[float, float],
        distance: int,
        map_directory: str,
        blur_seed: int,
        max_height: int,
        map_template: str | None = None,
        logger: Any = None,
    ):
        self.coordinates = coordinates
        self.distance = distance
        self.map_directory = map_directory

        if not logger:
            logger = Logger(__name__, to_stdout=True, to_file=False)
        self.logger = logger
        self.components: list[Component] = []

        os.makedirs(self.map_directory, exist_ok=True)
        if map_template:
            shutil.unpack_archive(map_template, self.map_directory)
            self.logger.info("Map template unpacked to %s", self.map_directory)
        else:
            self.logger.warning(
                "Map template not provided, if directory does not contain required files, "
                "it may not work properly in Giants Editor."
            )

        self._add_components(blur_seed, max_height)

    def _add_components(self, blur_seed: int, max_height: int) -> None:
        self.logger.debug("Starting adding components...")
        for component in BaseComponents:
            active_component = component(
                self.coordinates,
                self.distance,
                self.map_directory,
                self.logger,
                blur_seed=blur_seed,
                max_height=max_height,
            )
            setattr(self, component.__name__.lower(), active_component)
            self.components.append(active_component)
        self.logger.debug("Added %s components.", len(self.components))

    def generate(self) -> None:
        """Launch map generation using all components."""
        with tqdm(total=len(self.components), desc="Generating map...") as pbar:
            for component in self.components:
                try:
                    component.process()
                except Exception as e:  # pylint: disable=W0718
                    self.logger.error(
                        "Error processing component %s: %s",
                        component.__class__.__name__,
                        e,
                    )
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
