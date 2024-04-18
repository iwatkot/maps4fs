import os
from typing import Any

import cv2
import numpy as np

import maps4fs.globals as g
from maps4fs.generator import Component


class Texture(Component):
    def __init__(
        self,
        coordinates: tuple[float, float],
        distance: int,
        map_directory: str,
        logger: Any = None,
    ):
        super().__init__(coordinates, distance, map_directory, logger)
        self._weights_dir = os.path.join(self._map_directory, "maps", "map", "data")

    def process(self):
        self._prepare_weights()

    def _prepare_weights(self):
        self.logger.debug("Starting preparing weights...")
        for texture_name, layer_numbers in g.TEXTURES.items():
            self._generate_weights(texture_name, layer_numbers)
        self.logger.debug(f"Prepared weights for {len(g.TEXTURES)} textures.")

    def _generate_weights(self, texture_name: str, layer_numbers: int) -> None:
        """Generates weight files for textures. Each file is a numpy array of zeros and dtype uint8 (0-255).

        Args:
            texture_name (str): Name of the texture.
            layer_numbers (int): Number of layers in the texture.
        """
        size = self._distance * 2
        postfix = "_weight.png"
        if layer_numbers == 0:
            filepaths = [os.path.join(self._weights_dir, texture_name + postfix)]
        else:
            filepaths = [
                os.path.join(self._weights_dir, texture_name + str(i).zfill(2) + postfix)
                for i in range(1, layer_numbers + 1)
            ]

        for filepath in filepaths:
            img = np.zeros((size, size), dtype=np.uint8)
            cv2.imwrite(filepath, img)
