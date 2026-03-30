"""This module contains Map class, which is used to generate map using all components."""

from __future__ import annotations

import json
import os
import shutil
from time import perf_counter
from typing import Any, Generator

from pydtmdl import DTMProvider
from pydtmdl.base.dtm import DTMProviderSettings

from maps4fs.generator.component import Component
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
        output_size: int | None = None,
        texture_custom_schema: list[dict] | None = None,
        tree_custom_schema: list[dict] | None = None,
        buildings_custom_schema: list[dict] | None = None,
        electricity_custom_schema: list[dict] | None = None,
        custom_template_path: str | None = None,
        custom_background_path: str | None = None,
        **kwargs,
    ):

        self.game = game
        self.dtm_provider = dtm_provider
        self.dtm_provider_settings = dtm_provider_settings
        self.coordinates = coordinates
        self.size = size
        self.rotation = rotation
        self.output_size = output_size
        self._telemetry = kwargs
        self.logger = logger if logger else Logger()

        # When rotation is applied the raster canvas must be larger to cover the rotated area.
        self.rotated_size = int(size * 1.5) if rotation else size

        self.map_directory = map_directory or self.suggest_map_directory(
            coordinates=coordinates, game_code=game.code
        )
        game.set_map_directory(self.map_directory)
        os.makedirs(self.map_directory, exist_ok=True)

        # Domain-specific settings unpacked for convenient component access.
        self.dem_settings = generation_settings.dem_settings
        self.background_settings = generation_settings.background_settings
        self.grle_settings = generation_settings.grle_settings
        self.i3d_settings = generation_settings.i3d_settings
        self.texture_settings = generation_settings.texture_settings
        self.satellite_settings = generation_settings.satellite_settings
        self.building_settings = generation_settings.building_settings
        self._apply_settings_constraints()

        self.generation_settings_json = generation_settings.to_json()

        # Custom inputs.
        if custom_osm and not os.path.isfile(custom_osm):
            raise FileNotFoundError(f"Custom OSM file {custom_osm} does not exist.")
        check_and_fix_osm(custom_osm, save_directory=self.map_directory)
        self.custom_osm = custom_osm

        self.custom_background_path = self._copy_custom_dem(custom_background_path)

        # Custom schemas.
        self.texture_custom_schema = texture_custom_schema
        self.tree_custom_schema = tree_custom_schema
        self.buildings_custom_schema = buildings_custom_schema
        self.electricity_custom_schema = electricity_custom_schema

        # Persist settings to disk.
        self.main_settings_path = os.path.join(self.map_directory, "main_settings.json")
        main_settings = MainSettings.from_map(self)
        self._update_main_settings(main_settings.to_json())
        self._initial_main_settings = main_settings.to_json()

        self._save_json_files()

        # Unpack map template.
        self._unpack_template(custom_template_path or game.template_path)

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

    @property
    def size_scale(self) -> float:
        """Scale factor applied when output_size differs from size.

        Returns:
            float: Scale factor (1.0 when no output_size override).
        """
        return self.output_size / self.size if self.output_size else 1.0

    def _apply_settings_constraints(self) -> None:
        """Enforces inter-setting constraints (e.g. plateau must cover water depth)."""
        if self.dem_settings.water_depth > 0:
            self.dem_settings.plateau = max(
                self.dem_settings.plateau, self.dem_settings.water_depth
            )

    def _copy_custom_dem(self, custom_dem_path: str | None) -> str | None:
        """Copy a custom DEM file into the map directory.

        Arguments:
            custom_dem_path (str | None): Source path, or None to skip.

        Returns:
            str | None: Destination path, or None.
        """
        if not custom_dem_path:
            return None
        if not os.path.isfile(custom_dem_path):
            raise FileNotFoundError(f"Custom DEM file {custom_dem_path} does not exist.")
        save_path = os.path.join(self.map_directory, os.path.basename(custom_dem_path))
        shutil.copyfile(custom_dem_path, save_path)
        return save_path

    def _save_json_files(self) -> None:
        """Write generation settings and custom schemas to the map directory."""
        json_files = {
            "generation_settings.json": self.generation_settings_json,
            "texture_custom_schema.json": self.texture_custom_schema,
            "tree_custom_schema.json": self.tree_custom_schema,
            "buildings_custom_schema.json": self.buildings_custom_schema,
            "electricity_custom_schema.json": self.electricity_custom_schema,
        }
        for filename, data in json_files.items():
            self._dump_json(filename, self.map_directory, data)

    def _unpack_template(self, template_path: str) -> None:
        """Unpack the game map template archive into the map directory.

        Arguments:
            template_path (str): Path to the template archive.

        Raises:
            FileNotFoundError: If the template file does not exist.
            RuntimeError: If unpacking fails.
        """
        if not os.path.isfile(template_path):
            raise FileNotFoundError(f"Map template file {template_path} does not exist.")
        self.logger.info("Unpacking map template: %s", template_path)
        try:
            shutil.unpack_archive(template_path, self.map_directory)
            self.logger.debug("Map template unpacked to %s", self.map_directory)
        except Exception as e:
            raise RuntimeError(f"Can not unpack map template due to error: {e}") from e

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
                "Starting map generation. Game: %s, coords: %s, size: %s, rotation: %s.",
                self.game.code,
                self.coordinates,
                self.size,
                self.rotation,
            )
            generation_start = perf_counter()

            try:
                for game_component in self.game.components:
                    component = game_component(self.game, self)
                    self.components.append(component)
                    yield component.__class__.__name__
                    self._run_component(component)

                elapsed = perf_counter() - generation_start
                self.logger.info("Map generation completed in %.2f seconds.", elapsed)
                self._update_main_settings({"completed": True})
            finally:
                self._save_metrics(session_id)

        if self.i3d_settings.self_clear:
            self.logger.info(
                "Self-clear is enabled. Clearing map directory: %s", self.map_directory
            )
            self.self_clear(self.map_directory)

    def _run_component(self, component: Component) -> None:
        """Process a single component and commit its generation info.

        Arguments:
            component (Component): The component to run.

        Raises:
            Exception: Re-raises any exception from component processing.
        """
        name = component.__class__.__name__
        self.logger.debug("Processing component: %s", name)
        try:
            start = perf_counter()
            component.process()
            self.logger.debug(
                "Component %s processed in %.2f seconds.", name, perf_counter() - start
            )
            component.commit_generation_info()
        except Exception as e:
            self.logger.error("Error processing component %s: %s", name, e)
            self._update_main_settings({"error": f"{name} error: {repr(e)}"})
            raise

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
            if os.path.exists(self.main_settings_path):
                with open(self.main_settings_path, "r", encoding="utf-8") as file:
                    final_main_settings = json.load(file)
            else:
                final_main_settings = self._initial_main_settings.copy()

            final_main_settings["is_public"] = self._telemetry.get("is_public", False)

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
