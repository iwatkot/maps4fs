# Texture Schema Architecture

## Overview: The Core Engine of Map Generation

The texture schema is the **foundational blueprint** that transforms raw OpenStreetMap data into detailed Farming Simulator terrain. This JSON-based configuration system defines how every geographic feature—from highways to forests to farmlands—gets rendered as textured surfaces in your map.

**Critical Understanding**: The texture schema is not just a configuration file—it's the **intelligent translation layer** between real-world geographic data and game-ready assets.

## Schema Architecture

### Repository Structure
- **Primary Repository**: [maps4fsdata](https://github.com/iwatkot/maps4fsdata)
- **FS25 Schema**: [fs25-texture-schema.json](https://github.com/iwatkot/maps4fsdata/blob/main/fs25/fs25-texture-schema.json) 
- **FS22 Schema**: [fs22-texture-schema.json](https://github.com/iwatkot/maps4fsdata/blob/main/fs22/fs22-texture-schema.json)

Each game version maintains its own optimized schema, reflecting unique engine capabilities and asset libraries.

### Schema Example: Professional Configuration

```json
[
  {
    "name": "asphaltDusty",
    "count": 2,
    "tags": { "highway": ["motorway", "trunk", "primary"] },
    "width": 8,
    "color": [70, 70, 70],
    "priority": 1,
    "info_layer": "roads",
    "procedural": ["PG_roads"]
  },
  {
    "name": "forestGrass",
    "count": 2,
    "tags": { "natural": ["wood", "tree_row"], "landuse": "forest" },
    "precise_tags": { "leaf_type": "mixed" },
    "width": 2,
    "color": [11, 66, 0],
    "usage": "forest",
    "precise_usage": "mixed_forest",
    "priority": 5,
    "procedural": ["PG_forests"]
  },
  {
    "name": "mudDark",
    "count": 2,
    "tags": { "landuse": ["farmland", "meadow"] },
    "color": [47, 107, 85],
    "priority": 4,
    "info_layer": "fields",
    "usage": "field",
    "procedural": ["PG_acres"],
    "border": 10
  }
]
```

## Field Reference: Complete Configuration Guide

### Core Properties

**`name`** *(string, required)*  
**Purpose**: Texture identifier and file naming convention  
**Output**: Generates files like `asphaltDusty01_weight.png`, `asphaltDusty02_weight.png`  
**Best Practice**: Use descriptive, consistent naming that reflects the texture's purpose

**`count`** *(integer, required)*  
**Purpose**: Number of texture variations to generate  
**Range**: 0-N (0 = special case for deprecated textures like FS22's waterPuddle)  
**Strategic Use**: Multiple variations prevent repetitive visual patterns

### Geographic Mapping

**`tags`** *(object, conditional)*  
**Purpose**: OpenStreetMap feature matching - the core intelligence of the system  
**Examples**:
```json
"tags": { "highway": ["motorway", "trunk", "primary"] }
"tags": { "landuse": "farmland" }
"tags": { "natural": "water" }
```
**Critical**: Without tags, textures generate as empty layers with no geographic features

**`precise_tags`** *(object, optional)*  
**Purpose**: Advanced filtering for specific sub-categories  
**Use Case**: Differentiate forest types by `"leaf_type": "broadleaved"` vs `"leaf_type": "needleleaved"`  
**Advantage**: Enables highly detailed terrain categorization

### Spatial Configuration

**`width`** *(integer, conditional)*  
**Purpose**: Line feature width in meters (roads, rivers, paths)  
**Critical For**: Linear OSM features that need area conversion  
**Examples**: Highway = 8m, Service road = 4m, Footpath = 2m

**`border`** *(integer, optional)*  
**Purpose**: Edge buffer in pixels to prevent map boundary artifacts  
**Recommended**: 10 pixels for field textures to ensure clean edges
### Visual & Processing Control

**`color`** *(array [R,G,B], optional)*  
**Purpose**: Preview visualization color (no impact on final map)  
**Format**: RGB values 0-255: `[70, 70, 70]`  
**Strategic Importance**: Essential for visual validation during development cycles

**`priority`** *(integer, required for overlapping)*  
**Purpose**: Layer stacking order for overlapping features  
**Rules**:
- **Priority 0**: Base layer (fills all empty areas) 
- **Higher numbers**: Draw over lower priority layers
- **Critical for**: Ensuring roads appear over grass, buildings over terrain

**`usage`** *(string, categorization)*  
**Purpose**: Logical grouping of related textures  
**Categories**: `"grass"`, `"forest"`, `"field"`, `"drain"`  
**Benefit**: Enables batch processing and thematic consistency

**`precise_usage`** *(string, subcategorization)*  
**Purpose**: Fine-grained categorization within usage groups  
**Examples**: `"mixed_forest"`, `"broadleaved_forest"`, `"needleleaved_forest"`  
**Synergy**: Works with `precise_tags` for detailed terrain classification

### Advanced Features

**`background`** *(boolean, terrain modification)*  
**Purpose**: Influences background terrain generation  
**Primary Use**: Water depth subtraction from DEM elevation data  
**Impact**: Directly affects 3D terrain topology

**`info_layer`** *(string, data export)*  
**Purpose**: JSON data export identifier  
**Examples**: `"fields"`, `"roads"`, `"buildings"`  
**Output**: Coordinates and metadata saved to JSON for post-processing

**`invisible`** *(boolean, data-only)*  
**Purpose**: Save data without generating visible texture files  
**Use Case**: Coordinate collection without visual representation  
**Pairs With**: `info_layer` for pure data extraction

**`procedural`** *(array, mask generation)*  
**Purpose**: Procedural generation mask creation  
**Format**: `["PG_roads", "PG_buildings"]`  
**Output**: Creates `masks/PG_roads.png`, `masks/PG_buildings.png`  
**Advanced**: Multiple textures can contribute to single procedural masks

**`exclude_weight`** *(boolean, special case)*  
**Purpose**: FS25-specific handling for forestRockRoots texture  
**Effect**: Omits `_weight` suffix from filename  
**Usage**: Highly specialized - only for specific FS25 textures

**`area_type`** *(string, environment classification)*  
**Purpose**: Giants Editor environment categorization  
**Options**: `"open_land"`, `"city"`, `"village"`, `"harbor"`, `"industrial"`, `"open_water"`  
**Impact**: Affects lighting, sound, and atmospheric rendering

**`area_water`** *(boolean, water designation)*  
**Purpose**: Mark areas as water bodies for engine optimization  
**Effect**: Updates environment info layer for proper water rendering

**`indoor`** *(boolean, interior spaces)*  
**Purpose**: Designate interior/covered areas  
**Output**: Updates indoorMask info layer  
**Game Impact**: Affects weather effects and lighting behavior

**`merge_into`** *(string, layer consolidation)*  
**Purpose**: Combine layer content into target layer  
**Use Case**: Consolidating similar features for performance optimization  
**Result**: Source layer content transfers to specified target layer

## Custom Schema Editing

### Local Deployment Advantage

**⚠️ EXCLUSIVE FEATURE**: Schema editing is **only available with local deployment** (Python or Docker). Web app users cannot modify texture schemas.

**Why Local Only**: Schema files are mounted as volumes in your local environment, enabling real-time editing and immediate application to generation cycles.

### Direct Schema Modification

1. **Locate Schema Files**: Navigate to your mounted Maps4FS directory
2. **Find Target Schema**: 
   - FS25: `data/fs25-texture-schema.json`
   - FS22: `data/fs22-texture-schema.json`
3. **Edit Directly**: Use any JSON editor to modify the schema
4. **Immediate Effect**: Changes apply instantly to your next generation cycle

### Common Customization Scenarios

**Priority Adjustment**: Modify layer stacking order
```json
{
  "name": "customRoad",
  "priority": 10  // Higher priority = draws over other layers
}
```

**Custom OSM Tag Mapping**: Add support for unique geographic features
```json
{
  "name": "vineyards",
  "tags": { "landuse": "vineyard" },
  "color": [128, 0, 128],
  "usage": "agriculture"
}
```

**Procedural Mask Creation**: Generate custom masks for specialized tools
```json
{
  "name": "industrialZones",
  "tags": { "landuse": "industrial" },
  "procedural": ["PG_industry", "PG_pollution"]
}
```

### Best Practices for Schema Editing

**Backup First**: Always create schema backups before major modifications  
**Test Incrementally**: Make small changes and test generation results  
**Validate JSON**: Ensure proper JSON syntax to avoid generation failures  
**Document Changes**: Track modifications for future reference and troubleshooting

**Performance Tip**: Custom schemas with numerous high-priority layers may impact generation speed. Optimize priority assignments for best performance.