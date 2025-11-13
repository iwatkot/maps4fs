"""Base class for all components that primarily used to work with images."""

import os

import cv2
import numpy as np
from PIL import Image, ImageFile

from maps4fs.generator.component.base.component import Component
from maps4fs.generator.settings import Parameters


class ImageComponent(Component):
    """Base class for all components that primarily used to work with images."""

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
        center = (image.shape[0] // 2, image.shape[1] // 2)
        x1 = center[0] - half_size
        x2 = center[0] + half_size
        y1 = center[1] - half_size
        y2 = center[1] + half_size

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
        if data.shape[:2] != mask.shape[:2]:
            raise ValueError("Data and mask must have the same dimensions.")

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
        if data.shape[:2] != mask.shape[:2]:
            raise ValueError("Data and mask must have the same dimensions.")

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
        """Convert a PNG file to DDS format using PIL

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
            ImageFile.LOAD_TRUNCATED_IMAGES = True

            with Image.open(input_png_path) as img:
                # Convert to RGB if needed (DDS works better with RGB)
                if img.mode == "RGBA":
                    # Create RGB version on white background
                    rgb_img = Image.new("RGB", img.size, (255, 255, 255))
                    rgb_img.paste(img, mask=img.split()[-1])  # Use alpha as mask
                    img = rgb_img
                elif img.mode != "RGB":
                    img = img.convert("RGB")

                img.save(output_dds_path, format="DDS")
        except Exception as e:
            raise RuntimeError(f"DDS conversion failed: {e}")

    @staticmethod
    def get_image_safely(image_path: str) -> np.ndarray | None:
        """Safely gets an image from the provided path.

        Arguments:
            image_path (str): The path to the image.

        Returns:
            np.ndarray | None: The image or None if not found or failed to load.
        """
        if not os.path.isfile(image_path):
            return None

        try:
            image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
            return image
        except Exception:
            return None

    def get_dem_image_with_fallback(
        self, start_at: int = 0, end_on: int | None = None
    ) -> np.ndarray | None:
        """Gets the DEM image using fallback mechanism.

        Arguments:
            start_at (int, optional): The index to start checking from. Defaults to 0.
            end_on (int | None, optional): The index to end checking on. Defaults to None (end of
                the list, including the last item).

        Returns:
            np.ndarray | None: The DEM image or None if not found.
        """
        background_component = self.map.get_background_component()
        if not background_component:
            self.logger.warning("Background component not found.")
            return None

        items = background_component.not_resized_paths()
        result = self.get_item_with_fallback(
            items,
            self.get_image_safely,
            start_at,
            end_on,
        )
        return result
