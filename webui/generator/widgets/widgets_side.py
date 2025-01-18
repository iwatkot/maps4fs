import os
from datetime import datetime

import config
import streamlit as st
from generator.widgets.widget import Widget
from templates import Messages

import maps4fs as mfs


class SideTitleWidget(Widget):
    def content(self):
        st.title("Expert Settings")
        st.write(Messages.EXPERT_SETTINGS_INFO)


class EnableDebug(Widget):
    def content(self):
        if not self.ui.public:
            enable_debug = st.checkbox("Enable debug logs", key="debug_logs")
        if enable_debug:
            self.ui.logger = mfs.Logger(level="DEBUG", to_file=False)
        else:
            self.ui.logger = mfs.Logger(level="INFO", to_file=False)


class CustomOSM(Widget):
    def content(self):
        self.ui.custom_osm_enabled = st.checkbox(
            "Upload custom OSM file",
            value=False,
            key="custom_osm_enabled",
        )
        if self.ui.custom_osm_enabled:
            st.info(Messages.CUSTOM_OSM_INFO)

            uploaded_file = st.file_uploader("Choose a file", type=["osm"])
            if uploaded_file is not None:
                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                self.ui.custom_osm_path = os.path.join(
                    config.INPUT_DIRECTORY, f"custom_osm_{timestamp}.osm"
                )
                with open(self.ui.custom_osm_path, "wb") as f:
                    f.write(uploaded_file.read())
                st.success(f"Custom OSM file uploaded: {uploaded_file.name}")


side_widgets = [SideTitleWidget, EnableDebug, CustomOSM]
