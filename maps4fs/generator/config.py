"""This module contains configuration files for the maps4fs generator."""

import io
import os
import shutil
import ssl
import tempfile
import zipfile
from urllib.error import URLError
from urllib.request import urlopen

from osmnx import settings as ox_settings

from maps4fs.generator.monitor import Logger

TQDM_DISABLE = os.getenv("TQDM_DISABLE", "0") == "1"
logger = Logger(name="MAPS4FS.CONFIG")
I3D_CONVERTER_NAME = "i3dConverter.exe"


def get_i3d_executable_path() -> str | None:
    """Get the path to the i3d_converter executable.

    Returns:
        str | None: The path to the i3d_converter executable, or None if not found.
    """
    # Check if the executable exists in the MFS_EXECUTABLES_DIR
    expected_path = os.path.join(MFS_EXECUTABLES_DIR, I3D_CONVERTER_NAME)
    if os.path.isfile(expected_path):
        logger.info("Found i3d_converter executable at: %s", expected_path)
        return expected_path

    logger.warning(
        "i3d_converter executable not found in %s. Please ensure it is placed there.",
        MFS_EXECUTABLES_DIR,
    )
    return None


def _urlopen_with_ssl_fallback(url: str) -> bytes:
    """Try to open a URL with SSL verification; on failure retry without it.

    Arguments:
        url (str): The URL to fetch.

    Returns:
        bytes: The response body.
    """
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


MFS_TEMPLATES_DIR = os.path.join(os.getcwd(), "templates")
MFS_EXECUTABLES_DIR = os.path.join(os.getcwd(), "executables")

MFS_DEFAULTS_DIR = os.path.join(os.getcwd(), "defaults")
MFS_LOCALE_DIR = os.path.join(os.getcwd(), "locale")
MFS_DEM_DEFAULTS_DIR = os.path.join(MFS_DEFAULTS_DIR, "dem")
MFS_OSM_DEFAULTS_DIR = os.path.join(MFS_DEFAULTS_DIR, "osm")
MFS_MSETTINGS_DEFAULTS_DIR = os.path.join(MFS_DEFAULTS_DIR, "main_settings")
MFS_GSETTINGS_DEFAULTS_DIR = os.path.join(MFS_DEFAULTS_DIR, "generation_settings")
default_dirs = [
    MFS_DEM_DEFAULTS_DIR,
    MFS_LOCALE_DIR,
    MFS_OSM_DEFAULTS_DIR,
    MFS_MSETTINGS_DEFAULTS_DIR,
    MFS_GSETTINGS_DEFAULTS_DIR,
    MFS_EXECUTABLES_DIR,
]
for directory in default_dirs:
    os.makedirs(directory, exist_ok=True)

logger.info("MFS_TEMPLATES_DIR: %s. MFS_DEFAULTS_DIR: %s.", MFS_TEMPLATES_DIR, MFS_DEFAULTS_DIR)
logger.info(
    "MFS_DEM_DEFAULTS_DIR: %s. MFS_OSM_DEFAULTS_DIR: %s. "
    "MFS_MSETTINGS_DEFAULTS_DIR: %s. MFS_GSETTINGS_DEFAULTS_DIR: %s.",
    MFS_DEM_DEFAULTS_DIR,
    MFS_OSM_DEFAULTS_DIR,
    MFS_MSETTINGS_DEFAULTS_DIR,
    MFS_GSETTINGS_DEFAULTS_DIR,
)

TEMPLATES_STRUCTURE = {
    "fs25": ["texture_schemas", "tree_schemas", "buildings_schemas", "map_templates"],
    "fs22": ["texture_schemas", "map_templates"],
}


def ensure_templates():
    """Ensure templates directory exists and is populated with data.

    If MFS_TEMPLATES_DIR is empty or doesn't exist, download the maps4fsdata
    repository and prepare the data files (no git required).
    """
    # Check if templates directory exists and has content
    if os.path.exists(MFS_TEMPLATES_DIR):
        logger.info("Templates directory already exists: %s", MFS_TEMPLATES_DIR)

        files = [
            entry
            for entry in os.listdir(MFS_TEMPLATES_DIR)
            if os.path.isfile(os.path.join(MFS_TEMPLATES_DIR, entry))
        ]

        if files:
            logger.info("Templates directory contains files and will not be modified.")
            return

    logger.info("Templates directory is empty or missing, preparing data...")

    # Create templates directory if it doesn't exist
    os.makedirs(MFS_TEMPLATES_DIR, exist_ok=True)

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            logger.info("Downloading maps4fsdata repository as ZIP archive...")

            # Download repository as ZIP from GitHub
            zip_url = "https://github.com/iwatkot/maps4fsdata/archive/refs/heads/main.zip"
            zip_data = _urlopen_with_ssl_fallback(zip_url)

            logger.info("Extracting repository archive...")
            with zipfile.ZipFile(io.BytesIO(zip_data)) as zip_ref:
                zip_ref.extractall(temp_dir)

            # The extracted folder will be named "maps4fsdata-main"
            repo_dir = os.path.join(temp_dir, "maps4fsdata-main")

            if not os.path.exists(repo_dir):
                raise FileNotFoundError(f"Expected repository directory not found: {repo_dir}")

            logger.info("Processing data files...")
            _prepare_data_python(repo_dir, MFS_TEMPLATES_DIR)
            logger.info("Templates data prepared successfully")

    except Exception as e:
        logger.error("Error preparing templates: %s", str(e))
        raise


