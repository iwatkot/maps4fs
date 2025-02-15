import os

import streamlit as st
import streamlit.components.v1 as components
from config import DOCS_DIRECTORY, FAQ_MD, get_mds
from generator.generator import GeneratorUI
from templates import Messages, video_tutorials
from toolbox import ToolboxUI


class WebUI:
    def __init__(self):
        st.set_page_config(page_title="maps4FS", page_icon="🚜", layout="wide")
        (
            generator_tab,
            statistics_tab,
            step_by_step_tab,
            video_tutorials_tab,
            toolbox_tab,
            knowledge_tab,
            faq_tab,
        ) = st.tabs(
            [
                "🗺️ Map Generator",
                "📊 Statistics",
                "🔢 Step by step",
                "📹 Video Tutorials",
                "🧰 Modder Toolbox",
                "📖 Knowledge base",
                "📝 FAQ",
            ]
        )

        with generator_tab:
            self.generator = GeneratorUI()

        with statistics_tab:
            components.iframe(
                "https://stats.maps4fs.xyz/public/dashboard/"
                "f8defe6a-09db-4db1-911f-b6b02075d4b2#refresh=60",
                height=2500,
                scrolling=False,
            )

        with step_by_step_tab:
            step_by_step_tab_path = os.path.join(DOCS_DIRECTORY, "step_by_step.md")
            st.write(open(step_by_step_tab_path, "r", encoding="utf-8").read())

        with video_tutorials_tab:
            COLUMNS_PER_ROW = 3
            for i in range(0, len(video_tutorials), COLUMNS_PER_ROW):
                row = st.columns(COLUMNS_PER_ROW)
                for j, video_tutorial in enumerate(video_tutorials[i : i + COLUMNS_PER_ROW]):
                    with row[j]:
                        st.markdown(
                            f"[![]({video_tutorial.image})]({video_tutorial.link})  \n"
                            f"**Episode {video_tutorial.episode}:** {video_tutorial.title}  \n"
                            f"*{video_tutorial.description}*"
                        )

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
