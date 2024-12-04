import streamlit as st
from dem import DemUI
from templates import Messages


class ToolboxUI:
    def __init__(self):
        st.write(Messages.TOOLBOX_INFO)

        dem_tab, test_tab = st.tabs(["🏔️ DEM", "TEST"])

        with dem_tab:
            DemUI()
