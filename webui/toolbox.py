import streamlit as st
from templates import Messages
from tools.section import Section


class ToolboxUI:
    def __init__(self):
        st.write(Messages.TOOLBOX_INFO)
        st.warning(
            "DEPRECATION WARNING: Modder Toolbox is deprecated and will be removed in maps4fs 2.0. "
            "If you want to continue using it, do not update maps4fs to 2.0."
        )

        sections = Section.all()
        tabs = st.tabs([section.title for section in sections])

        for tab, section in zip(tabs, sections):
            with tab:
                section.add()
