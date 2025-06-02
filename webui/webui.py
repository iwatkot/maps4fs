import os
from datetime import datetime

import requests
import requests_cache
import streamlit as st
from config import DOCS_DIRECTORY, FAQ_MD, get_mds
from generator.generator import GeneratorUI
from templates import Messages, video_tutorials
from toolbox import ToolboxUI

requests_cache.install_cache("github_cache", expire_after=1800)


class WebUI:
    def __init__(self):
        st.set_page_config(page_title="maps4FS", page_icon="🚜", layout="wide")
        (
            generator_tab,
            step_by_step_tab,
            video_tutorials_tab,
            toolbox_tab,  # TODO: Replace with schema_editor_tab
            knowledge_tab,
            faq_tab,
            changelog_tab,
        ) = st.tabs(
            [
                "🗺️ Map Generator",
                "🔢 Step by step",
                "📹 Video Tutorials",
                "🧰 Modder Toolbox",  # TODO: Replace with "📑 Schema Editor"
                "📖 Knowledge base",
                "📝 FAQ",
                "📄 Changelog",
            ]
        )

        with generator_tab:
            self.generator = GeneratorUI()

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

        with changelog_tab:
            st.markdown("## Changelog")
            st.markdown(
                "This page provides information about the latest changes to the maps4fs project."
            )
            try:
                url = "https://api.github.com/repos/iwatkot/maps4fs/releases"
                response = requests.get(url)
                if response.status_code == 200:
                    releases = response.json()
                    for release in releases:
                        version = release.get("tag_name")
                        release_name = release.get("name")
                        published_at = release.get("published_at")
                        date_time = datetime.strptime(published_at, "%Y-%m-%dT%H:%M:%SZ")
                        html_url = release.get("html_url")

                        st.markdown(
                            f"![{version}](https://img.shields.io/badge/version-{version}-blue)  \n"
                            f"Date: **{date_time.strftime('%d.%m.%Y')}**  \n"
                            f"**{release_name}**  \n"
                            f"[More info]({html_url})"
                        )
                else:
                    st.text("Too many requests to GitHub API. Use the link below to see releases.")

                st.markdown("---")
                st.markdown(
                    "Older releases available on [GitHub]"
                    "(https://github.com/iwatkot/maps4fs/releases)."
                )
            except Exception as e:
                st.error(f"An error occurred while fetching the changelog: {e}")


WebUI()
