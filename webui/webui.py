import os
from datetime import datetime

import config
import streamlit as st
from PIL import Image

import maps4fs as mfs
from maps4fs.generator.dem import DEFAULT_BLUR_RADIUS, DEFAULT_MULTIPLIER


class Maps4FS:
    def __init__(self):
        self.download_path = None
        self.logger = mfs.Logger(__name__, level="DEBUG")

        st.set_page_config(page_title="Maps4FS", page_icon="🚜")
        st.title("Maps4FS")
        st.write("Generate map templates for Farming Simulator from real places.")

        st.markdown("---")

        if "generated" not in st.session_state:
            st.session_state.generated = False

        self.add_widgets()

    def add_widgets(self) -> None:
        # Game selection (FS22 or FS25).
        st.write("Select the game for which you want to generate the map:")
        self.game_code_input = st.selectbox(
            "Game",
            options=[
                "FS25",
                "FS22",
            ],
            key="game_code",
            label_visibility="collapsed",
        )

        # Latitude and longitude input.
        st.write("Enter latitude and longitude of the center point of the map:")
        self.lat_lon_input = st.text_input(
            "Latitude and Longitude",
            "45.26, 19.80",
            key="lat_lon",
            label_visibility="collapsed",
        )

        # Map size selection.
        st.write("Select size of the map:")
        self.map_size_input = st.selectbox(
            "Map Size (meters)",
            options=["2048x2048", "4096x4096", "8192x8192", "16384x16384", "Custom"],
            label_visibility="collapsed",
        )

        if self.map_size_input == "Custom":
            st.warning(
                "This feature is for advanced users only, you need to know exact correct values, "
                "otherwise the Giants Editor will crash on opening the file. Do not use it, "
                "if you are not sure what you are doing."
            )
            st.write("Enter map height (meters):")
            map_height_input = st.number_input(
                "Height (meters)", 1, 16384, 2048, key="map_height", label_visibility="collapsed"
            )

            st.write("Enter map width (meters):")
            map_width_input = st.number_input(
                "Width (meters)", 1, 16384, 2048, key="map_width", label_visibility="collapsed"
            )

            self.map_size_input = f"{map_height_input}x{map_width_input}"

        # Add checkbox for advanced settings.
        st.write("Advanced settings (do not change if you are not sure):")
        self.advanced_settings = st.checkbox("Show advanced settings", key="advanced_settings")
        self.multiplier_input = DEFAULT_MULTIPLIER
        self.blur_radius_input = DEFAULT_BLUR_RADIUS

        if self.advanced_settings:
            # Show multiplier and blur radius inputs.
            st.write("Enter multiplier for the DEM (elevation) map:")
            self.multiplier_input = st.number_input(
                "Multiplier",
                value=DEFAULT_MULTIPLIER,
                min_value=0,
                max_value=10000,
                key="multiplier",
                label_visibility="collapsed",
            )

            st.write("Enter blur radius for the DEM (elevation) map:")
            self.blur_radius_input = st.number_input(
                "Blur Radius",
                value=DEFAULT_BLUR_RADIUS,
                min_value=1,
                max_value=300,
                key="blur_radius",
                label_visibility="collapsed",
            )

        # Add an empty container for status messages.
        self.status_container = st.empty()

        # Add an empty container for buttons.
        self.buttons_container = st.empty()

        # Add an empty container for preview image.
        self.preview_container = st.container()

        # Generate button.
        with self.buttons_container:
            if st.button("Generate", key="launch_btn"):
                self.generate_map()

        # Download button.
        if st.session_state.generated:
            with open(self.download_path, "rb") as f:
                with self.buttons_container:
                    st.download_button(
                        label="Download",
                        data=f,
                        file_name=f"{self.download_path.split('/')[-1]}",
                        mime="application/zip",
                    )

            st.session_state.generated = False

    def generate_map(self) -> None:
        # Read game code from the input widget and create a game object.
        game_code = self.game_code_input
        game = mfs.Game.from_code(game_code)

        try:
            # Read latitude and longitude from the input widget
            # and try to convert them to float values.
            lat, lon = map(float, self.lat_lon_input.split(","))
        except ValueError:
            st.error("Invalid latitude and longitude!")
            return

        # Prepare a tuple with the coordinates of the center point of the map.
        coordinates = (lat, lon)

        # Read map size from the input widget.
        try:
            height, width = map(int, self.map_size_input.split("x"))
        except ValueError:
            st.error("Invalid map size!")
            return

        # Session name will be used for a directory name as well as a zip file name.
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        session_name = f"{game.code}_{timestamp}"

        # st.info("Started map generation...", icon="⏳")
        self.status_container.info("Started map generation...", icon="⏳")
        map_directory = os.path.join(config.MAPS_DIRECTORY, session_name)
        os.makedirs(map_directory, exist_ok=True)

        # Create an instance of the Map class and generate the map.
        mp = mfs.Map(
            game,
            coordinates,
            height,
            width,
            map_directory,
            logger=self.logger,
            multiplier=self.multiplier_input,
            blur_radius=self.blur_radius_input,
        )
        mp.generate()

        # Create a preview image.
        self.show_preview(mp)

        # Pack the generated map into a zip archive.
        archive_path = mp.pack(os.path.join(config.ARCHIVES_DIRECTORY, session_name))

        self.download_path = archive_path

        st.session_state.generated = True

        # st.success("Map generation completed!", icon="✅")
        self.status_container.success("Map generation completed!", icon="✅")

    def show_preview(self, mp: mfs.Map) -> None:
        # Get a list of all preview images.
        full_preview_paths = mp.previews()
        preview_captions = [
            "Preview of the texture map.",
            "Preview of the DEM (elevation) map in grayscale (original).",
            "Preview of the DEM (elevation) map in colored mode (only for demonstration).",
        ]
        if not full_preview_paths:
            return

        with self.preview_container:
            for caption, full_preview_path in zip(preview_captions, full_preview_paths):
                if not os.path.isfile(full_preview_path):
                    continue
                try:
                    image = Image.open(full_preview_path)
                    st.image(image, use_container_width=True, caption=caption)
                except Exception:
                    continue


ui = Maps4FS()
