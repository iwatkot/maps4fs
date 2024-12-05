from typing import Type

from tools.dem import CropGeotiffTool
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


class DEMSection(Section):
    title = "⛰️ DEM"
    description = "Tools for Digital Elevation Models"
    tools = [CropGeotiffTool]
