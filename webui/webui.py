import os
from datetime import datetime

import config
import osmp
import streamlit as st
import streamlit.components.v1 as components
from PIL import Image

import maps4fs as mfs
from maps4fs.generator.dem import DEFAULT_BLUR_RADIUS, DEFAULT_MULTIPLIER

DEFAULT_LAT = 45.28571409289627
DEFAULT_LON = 20.237433441210115


class Maps4FS:
    """Main class for the Maps4FS web interface.

    Attributes:
        download_path (str): The path to the generated map archive.
        logger (Logger): The logger instance.

    Properties:
        lat_lon (tuple[float, float]): The latitude and longitude of the center point of the map.
        map_size (tuple[int, int]): The size of the map in meters.

    Public methods:
        map_preview: Generate a preview of the map.
        add_right_widgets: Add widgets to the right column.
        add_left_widgets: Add widgets to the left column.
        generate_map: Generate the map.
        get_sesion_name: Generate a session name for the map.
        shorten_coordinate: Shorten a coordinate to a string.
        show_preview: Show the preview of the generated map.
    """

    def __init__(self):
        self.download_path = None
        self.logger = mfs.Logger(__name__, level="DEBUG", to_file=False)

        st.set_page_config(page_title="Maps4FS", page_icon="🚜", layout="wide")
        st.title("Maps4FS")
        st.write("Generate map templates for Farming Simulator from real places.")

        st.info(
            "ℹ️ When opening map first time in the Giants Editor, select **terrain** object, "
            "open **Terrain** tab in the **Attributes** window, scroll down to the end "
            "and press the **Reload material** button.  \n"
            "Otherwise you may (and will) face some glitches."
        )

        st.markdown("---")

        self.left_column, self.right_column = st.columns(2, gap="large")

        if "generated" not in st.session_state:
            st.session_state.generated = False

        with self.right_column:
            self.add_right_widgets()

        with self.left_column:
            self.add_left_widgets()

        self.map_preview()

    @property
    def lat_lon(self) -> tuple[float, float]:
        """Get the latitude and longitude of the center point of the map.

        Returns:
            tuple[float, float]: The latitude and longitude of the center point of the map.
        """
        return tuple(map(float, self.lat_lon_input.split(",")))

    @property
    def map_size(self) -> tuple[int, int]:
        """Get the size of the map in meters.

        Returns:
            tuple[int, int]: The size of the map in meters.
        """
        return tuple(map(int, self.map_size_input.split("x")))

    def map_preview(self) -> None:
        """Generate a preview of the map in the HTML container.
        This method is called when the latitude, longitude, or map size is changed.
        """
        try:
            lat, lon = self.lat_lon
        except ValueError:
            return

        try:
            map_size, _ = self.map_size
        except ValueError:
            return

        self.logger.info(
            "Generating map preview for lat=%s, lon=%s, map_size=%s", lat, lon, map_size
        )

        html_file = osmp.get_preview(lat, lon, map_size)

        with self.html_preview_container:
            components.html(open(html_file).read(), height=300)

    def add_right_widgets(self) -> None:
        """Add widgets to the right column."""
        self.logger.info("Adding widgets to the right column...")
        self.html_preview_container = st.empty()
        self.map_selector_container = st.container()
        self.preview_container = st.container()

    def add_left_widgets(self) -> None:
        """Add widgets to the left column."""
        self.logger.info("Adding widgets to the left column...")

        # Game selection (FS22 or FS25).
        st.write("Select the game for which you want to generate the map:")
        self.game_code = st.selectbox(
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
            f"{DEFAULT_LAT}, {DEFAULT_LON}",
            key="lat_lon",
            label_visibility="collapsed",
            on_change=self.map_preview,
        )

        # Map size selection.
        st.write("Select size of the map:")
        self.map_size_input = st.selectbox(
            "Map Size (meters)",
            options=["2048x2048", "4096x4096", "8192x8192", "16384x16384", "Custom"],
            label_visibility="collapsed",
            on_change=self.map_preview,
        )

        if self.map_size_input == "Custom":
            self.logger.info("Custom map size selected.")

            st.info("ℹ️ Map size can be only a power of 2. For example: 2, 4, ... 2048, 4096, ...")
            st.warning("⚠️ Large map sizes can crash on generation or import in the game.")
            st.write("Enter map size (meters):")
            custom_map_size_input = st.number_input(
                label="Height (meters)",
                min_value=2,
                value=2048,
                key="map_height",
                label_visibility="collapsed",
                on_change=self.map_preview,
            )

            self.map_size_input = f"{custom_map_size_input}x{custom_map_size_input}"

        st.info(
            "ℹ️ Remember to adjust the ***heightScale*** parameter in the Giants Editor to a value "
            "that suits your map. Learn more about it in repo's "
            "[README](https://github.com/iwatkot/maps4fs)."
        )

        self.auto_process = st.checkbox("Use auto preset", value=True, key="auto_process")
        if self.auto_process:
            self.logger.info("Auto preset is enabled.")
            st.info(
                "Auto preset will automatically apply different algorithms to make terrain more "
                "realistic. It's recommended for most cases. If you want to have more control over the "
                "terrain generation, you can disable this option and change the advanced settings."
            )

        self.multiplier_input = DEFAULT_MULTIPLIER
        self.blur_radius_input = DEFAULT_BLUR_RADIUS

        if not self.auto_process:
            self.logger.info("Auto preset is disabled.")

            st.info(
                "Auto preset is disabled. In this case you probably receive a full black DEM "
                "image file. But it is NOT EMPTY. Dem image value range is from 0 to 65535, "
                "while on Earth the highest point is 8848 meters. So, unless you are not "
                "working with map for Everest, you probably can't see anything on the DEM image "
                "by eye, because it is too dark. You can use the "
                "multiplier option from Advanced settings to make the terrain more pronounced."
            )
            # Add checkbox for advanced settings.
            st.write("Advanced settings (do not change if you are not sure):")
            self.advanced_settings = st.checkbox("Show advanced settings", key="advanced_settings")

            if self.advanced_settings:
                self.logger.info("Advanced settings are enabled.")

                st.warning("⚠️ Changing these settings can lead to unexpected results.")
                st.info(
                    "ℹ️ [DEM] is for settings related to the Digital Elevation Model (elevation map). "
                    "This file is used to generate the terrain of the map (hills, valleys, etc.)."
                )
                # Show multiplier and blur radius inputs.
                st.write("[DEM] Enter multiplier for the elevation map:")
                st.write(
                    "This multiplier can be used to make the terrain more pronounced. "
                    "By default the DEM file will be exact copy of the real terrain. "
                    "If you want to make it more steep, you can increase this value."
                )
                self.multiplier_input = st.number_input(
                    "Multiplier",
                    value=DEFAULT_MULTIPLIER,
                    min_value=0,
                    max_value=10000,
                    key="multiplier",
                    label_visibility="collapsed",
                )

                st.write("[DEM] Enter blur radius for the elevation map:")
                st.write(
                    "This value is used to blur the elevation map. Without blurring the terrain "
                    "may look too sharp and unrealistic. By default the blur radius is set to 21 "
                    "which corresponds to a 21x21 pixel kernel. You can increase this value to make "
                    "the terrain more smooth. Or make it smaller to make the terrain more sharp."
                )
                self.blur_radius_input = st.number_input(
                    "Blur Radius",
                    value=DEFAULT_BLUR_RADIUS,
                    min_value=1,
                    max_value=300,
                    key="blur_radius",
                    label_visibility="collapsed",
                    step=2,
                )

        # Add an empty container for status messages.
        self.status_container = st.empty()

        # Add an empty container for buttons.
        self.buttons_container = st.empty()

        # Generate button.
        with self.buttons_container:
            if st.button("Generate", key="launch_btn"):
                self.generate_map()

        # Download button.
        if st.session_state.generated:
            self.logger.info("Generated was set to True in the session state.")
            with open(self.download_path, "rb") as f:
                with self.buttons_container:
                    st.download_button(
                        label="Download",
                        data=f,
                        file_name=f"{self.download_path.split('/')[-1]}",
                        mime="application/zip",
                    )

            st.session_state.generated = False
            self.logger.info("Generated was set to False in the session state.")

    def get_sesion_name(self, coordinates: tuple[float, float]) -> str:
        """Return a session name for the map, using the coordinates and the current timestamp.

        Args:
            coordinates (tuple[float, float]): The latitude and longitude of the center point of
                the map.

        Returns:
            str: The session name for the map.
        """
        coordinates_str = "_".join(map(self.shorten_coordinate, coordinates))
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        return f"{self.game_code}_{coordinates_str}_{timestamp}"

    def shorten_coordinate(self, coordinate: float) -> str:
        """Shorten a coordinate to a string.

        Args:
            coordinate (float): The coordinate to shorten.

        Returns:
            str: The shortened coordinate.
        """
        return f"{coordinate:.5f}".replace(".", "_")

    def generate_map(self) -> None:
        """Generate the map."""
        game = mfs.Game.from_code(self.game_code)

        try:
            lat, lon = self.lat_lon
        except ValueError:
            st.error("Invalid latitude and longitude!")
            return

        # Prepare a tuple with the coordinates of the center point of the map.
        coordinates = (lat, lon)

        # Read map size from the input widget.
        try:
            height, width = self.map_size
        except ValueError:
            st.error("Invalid map size!")
            return

        if height % 2 != 0 or width % 2 != 0:
            st.error("Map size must be a power of 2. For example: 2, 4, ... 2048, 4096, ...")
            return

        if height != width:
            st.error("Map size must be square (height == width).")
            return

        # Session name will be used for a directory name as well as a zip file name.

        session_name = self.get_sesion_name(coordinates)

        self.status_container.info("Map is generating...", icon="⏳")
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
            auto_process=self.auto_process,
        )
        mp.generate()

        # Create a preview image.
        self.show_preview(mp)
        self.map_preview()

        # Pack the generated map into a zip archive.
        archive_path = mp.pack(os.path.join(config.ARCHIVES_DIRECTORY, session_name))

        self.download_path = archive_path

        st.session_state.generated = True

        self.status_container.success("Map generation completed!", icon="✅")

    def show_preview(self, mp: mfs.Map) -> None:
        """Show the preview of the generated map.

        Args:
            mp (Map): The generated map.
        """
        # Get a list of all preview images.
        full_preview_paths = mp.previews()
        preview_captions = [
            "Preview of the texture map.",
            "Preview of the DEM (elevation) map in grayscale (original).",
            "Preview of the DEM (elevation) map in colored mode (only for demonstration).",
        ]
        if not full_preview_paths or len(full_preview_paths) != len(preview_captions):
            # In case if generation of the preview images failed, we will not show them.
            return

        with self.preview_container:
            st.markdown("---")
            st.write("Previews of the generated map:")
            columns = st.columns(len(full_preview_paths))
            for column, caption, full_preview_path in zip(
                columns, preview_captions, full_preview_paths
            ):
                if not os.path.isfile(full_preview_path):
                    continue
                try:
                    image = Image.open(full_preview_path)
                    column.image(image, use_container_width=True, caption=caption)
                except Exception:
                    continue


ui = Maps4FS()
