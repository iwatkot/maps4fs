"""Bootstrap / setup functions for the maps4fs generator.

All functions here have observable side effects (network requests, filesystem
mutations, global osmnx settings), so they are isolated from pure constants.

Call :func:`bootstrap` once at application start-up. ``config.py`` calls it
automatically for backward compatibility.
"""

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

from maps4fs.generator.constants import (
    CACHE_DIRS,
    I3D_CONVERTER_NAME,
    I3D_CONVERTER_REMOTE_URL,
    MFS_DEM_DEFAULTS_DIR,
    MFS_EXECUTABLES_DIR,
    MFS_GSETTINGS_DEFAULTS_DIR,
    MFS_LOCALE_DIR,
    MFS_MSETTINGS_DEFAULTS_DIR,
    MFS_OSM_DEFAULTS_DIR,
    MFS_TEMPLATES_DIR,
    OSMNX_CACHE_DIR,
    OSMNX_DATA_DIR,
    TEMPLATES_STRUCTURE,
    TEXCONV_NAME,
    TEXCONV_REMOTE_URL,
)
from maps4fs.generator.monitor import Logger

logger = Logger(name="MAPS4FS.BOOTSTRAP")

# ---- Internal network helper ------------------------------------------------


def _urlopen_with_ssl_fallback(url: str) -> bytes:
    """Fetch *url*, retrying without SSL verification on certificate errors."""
    try:
        with urlopen(url) as response:
            return response.read()
    except (ssl.SSLError, URLError) as e:
        logger.warning(
            "SSL verification failed (%s), retrying without certificate verification...", str(e)
        )
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with urlopen(url, context=ctx) as response:
            return response.read()


# ---- Directory setup --------------------------------------------------------


def create_cache_dirs() -> None:
    """Create cache directories if they do not exist."""
    logger.info("Ensuring cache directories exist...")
    for cache_dir in CACHE_DIRS:
        os.makedirs(cache_dir, exist_ok=True)
        logger.debug("Cache directory ensured: %s", cache_dir)
    logger.info("All cache directories are ready.")


def clean_cache() -> None:
    """Clean all cache directories by removing and recreating them."""
    logger.info("Cleaning cache directories...")
    for cache_dir in CACHE_DIRS:
        if os.path.exists(cache_dir):
            shutil.rmtree(cache_dir)
            logger.debug("Removed cache directory: %s", cache_dir)
    create_cache_dirs()
    logger.info("Cache directories cleaned and recreated.")


# ---- Template management ----------------------------------------------------


def _prepare_data_python(repo_dir: str, output_dir: str) -> None:
    """Copy top-level files and zip subdirectories from a checked-out data repo.

    Arguments:
        repo_dir: Path to the extracted repository directory.
        output_dir: Destination directory for prepared data files.
    """
    fs_dirs = [
        d
        for d in os.listdir(repo_dir)
        if os.path.isdir(os.path.join(repo_dir, d)) and d.startswith("fs")
    ]

    for fs_dir_name in fs_dirs:
        fs_dir_path = os.path.join(repo_dir, fs_dir_name)
        logger.debug("Processing directory: %s", fs_dir_name)

        for item in os.listdir(fs_dir_path):
            item_path = os.path.join(fs_dir_path, item)
            if os.path.isfile(item_path):
                logger.debug("Copying file %s to templates directory", item)
                shutil.copy2(item_path, output_dir)

        for item in os.listdir(fs_dir_path):
            item_path = os.path.join(fs_dir_path, item)
            if os.path.isdir(item_path):
                zip_file = os.path.join(output_dir, f"{item}.zip")
                logger.debug("Packing contents of %s into %s", item, zip_file)
                with zipfile.ZipFile(zip_file, "w", zipfile.ZIP_DEFLATED) as zipf:
                    for root, _, files in os.walk(item_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, item_path)
                            zipf.write(file_path, arcname)

        logger.debug("Finished processing directory: %s", fs_dir_name)


def ensure_templates() -> None:
    """Ensure templates directory exists and is populated.

    Downloads the maps4fsdata repository if MFS_TEMPLATES_DIR is empty or absent.
    """
    if os.path.exists(MFS_TEMPLATES_DIR):
        logger.info("Templates directory already exists: %s", MFS_TEMPLATES_DIR)
        files = [
            e
            for e in os.listdir(MFS_TEMPLATES_DIR)
            if os.path.isfile(os.path.join(MFS_TEMPLATES_DIR, e))
        ]
        if files:
            logger.info("Templates directory contains files and will not be modified.")
            return

    logger.info("Templates directory is empty or missing, preparing data...")
    os.makedirs(MFS_TEMPLATES_DIR, exist_ok=True)

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            logger.info("Downloading maps4fsdata repository as ZIP archive...")
            zip_url = "https://github.com/iwatkot/maps4fsdata/archive/refs/heads/main.zip"
            zip_data = _urlopen_with_ssl_fallback(zip_url)

            logger.info("Extracting repository archive...")
            with zipfile.ZipFile(io.BytesIO(zip_data)) as zip_ref:
                zip_ref.extractall(temp_dir)

            repo_dir = os.path.join(temp_dir, "maps4fsdata-main")
            if not os.path.exists(repo_dir):
                raise FileNotFoundError(f"Expected repository directory not found: {repo_dir}")

            logger.info("Processing data files...")
            _prepare_data_python(repo_dir, MFS_TEMPLATES_DIR)
            logger.info("Templates data prepared successfully")

    except Exception as e:
        logger.error("Error preparing templates: %s", str(e))
        raise


