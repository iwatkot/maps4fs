import os

WORKING_DIRECTORY = os.getcwd()
ARCHIVES_DIRECTORY = os.path.join(WORKING_DIRECTORY, "archives")
MAPS_DIRECTORY = os.path.join(WORKING_DIRECTORY, "maps")
OSMPS_DIRECTORY = os.path.join(WORKING_DIRECTORY, "osmps")
os.makedirs(ARCHIVES_DIRECTORY, exist_ok=True)
os.makedirs(MAPS_DIRECTORY, exist_ok=True)
os.makedirs(OSMPS_DIRECTORY, exist_ok=True)

STREAMLIT_COMMUNITY_KEY = "HOSTNAME"
STREAMLIT_COMMUNITY_VALUE = "streamlit"


def is_on_community_server() -> bool:
    """Check if the script is running on the Streamlit Community server.

    Returns:
        bool: True if the script is running on the Streamlit Community server, False otherwise.
    """
    return os.environ.get(STREAMLIT_COMMUNITY_KEY) == STREAMLIT_COMMUNITY_VALUE
