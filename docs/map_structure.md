# Map Structure

This documentation explains the complete structure of generated map files and directories. Understanding this organization will help you navigate and customize your maps effectively.

## Archive Naming Convention

Generated map archives follow a standardized naming pattern that includes essential metadata:

**Format:** `[Date]_[Time]_[Latitude]_[Longitude]_[GameVersion]`

**Components:**
- **Game Version**: FS25 (Farming Simulator 25) or FS22 (Farming Simulator 22)
- **Latitude**: Center point latitude (e.g., 45.28571)
- **Longitude**: Center point longitude (e.g., 20.23743)  
- **Date**: Generation date (e.g., 2024-12-10)
- **Time**: Generation time (e.g., 23-43-55)

## Directory Structure Overview

## Directory Structure Overview

### Background Terrain
**Location:** `background/` and `assets/background/`

Contains the essential components for creating realistic background terrain meshes. This directory includes both 2D elevation data and 3D mesh files generated from Digital Elevation Models (DEM).

**Key Files:**
- **PNG Images**: Raw DEM data files (can be safely removed after mesh generation)
- **FULL.obj**: Complete 3D mesh file for background terrain rendering

**NEW for FS25 - Automated Assets:**
When **Download Satellite Images** and **Generate Background** are both enabled, Maps4FS automatically creates:
- **`assets/background/background_terrain.i3d`**: Ready-to-import Giants Editor file
- **`assets/background/textured_mesh/`**: Complete textured mesh files (obj, mtl, texture)

**Usage:**
- **FS25**: Simply import `assets/background/background_terrain.i3d` directly into Giants Editor
- **FS22**: Use `FULL.obj` with manual Blender workflow (see [Legacy Background Terrain](legacy_background_terrain.md))

For detailed implementation guidance, see the [Background Terrain](background_terrain.md) tutorial.

### Water Planes
**Location:** `water/` and `assets/water/`

Contains components for creating realistic water body meshes and planes. This directory includes both 2D water resource data and 3D mesh files generated from water areas in your map data.

**Key Files:**
- **PNG Images**: Water resource data files
- **elevated_water.obj**: 3D mesh file for elevated water surfaces
- **plane_water.obj**: 3D mesh file for flat water planes  
- **line_based_water.obj**: 3D mesh file for linear water features (if applicable)

**NEW for FS25 - Automated Assets:**
When **Generate Water** is enabled, Maps4FS automatically creates:
- **`assets/water/polygon_water.i3d`**: Ready-to-import Giants Editor file with proper ocean shader configuration

**Usage:**
- **FS25**: Simply import `assets/water/polygon_water.i3d` directly into Giants Editor, then configure water properties
- **FS22**: Use obj files with manual Blender workflow (see [Legacy Water Planes](legacy_water_planes.md))

For detailed implementation guidance, see the [Water Planes](water_planes.md) tutorial.

### Information Layers
**Location:** `info_layers/`

Internal storage directory for component data exchange and generation metadata. Currently utilized by the Texture component for storing field generation data.

**Safety Note:** This directory can be safely removed if you don't require generation data persistence.

#### Texture Generation Data
**File:** `textures.json`

Contains coordinate mapping for texture-associated InfoLayers, specifically field polygon data used by the I3D component for field generation.

**Structure Example:**
```json
{
    "fields": [
        [
            [458, 580],
            [390, 758],
            // Additional coordinates...
        ]
        // Additional field polygons...
    ]
    // Additional field data...
}
```

**Note:** This file can be safely removed if field generation is not required for your map.

## Core Map Components
**Location:** `map/`

Contains the primary map files and configuration data. This is the heart of your Farming Simulator map.

### Configuration Files
**Location:** `map/config/`

XML configuration files that define various map behaviors and properties. While most files are auto-generated, some require manual configuration.

#### Critical Configuration: Farmlands
**File:** `farmLands.xml`

