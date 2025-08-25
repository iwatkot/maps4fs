"""This module contains configuration files for the maps4fs generator."""

import os
import shutil
import subprocess
import tempfile

from osmnx import settings as ox_settings

from maps4fs.logger import Logger

logger = Logger()

MFS_TEMPLATES_DIR = os.path.join(os.getcwd(), "templates")


def ensure_templates():
    """Ensure templates directory exists and is populated with data.

    If MFS_TEMPLATES_DIR is empty or doesn't exist, clone the maps4fsdata
    repository and run the preparation script to populate it.
    """

    # Check if templates directory exists and has content
    if os.path.exists(MFS_TEMPLATES_DIR) and os.listdir(MFS_TEMPLATES_DIR):
        logger.info("Templates directory already exists and contains data: %s", MFS_TEMPLATES_DIR)
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

            # Make the preparation script executable
            prep_script = os.path.join(clone_dir, "prepare_data.sh")
            if os.path.exists(prep_script):
                os.chmod(prep_script, 0o755)

                logger.info("Running data preparation script...")
                # Run the preparation script from the cloned directory
                subprocess.run(
                    ["./prepare_data.sh"], cwd=clone_dir, check=True, capture_output=True, text=True
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


ensure_templates()

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
