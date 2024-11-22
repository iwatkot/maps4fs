import json
import os
from collections import defaultdict

import cv2

map_path = "data/FS25_EmptyMap"
inner_directory_name = "mapUS"
data_directory_name = "data"

inner_directory_path = os.path.join(map_path, inner_directory_name)
data_directory_path = os.path.join(map_path, inner_directory_name, data_directory_name)
print(f"Map path: {map_path}")
print(f"Inner directory path: {inner_directory_path}")
print(f"Data directory path: {data_directory_path}")

if not os.path.exists(data_directory_path):
    raise FileNotFoundError(f"Data directory not found: {data_directory_path}")

# data_files = os.listdir(data_directory_path)
# # "forestRockRoots02.png", "forestRockRoots01.png"

# # key - name, value - number of files
# weight_files = defaultdict(lambda: 0)
# for file in data_files:
#     if file.endswith("_weight.png"):
#         splitted_name = file.split("_weight.png")[0]
#         sliced_name = splitted_name[:-2]
#         weight_files[sliced_name] += 1

# # Sort by key by alphabet
# weight_files = dict(sorted(weight_files.items()))

# sliced_names_filepath = "sliced.json"
# with open(sliced_names_filepath, "w") as f:
#     json.dump(weight_files, f)

dem_path = os.path.join(data_directory_path, "dem.png")
unprocessed_dem_path = os.path.join(data_directory_path, "unprocessedHeightMap.png")

# Read both files and compare them

dem = cv2.imread(dem_path, cv2.IMREAD_UNCHANGED)
unprocessed_dem = cv2.imread(unprocessed_dem_path, cv2.IMREAD_UNCHANGED)

if dem.shape != unprocessed_dem.shape:
    print(
        f"Shapes are different. DEM shape: {dem.shape}, Unprocessed DEM shape: {unprocessed_dem.shape}"
    )
else:
    print(f"Shapes are equal: {dem.shape}")

if dem.dtype != unprocessed_dem.dtype:
    print(
        f"Data types are different. DEM dtype: {dem.dtype}, Unprocessed DEM dtype: {unprocessed_dem.dtype}"
    )
else:
    print(f"Data types are equal: {dem.dtype}")

# Compare pixel by pixel
for i in range(dem.shape[0]):
    for j in range(dem.shape[1]):
        if dem[i, j] != unprocessed_dem[i, j]:
            print(f"Pixel at {i}, {j} is different: {dem[i, j]} != {unprocessed_dem[i, j]}")
            break
