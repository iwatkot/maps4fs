import os
from typing import Literal

import cv2
import imageio
import numpy as np
import tifffile as tiff


def read(image_path: str) -> np.ndarray:
    """Read an image and return it as a NumPy array.

    Arguments:
        image_path (str): Path to the image.
    """
    if not os.path.isfile(image_path):
        raise FileNotFoundError(f"File not found: {image_path}")

    if image_path.lower().endswith(".dds"):
        image = imageio.imread(image_path)
    elif image_path.lower().endswith(".tif"):
        image = tiff.imread(image_path)
    else:
        image = cv2.imread(image_path)

    return image


def tiff_to_png(input_path: str, output_path: str) -> None:
    """Read a TIFF image and save it as a PNG image.
    Change the color space from RGB to BGR for compatibility with OpenCV.

    Arguments:
        input_path (str): Path to the input TIFF image.
        output_path (str): Path to the output PNG image.
    """
    image = tiff.imread(input_path)
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    cv2.imwrite(output_path, image)
    print(f"Converted {input_path} to {output_path}")


def tiff_to_dds(
    input_path: str, output_path: str, height: int | None = None, width: int | None = None
) -> None:
    """Read a TIFF image and save it as a DDS image.
    Change the color space from RGB to BGR for compatibility with OpenCV.

    Arguments:
        input_path (str): Path to the input TIFF image.
        output_path (str): Path to the output DDS image.
        height (int, optional): Height of the output image. Defaults to None.
        width (int, optional): Width of the output image. Defaults to None.
    """
    image = tiff.imread(input_path)

    if height and width:
        image = cv2.resize(image, (width, height), interpolation=cv2.INTER_AREA)

    imageio.imwrite(output_path, image)
    print(f"Converted {input_path} to {output_path}")


def to_dds(input_directory: str, output_format: Literal["png", "dds"]) -> None:
    """Recursively walks through the input directory and converts all TIFF images to PNG or DDS images.
    The new images are saved in the same directory structure with same file names
    (except for the extension), e.g., input_directory/image.tif -> input_directory/image.png.

    Arguments:
        input_directory (str): Path to the directory with TIFF images.
        output_format (str): The output format (png or dds).
    """
    converters = {
        "png": tiff_to_png,
        "dds": tiff_to_dds,
    }
    converter = converters.get(output_format)
    if not converter:
        raise ValueError(f"Unsupported output format: {output_format}")

    for root, _, files in os.walk(input_directory):
        for file in files:
            if file.lower().endswith(".tif"):
                input_path = os.path.join(root, file)
                output_path = os.path.splitext(input_path)[0] + f".{output_format}"
                converter(input_path, output_path)


def tiffs_to_png(input_directory: str) -> None:
    """Recursively walks through the input directory and converts all TIFF images to PNG images.
    The new PNG images are saved in the same directory structure with same file names
    (except for the extension), e.g., input_directory/image.tif -> input_directory/image.png.

    Arguments:
        input_directory (str): Path to the directory with TIFF images.
    """
    return to_dds(input_directory, "png")


def tiffs_to_dds(input_directory: str) -> None:
    """Recursively walks through the input directory and converts all TIFF images to DDS images.
    The new DDS images are saved in the same directory structure with same file names
    (except for the extension), e.g., input_directory/image.tif -> input_directory/image.dds.

    Arguments:
        input_directory (str): Path to the directory with TIFF images.
    """
    return to_dds(input_directory, "dds")
