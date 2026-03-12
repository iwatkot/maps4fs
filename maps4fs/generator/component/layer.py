"""This module contains the class representing a layer with textures and tags."""

from __future__ import annotations

import dataclasses
import os
import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Layer:
    """Class which represents a layer with textures and tags.
    It's using to obtain data from OSM using tags and make changes into corresponding textures.
    """

    name: str
    count: int
    tags: dict[str, str | list[str] | bool] | None = None
    width: int | None = None
    # None means "use default white"; resolved to (255,255,255) in __post_init__
    color: tuple[int, int, int] | list[int] | None = None
    exclude_weight: bool = False
    priority: int | None = None
    info_layer: str | None = None
    usage: str | None = None
    background: bool = False
    invisible: bool = False
    procedural: list[str] | None = None
    border: int | None = None
    precise_tags: dict[str, str | list[str] | bool] | None = None
    precise_usage: str | None = None
    area_type: str | None = None
    area_water: bool = False
    indoor: bool = False
    merge_into: str | None = None
    building_category: str | None = None
    external: bool = False
    road_texture: str | None = None
    save_tags: bool = False

    def __post_init__(self) -> None:
        """Normalize optional defaults after dataclass initialization."""
        if self.color is None:
            self.color = (255, 255, 255)

    def to_json(self) -> dict[str, str | list[str] | bool]:
        """Returns dictionary with layer data, omitting None values.

        Returns:
            dict: Dictionary with layer data.
        """
        raw = dataclasses.asdict(self)
        return {k: v for k, v in raw.items() if v is not None}

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> Layer:
        """Creates a new instance of the class from dictionary.

        Arguments:
            data (dict[str, Any]): Dictionary with layer data.

        Returns:
            Layer: New instance of the class.
        """
        return cls(**data)

    def path(self, weights_directory: str) -> str:
        """Returns path to the first texture of the layer.

        Arguments:
            weights_directory (str): Path to the directory with weights.

        Returns:
            str: Path to the texture.
        """
        idx = "01" if self.count > 0 else ""
        weight_postfix = "_weight" if not self.exclude_weight else ""
        return os.path.join(weights_directory, f"{self.name}{idx}{weight_postfix}.png")

    def path_preview(self, weights_directory: str) -> str:
        """Returns path to the preview of the first texture of the layer.

        Arguments:
            weights_directory (str): Path to the directory with weights.

        Returns:
            str: Path to the preview.
        """
        return self.path(weights_directory).replace(".png", "_preview.png")

    def get_preview_or_path(self, weights_directory: str) -> str:
        """Returns path to the preview of the first texture of the layer if it exists,
        otherwise returns path to the texture.

        Arguments:
            weights_directory (str): Path to the directory with weights.

        Returns:
            str: Path to the preview or texture.
        """
        preview_path = self.path_preview(weights_directory)
        return preview_path if os.path.isfile(preview_path) else self.path(weights_directory)

    def paths(self, weights_directory: str) -> list[str]:
        """Returns a list of paths to the textures of the layer.
        NOTE: Works only after the textures are generated, since it just lists the directory.

        Arguments:
            weights_directory (str): Path to the directory with weights.

        Returns:
            list[str]: List of paths to the textures.
        """
        weight_files = os.listdir(weights_directory)

        # Inconsistent names are the name of textures that are not following the pattern
        # of texture_name{idx}_weight.png.
        inconsistent_names = ["forestRockRoots", "waterPuddle"]

        if self.name in inconsistent_names:
            return [
                os.path.join(weights_directory, weight_file)
                for weight_file in weight_files
                if weight_file.startswith(self.name)
            ]

        return [
            os.path.join(weights_directory, weight_file)
            for weight_file in weight_files
            if re.match(rf"{self.name}\d{{2}}_weight.png", weight_file)
        ]
