"""This module contains configuration files for the maps4fs generator."""

import os
import shutil
import subprocess

from osmnx import settings as ox_settings

from maps4fs.logger import Logger

logger = Logger()

DEFAULT_TEMPLATES_DIR = os.path.join(os.getcwd(), "data")
MFS_TEMPLATES_DIR = os.getenv("MFS_TEMPLATES_DIRECTORY")
if MFS_TEMPLATES_DIR is None:
    logger.info("MFS_TEMPLATES_DIRECTORY is not set. Using default templates directory.")
    MFS_TEMPLATES_DIR = DEFAULT_TEMPLATES_DIR
else:
    logger.info("MFS_TEMPLATES_DIRECTORY is set to: %s", MFS_TEMPLATES_DIR)
    if not os.path.isdir(MFS_TEMPLATES_DIR):
        logger.info("Templates directory %s does not exist. Creating it.", MFS_TEMPLATES_DIR)
        os.makedirs(MFS_TEMPLATES_DIR, exist_ok=True)

    # Check if there any files (directory is empty).
    if not os.listdir(MFS_TEMPLATES_DIR):
        logger.info("Templates directory %s is empty. Copying default files.", MFS_TEMPLATES_DIR)
        for item in os.listdir(DEFAULT_TEMPLATES_DIR):
            s = os.path.join(DEFAULT_TEMPLATES_DIR, item)
            d = os.path.join(MFS_TEMPLATES_DIR, item)
            if os.path.isdir(s):
                shutil.copytree(s, d, False, None)
            else:
                shutil.copy2(s, d)
        logger.info("Default files copied to %s.", MFS_TEMPLATES_DIR)
    else:
        logger.warning(
            "Templates directory %s is not empty. Will not copy default files. "
            "Ensure that the directory contains the necessary template files.",
            MFS_TEMPLATES_DIR,
        )

MFS_ROOT_DIR = os.getenv("MFS_ROOT_DIRECTORY", os.path.join(os.getcwd(), "mfsrootdir"))
MFS_CACHE_DIR = os.path.join(MFS_ROOT_DIR, "cache")
MFS_DATA_DIR = os.path.join(MFS_ROOT_DIR, "data")
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
os.makedirs(osmnx_cache, exist_ok=True)
os.makedirs(osmnx_data, exist_ok=True)


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
