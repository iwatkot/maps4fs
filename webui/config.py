import os

WORKING_DIRECTORY = os.getcwd()
ARCHIVES_DIRECTORY = os.path.join(WORKING_DIRECTORY, "archives")
MAPS_DIRECTORY = os.path.join(WORKING_DIRECTORY, "maps")
os.makedirs(ARCHIVES_DIRECTORY, exist_ok=True)
os.makedirs(MAPS_DIRECTORY, exist_ok=True)
