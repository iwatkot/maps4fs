"""This module contains configuration files for the maps4fs generator."""

import os
import shutil
import subprocess
import tempfile

from osmnx import settings as ox_settings

from maps4fs.generator.monitor import Logger

TQDM_DISABLE = os.getenv("TQDM_DISABLE", "0") == "1"

logger = Logger(name="MAPS4FS.CONFIG")

MFS_TEMPLATES_DIR = os.path.join(os.getcwd(), "templates")

MFS_DEFAULTS_DIR = os.path.join(os.getcwd(), "defaults")
MFS_DEM_DEFAULTS_DIR = os.path.join(MFS_DEFAULTS_DIR, "dem")
MFS_OSM_DEFAULTS_DIR = os.path.join(MFS_DEFAULTS_DIR, "osm")
MFS_MSETTINGS_DEFAULTS_DIR = os.path.join(MFS_DEFAULTS_DIR, "main_settings")
MFS_GSETTINGS_DEFAULTS_DIR = os.path.join(MFS_DEFAULTS_DIR, "generation_settings")
default_dirs = [
    MFS_DEM_DEFAULTS_DIR,
    MFS_OSM_DEFAULTS_DIR,
    MFS_MSETTINGS_DEFAULTS_DIR,
    MFS_GSETTINGS_DEFAULTS_DIR,
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

    If MFS_TEMPLATES_DIR is empty or doesn't exist, clone the maps4fsdata
    repository and run the preparation script to populate it.
    """
    # Check if templates directory exists and has content
    if os.path.exists(MFS_TEMPLATES_DIR):  # and os.listdir(MFS_TEMPLATES_DIR):
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
            clone_dir = os.path.join(temp_dir, "maps4fsdata")

            logger.info("Cloning maps4fsdata repository to temporary directory...")
            # Clone the repository with depth 1 (shallow clone)
            subprocess.run(
                [
                    "git",
                    "clone",
                    "--depth",
                    "1",
                    "https://github.com/iwatkot/maps4fsdata.git",
                    clone_dir,
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            if os.name == "nt":
                logger.info("Detected Windows OS, running PowerShell preparation script...")
                prep_script = os.path.join(clone_dir, "prepare_data.ps1")
                for_subprocess = [
                    "powershell",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    "prepare_data.ps1",
                ]
            else:
                logger.info("Detected non-Windows OS, running bash preparation script...")
                prep_script = os.path.join(clone_dir, "prepare_data.sh")
                for_subprocess = ["./prepare_data.sh"]

            if os.path.exists(prep_script):
                try:
                    os.chmod(prep_script, 0o755)
                except Exception as e:
                    logger.warning("Could not set execute permissions on script: %s", str(e))

                logger.info("Running data preparation script...")
                # Run the preparation script from the cloned directory
                subprocess.run(
                    for_subprocess, cwd=clone_dir, check=True, capture_output=True, text=True
                )

                # Copy the generated data directory to templates directory
                data_src = os.path.join(clone_dir, "data")
                if os.path.exists(data_src):
                    logger.info(
                        "Copying prepared data to templates directory: %s", MFS_TEMPLATES_DIR
                    )
                    # Copy all files from data directory to MFS_TEMPLATES_DIR
                    for item in os.listdir(data_src):
                        src_path = os.path.join(data_src, item)
                        dst_path = os.path.join(MFS_TEMPLATES_DIR, item)
                        if os.path.isdir(src_path):
                            shutil.copytree(src_path, dst_path, dirs_exist_ok=True)
                        else:
                            shutil.copy2(src_path, dst_path)
                    logger.info("Templates data prepared successfully")
                else:
                    logger.error("Data directory not found after running preparation script")
                    raise FileNotFoundError(
                        "Data preparation script did not create expected data directory"
                    )
            else:
                logger.error("Preparation script not found: %s", prep_script)
                raise FileNotFoundError("prepare_data.sh not found in cloned repository")

    except subprocess.CalledProcessError as e:
        logger.error("Failed to prepare templates data: %s", str(e))
        if e.stdout:
            logger.error("Script stdout: %s", e.stdout)
        if e.stderr:
            logger.error("Script stderr: %s", e.stderr)
        raise
    except Exception as e:
        logger.error("Error preparing templates: %s", str(e))
        raise


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


ensure_templates()
ensure_template_subdirs()

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
        result = subprocess.run(
            [os.sys.executable, "-m", "pip", "show", package_name],  # type: ignore
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )
        for line in result.stdout.splitlines():
            if line.startswith("Version:"):
                return line.split(":", 1)[1].strip()
        return "unknown"
    except Exception:
        return "unknown"


PACKAGE_VERSION = get_package_version("maps4fs")
logger.info("maps4fs version: %s", PACKAGE_VERSION)
