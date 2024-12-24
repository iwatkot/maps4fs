import os
import threading
from time import sleep

import requests

import maps4fs as mfs

WORKING_DIRECTORY = os.getcwd()
ARCHIVES_DIRECTORY = os.path.join(WORKING_DIRECTORY, "archives")
MAPS_DIRECTORY = os.path.join(WORKING_DIRECTORY, "maps")
OSMPS_DIRECTORY = os.path.join(WORKING_DIRECTORY, "osmps")
TEMP_DIRECTORY = os.path.join(WORKING_DIRECTORY, "temp")
INPUT_DIRECTORY = os.path.join(TEMP_DIRECTORY, "input")
os.makedirs(ARCHIVES_DIRECTORY, exist_ok=True)
os.makedirs(MAPS_DIRECTORY, exist_ok=True)
os.makedirs(OSMPS_DIRECTORY, exist_ok=True)
os.makedirs(INPUT_DIRECTORY, exist_ok=True)


STREAMLIT_COMMUNITY_KEY = "HOSTNAME"
STREAMLIT_COMMUNITY_VALUE = "streamlit"
PUBLIC_HOSTNAME_KEY = "PUBLIC_HOSTNAME"
PUBLIC_HOSTNAME_VALUE = "maps4fs"

DOCS_DIRECTORY = os.path.join(WORKING_DIRECTORY, "docs")
MD_FILES = {
    "📁 Map structure": "map_structure.md",
    "⛰️ DEM": "dem.md",
    "🎨 Textures": "textures.md",
    "🌾 Farmlands": "farmlands.md",
    "🚜 Fields": "fields.md",
}
FAQ_MD = os.path.join(DOCS_DIRECTORY, "FAQ.md")

QUEUE_FILE = os.path.join(WORKING_DIRECTORY, "queue.json")
QUEUE_TIMEOUT = 180  # 3 minutes
QUEUE_INTERVAL = 10

REMOVE_DELAY = 300  # 5 minutes


def get_mds() -> dict[str, str]:
    """Get the paths to the Markdown files in the docs directory.

    Returns:
        dict[str, str]: The paths to the Markdown files in the docs directory.
    """
    return {
        md_file: os.path.join(DOCS_DIRECTORY, filename) for md_file, filename in MD_FILES.items()
    }


def is_on_community_server() -> bool:
    """Check if the script is running on the Streamlit Community server.

    Returns:
        bool: True if the script is running on the Streamlit Community server, False otherwise.
    """
    return os.environ.get(STREAMLIT_COMMUNITY_KEY) == STREAMLIT_COMMUNITY_VALUE


def is_public() -> bool:
    """Check if the script is running on a public server.

    Returns:
        bool: True if the script is running on a public server, False otherwise.
    """
    return os.environ.get(PUBLIC_HOSTNAME_KEY) == PUBLIC_HOSTNAME_VALUE


def remove_with_delay_without_blocking(
    file_path: str,
    logger: mfs.Logger,
    delay: int = REMOVE_DELAY,
) -> None:
    """Remove a file with a delay without blocking the main thread.

    Arguments:
        file_path (str): The path to the file to remove.
        logger (mfs.Logger): The logger instance.
        delay (int): The delay in seconds before removing the file.
    """

    def remove_file() -> None:
        logger.debug("Removing file from %s in %s seconds.", file_path, delay)
        sleep(delay)
        try:
            os.remove(file_path)
            logger.info("File %s removed.", file_path)
        except FileNotFoundError:
            logger.debug("File %s not found.", file_path)

    logger.debug("Starting a new thread to remove the file %s.", file_path)
    threading.Thread(target=remove_file).start()


def get_versions(logger: mfs.Logger) -> tuple[str, str] | None:
    """Get the latest version and the current version of the package.

    Returns:
        tuple[str, str] | None: The latest version and the current version if the package is not
            the latest version, None otherwise
    """
    try:
        response = requests.get("https://pypi.org/pypi/maps4fs/json")
        response.raise_for_status()

        latest_version = response.json()["info"]["version"]
        logger.debug("Latest version on PyPI: %s. Length: %s", latest_version, len(latest_version))

        current_version = get_package_version("maps4fs", logger)
        logger.debug("Current version: %s. Length: %s", current_version, len(current_version))

        return latest_version, current_version
    except Exception as e:
        logger.error("An error occurred while checking the package version: %s", e)
        return


def get_package_version(package_name: str, logger: mfs.Logger) -> str:
    """Get the package version.

    Returns:
        str: The package version.
    """
    response = os.popen(f"pip list | grep {package_name}").read()
    logger.debug("Grepped response: %s", response)
    cleared_response = response.replace(" ", "")
    logger.debug("Cleared response: %s", cleared_response)
    return response.replace(package_name, "").strip()