**⚠️ IMPORTANT:** This file requires manual configuration to match the `farmlands` InfoLayer in Giants Editor. Without proper configuration, land purchasing will not function in-game.  

**Configuration Example:**
```xml
<farmlands infoLayer="farmlands" pricePerHa="60000">
    <farmland id="1" priceScale="1" npcName="FORESTER" />
    <farmland id="2" priceScale="1" npcName="GRANDPA" />
</farmlands>
```

**Key Attributes:**
- **`pricePerHa`**: Global land price per hectare
- **`id`**: Unique farmland identifier
- **`priceScale`**: Price multiplier for individual plots
- **`npcName`**: Owner NPC designation

For comprehensive farmland configuration guidance, see the [Farmlands](farmlands.md) documentation.

### Map Data Directory
**Location:** `map/data/`

**⚠️ CRITICAL:** This directory contains all essential map assets. Missing files will cause Giants Editor crashes.

#### Texture Weight Files
Defines texture distribution across the map surface. Each weight file corresponds to a specific terrain texture.

For detailed texture management, see the [Textures](textures.md) documentation.

#### InfoLayer Images
Specialized images that define various map properties including fields, farmlands, and collision data. While you don't need to manually edit these files, they're essential for map functionality.

**Note:** InfoLayers require editing in Giants Editor, particularly for [Farmlands](farmlands.md) setup.

#### Digital Elevation Model (DEM)
**Location:** `map/data/`

Essential terrain elevation data that defines your map's topography.

**Key Files:**
- **`dem.png`**: Primary elevation data used by Giants Editor and in-game
- **`unprocessedHeightMap.png`**: Original elevation data before processing *(FS25 only)*

**Version Note:** The unprocessed height map is only available in Farming Simulator 25.

For comprehensive terrain elevation guidance, see the [DEM](dem.md) documentation.

## Map Definition Files

### Primary Map File
**File:** `map.i3d`

The core map definition file containing all 3D geometry, lighting, and object placement data. While this XML-based file can be edited manually, it's recommended to use Giants Editor for modifications.

### Map Configuration
**File:** `map.xml`

Contains references and paths to various map components. Manual editing should only be performed by experienced users who understand the file structure.

## Visual Assets

### In-Game Map Display
**File:** `overview.dds`

The minimap image displayed in-game.

**NEW for FS25**: Automatically generated when **Download Satellite Images** is enabled - no manual creation required!

**Manual Creation**: Required for FS22 or custom designs. For detailed creation and optimization guidance, see the [Overview Image](overview_image.md) documentation.

### Preview Assets
**Location:** `previews/`

Contains development and preview files generated during the map creation process. These files are safe to remove if not needed for future reference or debugging.

### Generation Metadata

**File:** `generation_info.json`

Comprehensive metadata about the map generation process, including data sources, coordinates, and processing parameters. Valuable for recreating maps or accessing original data sources.

For complete metadata documentation, see the [Generation Info](generation_info.md) documentation.

**File:** `generation_logs.json`

**NEW**: Detailed logging information from the map generation process, automatically collected and organized by log level for debugging and analysis purposes.

**Structure:**
```json
{
    "DEBUG": [
        {
            "level": "DEBUG",
            "timestamp": "2025-11-04 14:30:15,123", 
            "message": "Processing texture layer for grass..."
        }
    ],
    "INFO": [
        {
            "level": "INFO",
            "timestamp": "2025-11-04 14:30:16,456",
            "message": "Component Background processed in 2.45 seconds."
        }
    ],
    "WARNING": [
        {
            "level": "WARNING", 
            "timestamp": "2025-11-04 14:30:17,789",
            "message": "Custom texture schema not found, using default."
        }
    ],
    "ERROR": [
        {
            "level": "ERROR",
            "timestamp": "2025-11-04 14:30:18,012", 
            "message": "Failed to download satellite imagery for coordinates."
        }
    ]
}
```

