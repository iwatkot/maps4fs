import os

import streamlit as st
import streamlit.components.v1 as components
from osmp import get_bbox, get_center, get_preview
from tools.tool import Tool

from maps4fs.toolbox.dem import get_geo_tiff_bbox, read_geo_tiff

tiff_file = "C:/Users/iwatk/Downloads/Dovre 2011-dtm.tif"
DISTANCE = 500
if not os.path.isfile(tiff_file):
    raise FileNotFoundError(f"File not found: {tiff_file}")


class CropGeotiffTool(Tool):
    title = "Crop Geotiff"
    description = "Crop a GeoTIFF file to a specified size"
    icon = "🏔️"

    def content(self):
        self.html_preview_container = st.empty()

        # Add test button to launch the preview
        if st.button("Get DEM Preview"):
            self.get_preview()

    def get_preview(self):
        src = read_geo_tiff(tiff_file)

        full_bbox = get_geo_tiff_bbox(src)

        center = get_center(full_bbox)
        cropped_bbox = get_bbox(center, DISTANCE)

        bboxes = [cropped_bbox, full_bbox]
        html_file = get_preview(bboxes)

        with self.html_preview_container:
            st.cache_data.clear()
            components.html(open(html_file).read(), height=400)
