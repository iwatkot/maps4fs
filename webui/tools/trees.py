import json
from typing import NamedTuple

import streamlit as st
from config import FS25_TREE_SCHEMA_PATH
from tools.tool import Tool
from tools.trees_data import TREE_URLS

COLUMNS_PER_ROW = 5


class TreeInfo(NamedTuple):
    name: str
    reference_id: str
    url: str


class TreeSchemaEditorTool(Tool):
    title = "Tree Schema Editor"
    description = (
        "This tool allows you to select which trees will be included in your tree schema and then "
        "use it for the map generation."
    )
    icon = "🪵"

    def content(self):
        with open(FS25_TREE_SCHEMA_PATH, "r", encoding="utf-8") as f:
            self.tree_schema = json.load(f)

        tree_infos = []
        for tree in self.tree_schema:
            tree_name = tree["name"]
            tree_id = tree["reference_id"]
            tree_url = TREE_URLS.get(tree_name)
            if not tree_url:
                continue

            tree_infos.append(TreeInfo(tree_name, tree_id, tree_url))

        self.button_container = st.container()

        # Create a grid of images using the number of columns per row
        self.checkboxes = {}
        for i in range(0, len(tree_infos), COLUMNS_PER_ROW):
            row = st.columns(COLUMNS_PER_ROW)
            for j, tree_info in enumerate(tree_infos[i : i + COLUMNS_PER_ROW]):
                with row[j]:
                    st.image(tree_info.url, use_container_width=True)
                    tree_checkbox = st.checkbox(
                        tree_info.name,
                        value=True,
                        key=tree_info.reference_id,
                    )
                    self.checkboxes[tree_info] = tree_checkbox

        with self.button_container:
            if st.button("Show updated schema", key="show_updated_tree_schema"):
                tree_schema = self.read_schema()
                st.success(
                    "Tree schema was generated, click the copy button to copy it to the "
                    "clipboard.  \n"
                    "Then paste it into the tree schema input field in the generation tool."
                )
                st.json(tree_schema, expanded=False)

    def read_schema(self) -> list[dict[str, str | int]]:
        new_schema = []
        for tree_info, activated in self.checkboxes.items():
            if activated:
                active_entry = {"name": tree_info.name, "reference_id": tree_info.reference_id}
                new_schema.append(active_entry)

        return new_schema
