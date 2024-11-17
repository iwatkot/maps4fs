import os
from time import time

import config
import streamlit as st
from PIL import Image

import maps4fs as mfs


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
            options=["FS22"],  # TODO: Return "FS25" when the Giants Editor v10 will be released.
            key="game_code",
            label_visibility="collapsed",
        )

        # Latitude and longitude input.
        st.write("Enter latitude and longitude of the center point of the map:")
        self.lat_lon_input = st.text_input(
            "Latitude and Longitude",
            "45.2602, 19.8086",
            key="lat_lon",
            label_visibility="collapsed",
        )

        # Map size selection.
        st.write("Select size of the map:")
        self.map_size_input = st.selectbox(
            "Map Size",
            options=[
                (2048, "2048 x 2048 meters"),
                (4096, "4096 x 4096 meters"),
                (8192, "8192 x 8192 meters"),
                (16384, "16384 x 16384 meters"),
            ],
            format_func=lambda x: x[1],
            key="size",
            label_visibility="collapsed",
        )

        # Maximum height input.
        st.write("Enter maximum height:")
        self.max_height_input = st.number_input(
            "Maximum Height",
            value=200,
            key="max_height",
            label_visibility="collapsed",
            min_value=10,
            max_value=3000,
        )

        # Blur seed input.
        st.write("Enter blur seed:")
        self.blur_seed_input = st.number_input(
            "Blur Seed",
            value=5,
            key="blur_seed",
            label_visibility="collapsed",
            min_value=1,
            max_value=1000,
        )

        # Add an empty container for status messages.
        self.status_container = st.empty()

        # Add an empty container for buttons.
        self.buttons_container = st.empty()

        # Add an empty container for preview image.
        self.preview_container = st.empty()

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
        game = mfs.Game.from_code(self.game_code_input)

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
        map_size = self.map_size_input[0]
        if not isinstance(map_size, int):
            st.error("Invalid map size!")
            return

        # Distance is half of the map size (from the center to the edge).
        # Maps are always square, so the distance is the same in both directions.
        distance = int(map_size / 2)

        # Max height is a multiplier for calculations relative height.
        max_height = self.max_height_input
        if not isinstance(max_height, int):
            st.error("Invalid maximum height!")
            return

        # Blur seed is used to remove noise in DEM data.
        # Higher values will result in smoother terrain.
        blur_seed = self.blur_seed_input
        if not isinstance(blur_seed, int):
            st.error("Invalid blur seed!")
            return

        # Session name will be used for a directory name as well as a zip file name.
        session_name = str(time()).replace(".", "_")

        # st.info("Started map generation...", icon="⏳")
        self.status_container.info("Started map generation...", icon="⏳")
        map_directory = os.path.join(config.MAPS_DIRECTORY, session_name)
        os.makedirs(map_directory, exist_ok=True)

        # Create an instance of the Map class and generate the map.
        mp = mfs.Map(
            game,
            coordinates,
            distance,
            map_directory,
            blur_seed=blur_seed,
            max_height=max_height,
            logger=self.logger,
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
        if not full_preview_paths:
            return

        # Pick the first image from the list.
        full_previe_path = full_preview_paths[0]
        preview = Image.open(full_previe_path)

        with self.preview_container:
            st.image(preview, caption="Preview of the generated map", use_container_width=True)


ui = Maps4FS()
