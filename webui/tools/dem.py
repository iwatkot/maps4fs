import os

import streamlit as st
import streamlit.components.v1 as components
from config import INPUT_DIRECTORY, is_on_community_server
from osmp import get_bbox, get_center, get_preview
from tools.tool import Tool

from maps4fs.toolbox.dem import extract_roi, get_geo_tiff_bbox, read_geo_tiff

DEFAULT_SIZE = 2048
COMMUNITY_SIZE_LIMIT = 200


class GeoTIFFWindowingTool(Tool):
    title = "GeoTIFF Windowing"
    description = "Extract region of interest from GeoTIFF file using given center point and size."
    icon = "🪟"

    save_path = None
    full_bbox = None
    full_bbox_center = None
    download_path = None

    def content(self):
        if "windowed" not in st.session_state:
            st.session_state.windowed = False
        uploaded_file = st.file_uploader("Upload a GeoTIFF file", type=["tif", "tiff"])
        self.left_column, self.right_column = st.columns(2)
        with self.right_column:
            self.html_preview_container = st.empty()

        if uploaded_file is not None:
            if not uploaded_file.name.lower().endswith((".tif", ".tiff")):
                st.error("Please upload correct GeoTIFF file.")
                return

            size_in_mb = round(uploaded_file.size / 1024 / 1024, 2)

            if True and size_in_mb > COMMUNITY_SIZE_LIMIT:
                st.error(
                    f"The application is launched on Streamlit community server "
                    f"and file exceeds the size limit of {COMMUNITY_SIZE_LIMIT} MB.  \n"
                    f"Please run the application locally to process larger files."
                    "Learn more about the Docker version in the repo's "
                    "[README](https://github.com/iwatkot/maps4fs?tab=readme-ov-file#option-2-docker-version)."
                )
                return

            self.save_path = self.get_save_path(uploaded_file.name)
            with open(self.save_path, "wb") as f:
                f.write(uploaded_file.read())
            st.session_state.uploaded = True

            with self.left_column:
                self.read_geo_tiff(self.save_path)
                st.write("Enter latitude and longitude of the center point of the ROI:")

                full_center_lat, full_center_lon = self.full_bbox_center

                self.lat_lon_input = st.text_input(
                    "Latitude and Longitude",
                    f"{full_center_lat}, {full_center_lon}",
                    label_visibility="collapsed",
                    on_change=self.get_preview,
                )

                st.write("Enter the size of the ROI in meters:")
                self.size_input = st.number_input(
                    "Size",
                    value=DEFAULT_SIZE,
                    label_visibility="collapsed",
                    on_change=self.get_preview,
                )

                self.get_preview()

                if st.button("Extract ROI", icon="▶️"):
                    self.window()

        if st.session_state.windowed:
            with open(self.download_path, "rb") as f:
                st.download_button(
                    label="Download",
                    data=f,
                    file_name=f"{self.download_path.split('/')[-1]}",
                    mime="application/zip",
                    icon="📥",
                )

            st.session_state.windowed = False

    def window(self):
        try:
            roi_center = self.lat_lon
        except ValueError:
            st.error("Please enter the latitude and longitude in the correct format.")
            return

        roi_size = self.size_input
        roi_bbox = get_bbox(roi_center, roi_size)
        self.download_path = extract_roi(self.save_path, roi_bbox)
        st.session_state.windowed = True

    def read_geo_tiff(self, file_path: str) -> None:
        src = read_geo_tiff(file_path)

        st.write("Original CRS:", src.crs)
        st.write("Bounds (original CRS):", src.bounds)

        left, bottom, right, top = src.bounds
        st.write("Height (original CRS):", top - bottom)
        st.write("Width (original CRS):", right - left)

        self.full_bbox = get_geo_tiff_bbox(src)
        self.full_bbox_center = get_center(self.full_bbox)

        st.write("Bounding box (north, south, east, west):", self.full_bbox)
        st.write("Center (latitude, longitude):", self.full_bbox_center)

    def get_save_path(self, file_name: str) -> str:
        return os.path.join(INPUT_DIRECTORY, file_name)

    def get_preview(self):
        try:
            roi_center = self.lat_lon
        except ValueError:
            st.error("Please enter the latitude and longitude in the correct format.")
            return

        roi_size = self.size_input
        roi_bbox = get_bbox(roi_center, roi_size)
        bboxes = [roi_bbox, self.full_bbox]

        html_file = get_preview(bboxes)

        with self.html_preview_container:
            components.html(open(html_file).read(), height=600)

    @property
    def lat_lon(self) -> tuple[float, float]:
        """Get the latitude and longitude of the center point of the map.

        Returns:
            tuple[float, float]: The latitude and longitude of the center point of the map.
        """
        return tuple(map(float, self.lat_lon_input.split(",")))
