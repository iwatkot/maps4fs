import os

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