**Key Features:**
- **Comprehensive Coverage**: Includes ALL log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL) regardless of console output level
- **Detailed Timestamps**: Precise timing information for troubleshooting performance issues
- **Organized by Level**: Easy filtering and analysis of specific log types
- **Session-Specific**: Only contains logs from the specific generation session
- **Automatic Generation**: No user configuration required - generated automatically during map creation

**Usage:**
- **Debugging**: Identify specific issues during map generation
- **Performance Analysis**: Track component processing times and bottlenecks
- **Support**: Provide detailed logs when requesting help or reporting issues
- **Development**: Analyze generation patterns and optimize workflows

**Note:** This file is safe to remove if detailed logging information is not needed for your use case.

## Mod Package Files

### Visual Identity
- **`icon.dds`**: Mod icon (256×256 for FS22, 512×512 for FS25)
- **`preview.dds`**: Map preview image (2048×2048 pixels)

Both files use the DDS format. For conversion tools and optimization, see the [Getting Help](get_help.md) documentation.

### Mod Descriptor
**File:** `modDesc.xml`

Standard mod metadata including name, description, author information, and version details. This follows standard Farming Simulator modding conventions.

## Complete Directory Tree

Below is the complete file structure of a generated map package:

```text
📦FS25_45_28571_20_23743_2024-12-10_23-43-55
 ┣ 📂background
 ┃ ┣ 📄FULL.obj
 ┃ ┗ 📄FULL.png
 ┣ 📂info_layers
 ┃ ┗ 📄textures.json
 ┣ 📂map
 ┃ ┣ 📂config
 ┃ ┃ ┣ 📄aiSystem.xml
 ┃ ┃ ┣ 📄collectibles.xml
 ┃ ┃ ┣ 📄colorGrading.xml
 ┃ ┃ ┣ 📄colorGradingNight.xml
 ┃ ┃ ┣ 📄environment.xml
 ┃ ┃ ┣ 📄farmlands.xml
 ┃ ┃ ┣ 📄fieldGround.xml
 ┃ ┃ ┣ 📄fields.xml
 ┃ ┃ ┣ 📄footballField.xml
 ┃ ┃ ┣ 📄handTools.xml
 ┃ ┃ ┣ 📄items.xml
 ┃ ┃ ┣ 📄pedestrianSystem.xml
 ┃ ┃ ┣ 📄placeables.xml
 ┃ ┃ ┣ 📄storeItems.xml
 ┃ ┃ ┣ 📄trafficSystem.xml
 ┃ ┃ ┣ 📄vehicles.xml
 ┃ ┃ ┗ 📄weed.xml
 ┃ ┣ 📂data
 ┃ ┃ ┣ 📄asphalt01_weight.png
 ┃ ┃ ┣ 📄asphalt02_weight.png
 ┃ ┃ ┣ 📄asphaltCracks01_weight.png
 ┃ ┃ ┣ 📄asphaltCracks02_weight.png
 ┃ ┃ ┣ 📄asphaltDirt01_weight.png
 ┃ ┃ ┣ 📄asphaltDirt02_weight.png
 ┃ ┃ ┣ 📄asphaltDusty01_weight.png
 ┃ ┃ ┣ 📄asphaltDusty02_weight.png
 ┃ ┃ ┣ 📄asphaltGravel01_weight.png
 ┃ ┃ ┣ 📄asphaltGravel02_weight.png
 ┃ ┃ ┣ 📄asphaltTwigs01_weight.png
 ┃ ┃ ┣ 📄asphaltTwigs02_weight.png
 ┃ ┃ ┣ 📄concrete01_weight.png
 ┃ ┃ ┣ 📄concrete02_weight.png
 ┃ ┃ ┣ 📄concreteGravelSand01_weight.png
 ┃ ┃ ┣ 📄concreteGravelSand02_weight.png
 ┃ ┃ ┣ 📄concretePebbles01_weight.png
 ┃ ┃ ┣ 📄concretePebbles02_weight.png
 ┃ ┃ ┣ 📄concreteShattered01_weight.png
 ┃ ┃ ┣ 📄concreteShattered02_weight.png
 ┃ ┃ ┣ 📄dem.png
 ┃ ┃ ┣ 📄densityMap_fruits.gdm
 ┃ ┃ ┣ 📄densityMap_ground.gdm
 ┃ ┃ ┣ 📄densityMap_groundFoliage.gdm
 ┃ ┃ ┣ 📄densityMap_height.gdm
 ┃ ┃ ┣ 📄densityMap_stones.gdm
 ┃ ┃ ┣ 📄densityMap_weed.gdm
 ┃ ┃ ┣ 📄forestGrass01_weight.png
 ┃ ┃ ┣ 📄forestGrass02_weight.png
 ┃ ┃ ┣ 📄forestLeaves01_weight.png
 ┃ ┃ ┣ 📄forestLeaves02_weight.png
 ┃ ┃ ┣ 📄forestNeedels01_weight.png
 ┃ ┃ ┣ 📄forestNeedels02_weight.png
 ┃ ┃ ┣ 📄forestRockRoots01.png
 ┃ ┃ ┣ 📄forestRockRoots02.png
 ┃ ┃ ┣ 📄grass01_weight.png
 ┃ ┃ ┣ 📄grass01_weight_preview.png
 ┃ ┃ ┣ 📄grass02_weight.png
 ┃ ┃ ┣ 📄grassClovers01_weight.png
 ┃ ┃ ┣ 📄grassClovers02_weight.png
 ┃ ┃ ┣ 📄grassCut01_weight.png
 ┃ ┃ ┣ 📄grassCut02_weight.png
 ┃ ┃ ┣ 📄grassDirtPatchy01_weight.png
 ┃ ┃ ┣ 📄grassDirtPatchy01_weight_preview.png
 ┃ ┃ ┣ 📄grassDirtPatchy02_weight.png
 ┃ ┃ ┣ 📄grassDirtPatchyDry01_weight.png
 ┃ ┃ ┣ 📄grassDirtPatchyDry02_weight.png
 ┃ ┃ ┣ 📄grassDirtStones01_weight.png
 ┃ ┃ ┣ 📄grassDirtStones02_weight.png
 ┃ ┃ ┣ 📄grassFreshMiddle01_weight.png
 ┃ ┃ ┣ 📄grassFreshMiddle02_weight.png
 ┃ ┃ ┣ 📄grassFreshShort01_weight.png
 ┃ ┃ ┣ 📄grassFreshShort02_weight.png
 ┃ ┃ ┣ 📄grassMoss01_weight.png
 ┃ ┃ ┣ 📄grassMoss02_weight.png
 ┃ ┃ ┣ 📄gravel01_weight.png
 ┃ ┃ ┣ 📄gravel02_weight.png
 ┃ ┃ ┣ 📄gravelDirtMoss01_weight.png
 ┃ ┃ ┣ 📄gravelDirtMoss02_weight.png
 ┃ ┃ ┣ 📄gravelPebblesMoss01_weight.png
 ┃ ┃ ┣ 📄gravelPebblesMoss02_weight.png
 ┃ ┃ ┣ 📄gravelPebblesMossPatchy01_weight.png
 ┃ ┃ ┣ 📄gravelPebblesMossPatchy02_weight.png
 ┃ ┃ ┣ 📄gravelSmall01_weight.png
 ┃ ┃ ┣ 📄gravelSmall02_weight.png
 ┃ ┃ ┣ 📄infoLayer_environment.png
 ┃ ┃ ┣ 📄infoLayer_farmlands.png
 ┃ ┃ ┣ 📄infoLayer_fieldType.png
 ┃ ┃ ┣ 📄infoLayer_indoorMask.png
 ┃ ┃ ┣ 📄infoLayer_limeLevel.png
 ┃ ┃ ┣ 📄infoLayer_navigationCollision.png
 ┃ ┃ ┣ 📄infoLayer_placementCollision.png
 ┃ ┃ ┣ 📄infoLayer_placementCollisionGenerated.png
 ┃ ┃ ┣ 📄infoLayer_plowLevel.png
 ┃ ┃ ┣ 📄infoLayer_rollerLevel.png
 ┃ ┃ ┣ 📄infoLayer_sprayLevel.png
 ┃ ┃ ┣ 📄infoLayer_stubbleShredLevel.png
 ┃ ┃ ┣ 📄infoLayer_tipCollision.png
 ┃ ┃ ┣ 📄infoLayer_tipCollisionGenerated.png
 ┃ ┃ ┣ 📄infoLayer_weed.png
 ┃ ┃ ┣ 📄mudDark01_weight.png
 ┃ ┃ ┣ 📄mudDark01_weight_preview.png
 ┃ ┃ ┣ 📄mudDark02_weight.png
 ┃ ┃ ┣ 📄mudDarkGrassPatchy01_weight.png
 ┃ ┃ ┣ 📄mudDarkGrassPatchy02_weight.png
 ┃ ┃ ┣ 📄mudDarkMossPatchy01_weight.png
 ┃ ┃ ┣ 📄mudDarkMossPatchy02_weight.png
 ┃ ┃ ┣ 📄mudLeaves01_weight.png
 ┃ ┃ ┣ 📄mudLeaves02_weight.png
 ┃ ┃ ┣ 📄mudLight01_weight.png
 ┃ ┃ ┣ 📄mudLight01_weight_preview.png
 ┃ ┃ ┣ 📄mudLight02_weight.png
 ┃ ┃ ┣ 📄mudPebbles01_weight.png
 ┃ ┃ ┣ 📄mudPebbles02_weight.png
 ┃ ┃ ┣ 📄mudPebblesLight01_weight.png
 ┃ ┃ ┣ 📄mudPebblesLight02_weight.png
 ┃ ┃ ┣ 📄mudTracks01_weight.png
 ┃ ┃ ┣ 📄mudTracks02_weight.png
 ┃ ┃ ┣ 📄pebblesForestGround01_weight.png
 ┃ ┃ ┣ 📄pebblesForestGround02_weight.png
 ┃ ┃ ┣ 📄rock01_weight.png
 ┃ ┃ ┣ 📄rock02_weight.png
 ┃ ┃ ┣ 📄rockFloorTiles01_weight.png
 ┃ ┃ ┣ 📄rockFloorTiles02_weight.png
 ┃ ┃ ┣ 📄rockFloorTilesPattern01_weight.png
 ┃ ┃ ┣ 📄rockFloorTilesPattern02_weight.png
 ┃ ┃ ┣ 📄rockForest01_weight.png
 ┃ ┃ ┣ 📄rockForest02_weight.png
 ┃ ┃ ┣ 📄rockyForestGround01_weight.png
 ┃ ┃ ┣ 📄rockyForestGround02_weight.png
 ┃ ┃ ┣ 📄sand01_weight.png
 ┃ ┃ ┣ 📄sand01_weight_preview.png
 ┃ ┃ ┣ 📄sand02_weight.png
 ┃ ┃ ┗ 📄unprocessedHeightMap.png
 ┃ ┣ 📄map.i3d
 ┃ ┣ 📄map.i3d.shapes
 ┃ ┣ 📄map.xml
 ┃ ┗ 📄overview.dds
 ┣ 📂previews
 ┃ ┣ 📄background_dem.png
 ┃ ┣ 📄background_dem.stl
 ┃ ┣ 📄dem_colored.png
 ┃ ┣ 📄dem_grayscale.png
 ┃ ┗ 📄textures_osm.png
 ┣ 📄generation_info.json
 ┣ 📄generation_logs.json
 ┣ 📄icon.dds
 ┣ 📄modDesc.xml
 ┗ 📄preview.dds
```