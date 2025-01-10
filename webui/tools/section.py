from typing import Type

from tools.background import ConvertImageToObj
from tools.dem import GeoTIFFWindowingTool
from tools.textures import TextureSchemaEditorTool
from tools.tool import Tool
from tools.trees import TreeSchemaEditorTool


class Section:
    title: str
    description: str
    tools: list[Type[Tool]]

    @classmethod
    def all(cls):
        return cls.__subclasses__()

    @classmethod
    def add(cls):
        for tool in cls.tools:
            tool()


class Shemas(Section):
    title = "📄 Schemas"
    description = "Tools to work with different schemas."
    tools = [TreeSchemaEditorTool, TextureSchemaEditorTool]


class TexturesAndDEM(Section):
    title = "🖼️ Textures and DEM"
    description = "Tools to work with textures and digital elevation models."
    tools = [GeoTIFFWindowingTool]


class Background(Section):
    title = "🏔️ Background"
    description = "Tools to work with background terrain."
    tools = [ConvertImageToObj]
