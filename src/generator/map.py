import logging
import os
import shutil
from typing import Any


class Map:
    def __init__(
        self,
        coordinates: tuple[float, float],
        distance: int,
        map_directory: str,
        blur_seed: int,
        max_height: int,
        map_template: str = None,
        logger: Any = None,
    ):
        self.coordinates = coordinates
        self.distance = distance
        self.map_directory = map_directory

        if not logger:
            logger = logging.getLogger(__name__)
        self.logger = logger

        os.makedirs(self.map_directory, exist_ok=True)
        if map_template:
            shutil.unpack_archive(map_template, self.map_directory)
            self.logger.info(f"Map template {map_template} unpacked to {self.map_directory}")
        else:
            self.logger.info(
                "Map template not provided, if directory does not contain required files, "
                "it may not work properly in Giants Editor."
            )
