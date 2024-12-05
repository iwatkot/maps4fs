import streamlit as st
from templates import Messages
from tools.section import Section


class ToolboxUI:
    def __init__(self):
        st.write(Messages.TOOLBOX_INFO)

        sections = Section.all()
        tabs = st.tabs([section.title for section in sections])

        for tab, section in zip(tabs, sections):
            with tab:
                section.add()
