import os
import shutil
from typing import Any

import maps4fs as mfs


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
            logger = mfs.Logger(__name__, to_stdout=True, to_file=False)
        self.logger = logger
        self.components = []

        os.makedirs(self.map_directory, exist_ok=True)
        if map_template:
            shutil.unpack_archive(map_template, self.map_directory)
            self.logger.info(f"Map template {map_template} unpacked to {self.map_directory}")
        else:
            self.logger.warning(
                "Map template not provided, if directory does not contain required files, "
                "it may not work properly in Giants Editor."
            )

        self._add_components(blur_seed, max_height)

    def _add_components(self, blur_seed: int, max_height: int) -> None:
        self.logger.debug("Starting adding components...")
        for component in mfs.generator.BaseComponents:
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
        self.logger.debug(f"Added {len(self.components)} components.")

    def generate(self) -> None:
        try:
            from tqdm import tqdm

            with tqdm(total=len(self.components), desc="Generating map...") as pbar:
                for component in self.components:
                    component.process()
                    pbar.update(1)

        except ImportError:
            for component in self.components:
                component.process()

    def previews(self) -> list[str]:
        return self.texture.previews()
