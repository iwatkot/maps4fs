"""Pure path/name constants for the maps4fs generator.

Zero side effects — safe to import without triggering network requests or
filesystem mutations. All download/setup logic lives in bootstrap.py.
"""

import os


class Paths:
    """All static paths and names used by the generator.

    Every attribute is resolved once at class-definition time, so there are
    no repeated ``os.path.join`` calls scattered through the code base.
    Access via ``Paths.TEMPLATES_DIR``, etc.
    """

    # ---- Directory roots ------------------------------------------------
    TEMPLATES_DIR = os.path.join(os.getcwd(), "templates")
    EXECUTABLES_DIR = os.path.join(os.getcwd(), "executables")
    DEFAULTS_DIR = os.path.join(os.getcwd(), "defaults")
    LOCALE_DIR = os.path.join(os.getcwd(), "locale")

    DEM_DEFAULTS_DIR = os.path.join(DEFAULTS_DIR, "dem")
    OSM_DEFAULTS_DIR = os.path.join(DEFAULTS_DIR, "osm")
    MSETTINGS_DEFAULTS_DIR = os.path.join(DEFAULTS_DIR, "main_settings")
    GSETTINGS_DEFAULTS_DIR = os.path.join(DEFAULTS_DIR, "generation_settings")

    ROOT_DIR = os.getenv("MFS_ROOT_DIRECTORY", os.path.join(os.getcwd(), "mfsrootdir"))
    CACHE_DIR = os.path.join(ROOT_DIR, "cache")
    DATA_DIR = os.path.join(ROOT_DIR, "maps")

    DTM_CACHE_DIR = os.path.join(CACHE_DIR, "dtm")
    SAT_CACHE_DIR = os.path.join(CACHE_DIR, "sat")
    OSMNX_CACHE_DIR = os.path.join(CACHE_DIR, "osmnx")
    OSMNX_DATA_DIR = os.path.join(CACHE_DIR, "odata")

    CACHE_DIRS = [DTM_CACHE_DIR, SAT_CACHE_DIR, OSMNX_CACHE_DIR, OSMNX_DATA_DIR]

    # ---- Executable names and remote URLs --------------------------------
    I3D_CONVERTER_NAME = "i3dConverter.exe"
    I3D_CONVERTER_REMOTE_URL = "http://storage.atlasfs.xyz/mfsmdata/i3dConverter.exe"
    TEXCONV_NAME = "texconv.exe"
    TEXCONV_REMOTE_URL = (
        "https://github.com/microsoft/DirectXTex/releases/download/oct2025/texconv.exe"
    )

    # ---- Map template structure -----------------------------------------
    MAP_BOUNDS_FILENAME = "map_bounds"
    TEMPLATES_STRUCTURE = {
        "fs25": ["texture_schemas", "tree_schemas", "buildings_schemas", "map_templates"],
        "fs22": ["texture_schemas", "map_templates"],
    }

    TQDM_DISABLE = os.getenv("TQDM_DISABLE", "0") == "1"

    # ---- Path helpers ---------------------------------------------------

    @staticmethod
    def get_map_bounds_file_paths() -> tuple[str, str] | None:
        """Return paths to map_bounds.i3d and map_bounds.i3d.shapes, or None if missing."""
        i3d_path = os.path.join(Paths.TEMPLATES_DIR, f"{Paths.MAP_BOUNDS_FILENAME}.i3d")
        shapes_path = os.path.join(Paths.TEMPLATES_DIR, f"{Paths.MAP_BOUNDS_FILENAME}.i3d.shapes")
        if all(os.path.isfile(p) for p in (i3d_path, shapes_path)):
            return i3d_path, shapes_path
        return None

    @staticmethod
    def get_windows_executable_path(executable_name: str) -> str | None:
        """Return path to a Windows executable in EXECUTABLES_DIR, or None."""
        if os.name != "nt":
            return None
        expected = os.path.join(Paths.EXECUTABLES_DIR, executable_name)
        return expected if os.path.isfile(expected) else None

    @staticmethod
    def get_i3d_executable_path() -> str | None:
        """Return path to i3dConverter.exe, or None."""
        return Paths.get_windows_executable_path(Paths.I3D_CONVERTER_NAME)

    @staticmethod
    def get_texconv_executable_path() -> str | None:
        """Return path to texconv.exe, or None."""
        return Paths.get_windows_executable_path(Paths.TEXCONV_NAME)
