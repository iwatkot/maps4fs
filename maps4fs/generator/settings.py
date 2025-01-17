"""This module contains settings models for all components."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class Parameters:
    """Simple class to store string constants for parameters."""

    FIELD = "field"
    FIELDS = "fields"
    TEXTURES = "textures"
    FOREST = "forest"
    ROADS_POLYLINES = "roads_polylines"
    FARMYARDS = "farmyards"

    PREVIEW_MAXIMUM_SIZE = 2048


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

            settings[subclass.__name__] = subclass(**subclass_data)

        return settings

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
        multiplier (int): multiplier for the heightmap, every pixel will be multiplied by this
            value.
        blur_radius (int): radius of the blur filter.
        plateau (int): plateau height, will be added to each pixel.
        water_depth (int): water depth, will be subtracted from each pixel where the water
            is present.
    """

    multiplier: int = 1
    blur_radius: int = 35
    plateau: int = 0
    water_depth: int = 0


class BackgroundSettings(SettingsModel):
    """Represents the advanced settings for background component.

    Attributes:
        generate_background (bool): generate obj files for the background terrain.
        generate_water (bool): generate obj files for the water.
        resize_factor (int): resize factor for the background terrain and water.
            It will be used as 1 / resize_factor of the original size.
    """

    generate_background: bool = False
    generate_water: bool = False
    resize_factor: int = 8
    remove_center: bool = False
    apply_decimation: bool = False
    decimation_percent: int = 25
    decimation_agression: int = 3


class GRLESettings(SettingsModel):
    """Represents the advanced settings for GRLE component.

    Attributes:
        farmland_margin (int): margin around the farmland.
        random_plants (bool): generate random plants on the map or use the default one.
        add_farmyards (bool): If True, regions of frarmyards will be added to the map
            without corresponding fields.
    """

    farmland_margin: int = 0
    random_plants: bool = True
    add_farmyards: bool = False
    base_price: int = 60000
    price_scale: int = 100
    base_grass: tuple | str = ("smallDenseMix", "meadow")
    plants_island_minimum_size: int = 10
    plants_island_maximum_size: int = 200
    plants_island_vertex_count: int = 30
    plants_island_rounding_radius: int = 15
    plants_island_percent: int = 100


class I3DSettings(SettingsModel):
    """Represents the advanced settings for I3D component.

    Attributes:
        forest_density (int): density of the forest (distance between trees).
    """

    forest_density: int = 10
    trees_relative_shift: int = 20


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


class SplineSettings(SettingsModel):
    """Represents the advanced settings for spline component.

    Attributes:
        spline_density (int): the number of extra points that will be added between each two
            existing points.
    """

    spline_density: int = 2


class SatelliteSettings(SettingsModel):
    """Represents the advanced settings for satellite component.

    Attributes:
        download_images (bool): download satellite images.
        margin (int): margin around the map.
    """

    download_images: bool = False
    satellite_margin: int = 0
    zoom_level: int = 14
