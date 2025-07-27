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

import os
import shutil

import maps4fs as mfs

# 1️⃣ Define the game (FS22 or FS25).
game_code = "fs25"
game = mfs.Game.from_code(game_code)

# 2️⃣ Choose the DTM Provider and define it's settings.
dtm_provider = mfs.dtm.SRTM30Provider

# 3️⃣ Define the coordinates of the central point of the map, size and rotation.
lat, lon = 45.28664672442379, 20.23913383374618
coordinates = (lat, lon)
size = 1024
rotation = 0
# output_size = 1024

# 4️⃣ Define the output directory.
map_directory = "map_directory"
if os.path.isdir(map_directory):
    shutil.rmtree(map_directory)
os.makedirs(map_directory, exist_ok=True)

# 5️⃣ Optional: use a custom OSM file.
osm_file = "path/to/osm_file.osm"

# 6️⃣ Optional: advanced settings. You can use the default settings, but
# it's recommended to change them according to your needs.
dem_settings = mfs.settings.DEMSettings(multiplier=1, blur_radius=40, plateau=15, water_depth=10)
background_settings = mfs.settings.BackgroundSettings(
    # generate_background=True,
    generate_water=True,
    water_blurriness=100,
    remove_center=True,
)
grle_settings = mfs.settings.GRLESettings(
    farmland_margin=10, random_plants=True, add_farmyards=True
)
i3d_settings = mfs.settings.I3DSettings(forest_density=8)
texture_settings = mfs.settings.TextureSettings(
    dissolve=False,
    fields_padding=10,
    skip_drains=True,
)
satellite_settings = mfs.settings.SatelliteSettings(download_images=False, zoom_level=18)

# 7️⃣ Optional: define custom tree and textures schemas.
# Default schemas can be found in the `data` directory of the repository.
texture_custom_schema = [
    # Your texture schema here.
]
tree_custom_schema = [
    # Your tree schema here.
]

# 8️⃣ Create an instance of the Map class with specified settings.
mp = mfs.Map(
    game,
    dtm_provider,
    None,
    coordinates,
    size,
    rotation,
    map_directory,
    # custom_osm=osm_file,
    dem_settings=dem_settings,
    background_settings=background_settings,
    grle_settings=grle_settings,
    i3d_settings=i3d_settings,
    texture_settings=texture_settings,
    satellite_settings=satellite_settings,
    # texture_custom_schema=texture_custom_schema,
    # tree_custom_schema=tree_custom_schema,
    # output_size=output_size,
)

# 9️⃣ Launch the generation process.
for component_name in mp.generate():
    print(f"Generating {component_name}...")

# 1️⃣0️⃣ Optional: save the previews of the generated components.
previews_paths = mp.previews()
for preview_path in previews_paths:
    print(f"Preview saved to {preview_path}")
