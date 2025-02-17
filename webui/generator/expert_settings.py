import json
import os
from datetime import datetime

import config
import streamlit as st
from generator.base_component import BaseComponent
from templates import Messages

import maps4fs as mfs


class ExpertSettings(BaseComponent):
    def __init__(self, public: bool, **kwargs):
        super().__init__(public, **kwargs)
        self.game_code = kwargs["game_code"]
        self.settings = kwargs["settings"]
        self.logger = mfs.Logger(level="INFO", to_file=False)

        self.custom_background_path = None
        self.expert_mode = False
        self.raw_config = None

        self.custom_osm_path = None
        self.custom_template_path = None

        with st.sidebar:
            st.title("Expert Settings")
            st.write(Messages.EXPERT_SETTINGS_INFO)

            if not self.public:
                enable_debug = st.checkbox("Enable debug logs", key="debug_logs")
                if enable_debug:
                    self.logger = mfs.Logger(level="DEBUG", to_file=False)
                else:
                    self.logger = mfs.Logger(level="INFO", to_file=False)

            self.custom_osm_enabled = st.checkbox(
                "Upload custom OSM file",
                value=False,
                key="custom_osm_enabled",
            )
            if self.custom_osm_enabled:
                st.info(Messages.CUSTOM_OSM_INFO)

                uploaded_file = st.file_uploader("Choose a file", type=["osm"])
                if uploaded_file is not None:
                    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                    self.custom_osm_path = os.path.join(
                        config.INPUT_DIRECTORY, f"custom_osm_{timestamp}.osm"
                    )
                    with open(self.custom_osm_path, "wb") as f:
                        f.write(uploaded_file.read())
                    st.success(f"Custom OSM file uploaded: {uploaded_file.name}")
            self.expert_mode = st.checkbox("Show raw configuration", key="expert_mode")
            if self.expert_mode:
                st.info(Messages.EXPERT_MODE_INFO)

                self.raw_config = st.text_area(
                    "Raw configuration",
                    value=json.dumps(self.settings, indent=2),
                    height=600,
                    label_visibility="collapsed",
                )

            self.custom_schemas = False
            self.texture_schema_input = None
            self.tree_schema_input = None

            self.custom_schemas = st.checkbox("Show schemas", value=False, key="custom_schemas")
            if self.custom_schemas:
                with st.expander("Texture custom schema"):
                    st.write(Messages.TEXTURE_SCHEMA_INFO)

                    schema = config.get_schema(self.game_code, "texture")

                    self.texture_schema_input = st.text_area(
                        "Texture Schema",
                        value=json.dumps(schema, indent=2),
                        height=600,
                        label_visibility="collapsed",
                    )

                if self.game_code == "FS25":
                    with st.expander("Tree custom schema"):
                        st.write(Messages.TEXTURE_SCHEMA_INFO)

                        schema = config.get_schema(self.game_code, "tree")

                        self.tree_schema_input = st.text_area(
                            "Tree Schema",
                            value=json.dumps(schema, indent=2),
                            height=600,
                            label_visibility="collapsed",
                        )

            self.custom_template = st.checkbox(
                "Upload custom template", value=False, key="custom_template"
            )

            if self.custom_template:
                st.info(Messages.CUSTOM_TEMPLATE_INFO)

                uploaded_template = st.file_uploader("Upload a zip file", type=["zip"])
                if uploaded_template is not None:
                    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                    self.custom_template_path = os.path.join(
                        config.INPUT_DIRECTORY, f"custom_template_{timestamp}.zip"
                    )
                    with open(self.custom_template_path, "wb") as f:
                        f.write(uploaded_template.read())
                    st.success(f"Custom template uploaded: {uploaded_template.name}")

            self.custom_background = st.checkbox(
                "Upload custom background", value=False, key="custom_background"
            )

            if self.custom_background:
                st.info(Messages.CUSTOM_BACKGROUND_INFO)

                uploaded_file = st.file_uploader("Choose a file", type=["png"])
                if uploaded_file is not None:
                    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                    self.custom_background_path = os.path.join(
                        config.INPUT_DIRECTORY, f"custom_background_{timestamp}.png"
                    )
                    with open(self.custom_background_path, "wb") as f:
                        f.write(uploaded_file.read())
                    st.success(f"Custom background uploaded: {uploaded_file.name}")

            if not self.public:
                manage_cache = st.checkbox("Manage cache", value=False, key="manage_cache")
                if manage_cache:
                    temp_size = config.get_temp_size()
                    st.write(Messages.CACHE_INFO)
                    st.write(f"Cache size: {round(temp_size, 2)} MB")
                    if temp_size > 10:
                        if st.button("Clean cache"):
                            config.clean_temp()
                            st.success("Cache cleaned.")
