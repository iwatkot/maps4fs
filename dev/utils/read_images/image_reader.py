import os
from typing import Any

import cv2
import numpy as np


def read_image(image_path: str) -> dict[str, Any]:
    """Reads an image file and returns its metadata.

    Arguments:
        image_path (str): The path to the image file.

    Returns:
        dict[str, Any]: A dictionary containing the image metadata including path, shape,
                        data type, min, max, mean, and unique values.
    """
    if not os.path.isfile(image_path):
        raise FileNotFoundError(f"Image file not found: {image_path}")
    image_np = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    if image_np is None:
        raise ValueError(f"Could not read image file: {image_path}")

    return {
        "image_path": image_path,
        "shape": image_np.shape,
        "dtype": image_np.dtype,
        "min": int(image_np.min()),
        "max": int(image_np.max()),
        "unique_values": np.unique(image_np).tolist(),  # Convert to list for better readability
    }


def normalize_and_color_map(src_image_path: str, dst_image_path: str) -> None:
    """Normalizes an image and applies a color map, saving the result.

    Arguments:
        src_image_path (str): The path to the source image file.
        dst_image_path (str): The path where the processed image will be saved.
    """
    if not os.path.isfile(src_image_path):
        raise FileNotFoundError(f"Source image file not found: {src_image_path}")

    # Read the source image
    src_image = cv2.imread(src_image_path, cv2.IMREAD_UNCHANGED)
    if src_image is None:
        raise ValueError(f"Could not read source image file: {src_image_path}")

    # Normalize the image
    normalized_image = cv2.normalize(src_image, None, 0, 255, cv2.NORM_MINMAX)

    # Apply a color map
    colored_image = cv2.applyColorMap(normalized_image.astype(np.uint8), cv2.COLORMAP_BONE)

    # Save the processed image
    cv2.imwrite(dst_image_path, colored_image)
