"""This module contains settings models for all components."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any, Literal, NamedTuple, cast

from pydantic import BaseModel, ConfigDict, Field

from maps4fs.generator.bootstrap import Bootstrap
from maps4fs.generator.constants import Parameters

PACKAGE_VERSION = Bootstrap.package_version()
__all__ = ["Parameters"]

if TYPE_CHECKING:
    from maps4fs.generator.map import Map


class SettingsModel(BaseModel):
    """Base class for settings models. It provides methods to convert settings to and from JSON."""

    model_config = ConfigDict(
        frozen=False,
    )


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
        flatten_roads (bool): if True, roads will be flattened in the DEM data.
        flatten_water (bool): if True, smooth and flatten water bottoms while preserving
            broad elevation changes across the water area.
    """

    generate_background: bool = False
    generate_water: bool = False
    water_blurriness: int = 20
    remove_center: bool = True
    flatten_roads: bool = False
    flatten_water: bool = False


class GRLESettings(SettingsModel):
    """Represents the advanced settings for GRLE component.

    Attributes:
        farmland_margin (int): margin around the farmland.
        add_farmyards (bool): If True, regions of farmyards will be added to the map
            without corresponding fields.
        base_price (int): base price for the farmland.
        price_scale (int): scale for the price of the farmland.
        add_grass (bool): if True, grass will be added to the map.
        base_grass (Literal["smallDenseMix", "meadow", "grass"]): base grass type for the map.
        random_plants (bool): generate random plants on the map or use the default one.
        fill_empty_farmlands (bool): if True, empty farmlands will be filled with grass.

    """

    farmland_margin: int = 0
    add_farmyards: bool = False
    base_price: int = 60000
    price_scale: int = 100
    add_grass: bool = True
    base_grass: Literal["smallDenseMix", "meadow", "grass"] = "smallDenseMix"
    random_plants: bool = True
    fill_empty_farmlands: bool = True


class I3DSettings(SettingsModel):
    """Represents the advanced settings for I3D component.

    Attributes:
        add_trees (bool): add trees to the map.
        forest_density (int): density of the forest (distance between trees).
        tree_limit (int): maximum number of trees to be added to the map.
        trees_relative_shift (int): relative shift of the trees.
        spline_density (int): the number of extra points that will be added between each two
            existing points.
        add_reversed_splines (bool): if True, reversed splines will be added to the map.
        field_splines (bool): if True, splines will be added to the fields.
        license_plate_prefix (str): prefix for the license plates.
        displacement_layer_max_height (float): displacement layer maximum height value written
            to map.i3d.
    """

    add_trees: bool = True
    forest_density: int = 10
    tree_limit: int = 20000
    trees_relative_shift: int = 20

    spline_density: int = 2
    add_reversed_splines: bool = False
    field_splines: bool = False

    license_plate_prefix: str = "M4S"

    self_clear: bool = False
    displacement_layer_max_height: float = Field(default=0.2, ge=0.0, le=1.0)


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


class BuildingSettings(SettingsModel):
    """Represents the advanced settings for building component.

    Attributes:
        generate_buildings (bool): generate buildings on the map.
        region (Literal["auto", "all", "EU", "US"]): region for the buildings.
        tolerance_factor (int): tolerance factor representing allowed dimension difference
            between OSM building footprint and the building model footprint.
    """

    generate_buildings: bool = True
    region: Literal["auto", "all", "EU", "US"] = "auto"
    tolerance_factor: int = 30


