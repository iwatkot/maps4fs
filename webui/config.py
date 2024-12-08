import os
import threading
from time import sleep

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

DOCS_DIRECTORY = os.path.join(WORKING_DIRECTORY, "docs")
MD_FILES = {"⛰️ DEM": "dem.md"}
FAQ_MD = os.path.join(DOCS_DIRECTORY, "FAQ.md")

REMOVE_DELAY = 30  # 5 minutes


def get_mds() -> dict[str, str]:
    return {
        md_file: os.path.join(DOCS_DIRECTORY, filename) for md_file, filename in MD_FILES.items()
    }


def is_on_community_server() -> bool:
    """Check if the script is running on the Streamlit Community server.

    Returns:
        bool: True if the script is running on the Streamlit Community server, False otherwise.
    """
    return os.environ.get(STREAMLIT_COMMUNITY_KEY) == STREAMLIT_COMMUNITY_VALUE


def remove_with_delay_without_blocking(
    file_path: str,
    logger: mfs.Logger,
    delay: int = REMOVE_DELAY,
) -> None:
    """Remove a file with a delay without blocking the main thread.

    Args:
        file_path (str): The path to the file to remove.
        logger (mfs.Logger): The logger instance.
        delay (int): The delay in seconds before removing the file.
    """

    def remove_file() -> None:
        logger.info("Removing file from %s in %d seconds.", file_path, delay)
        sleep(delay)
        try:
            os.remove(file_path)
            logger.info("File %s removed.", file_path)
        except FileNotFoundError:
            logger.warning("File %s not found.", file_path)

    logger.debug("Starting a new thread to remove the file %s.", file_path)
    threading.Thread(target=remove_file).start()
