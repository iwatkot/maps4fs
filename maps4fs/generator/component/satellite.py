"""This module contains the Satellite class for the maps4fs package to download satellite images
for the map."""

import os
import shutil
from typing import NamedTuple

from pygmdl import save_image

import maps4fs.generator.config as mfscfg
from maps4fs.generator.component.base.component_image import ImageComponent
from maps4fs.generator.monitor import monitor_performance
from maps4fs.generator.settings import Parameters


class SatelliteImage(NamedTuple):
    """Named tuple for the satellite image download task.

    Attributes:
        lat (float): The latitude of the center of the map.
        lon (float): The longitude of the center of the map.
        size (int): The size of the map in pixels.
        output_path (str): The path where to save the image.
        rotation (int): The rotation angle of the map.
        zoom (int): The zoom level of the map.
        copy_from (str | None): If saving should be skipped and the image should be copied from
            another file.
    """

    lat: float
    lon: float
    size: int
    output_path: str
    rotation: int
    zoom: int
    copy_from: str | None = None


class Satellite(ImageComponent):
    """Component for to download satellite images for the map.

    Arguments:
        game (Game): The game instance for which the map is generated.
        coordinates (tuple[float, float]): The latitude and longitude of the center of the map.
        map_size (int): The size of the map in pixels.
        map_rotated_size (int): The size of the map in pixels after rotation.
        rotation (int): The rotation angle of the map.
        map_directory (str): The directory where the map files are stored.
        logger (Any, optional): The logger to use. Must have at least three basic methods: debug,
            info, warning. If not provided, default logging will be used.
    """

    @monitor_performance
    def process(self) -> None:
        """Downloads the satellite images for the map."""
        self.image_paths = []
        if not self.map.satellite_settings.download_images:
            self.logger.debug("Satellite images download is disabled.")
            return

        overview_size = self.map_size * 2
        overwiew_path = os.path.join(self.satellite_directory, "satellite_overview.png")

        self.assets.overview = overwiew_path

        background_size = self.map_size + Parameters.BACKGROUND_DISTANCE * 2
        background_path = os.path.join(self.satellite_directory, "satellite_background.png")

        self.assets.background = background_path

        sizes = [overview_size, background_size]
        self.image_paths = [overwiew_path, background_path]

        tasks = self.get_tasks(sizes, self.image_paths)

        for task in tasks:
            try:
                if task.copy_from and os.path.isfile(task.copy_from):
                    shutil.copy(task.copy_from, task.output_path)
                    continue

                save_image(
                    task.lat,
                    task.lon,
                    task.size,
                    output_path=task.output_path,
                    rotation=task.rotation,
                    zoom=task.zoom,
                    from_center=True,
                    logger=self.logger,
                    tiles_dir=mfscfg.SAT_CACHE_DIR,
                    show_progress=not mfscfg.TQDM_DISABLE,
                )

            except Exception as e:
                self.logger.error(f"Failed to download satellite image: {e}")
                continue

    def get_tasks(self, sizes: list[int], save_paths: list[str]) -> list[SatelliteImage]:
        """Prepares the tasks for downloading the satellite images.

        Arguments:
            sizes (list[int]): The sizes of the images to download.
            save_paths (list[str]): The paths where to save the images.

        Returns:
            list[SatelliteImage]: The list of tasks for downloading the satellite images.
        """
        tasks: list[SatelliteImage] = []

        for size, save_path in zip(sizes, save_paths):
            # Check if in tasks there's already a task with the same size.
            existing_task = next((t for t in tasks if t.size == size), None)
            copy_from = existing_task.output_path if existing_task else None

            lat, lon = self.coordinates
            tasks.append(
                SatelliteImage(
                    lat=lat,
                    lon=lon,
                    size=size,
                    output_path=save_path,
                    rotation=self.rotation,
                    zoom=self.map.satellite_settings.zoom_level,
                    copy_from=copy_from,
                )
            )

        return tasks

    @monitor_performance
    def previews(self) -> list[str]:
        """Returns the paths to the preview images.

        Returns:
            list[str]: List of paths to the preview images.
        """
        previews = []
        for image_path in self.image_paths:
            preview_path = os.path.join(self.previews_directory, os.path.basename(image_path))
            self.resize_to_preview(image_path, preview_path)
            previews.append(preview_path)

        return previews
