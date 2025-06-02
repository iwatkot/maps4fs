import os

import cv2
import numpy as np
import streamlit as st
from config import INPUT_DIRECTORY, is_on_community_server, is_public
from templates import Messages
from tools.tool import Tool

from maps4fs.toolbox.background import plane_from_np

DEFAULT_SIZE = 2048


class ConvertImageToObj(Tool):
    title = "Convert image to obj model"
    description = (
        "This tool allows you to convert an image to a 3D model in the *.obj format.  \n"
        "Note: this tool works only with single-channel images with unsigned integer data type."
    )
    icon = "🏞️"

    save_path = None
    download_path = None

    def content(self):
        st.warning(
            "DEPRECATION WARNING: This tool is deprecated and will be removed in maps4fs 2.0. "
            "If you want to continue using this tool, do not update maps4fs to 2.0."
        )
        if is_on_community_server() or is_public():
            st.warning(Messages.TOOL_LOCAL)
            return
        if "convertedtoobj" not in st.session_state:
            st.session_state.convertedtoobj = False
        uploaded_file = st.file_uploader(
            "Upload a single channel image", type=["tif", "tiff", "png"]
        )

        if uploaded_file is not None:
            self.save_path = self.get_save_path(uploaded_file.name)
            with open(self.save_path, "wb") as f:
                f.write(uploaded_file.read())

            base_name = os.path.basename(self.save_path).split(".")[0]
            output_name = f"{base_name}.obj"
            self.download_path = self.get_save_path(output_name)

            # Inputs for resize_factor (e.g. 0.25) and simplify_factor (e.g. 10)
            st.write("Enter the resize factor. Higher values will result bigger model.")
            self.resize_factor = st.number_input(
                "Resize factor",
                min_value=0.05,
                max_value=5.0,
                value=0.25,
                step=0.05,
            )

            st.write("Enter the simplify factor. Higher values will result less detailed model.")
            self.simplify_factor = st.number_input(
                "Simplify factor",
                min_value=1,
                max_value=100,
                value=10,
                step=1,
            )
            if st.button("Convert to obj", icon="▶️"):
                try:
                    image_np = self.image_to_np(self.save_path)
                except ValueError as e:
                    st.error(str(e))
                    return

                try:
                    plane_from_np(
                        image_np,
                        self.resize_factor,
                        self.simplify_factor,
                        self.download_path,
                    )
                    st.session_state.convertedtoobj = True
                except Exception as e:
                    st.error(str(e))
                    return

        if st.session_state.convertedtoobj:
            with open(self.download_path, "rb") as f:
                st.download_button(
                    label="Download",
                    data=f,
                    file_name=f"{self.download_path.split('/')[-1]}",
                    mime="application/zip",
                    icon="📥",
                )

            st.session_state.convertedtoobj = False

    def get_save_path(self, file_name: str) -> str:
        """Get the path to save the file in the input directory.

        Arguments:
            file_name {str} -- The name of the  file.

        Returns:
            str -- The path to save the file in the input directory.
        """
        return os.path.join(INPUT_DIRECTORY, file_name)

    def image_to_np(self, file_path: str) -> np.ndarray:
        """Convert an image to a NumPy array.

        Arguments:
            file_path {str} -- The path to the image file.

        Raises:
            ValueError: If the image is not single-channel or not unsigned integer
                (any bit depth).

        Returns:
            np.ndarray -- The NumPy array representation of the image.
        """
        array = cv2.imread(file_path, cv2.IMREAD_UNCHANGED)

        # Check if the image is single-channel and unsigned integer (any bit depth).
        if len(array.shape) != 2:
            raise ValueError("The image must be single-channel.")
        if "uint" not in array.dtype.name:
            raise ValueError("The image must be unsigned integer.")

        return array
