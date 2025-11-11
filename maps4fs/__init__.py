# pylint: disable=missing-module-docstring, wrong-import-position
import cv2

# Increase OpenCV image size limit for large map generation
# Default is 1024 * 1024 * 1024 = ~1 billion pixels (32,768 x 32,768 images)
# Setting to 4x larger: 4096 * 1024 * 1024 = ~4 billion pixels (65,536 x 65,536 images)

try:
    cv2.CV_IO_MAX_IMAGE_PIXELS = 4096 * 1024 * 1024  # type: ignore
except Exception as e:
    print(f"Warning: Could not set CV_IO_MAX_IMAGE_PIXELS: {e}")
import pydtmdl.providers as dtm
from pydtmdl import DTMProvider

import maps4fs.generator.component as component
import maps4fs.generator.settings as settings
from maps4fs.generator.game import Game
from maps4fs.generator.map import Map
from maps4fs.generator.monitor import Logger
from maps4fs.generator.settings import GenerationSettings, MainSettings
