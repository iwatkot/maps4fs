# Generation Information Reference

## Overview: Your Map's Complete Blueprint

The `generation_info.json` file serves as the **comprehensive metadata record** for your generated map. This critical file contains all parameters, coordinates, and technical specifications needed to reproduce, modify, or extend your map generation.

**Essential Practice**: Always preserve this file after successful generations. It's your map's "DNA" - enabling exact reproduction and compatibility maintenance across regeneration cycles.

**Location**: Generated automatically in your output directory alongside your map files.

## File Structure & Components

The generation info is organized into specialized components, each handling different aspects of the map generation pipeline:

- **`Texture`** - Geographic boundaries, coordinates, and spatial configuration
- **`Background`** - Terrain mesh information and elevation data processing  
- **`I3d`** - Scene objects including forests, fields, and procedural elements
- **`Config`** - Map metadata, overview settings, and environmental parameters
- **`GRLE`** - Weight map and texture layer information *(when applicable)*
- **`Satellite`** - Satellite imagery configuration *(when applicable)*

## Component Reference

### Texture Component

**Purpose**: Defines the core geographic and spatial parameters of your map.

```json
"Texture": {
    "coordinates": [45.2858, 20.219],
    "bbox": [45.31342712070634, 45.25817287929366, 20.258267006249493, 20.17973299375051],
    "map_size": 4096,
    "rotation": 25,
    "minimum_x": 20.17973299375051,
    "minimum_y": 45.25817287929366,
    "maximum_x": 20.258267006249493,
    "maximum_y": 45.31342712070634
}
```

**Field Descriptions:**
- **`coordinates`**: Center point [latitude, longitude] - your original input coordinates
- **`bbox`**: Geographic bounding box [north, south, east, west] defining map boundaries
- **`map_size`**: Map dimension in meters (e.g., 2048, 4096, 8192)
- **`rotation`**: Map rotation angle in degrees (0-360)
- **`minimum_x/y`**, **`maximum_x/y`**: Precise coordinate boundaries for spatial calculations

### Background Component

**Purpose**: Contains comprehensive terrain and elevation data for background mesh generation.

```json
"Background": {
    "center_latitude": 45.2858,
    "center_longitude": 20.219,
    "epsg3857_string": "2242026.418067859,2259511.150630538,5657889.513370422,5675374.254172803 [EPSG:3857]",
    "epsg3857_string_with_margin": "2241526,2260011,5657389,5675874 [EPSG:3857]",
    "height": 8192,
    "width": 8192,
    "north": 45.341054241412685,
    "south": 45.23054575858732,
    "east": 20.297534012498986,
    "west": 20.140465987501017,
    "DEM": {
        "original": {
            "min": 54.0,
            "max": 127.0,
            "deviation": 73.0,
            "dtype": "int16",
            "shape": "(398, 565)"
        },
        "height_scale": {
            "height_scale_from_settings": 255,
            "adjusted_height_scale": 255,
            "mesh_z_scaling_factor": 257.0,
            "height_scale_multiplier": 1.0
        }
    },
    "Mesh": [
        {
            "name": "FULL",
            "x_size": 8192.0,
            "y_size": 8192.0,
            "z_size": 63.3852,
            "x_center": 2.4181,
            "y_center": 2.184,
            "z_center": -31.8189
        }
    ]
}
```

**Critical Update**: The background terrain is now generated as a **single unified mesh**, not the legacy 8-tile system. This provides seamless terrain continuity and improved performance.

**Key Fields:**
- **Geographic Boundaries**: `center_latitude/longitude`, `north/south/east/west` - Define the extended terrain area
- **EPSG3857 Strings**: Ready-to-use coordinate strings for QGIS satellite imagery import
- **DEM Processing**: Complete elevation data pipeline from original through final normalization
- **Mesh Specifications**: Physical dimensions and positioning data for 3D terrain mesh
- **Height Scaling**: Elevation processing parameters and scaling factors

### I3d Component

**Purpose**: Tracks procedurally generated scene objects and their placement statistics.

```json
"I3d": {
    "Forests": {
        "available_tree_count": 2152116,
        "tree_count": 50050,
        "tree_limit": 50000,
        "step_by_limit": 43,
        "initial_step": 8,
        "actual_step": 43,
        "shift": 1.6
    },
    "Fields": {
        "added_fields": 56,
        "skipped_fields": 5,
        "skipped_field_ids": []
    }
}
```

**Forest Generation Metrics:**
- **`available_tree_count`**: Total trees possible in forest areas
- **`tree_count`**: Actual trees placed in the scene
- **`tree_limit`**: Maximum allowed trees (performance constraint)
- **`step`/`shift`**: Placement algorithm parameters for tree distribution

**Field Generation Results:**
- **`added_fields`**: Successfully created farmable fields
- **`skipped_fields`**: Fields rejected due to size/shape constraints
- **`skipped_field_ids`**: Specific field identifiers that were rejected

### Config Component

**Purpose**: Map metadata and environmental configuration settings.

```json
"Config": {
    "Overview": {
        "epsg3857_string": "2244940.540161639,2256597.028536758,5660801.272973384,5672457.763789897 [EPSG:3857]",
        "epsg3857_string_with_margin": "2244440,2257097,5660301,5672957 [EPSG:3857]",
        "height": 8192,
        "width": 8192
    },
    "Fog": {
        "minimum_height": 34,
        "maximum_height": 95
    }
}
```

**Overview Settings**: QGIS-compatible coordinate strings for satellite imagery import, typically 2× map size for proper context coverage.

**Environmental Parameters**: Automatically calculated settings like fog height ranges based on terrain elevation analysis.

## Practical Applications

### Reproduction & Consistency
Use the complete `generation_info.json` to regenerate identical maps with different settings or components.

### External Tool Integration
- **QGIS**: Use `epsg3857_string` fields for precise satellite imagery import
- **Blender**: Reference mesh dimensions and positioning for background terrain work
- **Custom Tools**: Access coordinate systems and boundaries for specialized map modifications

### Troubleshooting & Optimization
- **Performance Analysis**: Review tree counts and field statistics to optimize generation settings
- **Coordinate Verification**: Validate geographic boundaries and projections
- **Scale Planning**: Use DEM and mesh data for terrain modification planning

**Best Practice**: Archive generation info files alongside your map projects for complete reproducibility and technical reference.