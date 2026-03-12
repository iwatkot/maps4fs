"""Base class for all components that primarily used to work with images."""

import os
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image, ImageFile

from maps4fs.generator.component.base.component import Component
from maps4fs.generator.constants import Paths
from maps4fs.generator.settings import Parameters


class ImageComponent(Component):
    """Base class for all components that primarily used to work with images."""

    @staticmethod
    def _center_square_bounds(shape: tuple[int, ...], half_size: int) -> tuple[int, int, int, int]:
        """Return center square bounds (x1, x2, y1, y2) for an image-like shape."""
        center = (shape[0] // 2, shape[1] // 2)
        x1 = center[0] - half_size
        x2 = center[0] + half_size
        y1 = center[1] - half_size
        y2 = center[1] + half_size
        return x1, x2, y1, y2

    @staticmethod
    def _validate_same_spatial_shape(data: np.ndarray, mask: np.ndarray) -> None:
        """Ensure data and mask have identical spatial dimensions."""
        if data.shape[:2] != mask.shape[:2]:
            raise ValueError("Data and mask must have the same dimensions.")

    @staticmethod
    def polygon_points_to_np(
        polygon_points: list[tuple[int, int]], divide: int | None = None
    ) -> np.ndarray:
        """Converts the polygon points to a NumPy array.

        Arguments:
            polygon_points (list[tuple[int, int]]): The polygon points.
            divide (int, optional): The number to divide the points by. Defaults to None.

        Returns:
            np.array: The NumPy array of the polygon points.
        """
        array = np.array(polygon_points, dtype=np.int32).reshape((-1, 1, 2))
        if divide:
            return array // divide
        return array

    @staticmethod
    def cut_out_np(
        image: np.ndarray, half_size: int, set_zeros: bool = False, return_cutout: bool = False
    ) -> np.ndarray:
        """Cuts out a square from the center of the image.

        Arguments:
            image (np.ndarray): The image.
            half_size (int): The half size of the square.
            set_zeros (bool, optional): Whether to set the cutout to zeros. Defaults to False.
            return_cutout (bool, optional): Whether to return the cutout. Defaults to False.

        Returns:
            np.ndarray: The image with the cutout or the cutout itself.
        """
        x1, x2, y1, y2 = ImageComponent._center_square_bounds(image.shape, half_size)

        if return_cutout:
            return image[x1:x2, y1:y2]

        if set_zeros:
            image[x1:x2, y1:y2] = 0

        return image

    @staticmethod
    def subtract_by_mask(
        image: np.ndarray,
        image_mask: np.ndarray,
        subtract_by: int,
        mask_by: int = 255,
        erode_kernel: int | None = 3,
        erode_iter: int | None = 1,
        flatten_to: int | None = None,
    ) -> np.ndarray:
        """Subtracts a value from the image where the mask is equal to the mask by value.

        Arguments:
            image (np.ndarray): The image.
            image_mask (np.ndarray): The mask.
            subtract_by (int): The value to subtract by.
            mask_by (int, optional): The value to mask by. Defaults to 255.
            erode_kernel (int, optional): The kernel size for the erosion. Defaults to 3.
            erode_iter (int, optional): The number of iterations for the erosion. Defaults to 1.
            flatten_to_mean (bool, optional): Whether to flatten the image to the mean value.

        Returns:
            np.ndarray: The image with the subtracted value.
        """
        mask = image_mask == mask_by
        if erode_kernel and erode_iter:
            mask = cv2.erode(
                mask.astype(np.uint8),
                np.ones((erode_kernel, erode_kernel), np.uint8),
                iterations=erode_iter,
            ).astype(bool)

        image[mask] = image[mask] - subtract_by

        if flatten_to:
            image[mask] = flatten_to

        return image

    @staticmethod
    def resize_to_preview(image_path: str, save_path: str) -> None:
        """Resizes an image to the preview size.

        Arguments:
            image_path (str): The path to the image.
            save_path (str): The path to save the resized image.
        """
        if not os.path.isfile(image_path):
            return

        image = cv2.imread(image_path)
        if image is None:
            return

        if (
            image.shape[0] > Parameters.PREVIEW_MAXIMUM_SIZE
            or image.shape[1] > Parameters.PREVIEW_MAXIMUM_SIZE
        ):
            image = cv2.resize(
                image, (Parameters.PREVIEW_MAXIMUM_SIZE, Parameters.PREVIEW_MAXIMUM_SIZE)
            )

        cv2.imwrite(save_path, image)

    @staticmethod
    def transfer_border(src_image: np.ndarray, dst_image: np.ndarray | None, border: int) -> None:
        """Transfers the border of the source image to the destination image.

        Arguments:
            src_image (np.ndarray): The source image.
            dst_image (np.ndarray, optional): The destination image.
            border (int): The border size.
        """
        borders = [
            (slice(None, border), slice(None)),
            (slice(None), slice(-border, None)),
            (slice(-border, None), slice(None)),
            (slice(None), slice(None, border)),
        ]

        for row_slice, col_slice in borders:
            border_slice = (row_slice, col_slice)
            if dst_image is not None:
                dst_image[border_slice][src_image[border_slice] != 0] = 255
            src_image[border_slice] = 0

    def apply_blur(
        self, data: np.ndarray, blur_radius: int, sigma_x: int = 10, sigma_y: int = 10
    ) -> np.ndarray:
        """Apply blur to DEM data.

        Arguments:
            data (np.ndarray): DEM data.
            blur_radius (int): Radius of the blur.
            sigma_x (int, optional): Standard deviation in X direction. Defaults to 10.
            sigma_y (int, optional): Standard deviation in Y direction. Defaults to 10.

        Returns:
            np.ndarray: Blurred DEM data.
        """
        if blur_radius == 0:
            return data

        blurred_data = cv2.GaussianBlur(
            data, (blur_radius, blur_radius), sigmaX=sigma_x, sigmaY=sigma_y
        )

        return blurred_data

    def get_blur_radius(self) -> int:
        """Get the blur radius from the DEM settings.

        Returns:
            int: The blur radius.
        """
        blur_radius = self.map.dem_settings.blur_radius
        if blur_radius is None or blur_radius <= 0:
            # We'll disable blur if the radius is 0 or negative.
            blur_radius = 0
        elif blur_radius % 2 == 0:
            blur_radius += 1
        return blur_radius

    def blur_by_mask(self, data: np.ndarray, mask: np.ndarray, blur_radius: int = 3) -> np.ndarray:
        """Blurs the provided image only where the mask is set.

        Arguments:
            data (np.ndarray): The image data to be blurred.
            mask (np.ndarray): The mask where the blur should be applied.

        Returns:
            np.ndarray: The image with the blur applied according to the mask.
        """
        self._validate_same_spatial_shape(data, mask)

        # Create a blurred version of the data
        blurred_data = cv2.GaussianBlur(data, (blur_radius, blur_radius), sigmaX=10)

        # Combine the blurred data with the original data using the mask
        result = np.where(mask == 255, blurred_data, data)

        return result

    def blur_edges_by_mask(
        self,
        data: np.ndarray,
        mask: np.ndarray,
        bigger_kernel: int = 3,
        smaller_kernel: int = 1,
        iterations: int = 1,
    ) -> np.ndarray:
        """Blurs the edges of the edge region where changes were made by mask earlier.
        Creates a slightly bigger mask, a slightly smaller mask, subtract them
        and obtains the mask for the edges.
        Then applies blur to the image data only where the mask is set.

        Arguments:
            data (np.ndarray): The image data to be blurred.
            mask (np.ndarray): The mask where changes were made.
            blur_radius (int): The radius of the blur.

        Returns:
            np.ndarray: The image with the edges blurred according to the mask.
        """
        self._validate_same_spatial_shape(data, mask)

        bigger_mask = cv2.dilate(
            mask, np.ones((bigger_kernel, bigger_kernel), np.uint8), iterations=iterations
        )
        smaller_mask = cv2.erode(
            mask, np.ones((smaller_kernel, smaller_kernel), np.uint8), iterations=iterations
        )

        edge_mask = cv2.subtract(bigger_mask, smaller_mask)

        return self.blur_by_mask(data, edge_mask)

    @staticmethod
    def convert_png_to_dds(input_png_path: str, output_dds_path: str):
        """Convert a PNG file to DDS format.

        Arguments:
            input_png_path (str): Path to input PNG file
            output_dds_path (str): Path for output DDS file

        Raises:
            FileNotFoundError: If the input PNG file does not exist.
            RuntimeError: If the DDS conversion fails.
        """
        if not os.path.exists(input_png_path):
            raise FileNotFoundError(f"Input PNG file not found: {input_png_path}")

        try:
            ImageComponent.convert_png_to_dds_texconv(input_png_path, output_dds_path)
        except Exception:
            ImageComponent.convert_png_to_dds_pil(input_png_path, output_dds_path)

    @staticmethod
    def convert_png_to_dds_pil(input_png_path: str, output_dds_path: str):
        """Convert a PNG file to DDS format using PIL

        Arguments:
            input_png_path (str): Path to input PNG file
            output_dds_path (str): Path for output DDS file

        Raises:
            RuntimeError: If the DDS conversion fails.
        """
        try:
            ImageFile.LOAD_TRUNCATED_IMAGES = True

            with Image.open(input_png_path) as img:
                # Convert to RGB if needed (DDS works better with RGB)
                if img.mode == "RGBA":
                    # Create RGB version on white background
                    rgb_img = Image.new("RGB", img.size, (255, 255, 255))
                    rgb_img.paste(img, mask=img.split()[-1])  # Use alpha as mask
                    img = rgb_img  # type: ignore
                elif img.mode != "RGB":
                    img = img.convert("RGB")  # type: ignore

                img.save(output_dds_path, format="DDS")
        except Exception as e:
            raise RuntimeError(f"DDS conversion failed: {e}")

    @staticmethod
    def convert_png_to_dds_texconv(input_png_path: str, output_dds_path: str):
        """Convert a PNG file to DDS format using texconv

        Arguments:
            input_png_path (str): Path to input PNG file
            output_dds_path (str): Path for output DDS file

        Raises:
            RuntimeError: If the DDS conversion fails.
        """
        texconv_path = Paths.get_texconv_executable_path()
        if texconv_path is None:
            raise RuntimeError("texconv executable not found.")

        output_dir = os.path.dirname(os.path.abspath(output_dds_path))
        os.makedirs(output_dir, exist_ok=True)

        cmd = [texconv_path, "-f", "BC1_UNORM", "-m", "1", "-y", "-o", output_dir, input_png_path]

        # PyInstaller windowed apps have no console: stdin must be DEVNULL and on Windows
        # we suppress any new console window so texconv doesn't open one of its own.
        run_kwargs: dict = {
            "stdin": subprocess.DEVNULL,
            "capture_output": True,
            "text": True,
        }
        if sys.platform == "win32":
            run_kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW  # type: ignore[attr-defined]

        result = subprocess.run(cmd, **run_kwargs)  # pylint: disable=subprocess-run-check

        if result.returncode != 0:
            raise RuntimeError(
                f"texconv failed (exit code {result.returncode}). "
                f"stdout: {result.stdout.strip()} | stderr: {result.stderr.strip()}"
            )

        # texconv writes <stem>.dds into the output dir; rename if the caller wants a different name
        produced = os.path.join(
            output_dir,
            os.path.splitext(os.path.basename(input_png_path))[0] + ".dds",
        )
        if os.path.abspath(produced) != os.path.abspath(output_dds_path):
            os.replace(produced, output_dds_path)

    def rotate_image(
        self,
        image_path: str,
        angle: int,
        output_height: int,
        output_width: int,
        output_path: str | None = None,
    ) -> None:
        """Rotates an image by a given angle around its center and cuts out the center to match
        the output size.

        Arguments:
            image_path (str): The path to the image to rotate.
            angle (int): The angle to rotate the image by.
            output_height (int): The height of the output image.
            output_width (int): The width of the output image.
            output_path (str, optional): Output path. Defaults to overwriting input.
        """
        if not os.path.isfile(image_path):
            self.logger.warning("Image %s does not exist", image_path)
            return

        image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
        if image is None:
            self.logger.warning("Image %s could not be read", image_path)
            return

        self.logger.debug("Read image from %s with shape: %s", image_path, image.shape)

        if not output_path:
            output_path = image_path

        height, width = image.shape[:2]
        center = (width // 2, height // 2)

        rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(image, rotation_matrix, (width, height))

        start_x = center[0] - output_width // 2
        start_y = center[1] - output_height // 2
        end_x = start_x + output_width
        end_y = start_y + output_height

        cropped = rotated[start_y:end_y, start_x:end_x]
        cv2.imwrite(output_path, cropped)
