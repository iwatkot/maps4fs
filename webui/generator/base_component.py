import streamlit as st
from templates import Messages


class BaseComponent:
    def __init__(self, public: bool, **kwargs):
        self.public = public

    def _create_widget(
        self,
        prefix: str,
        field_name: str,
        raw_field_name: str,
        value: int | bool | str | tuple | dict,
        disabled: bool = False,
    ) -> int | bool | str:
        """Create a widget for the given field.

        Arguments:
            prefix (str): The prefix for the key, used to make sure the key is unique across different contexts (e.g. providers).
            field_name (str): The field name.
            raw_field_name (str): The raw field name.
            value (int | bool): The value of the field.
            disabled (bool): True if the field should be disabled, False otherwise.

        Returns:
            int | bool: The widget for the field.
        """
        key = f"{prefix}_{raw_field_name}"

        with st.container():
            if disabled:
                st.warning(Messages.SETTING_DISABLED_ON_PUBLIC.format(setting=field_name))
            if type(value) is str:
                return st.text_input(label=field_name, value=value, key=key, disabled=disabled)
            if type(value) is int:
                return st.number_input(
                    label=field_name, value=value, min_value=0, key=key, disabled=disabled
                )
            elif type(value) is bool:
                return st.checkbox(label=field_name, value=value, key=key, disabled=disabled)
            elif type(value) is tuple:
                return st.selectbox(label=field_name, key=key, options=value)
            elif type(value) is dict:
                return st.selectbox(
                    label=field_name,
                    options=value,
                    format_func=value.get,
                    key=key,
                    disabled=disabled,
                )
            else:
                raise ValueError(f"Unsupported type of the value: {type(value)}")

    def snake_to_human(self, snake_str: str) -> str:
        """Convert a snake_case string to a human readable string.

        Arguments:
            snake_str (str): The snake_case string to convert.

        Returns:
            str: The human readable string.
        """
        return " ".join(map(str.capitalize, snake_str.split("_")))
