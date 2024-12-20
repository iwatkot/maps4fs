import os

import streamlit as st
from config import DOCS_DIRECTORY, FAQ_MD, get_mds
from generator import GeneratorUI
from templates import Messages
from toolbox import ToolboxUI


class WebUI:
    def __init__(self):
        st.set_page_config(page_title="maps4FS", page_icon="🚜", layout="wide")
        generator_tab, step_by_step_tab, tips_tab, toolbox_tab, knowledge_tab, faq_tab = st.tabs(
            [
                "🗺️ Map Generator",
                "🔢 Step by step",
                "💡 Tips and Hints",
                "🧰 Modder Toolbox",
                "📖 Knowledge base",
                "📝 FAQ",
            ]
        )

        with generator_tab:
            self.generator = GeneratorUI()

        with step_by_step_tab:
            step_by_step_tab_path = os.path.join(DOCS_DIRECTORY, "step_by_step.md")
            st.write(open(step_by_step_tab_path, "r", encoding="utf-8").read())

        with tips_tab:
            tips_tab_path = os.path.join(DOCS_DIRECTORY, "tips_and_hints.md")
            st.write(open(tips_tab_path, "r", encoding="utf-8").read())

        with toolbox_tab:
            self.toolbox = ToolboxUI()

        with knowledge_tab:
            st.title("Knowledge base")
            st.write(Messages.KNOWLEDGE_INFO)
            mds = get_mds()

            tabs = st.tabs(list(mds.keys()))

            for tab, md_path in zip(tabs, mds.values()):
                with tab:
                    st.write(open(md_path, "r", encoding="utf-8").read())

        with faq_tab:
            st.write(open(FAQ_MD, "r", encoding="utf-8").read())


WebUI()
