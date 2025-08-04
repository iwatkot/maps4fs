"""This module contains configuration files for the maps4fs generator."""

import os
import subprocess

from osmnx import settings as ox_settings

MFS_ROOT_DIR = os.getenv("MFS_ROOT_DIRECTORY", os.path.join(os.getcwd(), "mfsrootdir"))
MFS_CACHE_DIR = os.path.join(MFS_ROOT_DIR, "cache")
MFS_DATA_DIR = os.path.join(MFS_ROOT_DIR, "data")
os.makedirs(MFS_CACHE_DIR, exist_ok=True)
os.makedirs(MFS_DATA_DIR, exist_ok=True)

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
