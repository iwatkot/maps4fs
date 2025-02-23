import streamlit as st
from generator.base_component import BaseComponent
from templates import Settings

import maps4fs as mfs


class AdvancedSettings(BaseComponent):
    def __init__(self, public: bool, **kwargs):
        super().__init__(public, **kwargs)
        dtm_provider = mfs.DTMProvider.get_provider_by_code(kwargs.get("dtm_provider_code"))
        self.provider_default_settings = dtm_provider.default_settings() if dtm_provider else {}
        self.get_settings()

    def get_settings(self):
        map_settings = mfs.settings.SettingsModel.all_settings()
        settings = {}
        for model in map_settings:
            raw_category_name = model.__class__.__name__
            category_name = raw_category_name.replace("Settings", " Settings")
            default_category_settings = self.provider_default_settings.get(raw_category_name, {})

            category = {}
            with st.expander(category_name, expanded=False):
                for idx, (raw_field_name, field_value) in enumerate(model.__dict__.items()):
                    default_value = default_category_settings.get(raw_field_name)
                    if default_value is not None:
                        field_value = default_value
                    field_name = self.snake_to_human(raw_field_name)
                    disabled = self.is_disabled_on_public(raw_field_name)

                    with st.empty():
                        widget = self._create_widget(
                            "main", field_name, raw_field_name, field_value, disabled
                        )
                    st.write(getattr(Settings, raw_field_name.upper()))
                    example = getattr(Settings, f"{raw_field_name.upper()}_EXAMPLE", None)
                    if example:
                        with st.popover("How it works"):
                            st.markdown(example)
                    if not idx == len(model.__dict__) - 1:
                        st.markdown("---")

                    category[raw_field_name] = widget

            settings[raw_category_name] = category

        self.settings = settings

    def is_disabled_on_public(self, raw_field_name: str) -> bool:
        """Check if the field should be disabled on the public server.

        Arguments:
            raw_field_name (str): The raw field name.

        Returns:
            bool: True if the field should be disabled, False otherwise.
        """
        if not self.public:
            return False

        disabled_fields = ["resize_factor", "zoom_level", "dissolve"]
        return raw_field_name in disabled_fields
