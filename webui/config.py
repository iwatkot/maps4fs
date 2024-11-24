import os

WORKING_DIRECTORY = os.getcwd()
ARCHIVES_DIRECTORY = os.path.join(WORKING_DIRECTORY, "archives")
MAPS_DIRECTORY = os.path.join(WORKING_DIRECTORY, "maps")
OSMPS_DIRECTORY = os.path.join(WORKING_DIRECTORY, "osmps")
os.makedirs(ARCHIVES_DIRECTORY, exist_ok=True)
os.makedirs(MAPS_DIRECTORY, exist_ok=True)
os.makedirs(OSMPS_DIRECTORY, exist_ok=True)

def print_all_env_vars(logger):
    logger.debug("All environment variables:")
    for key, value in os.environ.items():
        logger.debug(f"{key} = {value}")
