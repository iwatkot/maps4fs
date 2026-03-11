"""Pure path/name constants for the maps4fs generator.

Zero side effects — safe to import without triggering network requests or
filesystem mutations. All download/setup logic lives in bootstrap.py.
"""

import os

# ---- Directory roots --------------------------------------------------------

MFS_TEMPLATES_DIR = os.path.join(os.getcwd(), "templates")
MFS_EXECUTABLES_DIR = os.path.join(os.getcwd(), "executables")
MFS_DEFAULTS_DIR = os.path.join(os.getcwd(), "defaults")
MFS_LOCALE_DIR = os.path.join(os.getcwd(), "locale")

MFS_DEM_DEFAULTS_DIR = os.path.join(MFS_DEFAULTS_DIR, "dem")
MFS_OSM_DEFAULTS_DIR = os.path.join(MFS_DEFAULTS_DIR, "osm")
MFS_MSETTINGS_DEFAULTS_DIR = os.path.join(MFS_DEFAULTS_DIR, "main_settings")
MFS_GSETTINGS_DEFAULTS_DIR = os.path.join(MFS_DEFAULTS_DIR, "generation_settings")

MFS_ROOT_DIR = os.getenv("MFS_ROOT_DIRECTORY", os.path.join(os.getcwd(), "mfsrootdir"))
MFS_CACHE_DIR = os.path.join(MFS_ROOT_DIR, "cache")
MFS_DATA_DIR = os.path.join(MFS_ROOT_DIR, "maps")

DTM_CACHE_DIR = os.path.join(MFS_CACHE_DIR, "dtm")
SAT_CACHE_DIR = os.path.join(MFS_CACHE_DIR, "sat")

OSMNX_CACHE_DIR = os.path.join(MFS_CACHE_DIR, "osmnx")
OSMNX_DATA_DIR = os.path.join(MFS_CACHE_DIR, "odata")

CACHE_DIRS = [DTM_CACHE_DIR, SAT_CACHE_DIR, OSMNX_CACHE_DIR, OSMNX_DATA_DIR]

# ---- Executable names and remote URLs --------------------------------------

I3D_CONVERTER_NAME = "i3dConverter.exe"
I3D_CONVERTER_REMOTE_URL = "http://storage.atlasfs.xyz/mfsmdata/i3dConverter.exe"
TEXCONV_NAME = "texconv.exe"
TEXCONV_REMOTE_URL = "https://github.com/microsoft/DirectXTex/releases/download/oct2025/texconv.exe"

# ---- Map template structure -------------------------------------------------

MAP_BOUNDS_FILENAME = "map_bounds"

TEMPLATES_STRUCTURE = {
    "fs25": ["texture_schemas", "tree_schemas", "buildings_schemas", "map_templates"],
    "fs22": ["texture_schemas", "map_templates"],
}

TQDM_DISABLE = os.getenv("TQDM_DISABLE", "0") == "1"


# ---- Path helper functions (pure lookups, no side effects) ------------------


def get_map_bounds_file_paths() -> tuple[str, str] | None:
    """Return paths to map_bounds.i3d and map_bounds.i3d.shapes, or None if missing."""
    i3d_path = os.path.join(MFS_TEMPLATES_DIR, f"{MAP_BOUNDS_FILENAME}.i3d")
    shapes_path = os.path.join(MFS_TEMPLATES_DIR, f"{MAP_BOUNDS_FILENAME}.i3d.shapes")
    if all(os.path.isfile(p) for p in (i3d_path, shapes_path)):
        return i3d_path, shapes_path
    return None


def get_windows_executable_path(executable_name: str) -> str | None:
    """Return path to a Windows executable in MFS_EXECUTABLES_DIR, or None."""
    if os.name != "nt":
        return None
    expected = os.path.join(MFS_EXECUTABLES_DIR, executable_name)
    return expected if os.path.isfile(expected) else None


def get_i3d_executable_path() -> str | None:
    """Return path to i3dConverter.exe, or None."""
    return get_windows_executable_path(I3D_CONVERTER_NAME)


def get_texconv_executable_path() -> str | None:
    """Return path to texconv.exe, or None."""
    return get_windows_executable_path(TEXCONV_NAME)