def _prepare_data_python(repo_dir: str, output_dir: str) -> None:
    """Pure Python implementation of the prepare_data script.

    Processes fs* directories by:
    1. Copying top-level files to output directory
    2. Zipping subdirectories and placing them in output directory

    Arguments:
        repo_dir (str): Path to the extracted repository directory
        output_dir (str): Path where to place the prepared data files
    """
    # Find all directories starting with "fs" (e.g., fs22, fs25)
    fs_dirs = [
        d
        for d in os.listdir(repo_dir)
        if os.path.isdir(os.path.join(repo_dir, d)) and d.startswith("fs")
    ]

    for fs_dir_name in fs_dirs:
        fs_dir_path = os.path.join(repo_dir, fs_dir_name)
        logger.debug("Processing directory: %s", fs_dir_name)

        # Copy all top-level files from fs* directory to output directory
        for item in os.listdir(fs_dir_path):
            item_path = os.path.join(fs_dir_path, item)
            if os.path.isfile(item_path):
                logger.debug("Copying file %s to templates directory", item)
                shutil.copy2(item_path, output_dir)

        # Process subdirectories - create ZIP archives
        for item in os.listdir(fs_dir_path):
            item_path = os.path.join(fs_dir_path, item)
            if os.path.isdir(item_path):
                zip_file = os.path.join(output_dir, f"{item}.zip")
                logger.debug("Packing contents of %s into %s", item, zip_file)

                # Create ZIP archive of subdirectory contents
                with zipfile.ZipFile(zip_file, "w", zipfile.ZIP_DEFLATED) as zipf:
                    for root, _, files in os.walk(item_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            # Calculate relative path from the subdirectory
                            arcname = os.path.relpath(file_path, item_path)
                            zipf.write(file_path, arcname)

        logger.debug("Finished processing directory: %s", fs_dir_name)


def ensure_template_subdirs() -> None:
    """Ensure that all expected subdirectories exist in the templates directory."""
    for game_version, subdirs in TEMPLATES_STRUCTURE.items():
        for subdir in subdirs:
            dir_path = os.path.join(MFS_TEMPLATES_DIR, game_version, subdir)
            if not os.path.exists(dir_path):
                logger.debug("Expected template subdirectory missing: %s", dir_path)
                os.makedirs(dir_path, exist_ok=True)
    logger.info("Templates directory is ready at: %s", MFS_TEMPLATES_DIR)


def reload_templates() -> None:
    """Reload templates by removing existing files and re-preparing them.
    Does not affect nested directories containing user data.
    If needed, the files should be removed manually.
    """
    logger.info("Reloading templates...")
    # Remove files from the templates directory.
    # But do not remove nested directories, because they contain user data.
    # Only remove files in the top-level templates directory.
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


def ensure_locale() -> None:
    """Ensure locale directory is populated with up-to-date language files.

    Removes all existing files from MFS_LOCALE_DIR and downloads fresh
    language YML files from the maps4fslocale repository.
    """
    logger.info("Ensuring locale files are up-to-date...")

    # Remove all existing files in the locale directory
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


ensure_templates()
ensure_template_subdirs()
ensure_locale()

MFS_ROOT_DIR = os.getenv("MFS_ROOT_DIRECTORY", os.path.join(os.getcwd(), "mfsrootdir"))
MFS_CACHE_DIR = os.path.join(MFS_ROOT_DIR, "cache")
MFS_DATA_DIR = os.path.join(MFS_ROOT_DIR, "maps")
os.makedirs(MFS_CACHE_DIR, exist_ok=True)
os.makedirs(MFS_DATA_DIR, exist_ok=True)
logger.info(
    "MFS_ROOT_DIR: %s. MFS_CACHE_DIR: %s. MFS_DATA_DIR: %s.",
    MFS_ROOT_DIR,
    MFS_CACHE_DIR,
    MFS_DATA_DIR,
)

DTM_CACHE_DIR = os.path.join(MFS_CACHE_DIR, "dtm")
SAT_CACHE_DIR = os.path.join(MFS_CACHE_DIR, "sat")

osmnx_cache = os.path.join(MFS_CACHE_DIR, "osmnx")
osmnx_data = os.path.join(MFS_CACHE_DIR, "odata")

CACHE_DIRS = [DTM_CACHE_DIR, SAT_CACHE_DIR, osmnx_cache, osmnx_data]


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


create_cache_dirs()


ox_settings.cache_folder = osmnx_cache
ox_settings.data_folder = osmnx_data


def get_package_version(package_name: str) -> str:
    """Get the package version.

    Arguments:
        package_name (str): The name of the package to check.

    Returns:
        str: The version of the package, or "unknown" if it cannot be determined.
    """
    try:
        import importlib.metadata

        return importlib.metadata.version(package_name)
    except Exception:
        return "unknown"


PACKAGE_VERSION = get_package_version("maps4fs")
logger.info("maps4fs version: %s", PACKAGE_VERSION)
