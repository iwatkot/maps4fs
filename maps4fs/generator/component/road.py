"""Component for map roads processing and generation."""

import os
import shutil

import shapely

from maps4fs.generator.component.base.component_mesh import ComponentMesh
from maps4fs.generator.component.i3d import I3d
from maps4fs.generator.settings import Parameters


class Road(I3d, ComponentMesh):
    """Component for map roads processing and generation.

    Arguments:
        game (Game): The game instance for which the map is generated.
        coordinates (tuple[float, float]): The latitude and longitude of the center of the map.
        map_size (int): The size of the map in pixels.
        map_rotated_size (int): The size of the map in pixels after rotation.
        rotation (int): The rotation angle of the map.
        map_directoryPara (str): The directory where the map files are stored.
        logger (Any, optional): The logger to use. Must have at least three basic methods: debug,
            info, warning. If not provided, default logging will be used.
    """

    def preprocess(self) -> None:
        pass

    def process(self) -> None:
        roads_polylines = self.get_infolayer_data(Parameters.TEXTURES, Parameters.ROADS_POLYLINES)
        if not roads_polylines:
            self.logger.warning("Roads polylines data not found in textures info layer.")
            return

        linestrings: list[tuple[shapely.LineString, int]] = []
        for road_id, road_info in enumerate(roads_polylines, start=1):
            if isinstance(road_info, dict):
                points: list[int | float] = road_info.get("points")
                width: int = road_info.get("width")
            else:
                continue

            if not points or len(points) < 2 or not width:
                self.logger.debug("Invalid road data for road ID %s: %s", road_id, road_info)
                continue

            try:
                fitted_road = self.fit_object_into_bounds(
                    linestring_points=points, angle=self.rotation
                )
            except ValueError as e:
                self.logger.debug(
                    "Road %s could not be fitted into the map bounds with error: %s",
                    road_id,
                    e,
                )
                continue

            try:
                linestring = shapely.LineString(fitted_road)
            except ValueError as e:
                self.logger.debug(
                    "Road %s could not be converted to a LineString with error: %s",
                    road_id,
                    e,
                )
                continue

            linestrings.append((linestring, width))

        self.logger.info("Total found for mesh generation: %d", len(linestrings))

        if linestrings:
            self.generate_road_mesh(linestrings)

    def generate_road_mesh(self, linestrings: list[tuple[shapely.LineString, int]]) -> None:
        road_mesh_directory = os.path.join(self.map_directory, "roads")
        os.makedirs(road_mesh_directory, exist_ok=True)

        templates_directory = "templates"
        asphalt_texture_filename = "asphalt.png"
        asphalt_texture_path = os.path.join(
            templates_directory,
            asphalt_texture_filename,
        )
        if not os.path.isfile(asphalt_texture_path):
            self.logger.warning(
                "Asphalt texture file not found at %s. Skipping road mesh generation.",
                asphalt_texture_path,
            )
            return

        dst_texture_path = os.path.join(
            road_mesh_directory,
            asphalt_texture_filename,
        )

        shutil.copyfile(asphalt_texture_path, dst_texture_path)
        self.logger.info("Asphalt texture copied to %s", dst_texture_path)

        obj_output_path = os.path.join(road_mesh_directory, "roads.obj")
        mtl_output_path = os.path.join(road_mesh_directory, "roads.mtl")

        self.create_textured_linestrings_mesh(
            linestrings=linestrings,
            texture_path=dst_texture_path,
            obj_output_path=obj_output_path,
            mtl_output_path=mtl_output_path,
        )

    def create_textured_linestrings_mesh(
        self,
        linestrings: list[tuple[shapely.LineString, int]],
        texture_path: str,
        obj_output_path: str,
        mtl_output_path: str,
    ) -> None:
        # Implementation for creating the textured linestrings mesh
        pass

    def info_sequence(self):
        return {}
