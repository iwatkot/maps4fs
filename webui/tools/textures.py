import json
from typing import Any, NamedTuple

import streamlit as st
from config import FS25_TEXTURE_SCHEMA_PATH
from tools.textures_data import TEXTURE_URLS
from tools.tool import Tool

COLUMNS_PER_ROW = 5


class TextureInfo(NamedTuple):
    name: str
    data: dict[str, Any]
    url: str


class TextureSchemaEditorTool(Tool):
    title = "Texture Schema Editor"
    description = "This tool allows you to edit the texture schema for the map generation. "
    icon = "🎨"

    def content(self):
        with open(FS25_TEXTURE_SCHEMA_PATH, "r", encoding="utf-8") as f:
            self.texture_schema = json.load(f)

        texture_infos = []
        for texture in self.texture_schema:
            texture_name = texture["name"]
            texture_url = TEXTURE_URLS.get(texture_name)
            if not texture_url:
                continue

            texture_infos.append(TextureInfo(texture_name, texture, texture_url))

        self.button_container = st.container()

        # Create a grid of images using the number of columns per row
        self.text_areas = {}
        for i in range(0, len(texture_infos), COLUMNS_PER_ROW):
            row = st.columns(COLUMNS_PER_ROW)
            for j, texture_info in enumerate(texture_infos[i : i + COLUMNS_PER_ROW]):
                with row[j]:
                    st.image(texture_info.url, use_container_width=True)
                    text_area = st.text_area(
                        texture_info.name,
                        value=json.dumps(texture_info.data, indent=2),
                        key=texture_info.name,
                        height=160,
                    )
                    self.text_areas[texture_info.name] = text_area

        with self.button_container:
            if st.button("Show updated schema", key="show_updated_texture_schema"):
                texture_schema = self.read_schema()
                st.success(
                    "Texture schema was generated, click the copy button to copy it to the "
                    "clipboard.  \n"
                    "Then paste it into the texture schema input field in the generation tool."
                )
                st.json(texture_schema, expanded=False)

    def read_schema(self) -> list[dict[str, str | int]]:
        new_schema = []
        for texture_name, texture_data in self.text_areas.items():
            try:
                data = json.loads(texture_data)
            except json.JSONDecodeError:
                st.error(f"Error reading schema for texture name: {texture_name}")
                continue

            new_schema.append(data)

        return new_schema
