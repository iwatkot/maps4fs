import os
from datetime import datetime

import requests
import streamlit as st
import streamlit.components.v1 as components
from config import DOCS_DIRECTORY, FAQ_MD, get_mds
from generator.generator import GeneratorUI
from osmp import MapEntry, get_rotated_previews
from streamlit_folium import folium_static
from templates import Messages, video_tutorials
from toolbox import ToolboxUI

from maps4fs.generator.statistics import get_main_settings


class WebUI:
    def __init__(self):
        st.set_page_config(page_title="maps4FS", page_icon="🚜", layout="wide")
        (
            generator_tab,
            statistics_tab,
            step_by_step_tab,
            video_tutorials_tab,
            coverage_tab,
            toolbox_tab,
            knowledge_tab,
            faq_tab,
            changelog_tab,
        ) = st.tabs(
            [
                "🗺️ Map Generator",
                "📊 Statistics",
                "🔢 Step by step",
                "📹 Video Tutorials",
                "🌐 Coverage",
                "🧰 Modder Toolbox",
                "📖 Knowledge base",
                "📝 FAQ",
                "📄 Changelog",
            ]
        )

        with generator_tab:
            self.generator = GeneratorUI()

        with statistics_tab:
            components.iframe(
                "https://stats.maps4fs.xyz/public/dashboard/"
                "f8defe6a-09db-4db1-911f-b6b02075d4b2#refresh=60",
                height=2000,
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

        with coverage_tab:
            st.write(Messages.COVERAGE_INFO)
            add_bboxes = st.checkbox("Add bounding boxes", value=True)
            add_markers = st.checkbox("Add markers", value=False)
            limit = st.number_input("Limit of entries", value=0, min_value=0)

            if st.button("Show coverage map"):
                try:
                    entries_json = get_main_settings(
                        fields=["latitude", "longitude", "size", "rotation"], limit=limit
                    )

                    identifiers = []
                    filtered_entries = []
                    for entry in entries_json:
                        lat, lon = entry.get("latitude"), entry.get("longitude")
                        rotation = entry.get("rotation")
                        size = entry.get("size")
                        if lat and lon and rotation and size:
                            identifier = (lat, lon, rotation, size)
                            if identifier not in identifiers:
                                identifiers.append(identifier)
                                filtered_entries.append(entry)

                    unique_factor = len(filtered_entries) / len(entries_json) * 100

                    st.info(
                        f"Retrievied {len(filtered_entries)} unique entries "
                        f"from total {len(entries_json)}.  \nPercentage of "
                        f"unique entries: {unique_factor:.2f}%."
                    )

                    entries = [MapEntry(**entry) for entry in entries_json]

                    folium_map = get_rotated_previews(
                        entries,
                        add_markers=add_markers,
                        add_bboxes=add_bboxes,
                    )
                    folium_static(folium_map, height=500, width=1000)
                except Exception as e:
                    st.error(f"An error occurred: {e}")

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
                    st.error(f"An error occurred while fetching the changelog: {response.text}")

                st.markdown("---")
                st.markdown(
                    "Older releases available on [GitHub]"
                    "(https://github.com/iwatkot/maps4fs/releases)."
                )
            except Exception as e:
                st.error(f"An error occurred while fetching the changelog: {e}")


WebUI()
