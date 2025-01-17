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
dtm_provider = mfs.SRTM30Provider
dtm_provider_settings = mfs.SRTM30ProviderSettings(easy_mode=True, power_factor=0)

# 3️⃣ Define the coordinates of the central point of the map, size and rotation.
lat, lon = 45.28, 20.23
coordinates = (lat, lon)
size = 2048
rotation = 0

# 4️⃣ Define the output directory.
map_directory = "map_directory"
if os.path.isdir(map_directory):
    shutil.rmtree(map_directory)
os.makedirs(map_directory, exist_ok=True)

# 5️⃣ Optional: use a custom OSM file.
osm_file = "path/to/osm_file.osm"

# 6️⃣ Optional: advanced settings. You can use the default settings, but
# it's recommended to change them according to your needs.
dem_settings = mfs.DEMSettings(multiplier=1, blur_radius=15, plateau=3000, water_depth=2000)
background_settings = mfs.BackgroundSettings(
    generate_background=True,
    generate_water=True,
    resize_factor=8,
    remove_center=True,
    apply_decimation=True,
    decimation_percent=50,
    decimation_agression=4,
)
grle_settings = mfs.GRLESettings(farmland_margin=10, random_plants=True, add_farmyards=True)
i3d_settings = mfs.I3DSettings(forest_density=8)
texture_settings = mfs.TextureSettings(
    dissolve=False,
    fields_padding=10,
    skip_drains=True,
)
spline_settings = mfs.SplineSettings(spline_density=0)
satellite_settings = mfs.SatelliteSettings(download_images=False, zoom_level=18)

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
    dtm_provider_settings,
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
    spline_settings=spline_settings,
    satellite_settings=satellite_settings,
    # texture_custom_schema=texture_custom_schema,
    # tree_custom_schema=tree_custom_schema,
)

# 9️⃣ Launch the generation process.
for component_name in mp.generate():
    print(f"Generating {component_name}...")

# 1️⃣0️⃣ Optional: save the previews of the generated components.
previews_paths = mp.previews()
for preview_path in previews_paths:
    print(f"Preview saved to {preview_path}")