class GenerationSettings(BaseModel):
    """Represents the settings for the map generation process."""

    dem_settings: DEMSettings = DEMSettings()
    background_settings: BackgroundSettings = BackgroundSettings()
    grle_settings: GRLESettings = GRLESettings()
    i3d_settings: I3DSettings = I3DSettings()
    texture_settings: TextureSettings = TextureSettings()
    satellite_settings: SatelliteSettings = SatelliteSettings()
    building_settings: BuildingSettings = BuildingSettings()

    def to_json(self) -> dict[str, Any]:
        """Convert the GenerationSettings instance to JSON format.

        Returns:
            dict[str, Any]: JSON representation of the GenerationSettings.
        """
        return {
            "DEMSettings": self.dem_settings.model_dump(),
            "BackgroundSettings": self.background_settings.model_dump(),
            "GRLESettings": self.grle_settings.model_dump(),
            "I3DSettings": self.i3d_settings.model_dump(),
            "TextureSettings": self.texture_settings.model_dump(),
            "SatelliteSettings": self.satellite_settings.model_dump(),
            "BuildingSettings": self.building_settings.model_dump(),
        }

    @classmethod
    def from_json(
        cls, data: dict[str, Any], from_snake: bool = False, safe: bool = False
    ) -> GenerationSettings:
        """Create a GenerationSettings instance from JSON data.

        Arguments:
            data (dict[str, Any]): JSON data.
            from_snake (bool): if set to True will convert snake_case keys to camelCase.
            safe (bool): if set to True will ignore unknown keys.

        Returns:
            GenerationSettings: Instance of GenerationSettings.
        """

        def _get(cls_name: str, snake_name: str) -> dict:
            key = snake_name if from_snake else cls_name
            return data.get(key, {}) if safe else data[key]

        return cls(
            dem_settings=DEMSettings(**_get("DEMSettings", "dem_settings")),
            background_settings=BackgroundSettings(
                **_get("BackgroundSettings", "background_settings")
            ),
            grle_settings=GRLESettings(**_get("GRLESettings", "grle_settings")),
            i3d_settings=I3DSettings(**_get("I3DSettings", "i3d_settings")),
            texture_settings=TextureSettings(**_get("TextureSettings", "texture_settings")),
            satellite_settings=SatelliteSettings(**_get("SatelliteSettings", "satellite_settings")),
            building_settings=BuildingSettings(**_get("BuildingSettings", "building_settings")),
        )


class MainSettings(NamedTuple):
    """Represents the main settings for the map generation."""

    game: str
    latitude: float
    longitude: float
    country: str
    size: int
    output_size: int | None
    rotation: int
    dtm_provider: str
    custom_osm: bool
    custom_dem: bool
    is_public: bool
    date: str
    time: str
    version: str
    completed: bool
    error: str | None = None
    origin: str | None = None
    platform: str | None = None

    @classmethod
    def from_json(cls, data: dict[str, str | float | int | bool | None]) -> MainSettings:
        """Create a MainSettings instance from JSON data.

        Arguments:
            data (dict[str, str | float | int | bool | None]): JSON data.

        Returns:
            MainSettings: Instance of MainSettings.
        """
        return cls(
            game=cast(str, data["game"]),
            latitude=cast(float, data["latitude"]),
            longitude=cast(float, data["longitude"]),
            country=cast(str, data["country"]),
            size=cast(int, data["size"]),
            output_size=cast(int | None, data["output_size"]),
            rotation=cast(int, data["rotation"]),
            dtm_provider=cast(str, data["dtm_provider"]),
            custom_osm=cast(bool, data["custom_osm"]),
            custom_dem=cast(bool, data["custom_dem"]),
            is_public=cast(bool, data["is_public"]),
            date=cast(str, data["date"]),
            time=cast(str, data["time"]),
            version=cast(str, data["version"]),
            completed=cast(bool, data["completed"]),
            error=cast(str | None, data.get("error")),
            origin=cast(str | None, data.get("origin")),
            platform=cast(str | None, data.get("platform")),
        )

    def to_json(self) -> dict[str, str | float | int | bool | None]:
        """Convert the MainSettings instance to JSON format.

        Returns:
            dict[str, str | float | int | bool | None]: JSON representation of the MainSettings.
        """
        return self._asdict()

    @classmethod
    def from_map(cls, map: Map) -> MainSettings:
        """Create a MainSettings instance from a Map instance.

        Arguments:
            map (Map): Instance of Map.

        Returns:
            MainSettings: Instance of MainSettings.
        """
        from maps4fs.generator.geo import get_country_by_coordinates

        telemetry = getattr(map, "_telemetry", {})

        return cls(
            game=map.game.code,
            latitude=map.coordinates[0],
            longitude=map.coordinates[1],
            country=get_country_by_coordinates(map.coordinates),
            size=map.size,
            output_size=map.output_size,
            rotation=map.rotation,
            dtm_provider=map.dtm_provider.name(),
            custom_osm=bool(map.custom_osm),
            custom_dem=bool(map.custom_background_path),
            is_public=telemetry.get("is_public", False),
            date=datetime.now().strftime("%Y-%m-%d"),
            time=datetime.now().strftime("%H:%M:%S"),
            version=PACKAGE_VERSION,
            completed=False,
            error=None,
            origin=telemetry.get("origin", None),
            platform=telemetry.get("platform", None),
        )
