# Digital Elevation Model (DEM) Architecture

## Overview: The Foundation of Terrain

The Digital Elevation Model (DEM) serves as the **fundamental terrain foundation** for your Farming Simulator map. Every hill, valley, slope, and elevation change is precisely defined by this critical component.

**Core Concept**: A DEM is essentially a 2D grid where each cell contains a height value, creating a digital representation of real-world topography that the game engine transforms into 3D terrain.

## Technical Specifications

### File Requirements

| Game Version | Image Dimensions | File Path | Data Format |
|--------------|------------------|-----------|-------------|
| **FS25** | (map_size + 1) × (map_size + 1) | `map_directory/data/dem.png` | 16-bit PNG |
| **FS22** | (map_size ÷ 2 + 1) × (map_size ÷ 2 + 1) | `map_directory/data/map_dem.png` | 16-bit PNG |

**Data Structure:**
- **Channels**: Single channel (grayscale)
- **Data Type**: `uint16` (unsigned 16-bit integer)
- **Value Range**: 0 to 65,535 (2^16 possible elevation levels)
- **Color Depth**: 16-bit for maximum terrain detail precision

### Dimension Examples

**FS25 Standard Sizes:**
- 2048m map → 2049×2049 DEM
- 4096m map → 4097×4097 DEM  
- 8192m map → 8193×8193 DEM

**FS22 Legacy Sizes:**
- 2048m map → 1025×1025 DEM
- 4096m map → 2049×2049 DEM

## Height Scale System

### Understanding Height Conversion

**The Challenge**: DEM pixels store values 0-65,535, but real-world elevations can exceed 8,000 meters. How does this work?

**The Solution**: The `heightScale` parameter acts as a **conversion multiplier** that transforms pixel values into real-world heights.

### Height Scale Configuration

**Default Value**: 255 (in Giants Editor maps)  
**Maximum Terrain Height**: `65,535 × (heightScale ÷ 65,535) = heightScale meters`  
**With Default Settings**: Maximum possible elevation = 255 meters

**Example Calculations:**
```
heightScale = 255  → Max height: 255m
heightScale = 512  → Max height: 512m  
heightScale = 1000 → Max height: 1000m
```

### Practical Height Scale Selection

**For Flat Terrain (plains, farmland)**: 128-255m  
**For Moderate Hills**: 256-512m  
**For Mountain Regions**: 513-1000m+  
**For Extreme Terrain**: 1000m+ (with performance considerations)

### Giants Editor Configuration

1. **Open Map**: Load your map in Giants Editor
2. **Select Terrain**: Choose terrain object in Scenegraph
3. **Terrain Tab**: Navigate to Attributes → Terrain
4. **Set heightScale**: Enter your calculated value
5. **Apply Changes**: Save and reload map (File → Reload)

## Units Per Pixel System

### Spatial Resolution Control

The `unitsPerPixel` parameter defines the **terrain resolution** by specifying how many meters each DEM pixel represents.

**Game Version Defaults:**
- **FS25**: `unitsPerPixel = 1` (1 meter per pixel - highest detail)
- **FS22**: `unitsPerPixel = 2` (2 meters per pixel - moderate detail)

### Resolution Impact

**Higher Resolution (unitsPerPixel = 1)**:
- ✅ Maximum terrain detail and precision
- ✅ Sharp elevation transitions and fine features
- ⚠️ Larger file sizes and longer processing times

**Lower Resolution (unitsPerPixel = 2+)**:
- ✅ Faster processing and smaller files
- ✅ Suitable for large, gradually changing terrain
- ⚠️ Less detailed elevation features

### Custom Resolution Configuration

1. **Access Settings**: Giants Editor → Terrain → Attributes
2. **Modify unitsPerPixel**: Set integer value (1, 2, 4, etc.)
3. **Recalculate DEM Size**: Adjust DEM image dimensions accordingly
4. **Test Results**: Reload and verify terrain quality

## Advanced Optimization Strategies

### Terrain Quality vs Performance

**Maximum Quality Setup**:
- `unitsPerPixel = 1`
- `heightScale = terrain-appropriate value`
- Full-resolution DEM with detailed elevation data

**Balanced Performance Setup**:
- `unitsPerPixel = 2`
- `heightScale = 512`
- Moderate resolution suitable for most use cases

**Large Map Optimization**:
- `unitsPerPixel = 4`
- Focus on broad terrain features rather than fine detail
- Ideal for 16×16km maps with performance constraints

### Professional Workflow

1. **Analyze Source Terrain**: Study your real-world elevation data
2. **Calculate Height Range**: Determine minimum to maximum elevation difference
3. **Set Height Scale**: Choose value that accommodates your terrain range with headroom
4. **Configure Resolution**: Balance detail needs with performance requirements
5. **Generate & Test**: Create DEM and verify terrain quality in Giants Editor
6. **Iterative Refinement**: Adjust parameters based on visual and performance results

**Pro Tip**: Always maintain some headroom in your height scale to accommodate manual terrain sculpting in Giants Editor without reaching the maximum elevation limit.
