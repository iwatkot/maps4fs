import json
import os

from i3d_extractor import extract_building_dimensions

FOI_EXTENSIONS = [".i3d"]

# Yes, some files have typos in their names. :D
EXCLUDE_TEXT = [
    "placeable",
    "props",
    "infrastucture",
    "infrastructure",
    "drainage",
    "pavements",
    "bridge",
    "sign",
    "footballfield",
    "elements",
    "tunnel",
]

# Replace with the actual path to your Farming Simulator 25 data directory.
data_directory = "C:/Games/Steam/steamapps/common/Farming Simulator 25/data"
us_assets_directory = "/maps/mapUS/textures/buildings"
fs25_us_assets_directory = data_directory + us_assets_directory

if not os.path.isdir(fs25_us_assets_directory):
    raise FileNotFoundError(f"The directory {fs25_us_assets_directory} does not exist.")
print(f"Scanning directory: {fs25_us_assets_directory}")


def get_subrids(directory: str) -> list[str]:
    """Get a list of subdirectories in the given directory.

    Arguments:
        directory (str): The path to the directory to scan.

    Returns:
        list[str]: A list of subdirectory names.
    """
    return [name for name in os.listdir(directory) if os.path.isdir(os.path.join(directory, name))]


def get_foi_files(directory: str) -> list[str]:
    """Get a list of files of interest (FOI) in the given directory.

    Arguments:
        directory (str): The path to the directory to scan.

    Returns:
        list[str]: A list of FOI file names.
    """
    return [
        name
        for name in os.listdir(directory)
        if os.path.isfile(os.path.join(directory, name))
        and os.path.splitext(name)[1].lower() in FOI_EXTENSIONS
        and not any(exclude_text in name.lower() for exclude_text in EXCLUDE_TEXT)
    ]


def determine_categories(building_name: str) -> list[str]:
    """Determine OSM-aligned categories based on building name.

    Arguments:
        building_name (str): The name of the building.

    Returns:
        list[str]: A list of categories.
    """
    name_lower = building_name.lower()

    if any(word in name_lower for word in ["house", "home", "residential", "dwelling"]):
        return ["residential"]
    elif any(
        word in name_lower
        for word in ["store", "shop", "market", "restaurant", "cafe", "hotel", "bank"]
    ):
        return ["commercial"]
    elif any(
        word in name_lower for word in ["barn", "shed", "silo", "stable", "farm", "agriculture"]
    ):
        return ["farmyard"]
    elif any(word in name_lower for word in ["factory", "warehouse", "industrial", "plant"]):
        return ["industrial"]
    elif any(word in name_lower for word in ["school", "hospital", "church", "library", "civic"]):
        return ["civic"]
    else:
        return ["commercial"]  # Default


def schema_entry(relative_path: str, full_path: str) -> dict[str, str | int | list[str]]:
    """Create a schema entry for the given file path with real dimensions.

    Arguments:
        relative_path (str): The relative path to the file.
        full_path (str): The full path to the file for dimension extraction.

    Returns:
        dict[str, str | int | list[str]]: A dictionary representing the schema entry.
    """
    filename = os.path.basename(relative_path)
    building_name = os.path.splitext(filename)[0]

    # Extract real dimensions
    dims = extract_building_dimensions(full_path)

    # Use extracted dimensions or fallback to reasonable defaults
    width = dims["width"] if dims["width"] else 0
    depth = dims["depth"] if dims["depth"] else 0

    return {
        "file": relative_path,
        "name": building_name,
        "width": width,
        "depth": depth,
        "regions": ["US"],
        "categories": determine_categories(building_name),
    }


schema = []

for subdir in get_subrids(fs25_us_assets_directory):
    foi_files = get_foi_files(os.path.join(fs25_us_assets_directory, subdir))
    for foi_file in foi_files:
        full_path = os.path.join(fs25_us_assets_directory, subdir, foi_file).replace("\\", "/")
        relative_path = full_path.replace(data_directory, "$data")
        entry = schema_entry(relative_path, full_path)
        schema.append(entry)

no_dimensions = []
no_categories = []
for entry in schema:
    if entry["width"] == 0 or entry["depth"] == 0:
        no_dimensions.append(entry)
    if not entry["categories"]:
        no_categories.append(entry)

save_path = "fs25-buildings-schema-NEW.json"

print(f"Total FOI files found: {len(schema)}")
with open(save_path, "w", encoding="utf-8") as f:
    json.dump(schema, f, indent=4)
print(f"Schema saved to {save_path}")

print(f"Total buildings without dimensions: {len(no_dimensions)}")
if no_dimensions:
    print("Buildings without dimensions:")
    for entry in no_dimensions:
        print(f"- {entry['file']}")

print(f"Total buildings without categories: {len(no_categories)}")
if no_categories:
    print("Buildings without categories:")
    for entry in no_categories:
        print(f"- {entry['file']}")
