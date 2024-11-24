import os

from maps4fs.generator.dem import DEM


class Tile(DEM):
    def preprocess(self) -> None:
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
        return self.map_width, self.map_height

    def process(self) -> None:
        super().process()

    def make_copy(self, *args, **kwargs) -> None:
        pass
