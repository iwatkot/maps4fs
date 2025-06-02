## Migration to v2.0.0
This document outlines the changes made in version 2.0.0 of maps4fs and provides guidance on how to migrate your existing code to be compatible with the new version.

### Deprecations
- The whole module `maps4fs/generator/toolbox` along with all its submodules has been deprecated.
- The features related to custom OSM files fixes, such as `check_osm_file` and `fix_osm_file`, have been moved to the main `generator` features and will no longer available as separate functions.
- All the features related to the `DEM` and `background` components of the `Modder Toolbox` have been removed and will no longer be available in the new version. If you were using these features, consider using older versions, or use the source code from the old version as a reference to implement your own solution.
- The `Modder Toolbox` UI component have been removed along with the submodule.

### Docker images

The lite version of the Docker image will not be available in the new version.  
If you were using something like `docker pull iwatkot/maps4fs:1.9.3_lite`, you will need to switch to the full version of the image, which is now the only available version.  
The full version can be pulled using `docker pull iwatkot/maps4fs:latest`.