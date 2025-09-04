# Core Generat## Map Dimensions

### Standard Sizes
Choose from professionally optimized map sizes. Larger maps require [Local deployment](local_deployment.md) for sufficient processing power.

**Available Sizes:**
- **2×2 km** - Perfect for detailed farming operations
- **4×4 km** - Balanced size for diverse gameplay
- **8×8 km** - Expansive agricultural landscapes
- **16×16 km** - Maximum scale (⚠️ **FS25 Compatibility Warning**: May exceed engine limitations, causing Giants Editor crashes)s

## Game Platform Selection

Choose your target Farming Simulator version from the dropdown menu. Default: **Farming Simulator 25**.

**⚠️ IMPORTANT**: Farming Simulator 22 support is **officially discontinued**. FS22 lacks critical features including forest generation and advanced field creation. All future development focuses exclusively on FS25. **Strongly recommended**: Use FS25 for optimal results and continued feature support.

## Geographic Coordinates

**Latitude and Longitude**: Define the exact center point of your map using decimal coordinates (e.g., `45.28, 20.23`).

**Critical Requirement**: Use decimal format only. Other coordinate formats will cause generation failure.

### Map Size

#### Default sizes
The tool supports all possible sizes of maps, but some of them only available in the [Local deployment](local_deployment.md). <br>
The sizes are:
- 2x2 km
- 4x4 km
- 8x8 km
- 16x16 km

**NOTE:** 16 km maps probably won't work for FS25 due to the limitations of the game engine. The map will be generated, but you may have issues trying to open it in the Giants Editor.

### Advanced: Custom Dimensions

**Expert Feature**: Specify non-standard map sizes for specialized requirements.

**⚠️ CRITICAL LIMITATION**: Giants Editor **only supports** square maps with power-of-2 dimensions (2048m, 4096m, 8192m). Custom sizes will generate successfully but **will crash Giants Editor** during import.

**Recommended Use**: Research and testing purposes only.

### Scaling Configuration

**Output Size**: Apply intelligent scaling to fit larger real-world regions into compatible map dimensions.

**Example Use Case**: Capture a 3000m×3000m real-world area but output as a 2048m×2048m Giants Editor-compatible map. The terrain detail and geographic accuracy are preserved while ensuring editor compatibility.

**Strategic Advantage**: Access larger geographic regions without sacrificing Giants Editor stability.

## Elevation Data Sources

**DTM Provider**: Select your Digital Terrain Model data source for accurate elevation mapping.

**Default Provider**: `SRTM30Provider` - Global coverage with moderate resolution, reliable worldwide availability.

**Optimization Strategy**: Choose the **highest resolution provider available** for your region. The interface automatically filters providers based on your coordinates, showing only compatible options.

**Quality Hierarchy**: Regional providers typically offer superior resolution compared to global datasets. Prioritize local data sources when available.

**⚠️ Community Providers**: Third-party providers are experimental and unsupported. Use at your own risk - contact provider authors directly for technical issues.

## Orientation Control

**Map Rotation**: Apply precise angular adjustments to optimize map orientation for gameplay or geographic accuracy.

**Range**: 0° to 360° (decimal values accepted)  
**Default**: 0° (North-aligned)  
**Application**: Affects both terrain elevation and all geographic features uniformly

**Strategic Uses**:
- Align field boundaries with preferred farming patterns
- Optimize road networks for logical traffic flow
- Match real-world cardinal directions for immersive gameplay