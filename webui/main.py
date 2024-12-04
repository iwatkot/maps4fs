import streamlit as st
from generator import GeneratorUI
from toolbox import ToolboxUI


class WebUI:
    def __init__(self):
        st.set_page_config(page_title="maps4FS", page_icon="🚜", layout="wide")
        generator_tab, toolbox_tab = st.tabs(["🗺️ Map Generator", "🧰 Modder Toolbox"])

        with generator_tab:
            self.generator = GeneratorUI()

        with toolbox_tab:
            self.toolbox = ToolboxUI()


WebUI()
