import json
import os

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


def schema_entry(relative_path: str) -> dict[str, str | int | list[str]]:
    """Create a schema entry for the given file path.

    Arguments:
        relative_path (str): The relative path to the file.

    Returns:
        dict[str, str | int | list[str]]: A dictionary representing the schema entry.
    """
    filename = os.path.basename(relative_path)
    building_name = os.path.splitext(filename)[0]
    return {
        "file": relative_path,
        "name": building_name,
        "width": 0,
        "depth": 0,
        "regions": ["US"],
        "categories": [],
    }


schema = []
for subdir in get_subrids(fs25_us_assets_directory):
    foi_files = get_foi_files(os.path.join(fs25_us_assets_directory, subdir))
    for foi_file in foi_files:
        full_path = os.path.join(fs25_us_assets_directory, subdir, foi_file).replace("\\", "/")
        relative_path = full_path.replace(data_directory, "$data")
        entry = schema_entry(relative_path)
        schema.append(entry)

save_path = "fs25-buildings-schema-NEW.json"

print(f"Total FOI files found: {len(schema)}")
with open(save_path, "w", encoding="utf-8") as f:
    json.dump(schema, f, indent=4)
print(f"Schema saved to {save_path}")
