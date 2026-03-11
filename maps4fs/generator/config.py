"""Backward-compatible config shim.

All constants live in :mod:`maps4fs.generator.constants`.
All setup logic lives in :mod:`maps4fs.generator.bootstrap`.

Importing this module still triggers the full bootstrap sequence so that
existing code that does ``import maps4fs.generator.config as mfscfg`` and
then reads ``mfscfg.MFS_TEMPLATES_DIR`` etc. continues to work unchanged.
"""

# Re-export everything so callers using `mfscfg.<NAME>` keep working.
from maps4fs.generator.bootstrap import (  # noqa: F401
    _urlopen_with_ssl_fallback,
    bootstrap,
    clean_cache,
    create_cache_dirs,
    ensure_executables,
    ensure_locale,
    ensure_template_subdirs,
    ensure_templates,
    get_package_version,
    logger,
    reload_templates,
)
from maps4fs.generator.constants import *  # noqa: F401, F403
from maps4fs.generator.constants import (  # noqa: F401
    CACHE_DIRS,
    DTM_CACHE_DIR,
    I3D_CONVERTER_NAME,
    I3D_CONVERTER_REMOTE_URL,
    MAP_BOUNDS_FILENAME,
    MFS_CACHE_DIR,
    MFS_DATA_DIR,
    MFS_DEFAULTS_DIR,
    MFS_DEM_DEFAULTS_DIR,
    MFS_EXECUTABLES_DIR,
    MFS_GSETTINGS_DEFAULTS_DIR,
    MFS_LOCALE_DIR,
    MFS_MSETTINGS_DEFAULTS_DIR,
    MFS_OSM_DEFAULTS_DIR,
    MFS_ROOT_DIR,
    MFS_TEMPLATES_DIR,
    SAT_CACHE_DIR,
    TEMPLATES_STRUCTURE,
    TEXCONV_NAME,
    TEXCONV_REMOTE_URL,
    TQDM_DISABLE,
    get_i3d_executable_path,
    get_map_bounds_file_paths,
    get_texconv_executable_path,
    get_windows_executable_path,
)

bootstrap()

PACKAGE_VERSION = get_package_version("maps4fs")
