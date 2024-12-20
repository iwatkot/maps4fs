import os
from datetime import datetime

import config
import osmp
import streamlit as st
import streamlit.components.v1 as components
from PIL import Image
from queuing import add_to_queue, remove_from_queue, wait_in_queue
from streamlit_stl import stl_from_file
from templates import Messages

import maps4fs as mfs
from maps4fs.generator.dem import (
    DEFAULT_BLUR_RADIUS,
    DEFAULT_MULTIPLIER,
    DEFAULT_PLATEAU,
)

DEFAULT_LAT = 45.28571409289627
DEFAULT_LON = 20.237433441210115
Image.MAX_IMAGE_PIXELS = None


class GeneratorUI:
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
        self.logger = mfs.Logger(level="INFO", to_file=False)

        self.community = config.is_on_community_server()
        self.logger.debug("The application launched on the community server: %s", self.community)

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

        self.logger.debug(
            "Generating map preview for lat=%s, lon=%s, map_size=%s", lat, lon, map_size
        )

        html_file = osmp.get_rotated_preview(lat, lon, map_size, angle=-self.rotation)

        with self.html_preview_container:
            components.html(open(html_file).read(), height=600)

    def add_right_widgets(self) -> None:
        """Add widgets to the right column."""
        self.logger.debug("Adding widgets to the right column...")
        self.html_preview_container = st.empty()
        self.map_selector_container = st.container()
        self.preview_container = st.container()

    def add_left_widgets(self) -> None:
        """Add widgets to the left column."""
        self.logger.debug("Adding widgets to the left column...")

        st.title(Messages.TITLE)
        st.write(Messages.MAIN_PAGE_DESCRIPTION)
        if self.community:
            st.info(Messages.MAIN_PAGE_COMMUNITY_WARNING)
        # st.info(Messages.TERRAIN_RELOAD)
        st.markdown("---")

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

        size_options = ["2048x2048", "4096x4096", "8192x8192", "16384x16384", "Custom"]
        if self.community:
            size_options = size_options[:1]

        # Map size selection.
        st.write("Select size of the map:")
        self.map_size_input = st.selectbox(
            "Map Size (meters)",
            options=size_options,
            label_visibility="collapsed",
            on_change=self.map_preview,
        )

        if self.map_size_input == "Custom":
            self.logger.debug("Custom map size selected.")

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

        if self.community:
            st.warning(
                "💡 If you run the tool locally, you can generate larger maps, even with the custom size.  \n"
            )

        # Rotation input.
        st.write("[BETA] Enter the rotation of the map:")

        self.rotation = st.slider(
            "Rotation",
            min_value=-180,
            max_value=180,
            value=0,
            step=1,
            key="rotation",
            label_visibility="collapsed",
            disabled=self.community,
            on_change=self.map_preview,
        )
        if self.community:
            st.warning("💡 This feature is available in local version of the tool.")

        self.auto_process = st.checkbox("Use auto preset", value=True, key="auto_process")
        if self.auto_process:
            self.logger.debug("Auto preset is enabled.")
            st.info(Messages.AUTO_PRESET_INFO)

        self.multiplier_input = DEFAULT_MULTIPLIER
        self.blur_radius_input = DEFAULT_BLUR_RADIUS
        self.plateau_height_input = DEFAULT_PLATEAU
        self.only_full_tiles = True
        self.fields_padding = 0
        self.farmland_margin = 3

        if not self.auto_process:
            self.logger.info("Auto preset is disabled.")

            st.info(Messages.AUTO_PRESET_DISABLED)

            # Add checkbox for advanced settings.
            st.write("Advanced settings (do not change if you are not sure):")

            if self.community:
                st.warning(Messages.COMMUNITY_ADVANCED_SETTINGS)
                disabled = True
            else:
                disabled = False

            self.advanced_settings = st.checkbox(
                "Show advanced settings", key="advanced_settings", disabled=disabled
            )

            if self.advanced_settings:
                self.logger.debug("Advanced settings are enabled.")

                st.warning("⚠️ Changing these settings can lead to unexpected results.")

                with st.expander("DEM Advanced Settings", icon="⛰️"):
                    st.info(
                        "ℹ️ Settings related to the Digital Elevation Model (elevation map). "
                        "This file is used to generate the terrain of the map (hills, valleys, etc.)."
                    )
                    # Show multiplier and blur radius inputs.
                    st.write("Enter the multiplier for the elevation map:")
                    st.write(Messages.DEM_MULTIPLIER_INFO)

                    self.multiplier_input = st.number_input(
                        "Multiplier",
                        value=DEFAULT_MULTIPLIER,
                        min_value=0,
                        max_value=10000,
                        step=1,
                        key="multiplier",
                        label_visibility="collapsed",
                    )

                    st.write("Enter the blur radius for the elevation map:")
                    st.write(Messages.DEM_BLUR_RADIUS_INFO)

                    self.blur_radius_input = st.number_input(
                        "Blur Radius",
                        value=DEFAULT_BLUR_RADIUS,
                        min_value=0,
                        max_value=300,
                        key="blur_radius",
                        label_visibility="collapsed",
                        step=2,
                    )

                    st.write("Enter the plateau height (which will be added to the whole map):")
                    st.write(Messages.DEM_PLATEAU_INFO)
                    self.plateau_height_input = st.number_input(
                        "Plateau Height",
                        value=0,
                        min_value=0,
                        max_value=10000,
                        key="plateau_height",
                        label_visibility="collapsed",
                    )

                with st.expander("Background Terrain Advanced Settings", icon="🏞️"):
                    st.info(
                        "ℹ️ Settings related to the background terrain "
                        "which is a simple mesh around the playable area. "
                    )

                    st.write("Generate only full tiles (recommended) or all tiles:")
                    st.write(Messages.ONLY_FULL_TILES_INFO)
                    self.only_full_tiles = st.checkbox(
                        "Only Full Background Tiles",
                        key="only_full_tiles",
                        value=True,
                    )

                with st.expander("Textures Advanced Settings", icon="🎨"):
                    st.info(
                        "ℹ️ Settings related to the textures of the map, which represent different "
                        "types of terrain, such as grass, dirt, etc."
                    )

                    st.write("Enter the field padding (in meters):")
                    st.write(Messages.FIELD_PADDING_INFO)
                    self.fields_padding = st.number_input(
                        "Field Padding",
                        value=0,
                        min_value=0,
                        max_value=100,
                        key="field_padding",
                        label_visibility="collapsed",
                    )

                with st.expander("Farmlands Advanced Settings", icon="🌾"):
                    st.info(
                        "ℹ️ Settings related to the farmlands of the map, which represent the lands "
                        "that can be bought in the game by the player."
                    )

                    st.write("Enter the farmland margin (in meters):")
                    st.write(Messages.FARMLAND_MARGIN_INFO)

                    self.farmland_margin = st.number_input(
                        "Farmland Margin",
                        value=3,
                        min_value=0,
                        max_value=100,
                        key="farmland_margin",
                        label_visibility="collapsed",
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
            self.logger.debug("Generated was set to True in the session state.")
            with open(self.download_path, "rb") as f:
                with self.buttons_container:
                    st.download_button(
                        label="Download",
                        data=f,
                        file_name=f"{self.download_path.split('/')[-1]}",
                        mime="application/zip",
                        icon="📥",
                    )

            # st.info(f"The file will be removed in {int(config.REMOVE_DELAY / 60)} minutes.")
            config.remove_with_delay_without_blocking(self.download_path, self.logger)

            st.session_state.generated = False
            self.logger.debug("Generated was set to False in the session state.")

    def get_sesion_name(self, coordinates: tuple[float, float]) -> str:
        """Return a session name for the map, using the coordinates and the current timestamp.

        Arguments:
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

        Arguments:
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

        map_directory = os.path.join(config.MAPS_DIRECTORY, session_name)
        os.makedirs(map_directory, exist_ok=True)

        # Create an instance of the Map class and generate the map.
        mp = mfs.Map(
            game,
            coordinates,
            height,
            self.rotation,
            map_directory,
            logger=self.logger,
            multiplier=self.multiplier_input,
            blur_radius=self.blur_radius_input,
            auto_process=self.auto_process,
            plateau=self.plateau_height_input,
            light_version=self.community,
            only_full_tiles=self.only_full_tiles,
            fields_padding=self.fields_padding,
            farmland_margin=self.farmland_margin,
        )

        if self.community:
            add_to_queue(session_name)
            for position in wait_in_queue(session_name):
                self.status_container.info(
                    f"Your position in the queue: {position}. Please wait...", icon="⏳"
                )

            self.status_container.info("Started the map generation...", icon="🔄")

        try:
            step = int(100 / (len(game.components) + 2))
            completed = 0
            progress_bar = st.progress(0)
            for component_name in mp.generate():
                progress_bar.progress(completed, f"⏳ Generating {component_name}...")
                completed += step

            completed += step
            progress_bar.progress(completed, "🖼️ Creating previews...")

            # Create a preview image.
            self.show_preview(mp)
            self.map_preview()

            completed += step
            progress_bar.progress(completed, "🗃️ Packing the map...")

            # Pack the generated map into a zip archive.
            archive_path = mp.pack(os.path.join(config.ARCHIVES_DIRECTORY, session_name))

            self.download_path = archive_path

            st.session_state.generated = True

            self.status_container.success("Map generation completed!", icon="✅")
        finally:
            if self.community:
                remove_from_queue(session_name)

    def show_preview(self, mp: mfs.Map) -> None:
        """Show the preview of the generated map.

        Arguments:
            mp (Map): The generated map.
        """
        # Get a list of all preview images.
        full_preview_paths = mp.previews()
        if not full_preview_paths:
            # In case if generation of the preview images failed, we will not show them.
            return

        with self.preview_container:
            st.markdown("---")
            st.write("Previews of the generated map:")

            image_preview_paths = [
                preview for preview in full_preview_paths if preview.endswith(".png")
            ]

            columns = st.columns(len(image_preview_paths))
            for column, image_preview_path in zip(columns, image_preview_paths):
                if not os.path.isfile(image_preview_path):
                    continue
                try:
                    image = Image.open(image_preview_path)
                    column.image(image, use_container_width=True)
                except Exception:
                    continue

            stl_preview_paths = [
                preview for preview in full_preview_paths if preview.endswith(".stl")
            ]

            for stl_preview_path in stl_preview_paths:
                if not os.path.isfile(stl_preview_path):
                    continue
                try:
                    stl_from_file(
                        file_path=stl_preview_path,
                        color="#808080",
                        material="material",
                        auto_rotate=True,
                        height="400",
                        key=None,
                    )
                except Exception:
                    continue
