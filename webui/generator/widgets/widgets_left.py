import config
import streamlit as st
from generator.widgets.widget import Widget
from queuing import add_to_queue, get_queue_length, remove_from_queue, wait_in_queue
from templates import Messages

import maps4fs as mfs


class LeftTitle(Widget):
    def content(self):
        st.title(Messages.TITLE)
        self.ui._show_version()

        st.write(Messages.MAIN_PAGE_DESCRIPTION)
        st.markdown("---")


class SelectGame(Widget):
    def content(self):
        st.write("Select the game for which you want to generate the map:")
        self.ui.game_code = st.selectbox(
            "Game",
            options=config.GAMES,
            key="game_code",
            label_visibility="collapsed",
        )


class Coordinates(Widget):
    def content(self):
        st.write("Enter latitude and longitude of the center point of the map:")
        self.ui.lat_lon_input = st.text_input(
            "Latitude and Longitude",
            f"{config.DEFAULT_LAT}, {config.DEFAULT_LON}",
            key="lat_lon",
            label_visibility="collapsed",
            on_change=self.ui.map_preview,
        )


class MapSize(Widget):
    def content(self):
        size_options = config.MAP_SIZES.copy()
        if self.ui.public:
            size_options = size_options[:3]

        # Map size selection.
        st.write("Select size of the map:")
        self.ui.map_size_input = st.selectbox(
            "Map Size (meters)",
            options=size_options,
            label_visibility="collapsed",
            on_change=self.ui.map_preview,
        )


class CustomMapSize(Widget):
    def content(self):
        if self.ui.map_size_input == "Custom":
            self.ui.logger.debug("Custom map size selected.")

            st.write("Enter map size (meters):")
            custom_map_size_input = st.number_input(
                label="Height (meters)",
                min_value=2,
                value=2048,
                key="map_height",
                label_visibility="collapsed",
                on_change=self.ui.map_preview,
            )

            self.ui.map_size_input = custom_map_size_input


class DTMProviderSelect(Widget):
    def content(self):
        # DTM Provider selection.
        providers: dict[str, str] = mfs.DTMProvider.get_valid_provider_descriptions(self.ui.lat_lon)
        # Keys are provider codes, values are provider descriptions.
        # In selector we'll show descriptions, but we'll use codes in the background.

        st.write("Select the DTM provider:")
        self.ui.dtm_provider_code = st.selectbox(
            "DTM Provider",
            options=list(providers.keys()),
            format_func=lambda code: providers[code],
            key="dtm_provider",
            label_visibility="collapsed",
            disabled=self.ui.public,
            on_change=self.ui.provider_info,
        )
        self.ui.provider_settings = None
        self.ui.provider_info_container = st.empty()
        self.ui.provider_info()


class Rotation(Widget):
    def content(self):
        st.write("Enter the rotation of the map:")
        self.ui.rotation = st.slider(
            "Rotation",
            min_value=-180,
            max_value=180,
            value=0,
            step=1,
            key="rotation",
            label_visibility="collapsed",
            disabled=False,
            on_change=self.ui.map_preview,
        )


class GenerateButton(Widget):
    def content(self):
        self.ui.get_settings()
        self.ui.status_container = st.empty()
        self.ui.buttons_container = st.empty()
        generate_button_disabled = False
        if self.ui.public and get_queue_length() >= config.QUEUE_LIMIT:
            generate_button_disabled = True
            st.warning(Messages.OVERLOADED, icon="⚠️")

        with self.ui.buttons_container:
            if not config.is_on_community_server():
                if st.button("Generate", key="launch_btn", disabled=generate_button_disabled):
                    self.ui.generate_map()


class DownloadButton(Widget):
    def content(self):
        if st.session_state.generated:
            self.ui.logger.debug("Generated was set to True in the session state.")
            with open(self.ui.download_path, "rb") as f:
                with self.ui.buttons_container:
                    st.download_button(
                        label="Download",
                        data=f,
                        file_name=f"{self.ui.download_path.split('/')[-1]}",
                        mime="application/zip",
                        icon="📥",
                    )

            config.remove_with_delay_without_blocking(self.ui.download_path, self.ui.logger)

            st.session_state.generated = False
            self.ui.logger.debug("Generated was set to False in the session state.")


active_widgets = [
    LeftTitle,
    SelectGame,
    Coordinates,
    MapSize,
    CustomMapSize,
    DTMProviderSelect,
    Rotation,
    GenerateButton,
    DownloadButton,
]
