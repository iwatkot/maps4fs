# This is a demo script that shows how to use the maps4fs library.
# Option 1: To use from the source code:
# ➡️ git clone https://github.com/iwatkot/maps4fs.git
# ➡️ cd maps4fs
# For Windows
# ➡️ dev/create_venv.ps1
# ➡️ ./venv/scripts/activate
# For Linux
# ➡️ sh dev/create_venv.sh
# ➡️ source venv/bin/activate
# Option 2: To install as PyPI package:
# Create a new virtual environment.
# ➡️ pip install maps4fs
# Edit the demo.py file
# And run the script
# ➡️ python demo.py

import json
import os
import shutil

import maps4fs as mfs

# 1️⃣ Define the game (FS22 or FS25).
game_code = "fs25"
game = mfs.Game.from_code(game_code)

# 2️⃣ Choose the DTM Provider and define it's settings.
dtm_provider = mfs.dtm.SRTM30Provider

# 3️⃣ Define the coordinates of the central point of the map, size and rotation.
lat, lon = 45.2858, 20.219
coordinates = (lat, lon)
size = 4096
rotation = 25

# 4️⃣ Define the output directory.
map_directory = "map_directory"
if os.path.isdir(map_directory):
    shutil.rmtree(map_directory)
os.makedirs(map_directory, exist_ok=True)

# 5️⃣ Optional: use a custom OSM file.
osm_file = "C:/NewMaps/FS25_Titelski_breg_DEV/custom_osm.osm"

# 6️⃣ Optional: advanced settings. You can use the default settings, but
# it's recommended to change them according to your needs.
dem_settings = mfs.settings.DEMSettings(
    multiplier=1, blur_radius=35, plateau=15, water_depth=10, add_foundations=True
)
background_settings = mfs.settings.BackgroundSettings(
    generate_background=True,
    generate_water=True,
    remove_center=True,
    flatten_roads=True,
    flatten_water=True,
)
grle_settings = mfs.settings.GRLESettings(
    add_grass=True, farmland_margin=8, random_plants=True, add_farmyards=True
)
i3d_settings = mfs.settings.I3DSettings(
    forest_density=8,
    add_trees=True,
    tree_limit=50000,
    trees_relative_shift=5,
    license_plate_prefix="NS",
)
texture_settings = mfs.settings.TextureSettings(
    dissolve=True,
    fields_padding=10,
    skip_drains=True,
)
satellite_settings = mfs.settings.SatelliteSettings(download_images=True, zoom_level=16)

buildings_settings = mfs.settings.BuildingSettings(
    generate_buildings=True, region="all", tolerance_factor=0.3
)

# 7️⃣ Optional: define custom tree and textures schemas.
# Default schemas can be found in the `data` directory of the repository.
tree_custom_schema_path = "C:/NewMaps/FS25_Titelski_breg_DEV/tree_custom_schema.json"
tree_custom_schema = json.load(open(tree_custom_schema_path, "r", encoding="utf-8"))

texture_custom_schema_path = "templates/fs25-texture-schema.json"
texture_custom_schema = json.load(open(texture_custom_schema_path, "r", encoding="utf-8"))

generation_settings = mfs.GenerationSettings(
    dem_settings=dem_settings,
    background_settings=background_settings,
    grle_settings=grle_settings,
    i3d_settings=i3d_settings,
    texture_settings=texture_settings,
    satellite_settings=satellite_settings,
    building_settings=buildings_settings,
)

# 8️⃣ Create an instance of the Map class with specified settings.
mp = mfs.Map(
    game,
    dtm_provider,
    None,
    coordinates,
    size,
    rotation,
    map_directory,
    custom_osm=osm_file,
    generation_settings=generation_settings,
    # texture_custom_schema=texture_custom_schema,
    tree_custom_schema=tree_custom_schema,
)

# 9️⃣ Launch the generation process.
for component_name in mp.generate():
    print(f"Generating {component_name}...")

# 1️⃣0️⃣ Optional: save the previews of the generated components.
previews_paths = mp.previews()
for preview_path in previews_paths:
    print(f"Preview saved to {preview_path}")
