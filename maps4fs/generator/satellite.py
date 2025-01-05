"""This module contains the Satellite class for the maps4fs package to download satellite images
for the map."""

import os

import cv2
from pygmdl import save_image  # type: ignore

from maps4fs.generator.background import DEFAULT_DISTANCE
from maps4fs.generator.component import Component
from maps4fs.generator.texture import PREVIEW_MAXIMUM_SIZE


# pylint: disable=W0223
class Satellite(Component):
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

    def preprocess(self) -> None:
        """This component does not require any preprocessing."""
        return

    def process(self) -> None:
        """Downloads the satellite images for the map."""
        self.image_paths = []  # pylint: disable=W0201
        if not self.map.satellite_settings.download_images:
            self.logger.debug("Satellite images download is disabled.")
            return

        margin = self.map.satellite_settings.satellite_margin
        overview_size = (self.map_size + margin) * 2
        overwiew_path = os.path.join(self.satellite_directory, "satellite_overview.png")

        background_size = self.map_size + (DEFAULT_DISTANCE + margin) * 2
        background_path = os.path.join(self.satellite_directory, "satellite_background.png")

        sizes = [overview_size, background_size]
        self.image_paths = [overwiew_path, background_path]  # pylint: disable=W0201

        for size, path in zip(sizes, self.image_paths):
            try:
                lat, lon = self.coordinates
                zoom = self.map.satellite_settings.zoom_level
                save_image(
                    lat,
                    lon,
                    size,
                    output_path=path,
                    rotation=self.rotation,
                    zoom=zoom,
                    from_center=True,
                    logger=self.logger,
                )
            except Exception as e:  # pylint: disable=W0718
                self.logger.error(f"Failed to download satellite image: {e}")
                continue

    # pylint: disable=no-member
    def previews(self) -> list[str]:
        """Returns the paths to the preview images.

        Returns:
            list[str]: List of paths to the preview images.
        """
        previews = []
        for image_path in self.image_paths:
            if not os.path.isfile(image_path):
                self.logger.warning(f"File {image_path} does not exist.")
                continue
            image = cv2.imread(image_path)
            if image is None:
                self.logger.warning(f"Failed to read image from {image_path}")
                continue

            if image.shape[0] > PREVIEW_MAXIMUM_SIZE or image.shape[1] > PREVIEW_MAXIMUM_SIZE:
                image = cv2.resize(image, (PREVIEW_MAXIMUM_SIZE, PREVIEW_MAXIMUM_SIZE))

            preview_path = os.path.join(self.previews_directory, os.path.basename(image_path))
            cv2.imwrite(preview_path, image)
            previews.append(preview_path)

        return previews
