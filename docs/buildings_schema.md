# Buildings Schema Architecture

## Overview: Intelligent Building Placement System

The buildings schema is the **intelligent placement engine** that automatically positions appropriate buildings within designated areas on your generated map. This JSON-based configuration system defines building characteristics, placement rules, and integration with OpenStreetMap area categories.

**Critical Understanding**: The buildings schema works in **conjunction with texture schema** and **OSM area categories** to create contextually appropriate building placement based on real-world land use patterns.

## Schema Architecture

### Repository Structure
- **Primary Repository**: [maps4fsdata](https://github.com/iwatkot/maps4fsdata)
- **FS25 Schema**: [fs25-buildings-schema.json](https://github.com/iwatkot/maps4fsdata/blob/main/fs25/fs25-buildings-schema.json)
- **Local Template**: `templates/fs25-buildings-schema.json` (in your Maps4FS installation)

**⚠️ Farming Simulator 25 Only**: Buildings schema is **exclusively available for FS25**. FS22 does not support automated building placement.

### Schema Example: Professional Configuration

```json
[
  {
    "file": "$data/maps/mapEU/textures/buildings/apartmentBuildings/apartmentBuilding01.i3d",
    "name": "apartmentBuilding01",
    "width": 32.0,
    "depth": 12.0,
    "type": "apartment",
    "categories": ["residential"],
    "regions": ["EU"]
  },
  {
    "file": "$data/maps/mapEU/textures/buildings/gasStation/gasStation.i3d",
    "name": "gasStation",
    "width": 40.0,
    "depth": 30.0,
    "type": "station",
    "categories": ["retail", "commercial"],
    "regions": ["EU"]
  },
  {
    "file": "/assets/buildings/customWarehouse/customWarehouse.i3d",
    "name": "customWarehouse",
    "width": 50.0,
    "depth": 25.0,
    "type": "warehouse",
    "categories": ["industrial"],
    "regions": ["EU"]
  }
]
```

## Integration with Map Generation Workflow

### Step 1: OSM Area Definition
Buildings are placed within **designated land use areas** defined in OpenStreetMap. Reference the [OSM Area Categories](OSM_Area_Categories.md) for complete area definitions.

**Common Area Types:**
- `landuse=residential` → Residential buildings
- `landuse=commercial` → Commercial buildings  
- `landuse=industrial` → Industrial buildings
- `landuse=farmyard` → Agricultural buildings

### Step 2: Texture Schema Integration
The **texture schema** defines how land use areas are rendered and enables building placement through special entries:

```json
{
  "name": "BC_residential",
  "count": 1,
  "external": true,
  "tags": { "landuse": "residential" },
  "building_category": "residential"
}
```

**Key Properties:**
- `external: true` - Enables building placement
- `building_category` - Links to buildings schema categories
- `tags` - Matches OSM area tags

### Step 3: Building Selection & Placement
Maps4FS automatically:
1. **Identifies** areas marked for building placement
2. **Filters** buildings by matching categories
3. **Selects** appropriate buildings based on area size and type
4. **Places** buildings with proper spacing and orientation

## Field Reference: Complete Configuration Guide

### Core Properties

**`file`** *(string, required)*  
**Purpose**: Path to the building's 3D model file  
**Game Assets**: `$data/maps/mapEU/textures/buildings/...`  
**Custom Assets**: `/assets/buildings/...`  
**Critical**: File path determines whether building uses game assets or custom template assets

**`name`** *(string, required)*  
**Purpose**: Unique building identifier for internal reference  
**Best Practice**: Use descriptive, consistent naming that reflects building purpose  
**Examples**: `apartmentBuilding01`, `gasStation`, `customWarehouse`

### Physical Dimensions

**`width`** *(float, required)*  
**Purpose**: Building width in meters (X-axis dimension)  
**Measurement**: Real-world meter scale for accurate placement  
**Precision**: Decimal values supported for exact dimensions

**`depth`** *(float, required)*  
**Purpose**: Building depth in meters (Z-axis dimension)  
**Measurement**: Real-world meter scale for accurate placement  
**Precision**: Decimal values supported for exact dimensions

**⚠️ Height Deprecated**: Height values are **no longer used** in FS25 buildings schema. The game engine determines building height automatically from the 3D model.

### Classification System

**`type`** *(string, required)*  
**Purpose**: Building functional classification  
**Examples**: `"apartment"`, `"station"`, `"mill"`, `"silo"`, `"warehouse"`  
**Strategic Use**: Enables filtering and specialized placement logic

**`categories`** *(array, required)*  
**Purpose**: Land use compatibility categories - **the core placement intelligence**  
**Critical Function**: Must match `building_category` values in texture schema  
**Examples**: 
- `["residential"]` - Only placed in residential areas
- `["retail", "commercial"]` - Placed in retail OR commercial areas
- `["farmyard", "industrial"]` - Placed in farmyard OR industrial areas

### Geographic Constraints

**`regions`** *(array, required)*  
**Purpose**: Geographic/cultural region compatibility  
**Current Options**: `["EU"]` (European assets)  
**Future Expansion**: Additional regions (US, etc.) planned for multi-regional support  
**Filtering**: Buildings only appear in compatible regional contexts

## Building Asset Integration

### Game Asset Buildings

**Path Format**: `$data/maps/mapEU/textures/buildings/[category]/[building].i3d`

**Advantages:**
- ✅ **Always available** - No additional assets required
- ✅ **Performance optimized** - Pre-optimized by Giants Software
- ✅ **Consistent quality** - Professional 3D models and textures
- ✅ **Automatic compatibility** - Guaranteed to work in all FS25 installations

**Example:**
```json
{
  "file": "$data/maps/mapEU/textures/buildings/grainSilo/grainSilo.i3d",
  "name": "grainSilo",
  "width": 30.0,
  "depth": 30.0,
  "type": "silo",
  "categories": ["farmyard", "industrial"],
  "regions": ["EU"]
}
```

### Custom Asset Buildings

**Path Format**: `/assets/buildings/[building-name]/[building-name].i3d`

**Requirements:**
- 🔧 **Custom map template** with building assets
- 🔧 **Complete asset package** (i3d, textures, materials)
- 🔧 **FS25 compatibility** - Models must follow FS25 standards
- 🔧 **Template integration** - Assets must be included during generation

**Advantages:**
- 🎨 **Unlimited customization** - Any building design possible
- 🎨 **Unique visual identity** - Distinctive map appearance  
- 🎨 **Specialized functionality** - Buildings tailored for specific purposes

**Example:**
```json
{
  "file": "/assets/buildings/modernOffice/modernOffice.i3d",
  "name": "modernOffice",
  "width": 45.0,
  "depth": 20.0,
  "type": "office",
  "categories": ["commercial"],
  "regions": ["EU"]
}
```

**⚠️ Critical Warning**: Custom buildings **will not function** if the required assets are missing from your map template. The building entries will be added to `map.i3d` but will appear as missing/broken objects in-game.

## Category System & Placement Logic

### Available Categories

**`residential`** - Housing and residential facilities
- **OSM Areas**: `landuse=residential`
- **Buildings**: Houses, apartments, residential complexes
- **Placement**: Distributed throughout residential neighborhoods

**`commercial`** - General business and office areas  
- **OSM Areas**: `landuse=commercial`
- **Buildings**: Offices, business centers, mixed-use facilities
- **Placement**: Concentrated in business districts

**`retail`** - Shopping and customer-facing businesses
- **OSM Areas**: `landuse=retail`  
- **Buildings**: Stores, gas stations, pharmacies, dealerships
- **Placement**: Along major roads and commercial strips

**`industrial`** - Manufacturing and heavy industry
- **OSM Areas**: `landuse=industrial`
- **Buildings**: Factories, mills, power plants, processing facilities  
- **Placement**: Industrial zones, often near transportation

**`farmyard`** - Agricultural facilities and farm buildings
- **OSM Areas**: `landuse=farmyard`
- **Buildings**: Silos, barns, grain elevators, storage buildings
- **Placement**: Rural areas, farm complexes

**`religious`** - Religious and spiritual sites
- **OSM Areas**: `landuse=religious`
- **Buildings**: Churches, sanctuaries, religious facilities
- **Placement**: Community centers, often prominently positioned

**`recreation`** - Sports and leisure facilities  
- **OSM Areas**: `landuse=recreation_ground`
- **Buildings**: Sports facilities, recreational buildings
- **Placement**: Parks, sports complexes, community areas

### Multi-Category Buildings

Buildings can belong to **multiple categories** for flexible placement:

```json
{
  "name": "vehicleShop",
  "categories": ["retail", "commercial"],
  "type": "shop"
}
```

**Placement Logic**: This building can be placed in **either** retail areas **or** commercial areas, providing greater placement flexibility.

## Custom Schema Development

### Schema Editing

You can create and modify building schemas to customize which buildings are placed in your maps and how they are distributed.

### Schema Modification Workflow

1. **Locate Schema**: Navigate to `templates/fs25-buildings-schema.json` in your Maps4FS installation
2. **Backup Original**: Always create backup before modifications
3. **Edit JSON**: Use any JSON editor to modify the schema  
4. **Validate Syntax**: Ensure proper JSON formatting
5. **Test Generation**: Generate small test maps to verify changes

### Adding Custom Buildings

**Prerequisites:**
- Custom building assets integrated in map template
- Complete i3d models with textures and materials
- FS25-compatible asset structure

**Schema Entry:**
```json
{
  "file": "/assets/buildings/myBuilding/myBuilding.i3d",
  "name": "myBuilding", 
  "width": 25.0,
  "depth": 15.0,
  "type": "custom",
  "categories": ["commercial"],
  "regions": ["EU"]
}
```

### Removing Buildings

Simply **delete entries** from the schema to prevent placement:
- **Individual removal**: Delete specific building entries
- **Category filtering**: Remove all buildings of certain categories
- **Regional filtering**: Remove buildings from specific regions

### Modifying Existing Buildings

**Dimension Updates**: Correct width/depth measurements
```json
{
  "name": "gasStation",
  "width": 35.0,  // Updated measurement
  "depth": 25.0   // Updated measurement
}
```

**Category Reassignment**: Change placement contexts
```json
{
  "name": "smallGroceryStore",
  "categories": ["retail", "residential"]  // Now places in residential areas too
}
```

## Best Practices

### Schema Management
- **Backup first**: Always save original schema before edits
- **Test incrementally**: Make small changes and test results
- **Document changes**: Track modifications for future reference
- **Version control**: Maintain schema versions alongside templates

### Building Development
- **Measure accurately**: Use precise width/depth measurements for proper spacing
- **Category appropriately**: Assign logical categories for realistic placement
- **Test in context**: Verify buildings work well in target land use areas
- **Performance conscious**: Consider impact of complex custom models

### Template Integration
- **Asset completeness**: Ensure all required files are included
- **Path consistency**: Maintain consistent file organization
- **Quality standards**: Follow FS25 modeling and texturing standards
- **Compatibility testing**: Verify assets work across different scenarios

### ⚠️ Critical Polygon Design Guidelines

**Building Area Shape Design:**
- **❌ Avoid complex polygonal shapes** - Buildings are automatically transformed to rectangular bounding boxes during placement. Complex shapes (L-shapes, curves, irregular polygons) will result in poor fitting and misaligned buildings
- **✅ Use simple rectangular areas** - Design building areas as clean rectangles that match the intended building footprint for optimal placement accuracy

**Tolerance Factor Optimization:**
- **❌ Avoid high tolerance values (>50%)** - While higher tolerance may place more buildings, it often results in significantly mismatched building sizes that look unrealistic
- **✅ Use moderate tolerance (20-35%)** - Provides good balance between coverage and visual accuracy
- **✅ Configure in Building Settings** - Adjust tolerance in the [Building Settings](settings.md#-building-settings-fs25-only) section of your generation configuration

**Polygon Spacing Requirements:**
- **❌ Avoid overlapping building areas** - Overlapping polygons will cause buildings to be placed on top of each other, creating visual conflicts and gameplay issues
- **✅ Maintain adequate spacing** - Leave clear gaps (minimum 5-10 meters) between building area polygons to ensure proper building separation
- **✅ Consider building dimensions** - Larger buildings require more spacing buffer to prevent unintentional overlap during placement

## Troubleshooting

### Common Issues

**Buildings not appearing**:
- ✅ Verify matching categories between texture schema and buildings schema
- ✅ Check OSM areas are properly tagged with correct landuse values
- ✅ Ensure regions match between building and generation settings

**Missing/broken buildings in-game**:
- ✅ Confirm custom building assets are included in map template
- ✅ Verify file paths are correct in schema
- ✅ Check i3d files and dependencies are properly structured

**JSON syntax errors**:
- ✅ Validate JSON formatting using online validators
- ✅ Check for missing commas, brackets, or quotes
- ✅ Ensure proper array and object structures

**Placement issues**:
- ✅ Verify width/depth dimensions are accurate
- ✅ Check category assignments are logical for target areas
- ✅ Ensure adequate space exists in designated areas

### Performance Optimization

**Large schemas**: Consider removing unused buildings to improve processing speed  
**Complex models**: Simplify custom building geometry for better performance  
**Category overlap**: Optimize category assignments to prevent placement conflicts  
**Regional filtering**: Use regional constraints to limit building sets appropriately

## Integration Examples

### Complete Workflow Example

1. **OSM Area Setup**:
   ```
   Draw polygon in OSM with landuse=commercial
   ```

2. **Texture Schema Entry**:
   ```json
   {
     "name": "BC_commercial",
     "count": 1,
     "external": true,  
     "tags": { "landuse": "commercial" },
     "building_category": "commercial"
   }
   ```

3. **Buildings Schema Entries**:
   ```json
   [
     {
       "name": "vehicleShop",
       "categories": ["commercial"],
       "width": 40.0,
       "depth": 15.0
     },
     {
       "name": "gasStation", 
       "categories": ["retail", "commercial"],
       "width": 40.0,
       "depth": 30.0
     }
   ]
   ```

4. **Result**: Maps4FS places vehicle shops and gas stations within the commercial area based on available space and building dimensions.

## ⚠️ Important Limitations

- **FS25 exclusive**: No building schema support for FS22
- **Schema editing**: Create and modify custom building placement configurations
- **Template dependency**: Custom buildings require proper map template integration  
- **Asset requirements**: Custom buildings must include complete asset packages
- **Performance impact**: Large building schemas may slow generation processing
- **Regional constraints**: Buildings limited to compatible regional contexts

For additional guidance, consult [Map Templates](map_templates.md) for asset integration and [Texture Schema](texture_schema.md) for area definition workflows.