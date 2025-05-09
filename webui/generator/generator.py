import json
import os
from datetime import datetime
from time import perf_counter

import config
import streamlit as st
from generator.advanced_settings import AdvancedSettings
from generator.expert_settings import ExpertSettings
from generator.main_settings import MainSettings
from PIL import Image
from queuing import add_to_queue, get_queue_length, remove_from_queue, wait_in_queue
from streamlit_stl import stl_from_file
from templates import Messages

import maps4fs as mfs

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

        self.public = config.is_public()

        self.left_column, self.right_column = st.columns(2, gap="large")

        if "generated" not in st.session_state:
            st.session_state.generated = False

        with self.right_column:
            self.add_right_widgets()

        with self.left_column:
            if config.is_on_community_server():
                st.error(Messages.MOVED, icon="🚜")

            self.add_left_widgets()

        self.main_settings.map_preview()

    def add_right_widgets(self) -> None:
        """Add widgets to the right column."""
        self.html_preview_container = st.empty()
        self.map_selector_container = st.container()
        self.preview_container = st.container()

    def _show_version(self) -> None:
        """Show the current version of the package."""
        versions = config.get_versions()
        try:
            if versions:
                latest_version, current_version = versions
                if not current_version:
                    return
                st.write(f"`{current_version}`")
                if self.public:
                    return
                if current_version != latest_version:
                    st.warning(
                        f"🆕 New version is available!   \n"
                        f"Your current version: `{current_version}`, "
                        f"latest version: `{latest_version}`.   \n"
                        "Use the following commands to upgrade:   \n"
                        "```bash   \n"
                        "docker stop maps4fs   \n"
                        "docker rm maps4fs   \n"
                        "docker run -d -p 8501:8501 --name maps4fs "
                        f"iwatkot/maps4fs:{latest_version}   \n"
                        "```"
                    )
        except Exception:
            pass

    def add_left_widgets(self) -> None:
        """Add widgets to the left column."""
        st.title(Messages.TITLE)
        self._show_version()

        st.write(Messages.MAIN_PAGE_DESCRIPTION)
        if self.public:
            with st.expander("How to launch the tool locally", icon="ℹ️"):
                st.markdown(Messages.LOCAL_VERSION)
        st.markdown("---")

        self.main_settings = MainSettings(
            self.public, html_preview_container=self.html_preview_container
        )

        self.advanced_settings = AdvancedSettings(
            self.public, dtm_provider_code=self.main_settings.dtm_provider_code
        )
        self.expert_settings = ExpertSettings(
            self.public,
            game_code=self.main_settings.game_code,
            settings=self.advanced_settings.settings,
        )

        # Add an empty container for status messages.
        self.status_container = st.empty()

        # Add an empty container for buttons.
        self.buttons_container = st.empty()

        # Generate button.
        generate_button_disabled = False
        if self.public and get_queue_length() >= config.QUEUE_LIMIT:
            generate_button_disabled = True
            st.warning(Messages.OVERLOADED, icon="⚠️")

        with self.buttons_container:
            if not config.is_on_community_server():
                if st.button("Generate", key="launch_btn", disabled=generate_button_disabled):
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
                        icon="📥",
                    )

            config.remove_with_delay_without_blocking(self.download_path)

            st.session_state.generated = False

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
        return f"{self.main_settings.game_code}_{coordinates_str}_{timestamp}"

    def shorten_coordinate(self, coordinate: float) -> str:
        """Shorten a coordinate to a string.

        Arguments:
            coordinate (float): The coordinate to shorten.

        Returns:
            str: The shortened coordinate.
        """
        return f"{coordinate:.5f}".replace(".", "_")

    def limit_on_public(self, settings_json: dict) -> dict:
        """Limit settings on the public server.

        Arguments:
            settings_json (dict): The settings JSON.

        Returns:
            dict: The limited settings JSON.
        """
        if not self.public:
            return settings_json

        limited_settings = settings_json.copy()
        limited_settings["BackgroundSettings"]["resize_factor"] = 8
        limited_settings["TextureSettings"]["dissolve"] = False
        limited_settings["SatelliteSettings"]["zoom_level"] = 16
        # limited_settings["SatelliteSettings"]["download_images"] = False
        return limited_settings

    def get_json_settings(self) -> dict[str, mfs.settings.SettingsModel]:
        """Retrieve the settings from the JSON.

        Returns:
            dict[str, SettingsModel]: The settings.
        """
        if not self.expert_settings.expert_mode:
            json_settings = self.advanced_settings.settings
        else:
            try:
                json_settings = json.loads(self.expert_settings.raw_config)
            except json.JSONDecodeError as e:
                st.error(f"Invalid raw configuration was provided: {repr(e)}")
                return

        # Limit settings on the public server.
        json_settings = self.limit_on_public(json_settings)

        # Parse settings from the JSON.
        all_settings = mfs.settings.SettingsModel.all_settings_from_json(json_settings)
        return all_settings

    def read_generation_settings(self) -> tuple[mfs.Map, str]:
        """Read the generation settings and create a Map object.

        Returns:
            tuple[Map, str]: The Map object and the session name.
        """
        game = mfs.Game.from_code(
            self.main_settings.game_code, self.expert_settings.custom_template_path
        )

        try:
            lat, lon = self.main_settings.lat_lon
        except ValueError:
            st.error("Invalid latitude and longitude!")
            return None, None

        # Prepare a tuple with the coordinates of the center point of the map.
        coordinates = (lat, lon)

        # Session name will be used for a directory name as well as a zip file name.

        session_name = self.get_sesion_name(coordinates)

        map_directory = os.path.join(config.MAPS_DIRECTORY, session_name)
        os.makedirs(map_directory, exist_ok=True)

        texture_schema = None
        tree_schema = None
        if self.expert_settings.custom_schemas:
            if self.expert_settings.texture_schema_input:
                try:
                    texture_schema = json.loads(self.expert_settings.texture_schema_input)
                except json.JSONDecodeError as e:
                    st.error(f"Invalid texture schema was provided: {repr(e)}")
                    return
            if self.expert_settings.tree_schema_input:
                try:
                    tree_schema = json.loads(self.expert_settings.tree_schema_input)
                except json.JSONDecodeError as e:
                    st.error(f"Invalid tree schema was provided: {repr(e)}")
                    return

        if self.expert_settings.custom_osm_enabled:
            osm_path = self.expert_settings.custom_osm_path
        else:
            osm_path = None

        dtm_provider = mfs.DTMProvider.get_provider_by_code(self.main_settings.dtm_provider_code)

        if self.main_settings.provider_settings is not None:
            try:
                dtm_provider_settings = dtm_provider.settings()(
                    **self.main_settings.provider_settings
                )
            except Exception as e:
                st.error(f"Invalid DTM provider settings: {repr(e)}")
                return
        else:
            dtm_provider_settings = None

        output_size = None
        if self.main_settings.output_size != self.main_settings.map_size_input:
            output_size = self.main_settings.output_size

        mp = mfs.Map(
            game,
            dtm_provider,
            dtm_provider_settings,
            coordinates,
            self.main_settings.map_size_input,
            self.main_settings.rotation,
            map_directory,
            logger=self.expert_settings.logger,
            custom_osm=osm_path,
            **self.get_json_settings(),
            texture_custom_schema=texture_schema,
            tree_custom_schema=tree_schema,
            custom_background_path=self.expert_settings.custom_background_path,
            is_public=self.public,
            output_size=output_size,
        )

        return mp, session_name

    def generate_map(self) -> None:
        """Generate the map."""

        mp, session_name = self.read_generation_settings()

        if mp is None or session_name is None:
            st.error("Incorrect settings were provided.")
            return

        if self.public:
            add_to_queue(session_name)
            for position in wait_in_queue(session_name):
                self.status_container.info(
                    f"Your position in the queue: {position}. Please wait...", icon="⏳"
                )
        self.status_container.info("Map generation started...", icon="🔄")

        try:
            step = int(100 / (len(mp.game.components) + 2))
            completed = 0
            progress_bar = st.progress(0)

            generation_started_at = perf_counter()
            for component_name in mp.generate():
                progress_bar.progress(completed, f"⏳ Generating {component_name}...")
                completed += step

            completed += step
            progress_bar.progress(completed, "🖼️ Creating previews...")

            # Create a preview image.
            self.show_preview(mp)
            self.main_settings.map_preview()

            completed += step
            progress_bar.progress(completed, "🗃️ Packing the map...")

            # Pack the generated map into a zip archive.
            archive_path = mp.pack(os.path.join(config.ARCHIVES_DIRECTORY, session_name))

            self.download_path = archive_path

            st.session_state.generated = True

            generation_finished_at = perf_counter()
            generation_time = round(generation_finished_at - generation_started_at, 3)
            self.expert_settings.logger.info(
                "Map for game %s, coordinates %s, size %s, rotation %s generated in %s seconds.",
                self.main_settings.game_code,
                mp.coordinates,
                self.main_settings.map_size_input,
                self.main_settings.rotation,
                generation_time,
            )
            self.status_container.success(f"Map generated in {generation_time} seconds.", icon="✅")
        except Exception as e:
            self.expert_settings.logger.error(
                "An error occurred while generating the map: %s", repr(e)
            )
            self.status_container.error(
                f"An error occurred while generating the map: {repr(e)}.", icon="❌"
            )
        finally:
            if self.public:
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
            ROW_SIZE = 4

            image_preview_paths = [
                preview for preview in full_preview_paths if preview.endswith(".png")
            ]

            # Split image_preview_paths into ROW_SIZE chunks.

            for row in range(0, len(image_preview_paths), ROW_SIZE):
                columns = st.columns(ROW_SIZE)
                for column, image_preview_path in zip(
                    columns, image_preview_paths[row : row + ROW_SIZE]
                ):
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
                        max_view_distance=10000,
                    )
                except Exception:
                    continue
