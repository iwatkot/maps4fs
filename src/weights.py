import os
import random
import re

import cv2

import src.globals as g

weights_files = [
    os.path.join(g.weights_dir, f) for f in os.listdir(g.weights_dir) if f.endswith("_weight.png")
]
g.console.log(f"Fetched {len(weights_files)} weight files.")


class Texture:
    def __init__(self, name: str):
        self.name = name
        self._get_paths()
        self._check_shapes()
        g.console.log(f"Weights file for texture {self.name} loaded and checked.")

    def _get_paths(self):
        pattern = re.compile(rf"{self.name}\d{{2}}_weight")
        paths = [path for path in weights_files if pattern.search(path)]
        if not paths:
            raise FileNotFoundError(f"Texture not found: {self.name}")
        self.paths = paths

    def _check_shapes(self):
        unique_shapes = set()
        for path in self.paths:
            img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
            unique_shapes.add(img.shape)
        if len(unique_shapes) > 1:
            raise ValueError(f"Texture {self.name} has multiple shapes: {unique_shapes}")

    def get_random_path(self):
        return random.choice(self.paths)


class Textures(metaclass=g.Singleton):
    g.console.log("Loading texture weight files...")
    animalMud = Texture("animalMud")
    asphalt = Texture("asphalt")
    cobbleStone = Texture("cobbleStone")
    concrete = Texture("concrete")
    concreteRubble = Texture("concreteRubble")
    concreteTiles = Texture("concreteTiles")
    dirt = Texture("dirt")
    dirtDark = Texture("dirtDark")
    forestGround = Texture("forestGround")
    forestGroundLeaves = Texture("forestGroundLeaves")
    grass = Texture("grass")
    grassDirt = Texture("grassDirt")
    gravel = Texture("gravel")
    groundBricks = Texture("groundBricks")
    mountainRock = Texture("mountainRock")
    mountainRockDark = Texture("mountainRockDark")
    riverMud = Texture("riverMud")
    g.console.log("All texture weight files loaded.")
