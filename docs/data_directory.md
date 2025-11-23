# Data Directory

The Data Directory is a crucial component of Maps4FS that serves as the central hub for all map generation data, user inputs, and system resources. This directory bridges your local file system with the application's data management needs.

## What is the Data Directory?

The Data Directory is a local folder (typically `C:/Users/<username>/maps4fs` on Windows) that gets mounted into the Maps4FS Docker container, providing persistent storage and easy access to your map generation workflow.

**Key Benefits:**
- **Persistent Storage** - Your data survives container restarts and updates
- **Easy Access** - Direct file system access to all generated content
- **Flexible Input** - Upload custom OSM data, DEM files, and other resources
- **Organized Workflow** - Structured approach to map generation and management

## Why Do You Need It?

### **Local Development Benefits**
- **Direct File Access** - Edit, backup, and manage files directly on your system
- **Resource Management** - Control disk space and organize your map projects
- **Custom Data Integration** - Easily add custom OSM files, elevation data, and templates
- **Performance** - Local storage provides faster access than cloud-based alternatives

### **Production Workflow**
- **Batch Processing** - Generate multiple maps with consistent settings
- **Version Control** - Maintain different versions of maps and configurations
- **Resource Sharing** - Share templates and defaults across multiple projects

## Directory Structure Overview

The Data Directory contains three main components:

```
📁 Data Directory (~/maps4fs)
├── 📂 mfsrootdir/          # Generated content & user inputs
├── 📂 templates/           # Map templates & schemas  
└── 📂 defaults/            # Default source data
```

### **mfsrootdir** - Generation Hub
**Purpose**: Active workspace for map generation and user-provided content

**Contents:**
- **Generated Maps** - Completed map packages ready for use
- **Cache Data** - Downloaded elevation and satellite imagery
- **Custom Inputs** - User-uploaded OSM files and custom data
- **Processing Files** - Temporary files during generation

**Usage**: This is where your completed maps appear and where you place custom data for processing.

### **templates** - System Resources
**Purpose**: Core Maps4FS templates and configuration schemas

**Contents:**
- **Map Templates** - Base FS22/FS25 map structures  
- **Texture Schemas** - Object-to-texture mapping definitions
- **Configuration Files** - System-wide generation settings

**Usage**: Provides the foundation for all map generation. See [Map Templates](map_templates.md) for detailed information.

### **defaults** - Source Data Repository & Presets
**Purpose**: Default geographic data and the new [Presets](presets.md) system for managing multiple configurations

**Presets Structure**:
```
📂 defaults/
├── 📂 osm/                         # OpenStreetMap data files
│   ├── 📄 germany_rural.osm        # Preset: German rural roads  
│   ├── 📄 france_vineyards.osm     # Preset: French vineyards
│   ├── 📄 mountain_roads.osm       # Preset: Mountain terrain
│   └── 📄 [multiple_osm_files].osm # Multiple OSM presets
├── 📂 dem/                         # Digital Elevation Models
│   ├── 📄 alps_mountains.png       # Preset: Alpine terrain
│   ├── 📄 plains_farmland.png      # Preset: Flat farmland
│   ├── 📄 coastal_norway.png       # Preset: Coastal terrain
│   └── 📄 [multiple_dem_files].png # Multiple DEM presets
├── 📂 main_settings/              # Main Settings presets
│   ├── 📄 germany_4x4.json         # German coordinates, 4x4km
│   ├── 📄 france_large.json        # French coordinates, 8x8km  
│   └── 📄 [settings_presets].json  # Multiple main settings
└── 📂 generation_settings/        # Generation Settings presets
    ├── 📄 realistic_fields.json    # Realistic field patterns
    ├── 📄 dense_forests.json       # Heavy forest coverage
    └── 📄 [gen_presets].json       # Multiple generation settings
```

**Key Features:**
- **🆕 OSM Presets** - Multiple OpenStreetMap configurations for different regions and road patterns
- **🏔️ DEM Presets** - Various elevation models for mountains, plains, coastal areas, and custom terrain
- **⚙️ Settings Presets** - Pre-configured main settings for different map types and regions
- **🔧 Generation Presets** - Advanced generation settings for specific map styles and requirements
- **� Selective Application** - Mix and match different preset components as needed

## Presets Integration

🆕 **New Feature**: The Data Directory now supports the [Presets](presets.md) system, enabling:

- **Multiple Configurations** - Store unlimited OSM files, DEM files, and settings
- **One-Click Switching** - Apply different presets instantly through the UI
- **Organized Workflow** - Manage complex projects with multiple variations
- **Template Libraries** - Build collections of proven configurations

**Presets Benefits:**
- **Efficiency** - No more manual file swapping or renaming
- **Organization** - Descriptive names instead of generic filenames  
- **Flexibility** - Mix and match different preset components
- **Backup Safety** - Multiple versions prevent configuration loss

## Integration with Maps4FS

The Data Directory becomes the bridge between your file system and Maps4FS:

1. **Docker Mount** - Directory is mounted into the container at runtime
2. **Persistent Storage** - Data persists across container restarts and updates
3. **File System Access** - Direct access to all generation inputs and outputs
4. **Resource Management** - Control over disk usage and data organization

## Getting Started

### **Initial Setup**
The Data Directory is automatically created during setup. You'll find a realistic example in the `maps4fs_DD` folder in the Maps4FS repository.

### **Basic Workflow**
1. **Place custom data** in `defaults/` folders if needed
2. **Run map generation** through Maps4FS interface
3. **Access completed maps** in `mfsrootdir/maps/`
4. **Manage cache** in `mfsrootdir/cache/` as needed

### **Advanced Usage**
- **Custom Templates** - Modify templates for specialized map types
- **Regional Defaults** - Set up region-specific default data
- **Batch Processing** - Organize multiple map projects efficiently

## Data Management Best Practices

### **Organization**
- Keep custom data organized in appropriate `defaults/` subfolders
- Regularly clean cache data to manage disk space
- Archive completed maps to separate storage when not actively used

### **Backup Strategy**
- Back up custom templates and default data regularly
- Consider version control for important custom configurations
- Export completed maps to separate storage for long-term preservation

### **Performance Optimization**
- Use fast local storage (SSD recommended) for the Data Directory
- Monitor disk space usage, especially in cache folders
- Clean temporary files periodically to maintain performance

## Related Documentation

- **[Map Templates](map_templates.md)** - Detailed template structure and customization
- **[Custom DEM](custom_dem.md)** - Working with custom elevation data
- **[Custom OSM](custom_osm.md)** - Managing custom OpenStreetMap data
- **[Local Deployment](local_deployment.md)** - Setting up your local Maps4FS environment

---

**Ready to dive deeper?** Explore the detailed documentation for each component to master your Maps4FS workflow and create amazing custom maps!
