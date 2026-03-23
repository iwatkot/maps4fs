"""Bootstrap / setup for the maps4fs generator.

All methods here have observable side effects (network requests, filesystem
mutations, global osmnx settings), so they are isolated from pure constants.

Call ``Bootstrap.run()`` once at application start-up.
"""

from __future__ import annotations

import importlib.metadata
import io
import os
import shutil
import ssl
import tempfile
import zipfile
from urllib.error import URLError
from urllib.request import urlopen

from osmnx import settings as ox_settings

from maps4fs.generator.constants import Paths
from maps4fs.generator.monitor import Logger

_logger = Logger(name="MAPS4FS.BOOTSTRAP")


class Bootstrap:
    """One-stop shop for all application setup tasks.

    All methods are static — there is no instance state.  Call
    ``Bootstrap.run()`` at startup; the individual methods are available for
    finer-grained control (e.g. ``Bootstrap.clean_cache()`` from a UI action).
    """

    # ---- Package version ------------------------------------------------

    @staticmethod
    def package_version(package_name: str = "maps4fs") -> str:
        """Return the installed version of a package, or ``"unknown"``.

        Arguments:
            package_name (str): Name of the installed Python package.

        Returns:
            str: Installed package version or ``"unknown"`` on lookup failure.
        """
        try:
            return importlib.metadata.version(package_name)
        except Exception:
            return "unknown"

    # ---- Network helper -------------------------------------------------

    @staticmethod
    def _fetch(url: str) -> bytes:
        """Fetch remote content as bytes with SSL fallback handling.

        Arguments:
            url (str): Absolute URL to fetch.

        Returns:
            bytes: Response body.

        Raises:
            URLError: If the request fails after retry attempts.
        """
        try:
            with urlopen(url) as response:
                return response.read()
        except (ssl.SSLError, URLError) as e:
            _logger.warning(
                "SSL verification failed (%s), retrying without certificate verification...",
                str(e),
            )
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            with urlopen(url, context=ctx) as response:
                return response.read()

    # ---- Directory setup ------------------------------------------------

    @staticmethod
    def create_default_dirs() -> None:
        """Create static default/asset directories that must exist before other steps."""
        for directory in [
            Paths.DEM_DEFAULTS_DIR,
            Paths.LOCALE_DIR,
            Paths.OSM_DEFAULTS_DIR,
            Paths.MSETTINGS_DEFAULTS_DIR,
            Paths.GSETTINGS_DEFAULTS_DIR,
            Paths.EXECUTABLES_DIR,
        ]:
            os.makedirs(directory, exist_ok=True)

    @staticmethod
    def create_cache_dirs() -> None:
        """Create cache directories if they do not exist."""
        _logger.info("Ensuring cache directories exist...")
        for cache_dir in Paths.CACHE_DIRS:
            os.makedirs(cache_dir, exist_ok=True)
            _logger.debug("Cache directory ensured: %s", cache_dir)
        _logger.info("All cache directories are ready.")

    @staticmethod
    def clean_cache() -> None:
        """Clean all cache directories by removing and recreating them."""
        _logger.info("Cleaning cache directories...")
        for cache_dir in Paths.CACHE_DIRS:
            if os.path.exists(cache_dir):
                shutil.rmtree(cache_dir)
                _logger.debug("Removed cache directory: %s", cache_dir)
        Bootstrap.create_cache_dirs()
        _logger.info("Cache directories cleaned and recreated.")

    # ---- Template management --------------------------------------------

    @staticmethod
    def _prepare_data(repo_dir: str, output_dir: str) -> None:
        """Copy files and package subdirectories from a data repository checkout.

        Arguments:
            repo_dir (str): Path to extracted repository root.
            output_dir (str): Destination templates directory.
        """
        fs_dirs = [
            d
            for d in os.listdir(repo_dir)
            if os.path.isdir(os.path.join(repo_dir, d)) and d.startswith("fs")
        ]
        for fs_dir_name in fs_dirs:
            fs_dir_path = os.path.join(repo_dir, fs_dir_name)
            _logger.debug("Processing directory: %s", fs_dir_name)
            for item in os.listdir(fs_dir_path):
                item_path = os.path.join(fs_dir_path, item)
                if os.path.isfile(item_path):
                    _logger.debug("Copying file %s to templates directory", item)
                    shutil.copy2(item_path, output_dir)
            for item in os.listdir(fs_dir_path):
                item_path = os.path.join(fs_dir_path, item)
                if os.path.isdir(item_path):
                    zip_file = os.path.join(output_dir, f"{item}.zip")
                    _logger.debug("Packing contents of %s into %s", item, zip_file)
                    with zipfile.ZipFile(zip_file, "w", zipfile.ZIP_DEFLATED) as zipf:
                        for root, _, files in os.walk(item_path):
                            for file in files:
                                file_path = os.path.join(root, file)
                                arcname = os.path.relpath(file_path, item_path)
                                zipf.write(file_path, arcname)
            _logger.debug("Finished processing directory: %s", fs_dir_name)

        # Handle any top-level directories non-conforming to "fs*" pattern (e.g. "common").
        other_dirs = [
            d
            for d in os.listdir(repo_dir)
            if os.path.isdir(os.path.join(repo_dir, d)) and not d.startswith("fs")
        ]
        for other_dir_name in other_dirs:
            # Copy directories as-is without zipping, since they likely contain shared assets.
            other_dir_path = os.path.join(repo_dir, other_dir_name)
            _logger.debug("Copying non-fs directory %s to templates directory", other_dir_name)
            template_dir_path = os.path.join(output_dir, other_dir_name)
            shutil.copytree(other_dir_path, template_dir_path, dirs_exist_ok=True)

    @staticmethod
    def ensure_templates() -> None:
        """Ensure templates directory exists and is populated.

        Downloads the maps4fsdata repository if the directory is empty or absent.

        Raises:
            FileNotFoundError: If expected extracted repository paths are missing.
            Exception: Propagates unexpected download/extraction/copy errors.
        """
        if os.path.exists(Paths.TEMPLATES_DIR):
            _logger.info("Templates directory already exists: %s", Paths.TEMPLATES_DIR)
            files = [
                e
                for e in os.listdir(Paths.TEMPLATES_DIR)
                if os.path.isfile(os.path.join(Paths.TEMPLATES_DIR, e))
            ]
            if files:
                _logger.info("Templates directory contains files and will not be modified.")
                return

        _logger.info("Templates directory is empty or missing, preparing data...")
        os.makedirs(Paths.TEMPLATES_DIR, exist_ok=True)

        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                _logger.info("Downloading maps4fsdata repository as ZIP archive...")
                zip_url = "https://github.com/iwatkot/maps4fsdata/archive/refs/heads/shared.zip"
                zip_data = Bootstrap._fetch(zip_url)

                _logger.info("Extracting repository archive...")
                with zipfile.ZipFile(io.BytesIO(zip_data)) as zip_ref:
                    zip_ref.extractall(temp_dir)

                repo_dir = os.path.join(temp_dir, "maps4fsdata-shared")
                if not os.path.exists(repo_dir):
                    raise FileNotFoundError(f"Expected repository directory not found: {repo_dir}")

                _logger.info("Processing data files...")
                Bootstrap._prepare_data(repo_dir, Paths.TEMPLATES_DIR)
                _logger.info("Templates data prepared successfully")

        except Exception as e:
            _logger.error("Error preparing templates: %s", str(e))
            raise

    @staticmethod
    def ensure_template_subdirs() -> None:
        """Ensure all expected subdirectories exist under TEMPLATES_DIR."""
        for game_version, subdirs in Paths.TEMPLATES_STRUCTURE.items():
            for subdir in subdirs:
                dir_path = os.path.join(Paths.TEMPLATES_DIR, game_version, subdir)
                if not os.path.exists(dir_path):
                    _logger.debug("Expected template subdirectory missing: %s", dir_path)
                    os.makedirs(dir_path, exist_ok=True)
        _logger.info("Templates directory is ready at: %s", Paths.TEMPLATES_DIR)

    @staticmethod
    def reload_templates() -> None:
        """Remove top-level template files and re-download them from remote.

        Nested directories (containing user data) are untouched.
        """
        _logger.info("Reloading templates...")
        for item in os.listdir(Paths.TEMPLATES_DIR):
            item_path = os.path.join(Paths.TEMPLATES_DIR, item)
            if os.path.isfile(item_path):
                try:
                    os.remove(item_path)
                except Exception as e:
                    _logger.warning("Could not remove file %s: %s", item_path, str(e))
        Bootstrap.ensure_templates()
        Bootstrap.ensure_template_subdirs()
        _logger.info("Templates reloaded successfully.")

    # ---- Locale ---------------------------------------------------------

    @staticmethod
    def ensure_locale() -> None:
        """Ensure locale directory is populated with up-to-date language files.

        Raises:
            FileNotFoundError: If expected extracted locale paths are missing.
            Exception: Propagates unexpected download/extraction/copy errors.
        """
        _logger.info("Ensuring locale files are up-to-date...")

        if os.path.exists(Paths.LOCALE_DIR):
            for item in os.listdir(Paths.LOCALE_DIR):
                item_path = os.path.join(Paths.LOCALE_DIR, item)
                if os.path.isfile(item_path):
                    try:
                        os.remove(item_path)
                        _logger.debug("Removed locale file: %s", item_path)
                    except Exception as e:
                        _logger.warning("Could not remove locale file %s: %s", item_path, str(e))

        os.makedirs(Paths.LOCALE_DIR, exist_ok=True)

        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                _logger.info("Downloading maps4fslocale repository as ZIP archive...")
                zip_url = "https://github.com/iwatkot/maps4fslocale/archive/refs/heads/main.zip"
                zip_data = Bootstrap._fetch(zip_url)

                _logger.info("Extracting locale archive...")
                with zipfile.ZipFile(io.BytesIO(zip_data)) as zip_ref:
                    zip_ref.extractall(temp_dir)

                repo_dir = os.path.join(temp_dir, "maps4fslocale-main")
                if not os.path.exists(repo_dir):
                    raise FileNotFoundError(f"Expected repository directory not found: {repo_dir}")
                languages_dir = os.path.join(repo_dir, "languages")
                if not os.path.exists(languages_dir):
                    raise FileNotFoundError(
                        f"Expected languages directory not found: {languages_dir}"
                    )

                for item in os.listdir(languages_dir):
                    if item.endswith(".yml"):
                        src = os.path.join(languages_dir, item)
                        dst = os.path.join(Paths.LOCALE_DIR, item)
                        shutil.copy2(src, dst)
                        _logger.debug("Copied locale file: %s", item)

                _logger.info("Locale files updated successfully in: %s", Paths.LOCALE_DIR)

        except Exception as e:
            _logger.error("Error updating locale files: %s", str(e))
            raise

    # ---- Executables ----------------------------------------------------

    @staticmethod
    def ensure_executables() -> None:
        """Download required Windows executables if absent.

        No-op on non-Windows platforms.
        """
        if os.name != "nt":
            return

        required = [
            (Paths.I3D_CONVERTER_NAME, Paths.I3D_CONVERTER_REMOTE_URL),
            (Paths.TEXCONV_NAME, Paths.TEXCONV_REMOTE_URL),
        ]

        _logger.info("Checking for required executables in: %s", Paths.EXECUTABLES_DIR)

        for executable_name, remote_url in required:
            expected_path = os.path.join(Paths.EXECUTABLES_DIR, executable_name)
            if os.path.isfile(expected_path):
                _logger.info("%s already present at: %s", executable_name, expected_path)
                continue

            _logger.info("%s not found, downloading from %s...", executable_name, remote_url)
            try:
                data = Bootstrap._fetch(remote_url)
                with open(expected_path, "wb") as f:
                    f.write(data)
                _logger.info("Downloaded %s to: %s", executable_name, expected_path)
            except Exception as e:
                _logger.warning("Could not download %s: %s", executable_name, e)

        _logger.info("Executable check complete.")

    # ---- Entry point ----------------------------------------------------

    @staticmethod
    def run() -> None:
        """Run all one-time setup steps.

        Idempotent — safe to call multiple times.  Call once at application
        startup before generating any maps.
        """
        Bootstrap.create_default_dirs()
        Bootstrap.create_cache_dirs()
        Bootstrap.ensure_templates()
        Bootstrap.ensure_template_subdirs()
        Bootstrap.ensure_locale()
        Bootstrap.ensure_executables()
        ox_settings.cache_folder = Paths.OSMNX_CACHE_DIR
        ox_settings.data_folder = Paths.OSMNX_DATA_DIR
        _logger.info("Bootstrap complete. maps4fs version: %s", Bootstrap.package_version())
