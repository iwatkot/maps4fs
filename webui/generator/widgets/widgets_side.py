import json
import os
from datetime import datetime

import config
import streamlit as st
from generator.widgets.widget import Widget
from templates import Messages

import maps4fs as mfs


class SideTitle(Widget):
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


class RawConfiguration(Widget):
    def content(self):
        self.ui.expert_mode = st.checkbox("Show raw configuration", key="expert_mode")
        if self.ui.expert_mode:
            st.info(Messages.EXPERT_MODE_INFO)

            self.ui.raw_config = st.text_area(
                "Raw configuration",
                value=json.dumps(self.ui.settings, indent=2),
                height=600,
                label_visibility="collapsed",
            )


class CustomSchemas(Widget):
    def content(self):
        self.ui.custom_schemas = False
        self.ui.texture_schema_input = None
        self.ui.tree_schema_input = None

        if self.ui.game_code == "FS25":
            self.ui.custom_schemas = st.checkbox("Show schemas", value=False, key="custom_schemas")

            if self.ui.custom_schemas:
                self.ui.logger.debug("Custom schemas are enabled.")

                with st.expander("Texture custom schema"):
                    st.write(Messages.TEXTURE_SCHEMA_INFO)

                    with open(config.FS25_TEXTURE_SCHEMA_PATH, "r", encoding="utf-8") as f:
                        schema = json.load(f)

                    self.ui.texture_schema_input = st.text_area(
                        "Texture Schema",
                        value=json.dumps(schema, indent=2),
                        height=600,
                        label_visibility="collapsed",
                    )

                with st.expander("Tree custom schema"):
                    st.write(Messages.TEXTURE_SCHEMA_INFO)

                    with open(config.FS25_TREE_SCHEMA_PATH, "r", encoding="utf-8") as f:
                        schema = json.load(f)

                    self.ui.tree_schema_input = st.text_area(
                        "Tree Schema",
                        value=json.dumps(schema, indent=2),
                        height=600,
                        label_visibility="collapsed",
                    )


class CustomTemplate(Widget):
    def content(self):
        self.ui.custom_template = st.checkbox(
            "Upload custom template", value=False, key="custom_template"
        )

        if self.ui.custom_template:
            self.ui.logger.debug("Custom template is enabled.")
            st.info(Messages.CUSTOM_TEMPLATE_INFO)

            uploaded_template = st.file_uploader("Upload a zip file", type=["zip"])
            if uploaded_template is not None:
                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                self.ui.custom_template_path = os.path.join(
                    config.INPUT_DIRECTORY, f"custom_template_{timestamp}.zip"
                )
                with open(self.ui.custom_template_path, "wb") as f:
                    f.write(uploaded_template.read())
                st.success(f"Custom template uploaded: {uploaded_template.name}")


class CustomBackground(Widget):
    def content(self):
        self.ui.custom_background = st.checkbox(
            "Upload custom background", value=False, key="custom_background"
        )

        if self.ui.custom_background:
            st.info(Messages.CUSTOM_BACKGROUND_INFO)

            uploaded_file = st.file_uploader("Choose a file", type=["png"])
            if uploaded_file is not None:
                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                self.ui.custom_background_path = os.path.join(
                    config.INPUT_DIRECTORY, f"custom_background_{timestamp}.png"
                )
                with open(self.ui.custom_background_path, "wb") as f:
                    f.write(uploaded_file.read())
                st.success(f"Custom background uploaded: {uploaded_file.name}")


class ManageCache(Widget):
    def content(self):
        if not self.ui.public:
            manage_cache = st.checkbox("Manage cache", value=False, key="manage_cache")
            if manage_cache:
                temp_size = config.get_temp_size()
                st.write(Messages.CACHE_INFO)
                st.write(f"Cache size: {round(temp_size, 2)} MB")
                if temp_size > 10:
                    if st.button("Clean cache"):
                        config.clean_temp()
                        st.success("Cache cleaned.")


active_widgets = [
    SideTitle,
    EnableDebug,
    CustomOSM,
    RawConfiguration,
    CustomSchemas,
    CustomTemplate,
    CustomBackground,
    ManageCache,
]
