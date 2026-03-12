"""This module contains Map class, which is used to generate map using all components."""

from __future__ import annotations

import json
import os
import shutil
from time import perf_counter
from typing import Any, Generator

from pydtmdl import DTMProvider
from pydtmdl.base.dtm import DTMProviderSettings

from maps4fs.generator.component import Background, Component, Layer, Satellite, Texture
from maps4fs.generator.constants import Paths
from maps4fs.generator.context import MapContext
from maps4fs.generator.game import Game
from maps4fs.generator.monitor import Logger, PerformanceMonitor, performance_session
from maps4fs.generator.osm import check_and_fix_osm
from maps4fs.generator.settings import GenerationSettings, MainSettings
from maps4fs.generator.statistics import StatisticsClient

_stats = StatisticsClient()


class Map:
    """Class used to generate map using all components.

    Arguments:
        game (Type[Game]): Game for which the map is generated.
        coordinates (tuple[float, float]): Coordinates of the center of the map.
        size (int): Height and width of the map in pixels (it's a square).
        map_directory (str): Path to the directory where map files will be stored.
        logger (Any): Logger instance
    """

    def __init__(
        self,
        game: Game,
        dtm_provider: DTMProvider,
        dtm_provider_settings: DTMProviderSettings | None,
        coordinates: tuple[float, float],
        size: int,
        rotation: int,
        map_directory: str | None = None,
        logger: Any = None,
        custom_osm: str | None = None,
        generation_settings: GenerationSettings = GenerationSettings(),
        **kwargs,
    ):

        # region main properties
        self.game = game
        self.dtm_provider = dtm_provider
        self.dtm_provider_settings = dtm_provider_settings
        self.coordinates = coordinates
        self.map_directory = map_directory or self.suggest_map_directory(
            coordinates=coordinates, game_code=game.code  # type: ignore
        )
        game.set_map_directory(self.map_directory)
        self.rotation = rotation
        self.kwargs = kwargs
        # endregion

        # region size properties
        self.size = size
        rotation_multiplier = 1.5 if rotation else 1
        self.rotated_size = int(size * rotation_multiplier)
        self.output_size = kwargs.get("output_size", None)
        self.size_scale = 1.0 if not self.output_size else self.output_size / size
        # endregion

        # region custom OSM properties
        if custom_osm and not os.path.isfile(custom_osm):
            raise FileNotFoundError(f"Custom OSM file {custom_osm} does not exist.")
        check_and_fix_osm(custom_osm, save_directory=self.map_directory)
        self.custom_osm = custom_osm
        # endregion

        # region custom DEM handling
        self.custom_background_path: str | None = None
        custom_dem = kwargs.get("custom_background_path", None)
        if custom_dem and not os.path.isfile(custom_dem):
            raise FileNotFoundError(f"Custom DEM file {custom_dem} does not exist.")

        # Make a copy of the custom DEM to the map directory.
        if custom_dem:
            save_path = os.path.join(self.map_directory, os.path.basename(custom_dem))
            shutil.copyfile(custom_dem, save_path)
            self.custom_background_path = save_path
        # endregion

        # region main settings
        main_settings = MainSettings.from_map(self)
        main_settings_json = main_settings.to_json()
        self.main_settings_path = os.path.join(self.map_directory, "main_settings.json")
        self._update_main_settings(main_settings_json)
        # endregion

        # region generation settings
        self.dem_settings = generation_settings.dem_settings
        self.background_settings = generation_settings.background_settings
        self.grle_settings = generation_settings.grle_settings
        self.i3d_settings = generation_settings.i3d_settings
        self.texture_settings = generation_settings.texture_settings
        self.satellite_settings = generation_settings.satellite_settings
        self.building_settings = generation_settings.building_settings
        self.process_settings()

        self.logger = logger if logger else Logger()
        self.generation_settings_json = generation_settings.to_json()

        # Store data for statistics sending after generation
        self.initial_main_settings_json = main_settings_json.copy()
        # endregion

        # region JSON data saving
        os.makedirs(self.map_directory, exist_ok=True)
        self.texture_custom_schema = kwargs.get("texture_custom_schema", None)
        self.tree_custom_schema = kwargs.get("tree_custom_schema", None)
        self.buildings_custom_schema = kwargs.get("buildings_custom_schema", None)

        json_data = {
            "generation_settings.json": self.generation_settings_json,
            "texture_custom_schema.json": self.texture_custom_schema,
            "tree_custom_schema.json": self.tree_custom_schema,
            "buildings_custom_schema.json": self.buildings_custom_schema,
        }

        for filename, data in json_data.items():
            self._dump_json(filename, self.map_directory, data)
        # endregion

        # region prepare map working directory
        custom_template_path = kwargs.get("custom_template_path", None)
        if custom_template_path:
            self.logger.info("Using custom map template: %s", custom_template_path)
            if not os.path.isfile(custom_template_path):
                self.logger.error(
                    "Custom map template file %s does not exist.", custom_template_path
                )
                raise FileNotFoundError(
                    f"Custom map template file {custom_template_path} does not exist."
                )
            template_path = custom_template_path
        else:
            self.logger.info("Using default map template: %s", game.template_path)
            template_path = game.template_path
        try:
            shutil.unpack_archive(template_path, self.map_directory)
            self.logger.debug("Map template unpacked to %s", self.map_directory)
        except Exception as e:
            raise RuntimeError(f"Can not unpack map template due to error: {e}") from e
        # endregion

        self.assets_directory = os.path.join(self.map_directory, "assets")
        os.makedirs(self.assets_directory, exist_ok=True)

        self.context = MapContext()
        self.components: list[Component] = []

    @staticmethod
    def _dump_json(filename: str, directory: str, data) -> None:
        """Write data to a JSON file, silently skipping falsy or empty data."""
        if not data:
            return
        if not isinstance(data, (dict, list)):
            raise TypeError("Data must be a dictionary or a list.")
        save_path = os.path.join(directory, filename)
        with open(save_path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)

    def process_settings(self) -> None:
        """Checks the settings by predefined rules and updates them accordingly."""
        if self.dem_settings.water_depth > 0:
            # Make sure that the plateau value is >= water_depth
            self.dem_settings.plateau = max(
                self.dem_settings.plateau, self.dem_settings.water_depth
            )

    @staticmethod
    def suggest_map_directory(coordinates: tuple[float, float], game_code: str) -> str:
        """Generate map directory path from coordinates and game code.

        Returns:
            str: Map directory path.
        """
        return os.path.join(Paths.DATA_DIR, Map.suggest_directory_name(coordinates, game_code))

    @staticmethod
    def suggest_directory_name(coordinates: tuple[float, float], game_code: str) -> str:
        """Generate directory name from coordinates and game code.

        Returns:
            str: Directory name.
        """
        from datetime import datetime

        lat, lon = coordinates
        latr = f"{lat:.3f}".replace(".", "_")
        lonr = f"{lon:.3f}".replace(".", "_")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{timestamp}_{game_code}_{latr}_{lonr}".lower()

    @property
    def texture_schema(self) -> list[dict[str, Any]] | None:
        """Return texture schema (custom if provided, default otherwise).

        Returns:
            list[dict[str, Any]] | None: Texture schema.
        """
        if self.texture_custom_schema:
            return self.texture_custom_schema
        with open(self.game.texture_schema, "r", encoding="utf-8") as file:
            return json.load(file)

    def generate(self) -> Generator[str, None, None]:
        """Launch map generation using all components. Yield component names during the process.

        Yields:
            Generator[str, None, None]: Component names.
        """
        with performance_session() as session_id:
            self.logger.info(
                "Starting map generation. Game code: %s. Coordinates: %s, size: %s. Rotation: %s.",
                self.game.code,
                self.coordinates,
                self.size,
                self.rotation,
            )
            generation_start = perf_counter()

            try:
                for game_component in self.game.components:
                    component = game_component(
                        self.game,
                        self,
                        self.coordinates,
                        self.size,
                        self.rotated_size,
                        self.rotation,
                        self.map_directory,
                        self.logger,
                        texture_custom_schema=self.texture_custom_schema,  # type: ignore
                        tree_custom_schema=self.tree_custom_schema,  # type: ignore
                    )
                    self.components.append(component)
                    component_name = component.__class__.__name__
                    self.logger.debug("Processing component: %s", component_name)

                    yield component_name

                    try:
                        component_start = perf_counter()
                        component.process()
                        component_finish = perf_counter()
                        self.logger.info(
                            "Component %s processed in %.2f seconds.",
                            component_name,
                            component_finish - component_start,
                        )
                        component.commit_generation_info()
                    except Exception as e:
                        self.logger.error(
                            "Error processing or committing generation info for component %s: %s",
                            component_name,
                            e,
                        )
                        self._update_main_settings({"error": f"{component_name} error: {repr(e)}"})
                        raise e

                generation_finish = perf_counter()
                self.logger.info(
                    "Map generation completed in %.2f seconds.",
                    generation_finish - generation_start,
                )

                self._update_main_settings({"completed": True})

                self.logger.info(
                    "Map generation completed. Game code: %s. Coordinates: %s, size: %s. Rotation: %s.",
                    self.game.code,
                    self.coordinates,
                    self.size,
                    self.rotation,
                )

            finally:
                self._save_metrics(session_id)

        if self.i3d_settings.self_clear:
            self.logger.info(
                "Self-clear is enabled. Clearing map directory: %s", self.map_directory
            )
            self.self_clear(self.map_directory)

    def _save_metrics(self, session_id: str) -> None:
        """Save logs and performance metrics to JSON files.

        Arguments:
            session_id (str): Session ID.
        """
        try:
            logs_json = self.logger.group_by_level(session_id)
            if logs_json:
                logs_filename = "generation_logs.json"
                with open(
                    os.path.join(self.map_directory, logs_filename), "w", encoding="utf-8"
                ) as file:
                    json.dump(logs_json, file, indent=4)
        except Exception as e:
            self.logger.error("Error saving logs to JSON: %s", e)

        try:
            session_json = PerformanceMonitor().pop_session_json(session_id)
            if session_json:
                report_filename = "performance_report.json"
                with open(
                    os.path.join(self.map_directory, report_filename), "w", encoding="utf-8"
                ) as file:
                    json.dump(session_json, file, indent=4)
                _stats.send_performance_report(session_json)
        except Exception as e:
            self.logger.error("Error saving performance report to JSON: %s", e)

        # Send statistics after generation is complete
        try:
            # Read the current main settings (which may have been updated during generation)
            if os.path.exists(self.main_settings_path):
                with open(self.main_settings_path, "r", encoding="utf-8") as file:
                    final_main_settings = json.load(file)
            else:
                final_main_settings = self.initial_main_settings_json.copy()

            # Ensure we preserve the is_public flag and other kwargs
            final_main_settings["is_public"] = self.kwargs.get("is_public", False)

            _stats.send_main_settings(final_main_settings)
            _stats.send_advanced_settings(self.generation_settings_json)
            self.logger.info("Statistics sent successfully after generation.")
        except Exception as e:
            self.logger.warning("Error sending statistics after generation: %s", e)

    def _update_main_settings(self, data: dict[str, Any]) -> None:
        """Update main settings with provided data.
        If the main settings file exists, it will be updated with the new data.
        If it does not exist, a new file will be created.

        Arguments:
            data (dict[str, Any]): Data to update main settings.
        """
        if os.path.exists(self.main_settings_path):
            with open(self.main_settings_path, "r", encoding="utf-8") as file:
                main_settings_json = json.load(file)

            main_settings_json.update(data)
        else:
            main_settings_json = data

        with open(self.main_settings_path, "w", encoding="utf-8") as file:
            json.dump(main_settings_json, file, indent=4)

    def get_component(self, component_name: str) -> Component | None:
        """Get component by name.

        Arguments:
            component_name (str): Name of the component.

        Returns:
            Component | None: Component instance or None if not found.
        """
        for component in self.components:
            if component.__class__.__name__ == component_name:
                return component
        return None

    def get_texture_component(self) -> Texture | None:
        """Get texture component.

        Returns:
            Texture | None: Texture instance or None if not found.
        """
        component = self.get_component("Texture")
        if not isinstance(component, Texture):
            return None
        return component

    def get_background_component(self) -> Background | None:
        """Get background component.

        Returns:
            Background | None: Background instance or None if not found.
        """
        component = self.get_component("Background")
        if not isinstance(component, Background):
            return None
        return component

    def get_satellite_component(self) -> Satellite | None:
        """Get satellite component.

        Returns:
            Satellite | None: Satellite instance or None if not found.
        """
        component = self.get_component("Satellite")
        if not isinstance(component, Satellite):
            return None
        return component

    def get_texture_layer(self, by_usage: str | None = None) -> Layer | None:
        """Get texture layer by usage.

        Arguments:
            by_usage (str, optional): Texture usage.

        Returns:
            Layer | None: Texture layer instance or None if not found.
        """
        texture_component = self.get_texture_component()
        if not texture_component:
            return None
        if by_usage:
            return texture_component.get_layer_by_usage(by_usage)
        return None

    def get_texture_layers(
        self,
        by_usage: str | None = None,
    ) -> None | list[Layer]:
        """Get texture layers by usage.

        Arguments:
            by_usage (str, optional): Texture usage.

        Returns:
            None | list[Layer]: List of texture layers.
        """
        texture_component = self.get_texture_component()
        if not texture_component:
            return None
        if by_usage:
            return texture_component.get_layers_by_usage(by_usage)
        return None

    def previews(self) -> list[str]:
        """Get list of preview images.

        Returns:
            list[str]: List of preview images.
        """
        previews = []
        for component in self.components:
            try:
                previews.extend(component.previews())
            except Exception as e:
                self.logger.error(
                    "Error getting previews for component %s: %s",
                    component.__class__.__name__,
                    e,
                )
        return previews

    def pack(self, archive_path: str, remove_source: bool = True) -> str:
        """Pack map directory to zip archive.

        Arguments:
            archive_path (str): Path to the archive.
            remove_source (bool, optional): Remove source directory after packing.

        Returns:
            str: Path to the archive.
        """
        archive_path = shutil.make_archive(archive_path, "zip", self.map_directory)
        self.logger.debug("Map packed to %s.zip", archive_path)
        if remove_source:
            try:
                shutil.rmtree(self.map_directory)
                self.logger.debug("Map directory removed: %s", self.map_directory)
            except Exception as e:
                self.logger.debug("Error removing map directory %s: %s", self.map_directory, e)
        return archive_path

    @staticmethod
    def self_clear(map_directory: str) -> None:
        """Clear map directory.

        Arguments:
            map_directory (str): Path to the map directory.
        """
        optional_directories = [
            "background",
            "buildings",
            "info_layers",
            "positions",
            "previews",
            "satellite",
            "scripts",
            "water",
            "roads",
        ]

        optional_files = [
            "main_settings.json",
            "generation_settings.json",
            "texture_custom_schema.json",
            "tree_custom_schema.json",
            "buildings_custom_schema.json",
            "generation_info.json",
            "generation_logs.json",
            "performance_report.json",
            "custom_osm.osm",
            "custom_dem.png",
        ]

        for directory in optional_directories:
            dir_path = os.path.join(map_directory, directory)
            if os.path.exists(dir_path):
                try:
                    shutil.rmtree(dir_path)
                except Exception:
                    pass

        for file in optional_files:
            file_path = os.path.join(map_directory, file)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception:
                    pass
