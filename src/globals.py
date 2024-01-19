import os
import shutil

from rich.console import Console

console = Console()
WORKING_DIR = os.getcwd()
console.log(f"Working directory: {WORKING_DIR}")
MOD_SAVE_PATH = os.path.join(WORKING_DIR, "FS22_MapTemplate")

DATA_DIR = os.path.join(WORKING_DIR, "data")
TEMPLATE_ARCHIVE = os.path.join(DATA_DIR, "map-template.zip")

MAP_SIZE = (2048, 2048)
console.log(f"Map size: {MAP_SIZE}")

if not os.path.isfile(TEMPLATE_ARCHIVE):
    raise FileNotFoundError(
        f"Template archive not found: {TEMPLATE_ARCHIVE}. Please clone the repository again."
    )

OUTPUT_DIR = os.path.join(WORKING_DIR, "output")
console.log(f"Output directory: {OUTPUT_DIR}")
if not os.path.isdir(OUTPUT_DIR):
    os.mkdir(OUTPUT_DIR)
    console.log("Output directory created.")
else:
    console.log("Output directory already exists and will be deleted.")
    shutil.rmtree(OUTPUT_DIR)
    os.mkdir(OUTPUT_DIR)

shutil.unpack_archive(TEMPLATE_ARCHIVE, OUTPUT_DIR)
console.log("Template archive unpacked.")

weights_dir = os.path.join(OUTPUT_DIR, "maps", "map", "data")
# weights_files = [
#     os.path.join(weights_dir, f) for f in os.listdir(weights_dir) if f.endswith("_weight.png")
# ]
# console.log(f"Fetched {len(weights_files)} weight files.")


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


# ! DEBUG SECTION
game_mod_path = "C:\\Users\\iwatk\\OneDrive\\Documents\\My Games\\FarmingSimulator2022\\mods\\FS22_MapTemplate.zip"
try:
    os.remove(game_mod_path)
    console.log(f"Removed old mod file: {game_mod_path}")
except FileNotFoundError:
    pass
