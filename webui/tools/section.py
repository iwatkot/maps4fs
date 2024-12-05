from typing import Type

from tools.dem import GeoTIFFWindowingTool
from tools.tool import Tool


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


class TexturesAndDEM(Section):
    title = "🖼️ Textures and DEM"
    description = "Tools to work with textures and digital elevation models."
    tools = [GeoTIFFWindowingTool]