def ensure_template_subdirs() -> None:
    """Ensure all expected subdirectories exist under MFS_TEMPLATES_DIR."""
    for game_version, subdirs in TEMPLATES_STRUCTURE.items():
        for subdir in subdirs:
            dir_path = os.path.join(MFS_TEMPLATES_DIR, game_version, subdir)
            if not os.path.exists(dir_path):
                logger.debug("Expected template subdirectory missing: %s", dir_path)
                os.makedirs(dir_path, exist_ok=True)
    logger.info("Templates directory is ready at: %s", MFS_TEMPLATES_DIR)


def reload_templates() -> None:
    """Remove top-level template files and re-download them from remote.

    Nested directories (containing user data) are untouched.
    """
    logger.info("Reloading templates...")
    for item in os.listdir(MFS_TEMPLATES_DIR):
        item_path = os.path.join(MFS_TEMPLATES_DIR, item)
        if os.path.isfile(item_path):
            try:
                os.remove(item_path)
            except Exception as e:
                logger.warning("Could not remove file %s: %s", item_path, str(e))
    ensure_templates()
    ensure_template_subdirs()
    logger.info("Templates reloaded successfully.")


# ---- Locale -----------------------------------------------------------------


def ensure_locale() -> None:
    """Ensure locale directory is populated with up-to-date language files.

    Removes stale files and downloads fresh YML files from maps4fslocale.
    """
    logger.info("Ensuring locale files are up-to-date...")

    if os.path.exists(MFS_LOCALE_DIR):
        for item in os.listdir(MFS_LOCALE_DIR):
            item_path = os.path.join(MFS_LOCALE_DIR, item)
            if os.path.isfile(item_path):
                try:
                    os.remove(item_path)
                    logger.debug("Removed locale file: %s", item_path)
                except Exception as e:
                    logger.warning("Could not remove locale file %s: %s", item_path, str(e))

    os.makedirs(MFS_LOCALE_DIR, exist_ok=True)

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            logger.info("Downloading maps4fslocale repository as ZIP archive...")
            zip_url = "https://github.com/iwatkot/maps4fslocale/archive/refs/heads/main.zip"
            zip_data = _urlopen_with_ssl_fallback(zip_url)

            logger.info("Extracting locale archive...")
            with zipfile.ZipFile(io.BytesIO(zip_data)) as zip_ref:
                zip_ref.extractall(temp_dir)

            repo_dir = os.path.join(temp_dir, "maps4fslocale-main")
            if not os.path.exists(repo_dir):
                raise FileNotFoundError(f"Expected repository directory not found: {repo_dir}")
            languages_dir = os.path.join(repo_dir, "languages")
            if not os.path.exists(languages_dir):
                raise FileNotFoundError(f"Expected languages directory not found: {languages_dir}")

            for item in os.listdir(languages_dir):
                if item.endswith(".yml"):
                    src = os.path.join(languages_dir, item)
                    dst = os.path.join(MFS_LOCALE_DIR, item)
                    shutil.copy2(src, dst)
                    logger.debug("Copied locale file: %s", item)

            logger.info("Locale files updated successfully in: %s", MFS_LOCALE_DIR)

    except Exception as e:
        logger.error("Error updating locale files: %s", str(e))
        raise


# ---- Executables ------------------------------------------------------------


def ensure_executables() -> None:
    """Download required Windows executables if absent.

    No-op on non-Windows platforms.
    """
    if os.name != "nt":
        return

    required = [
        (I3D_CONVERTER_NAME, I3D_CONVERTER_REMOTE_URL),
        (TEXCONV_NAME, TEXCONV_REMOTE_URL),
    ]

    logger.info("Checking for required executables in: %s", MFS_EXECUTABLES_DIR)

    for executable_name, remote_url in required:
        expected_path = os.path.join(MFS_EXECUTABLES_DIR, executable_name)
        if os.path.isfile(expected_path):
            logger.info("%s already present at: %s", executable_name, expected_path)
            continue

        logger.info("%s not found, downloading from %s...", executable_name, remote_url)
        try:
            data = _urlopen_with_ssl_fallback(remote_url)
            with open(expected_path, "wb") as f:
                f.write(data)
            logger.info("Downloaded %s to: %s", executable_name, expected_path)
        except Exception as e:
            logger.warning("Could not download %s: %s", executable_name, e)

    logger.info("Executable check complete.")


# ---- Package version --------------------------------------------------------


def get_package_version(package_name: str) -> str:
    """Return the installed version of *package_name*, or ``"unknown"``."""
    try:
        return importlib.metadata.version(package_name)
    except Exception:
        return "unknown"


# ---- Bootstrap entry point --------------------------------------------------


def bootstrap() -> None:
    """Run all one-time setup steps.

    Safe to call multiple times (individual functions are idempotent or
    guarded). Call once at application startup before generating any maps.
    """
    _ensure_default_dirs()
    create_cache_dirs()
    ensure_templates()
    ensure_template_subdirs()
    ensure_locale()
    ensure_executables()
    ox_settings.cache_folder = OSMNX_CACHE_DIR
    ox_settings.data_folder = OSMNX_DATA_DIR
    logger.info("Bootstrap complete. maps4fs version: %s", get_package_version("maps4fs"))


def _ensure_default_dirs() -> None:
    """Create static default/asset directories that must exist before other steps."""
    for directory in [
        MFS_DEM_DEFAULTS_DIR,
        MFS_LOCALE_DIR,
        MFS_OSM_DEFAULTS_DIR,
        MFS_MSETTINGS_DEFAULTS_DIR,
        MFS_GSETTINGS_DEFAULTS_DIR,
        MFS_EXECUTABLES_DIR,
    ]:
        os.makedirs(directory, exist_ok=True)
