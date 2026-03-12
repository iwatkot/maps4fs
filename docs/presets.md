# Presets

The Presets feature revolutionizes your Maps4FS workflow by allowing you to store and manage multiple configurations for different map types. Instead of manually setting up OSM files, DEM data, and generation settings each time, you can create, save, and apply presets with a single click.

## What are Presets?

Presets are pre-configured collections of map generation resources that include:

- **OSM Files** - OpenStreetMap data for realistic map features
- **DEM Files** - Digital Elevation Models for terrain height data
- **Main Settings** - Core map parameters like size, coordinates, and game version
- **Generation Settings** - Advanced generation options and fine-tuning parameters

Each preset acts as a complete "recipe" for generating a specific type or style of map, eliminating repetitive setup and ensuring consistency across your projects.

![Presets Interface](https://github.com/iwatkot/maps4fsui/releases/download/2.6.2.8/presets1.png)

## Why Use Presets?

### **Workflow Efficiency**
- **One-Click Setup** - Apply complete configurations instantly
- **No Repetitive Work** - Set up once, use many times
- **Batch Processing** - Generate multiple similar maps quickly
- **Consistent Results** - Same settings produce predictable outcomes

### **Organization Benefits**
- **Multiple Configurations** - Store unlimited preset variations
- **Easy Comparison** - Switch between different setups instantly
- **Project Management** - Organize presets by map type or region
- **Template Library** - Build a collection of proven configurations

### **Quality Control**
- **Tested Settings** - Save configurations that work well
- **Version Control** - Maintain different versions of the same preset
- **Backup Safety** - Never lose your perfect settings again

## 📁 Preset Types

The Presets system organizes your resources into four main categories:

### 1. 🗺️ OSM Presets
**📍 Location**: `defaults/osm/`
**🎯 Purpose**: Collection of OpenStreetMap data files

OSM files contain the road networks, buildings, forests, and water bodies that define your map's structure and layout. Multiple OSM files let you:
- 🔄 Store different regions for comparison
- 💾 Maintain backup versions of edited data
- 🧪 Test variations without losing originals

**📋 File Format**: `.osm` files from JOSM, Overpass API, or other OSM editors

📖 **Learn More**: See [Custom OSM](custom_osm.md) for detailed creation and editing guides.

### 2. 🏔️ DEM Presets
**📍 Location**: `defaults/dem/`
**🎯 Purpose**: Digital Elevation Model heightmaps

DEM files define the terrain elevation for both playable areas and background landscapes. Multiple DEM files enable:
- 🌄 Different elevation scenarios for the same region
- 🍂 Seasonal or modified terrain versions
- 💾 Backup copies of processed heightmaps

**📋 File Format**: PNG images (16-bit grayscale, specific dimensions required)

📖 **Learn More**: See [Custom DEM](custom_dem.md) for file requirements and creation workflows.

### 3. ⚙️ Main Settings Presets
**📍 Location**: `defaults/main_settings/`
**🎯 Purpose**: Core map configuration parameters

Main Settings define the fundamental properties that control overall map structure:
- 🎮 **Game Version** - compatibility
- 🌍 **Map Coordinates** - Latitude/longitude positioning
- 📏 **Map Size** - 2×2, 4×4, 8×8, or 16×16 km dimensions
- 🧭 **Rotation** - Map orientation adjustments
- 🔧 **Other Core Properties** - Essential generation parameters

**📋 File Format**: JSON configuration files

📖 **Learn More**: See [Main Settings](main_settings.md) for detailed parameter explanations.

### 4. 🛠️ Generation Settings Presets
**📍 Location**: `defaults/generation_settings/`
**🎯 Purpose**: Advanced generation control parameters

Generation Settings control detailed aspects of the map creation process:
- 🏞️ **Background Terrain** - Surrounding landscape generation
- 💧 **Water Planes** - Lake and river configuration
- 🌾 **Field Boundaries** - Agricultural area definitions
- 🌲 **Forest Density** - Tree coverage parameters
- 🔬 **Other Advanced Options** - Fine-tuning controls

**📋 File Format**: JSON configuration files

📖 **Learn More**: See [Generation Settings](generation_settings.md) for comprehensive parameter documentation.

![Manage Presets](https://github.com/iwatkot/maps4fsui/releases/download/2.6.2.8/presets2.png)

### 📊 Preset Types Quick Reference

| Preset Type | Directory | File Format | Purpose | Documentation |
|-------------|-----------|-------------|---------|---------------|
| 🗺️ **OSM** | `defaults/osm/` | `.osm` | Road networks, buildings, features | [Custom OSM](custom_osm.md) |
| 🏔️ **DEM** | `defaults/dem/` | `.png` (16-bit) | Terrain elevation data | [Custom DEM](custom_dem.md) |
| ⚙️ **Main Settings** | `defaults/main_settings/` | `.json` | Core map parameters | [Main Settings](main_settings.md) |
| 🛠️ **Generation** | `defaults/generation_settings/` | `.json` | Advanced generation options | [Generation Settings](generation_settings.md) |

## 🖥️ Using Presets (Local Version Only)

ℹ️ **Note**: The Presets feature is available in the Windows App and Docker deployment. The web version does not support this functionality.

### Setting Up Preset Directories

1. **Navigate to your Data Directory**: Usually `~/maps4fs/defaults/`
2. **Create preset directories** if they don't exist:
   ```
   defaults/
   ├── osm/
   ├── dem/
   ├── main_settings/
   └── generation_settings/
   ```
3. **Add your preset files** to the appropriate directories

### 🎛️ Managing Presets in the UI

The Maps4FS interface provides powerful preset management tools:

#### 👁️ **Preview Function**
- 📋 **Visual Overview** - See preset contents before applying
- 📊 **Configuration Summary** - Quick review of all settings
- ✅ **Compatibility Check** - Verify preset works with current setup

#### 📥 **Save from My Maps**
- 🏆 **Import Successful Configs** - Copy settings from previously generated maps
- 🔍 **Reverse Engineering** - Extract presets from existing projects
- 📚 **Build Library** - Create presets from your best maps

#### 🚀 **Apply Presets**
- 🎯 **One-Click Application** - Load complete configurations instantly
- 🎛️ **Selective Loading** - Choose which preset components to apply
- 🛡️ **Override Protection** - Prevent accidental setting overwrites

### 🔄 Preset Workflow Example

**🎯 Scenario**: Creating presets for different European farming regions

1. **🏔️ Create Base DEM Preset**:
   - Generate high-quality DEM for German countryside using [Custom DEM](custom_dem.md) techniques
   - Save as `defaults/dem/germany_plains.png`

2. **🗺️ Add OSM Variations**:
   - `defaults/osm/germany_roads_heavy.osm` - Dense road network
   - `defaults/osm/germany_roads_light.osm` - Rural road layout
   - Created using [Custom OSM](custom_osm.md) methods

3. **⚙️ Configure Settings Presets**:
   - `defaults/main_settings/germany_4x4.json` - 4×4km German coordinates ([Main Settings](main_settings.md))
   - `defaults/generation_settings/realistic_fields.json` - Authentic field patterns ([Generation Settings](generation_settings.md))

4. **🚀 Generate Maps**:
   - Apply "germany_plains.png" DEM preset
   - Choose road density OSM preset
   - Load German coordinates and realistic field settings
   - Generate multiple variations quickly with consistent quality

## 📁 File Management Best Practices

### 📝 **Naming Conventions**
Use descriptive, consistent names for easy identification:
```
Good Examples:
├── scotland_highlands_dem.png
├── france_vineyard_roads.osm
├── large_fields_4x4.json
└── forest_dense_mountains.json

Avoid:
├── map1.png
├── test.osm
├── settings.json
└── new_config.json
```

### 🗂️ **Organization Structure**
Group related presets by project or region:
```
defaults/
├── osm/
│   ├── europe_germany_rural.osm
│   ├── europe_france_vineyard.osm
│   └── usa_midwest_plains.osm
├── dem/
│   ├── mountains_alps_4x4.png
│   ├── plains_midwest_8x8.png
│   └── coastal_norway_2x2.png
└── main_settings/
    ├── germany_standard.json
    ├── france_wine_region.json
    └── usa_corn_belt.json
```

### 🔄 **Version Control**
Maintain multiple versions of successful configurations:
```
├── mountain_terrain_v1.png
├── mountain_terrain_v2_enhanced.png
├── mountain_terrain_final.png
```

## Integration with My Maps

The Presets system integrates seamlessly with the **My Maps** feature, creating a complete map management ecosystem:

### **Save to Presets from My Maps**
- **Extract Successful Configurations** - Pull settings from your best generated maps directly into your presets library
- **Build Preset Templates** - Convert proven map configurations into reusable presets
- **Preserve Working Settings** - Backup configurations that produced great results
- **Cross-Project Reuse** - Apply successful settings from one project to new maps
- **Iterative Improvement** - Save variations and refinements of your best configurations

![My Maps Integration](https://github.com/iwatkot/maps4fsui/releases/download/2.6.2.8/presets3.png)

## 🔧 Troubleshooting

### ⚠️ **Common Issues**

#### 🚫 **Preset Not Appearing in UI**
- ✅ Verify file is in correct directory (`defaults/[type]/`)
- 📋 Check file naming and format requirements
- 🔐 Ensure Maps4FS has read access to the directory
- 🔄 Try refreshing the interface or restarting Maps4FS

#### ⚙️ **Settings Not Loading Properly**
- 🧩 Validate JSON syntax for settings files
- 📝 Confirm file encoding is UTF-8
- 🎯 Check for required fields in JSON structure
- 📖 Compare with working examples from [My Maps](my_maps.md)

#### 🗺️ **DEM/OSM Files Not Working**
- 📋 Verify file format requirements (PNG for DEM, OSM for map data)
- 📏 Check file dimensions match map size requirements
- 🔍 Ensure files aren't corrupted during transfer
- 📖 Review [Custom DEM](custom_dem.md) and [Custom OSM](custom_osm.md) requirements

### 📋 **File Format Requirements**

| File Type | Format | Requirements | Documentation |
|-----------|---------|--------------|---------------|
| 🗺️ **OSM Files** | `.osm` (XML) | Valid OSM XML structure | [Custom OSM](custom_osm.md) |
| 🏔️ **DEM Files** | `.png` (16-bit) | Grayscale, Map size + 4096px | [Custom DEM](custom_dem.md) |
| ⚙️ **Settings Files** | `.json` | Valid JSON, UTF-8 encoding | [Main Settings](main_settings.md) / [Generation Settings](generation_settings.md) |

## 🚀 Advanced Usage

### 🎛️ **Preset Combinations**
Mix and match different preset types for maximum flexibility:
- 🌍 Use European DEM with American road patterns
- 🏔️ Apply mountain terrain with plains field layouts
- ⚙️ Combine different generation settings with same base data
- 🔄 Create unique combinations not possible with single presets

### 🏭 **Batch Generation**
Leverage presets for efficient batch processing:
1. 🏔️ Set up multiple DEM presets for different terrains
2. ⚙️ Apply same generation settings across all variants
3. 🎯 Generate complete map series with consistent quality
4. 📊 Use [My Maps](my_maps.md) to track and manage your generated series

### 📚 **Template Development**
Build comprehensive template libraries:
- 🌍 **Regional Collections** - Complete preset sets for specific areas
- 🎮 **Gameplay Styles** - Different configurations for various play styles
- 🍂 **Seasonal Variations** - Same region with different characteristics
- 🏆 **Proven Configurations** - Save your most successful combinations

### 🔗 **Integration with Workflow**
Maximize efficiency by combining presets with other Maps4FS features:
- 📖 Use [Workflow Optimizations](workflow_optimizations.md) principles
- 🗂️ Leverage [Data Directory](data_directory.md) organization
- 📋 Follow [Step-by-Step Guide](step_by_step_guide.md) best practices
- 🗺️ Build on [Map Templates](map_templates.md) foundations

---

🎉 **The Presets feature transforms Maps4FS from a single-use tool into a comprehensive map development platform, enabling efficient workflows and professional-quality results.**



