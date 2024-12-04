import os

import streamlit as st
import streamlit.components.v1 as components
from osmp import get_bbox, get_center, get_preview

from maps4fs.toolbox.dem import get_geo_tiff_bbox, read_geo_tiff

tiff_file = "C:/Users/iwatk/Downloads/Dovre 2011-dtm.tif"
DISTANCE = 500
if not os.path.isfile(tiff_file):
    raise FileNotFoundError(f"File not found: {tiff_file}")


class DemUI:
    def __init__(self) -> None:
        src = read_geo_tiff(tiff_file)

        full_bbox = get_geo_tiff_bbox(src)

        center = get_center(full_bbox)
        cropped_bbox = get_bbox(center, DISTANCE)

        bboxes = [cropped_bbox, full_bbox]
        html_file = get_preview(bboxes)

        left_column, right_column = st.columns(2)
        with left_column:
            components.html(open(html_file).read(), height=400)
