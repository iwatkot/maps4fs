"""This module contains settings models for all components."""

from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, ConfigDict


class Parameters:
    """Simple class to store string constants for parameters."""

    FIELD = "field"
    FIELDS = "fields"
    BUILDINGS = "buildings"
    TEXTURES = "textures"
    BACKGROUND = "background"
    FOREST = "forest"
    ROADS_POLYLINES = "roads_polylines"
    WATER_POLYLINES = "water_polylines"
    FARMYARDS = "farmyards"

    PREVIEW_MAXIMUM_SIZE = 2048

    BACKGROUND_DISTANCE = 2048
    FULL = "FULL"
    PREVIEW = "PREVIEW"

    RESIZE_FACTOR = 8

    FARMLAND_ID_LIMIT = 254

    PLANTS_ISLAND_PERCENT = 100
    PLANTS_ISLAND_MINIMUM_SIZE = 10
    PLANTS_ISLAND_MAXIMUM_SIZE = 200
    PLANTS_ISLAND_VERTEX_COUNT = 30
    PLANTS_ISLAND_ROUNDING_RADIUS = 15

    WATER_ADD_WIDTH = 2


class SharedSettings(BaseModel):
    """Represents the shared settings for all components."""

    mesh_z_scaling_factor: float | None = None
    height_scale_multiplier: float | None = None
    height_scale_value: float | None = None
    change_height_scale: bool = False

    model_config = ConfigDict(
        frozen=False,
    )


class SettingsModel(BaseModel):
    """Base class for settings models. It provides methods to convert settings to and from JSON."""

    model_config = ConfigDict(
        frozen=False,
    )

    @classmethod
    def all_settings_to_json(cls) -> dict[str, dict[str, Any]]:
        """Get all settings of the current class and its subclasses as a dictionary.

        Returns:
            dict[str, dict[str, Any]]: Dictionary with settings of the current class and its
                subclasses.
        """
        all_settings = {}
        for subclass in cls.__subclasses__():
            all_settings[subclass.__name__] = subclass().model_dump()

        return all_settings

    @classmethod
    def all_settings_from_json(
        cls, data: dict, flattening: bool = True
    ) -> dict[str, SettingsModel]:
        """Create settings instances from JSON data.

        Arguments:
            data (dict): JSON data.
            flattening (bool): if set to True will flattet iterables to use the first element
                of it.

        Returns:
            dict[str, Type[SettingsModel]]: Dictionary with settings instances.
        """
        settings = {}
        for subclass in cls.__subclasses__():
            subclass_data = data[subclass.__name__]
            if flattening:
                for key, value in subclass_data.items():
                    if isinstance(value, (list, tuple)):
                        subclass_data[key] = value[0]

            settings[cls.camel_to_snake(subclass.__name__)] = subclass(**subclass_data)

        return settings

    @staticmethod
    def camel_to_snake(camel_string: str) -> str:
        """Convert a camel case string to snake case.

        Arguments:
            camel_string (str): Camel case string.

        Returns:
            str: Snake case string.
        """
        splitted = re.split(r"(Settings)", camel_string)
        joined = "_".join(part.lower() for part in splitted if part)
        return joined

    @classmethod
    def all_settings(cls) -> list[SettingsModel]:
        """Get all settings of the current class and its subclasses.

        Returns:
            list[SettingsModel]: List with settings of the current class and its subclasses.
        """
        settings = []
        for subclass in cls.__subclasses__():
            settings.append(subclass())

        return settings


class DEMSettings(SettingsModel):
    """Represents the advanced settings for DEM component.

    Attributes:
        adjust_terrain_to_ground_level (bool): adjust terrain to ground level or not.
        multiplier (int): multiplier for the heightmap.
        blur_radius (int): radius of the blur filter.
        minimum_height_scale (int): minimum height scale for the i3d.
        plateau (int): plateau height.
        ceiling (int): ceiling height.
        water_depth (int): water depth.
    """

    adjust_terrain_to_ground_level: bool = True
    multiplier: int = 1
    minimum_height_scale: int = 255
    plateau: int = 0
    ceiling: int = 0
    water_depth: int = 0
    blur_radius: int = 3
    add_foundations: bool = False


class BackgroundSettings(SettingsModel):
    """Represents the advanced settings for background component.

    Attributes:
        generate_background (bool): generate obj files for the background terrain.
        generate_water (bool): generate obj files for the water.
        water_blurriness (int): blurriness of the water.
        remove_center (bool): remove the center of the background terrain.
            It will be used to remove the center of the map where the player starts.
    """

    generate_background: bool = False
    generate_water: bool = False
    water_blurriness: int = 20
    remove_center: bool = True


class GRLESettings(SettingsModel):
    """Represents the advanced settings for GRLE component.

    Attributes:
        farmland_margin (int): margin around the farmland.
        add_farmyards (bool): If True, regions of farmyards will be added to the map
            without corresponding fields.
        base_price (int): base price for the farmland.
        price_scale (int): scale for the price of the farmland.
        add_grass (bool): if True, grass will be added to the map.
        base_grass (tuple | str): base grass to be used on the map.
        random_plants (bool): generate random plants on the map or use the default one.
        fill_empty_farmlands (bool): if True, empty farmlands will be filled with grass.

    """

    farmland_margin: int = 0
    add_farmyards: bool = False
    base_price: int = 60000
    price_scale: int = 100
    add_grass: bool = True
    base_grass: tuple | str = ("smallDenseMix", "meadow")
    random_plants: bool = True
    fill_empty_farmlands: bool = False


class I3DSettings(SettingsModel):
    """Represents the advanced settings for I3D component.

    Attributes:
        add_trees (bool): add trees to the map.
        forest_density (int): density of the forest (distance between trees).
        trees_relative_shift (int): relative shift of the trees.
        spline_density (int): the number of extra points that will be added between each two
            existing points.
        add_reversed_splines (bool): if True, reversed splines will be added to the map.
        field_splines (bool): if True, splines will be added to the fields.
    """

    add_trees: bool = True
    forest_density: int = 10
    trees_relative_shift: int = 20

    spline_density: int = 2
    add_reversed_splines: bool = False
    field_splines: bool = False


class TextureSettings(SettingsModel):
    """Represents the advanced settings for texture component.

    Attributes:
        dissolve (bool): dissolve the texture into several images.
        fields_padding (int): padding around the fields.
        skip_drains (bool): skip drains generation.
    """

    dissolve: bool = False
    fields_padding: int = 0
    skip_drains: bool = False
    use_cache: bool = True
    use_precise_tags: bool = False


class SatelliteSettings(SettingsModel):
    """Represents the advanced settings for satellite component.

    Attributes:
        download_images (bool): download satellite images.
        margin (int): margin around the map.
    """

    download_images: bool = False
    zoom_level: int = 16
