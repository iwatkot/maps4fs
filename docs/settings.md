# Settings

The Settings feature provides centralized management of game-specific configurations that define how Maps4FS generates your maps. This powerful tool allows you to customize and organize your texture schemas, tree schemas, and map templates across different Farming Simulator versions.

⚠️ **Local Deployment Only**: Settings management is exclusively available in [Local Deployment](local_deployment.md), similar to the [Presets](presets.md) feature.

## What are Settings?

Settings in Maps4FS refer to the configuration files that control various aspects of map generation:

- **[Texture Schemas](texture_schema.md)** - Define how OpenStreetMap data translates to Farming Simulator textures
- **[Tree Schemas](tree_schema.md)** - Control which tree species are available for procedural placement
- **Map Templates** - Provide the foundational structure for generated maps
- **General Settings** - Software-wide configurations *(coming soon)*

![Settings Interface](https://github.com/iwatkot/maps4fsui/releases/download/2.7.7/settingstab01.png)

## How Settings Work

### 🎯 **Game Version Support**
Settings are organized by Farming Simulator version with different capabilities:

**Farming Simulator 25:**
- ✅ Texture Schemas
- ✅ Tree Schemas  
- ✅ Map Templates

**Farming Simulator 22:**
- ✅ Texture Schemas
- ✅ Map Templates
- ❌ Tree Schemas *(not supported)*

### 📁 **Directory Structure**
Settings are stored in the `templates/` folder within your [Data Directory](data_directory.md):

```
📂 templates/
├── 📂 fs25/                    # Farming Simulator 25 settings
│   ├── 📂 texture_schemas/     # FS25 texture configurations
│   │   ├── 📄 default.json     # Default texture schema
│   │   ├── 📄 realistic.json   # Custom realistic textures
│   │   └── 📄 simplified.json  # Simplified texture set
│   ├── 📂 tree_schemas/        # FS25 tree configurations  
│   │   ├── 📄 default.json     # Default tree selection
│   │   ├── 📄 european.json    # European tree species
│   │   └── 📄 minimal.json     # Minimal tree variety
│   └── 📂 map_templates/       # FS25 map templates
│       ├── 📄 standard.zip     # Standard FS25 template
│       └── 📄 custom.zip       # Custom map template
└── 📂 fs22/                    # Farming Simulator 22 settings
    ├── 📂 texture_schemas/     # FS22 texture configurations
    │   ├── 📄 default.json     # Default texture schema
    │   └── 📄 custom.json      # Custom texture set
    └── 📂 map_templates/       # FS22 map templates
        ├── 📄 standard.zip     # Standard FS22 template  
        └── 📄 modded.zip       # Modded map template
```

## Settings Management Interface

The Settings tab provides intuitive management similar to the [Presets](presets.md) system:

### 🗂️ **List View**
- **Visual Overview** - See all available settings organized by category
- **Quick Details** - File size, creation date, and modification date
- **Status Indicators** - Identify default settings and active configurations

### ⚙️ **Management Actions**
- **👁️ View** - Preview setting content without editing
- **✏️ Rename** - Give descriptive names to your configurations  
- **🗑️ Delete** - Remove unwanted settings (with safety confirmations)
- **⭐ Set Default** - Mark settings as default for new map generations

### 🔄 **Integration with Generation**
- **Automatic Selection** - Default settings are applied automatically
- **Custom Override** - Choose specific settings for individual maps
- **Validation** - Ensures settings compatibility with selected game version

## Setting Types Explained

### 🎨 **Texture Schemas**
Control how OpenStreetMap features become Farming Simulator terrain textures.

**What they define:**
- Road surface types and widths
- Field and farmland appearances  
- Forest and vegetation textures
- Water and shoreline materials
- Building and structure surfaces

**Use cases:**
- **Regional Authenticity** - European vs. American road styles
- **Visual Style** - Realistic vs. stylized appearances
- **Performance Optimization** - Simplified textures for better performance

**Learn more:** [Texture Schema Documentation](texture_schema.md)

### 🌳 **Tree Schemas** *(FS25 Only)*
Define which tree species are available for procedural forest generation.

**What they control:**
- Available tree species (oak, pine, birch, etc.)
- Growth stage variations (young to ancient)
- Regional tree distributions
- Performance optimization through species selection

**Use cases:**
- **Geographic Realism** - Native species for specific regions
- **Seasonal Variation** - Appropriate tree types for climate zones
- **Performance Tuning** - Optimized tree selection for hardware capabilities

**Learn more:** [Tree Schema Documentation](tree_schema.md)

### 🗺️ **Map Templates**
Provide the foundational structure and assets for generated maps.

**What they include:**
- Basic map geometry and terrain structure
- Standard buildings and objects
- Game-specific configuration files
- Required texture and model assets

**Use cases:**
- **Game Compatibility** - Ensure maps work with specific FS versions
- **Custom Features** - Templates with specialized buildings or layouts
- **Mod Integration** - Templates designed for specific mod requirements

**Learn more:** [Map Templates Documentation](map_templates.md)

## Getting Started with Settings

### 1️⃣ **Access Settings**
Navigate to the Settings tab in your local Maps4FS interface.

### 2️⃣ **Select Game Version**  
Choose between Farming Simulator 25 or Farming Simulator 22.

### 3️⃣ **Browse Categories**
Explore Texture Schemas, Tree Schemas (FS25), and Map Templates.

### 4️⃣ **Manage Your Settings**
- View existing configurations
- Rename settings with descriptive names
- Set defaults for automatic use
- Delete unused configurations

### 5️⃣ **Apply to Generation**
Your default settings are automatically used, or select specific settings during map creation.

![Selected settings](https://github.com/iwatkot/maps4fsui/releases/download/2.7.7/settingstab02.png)

## Advanced Settings Management

### 🔄 **Import/Export Workflow**
- **Backup Configurations** - Export important settings for safekeeping
- **Share Settings** - Exchange configurations with other Maps4FS users
- **Version Control** - Maintain different versions of the same configuration type

### 🎯 **Default Management Strategy**
- **Set Sensible Defaults** - Choose your most commonly used configurations
- **Project-Specific Overrides** - Select specialized settings for specific map projects
- **Fallback Safety** - Always maintain working default configurations

### 📊 **Organization Best Practices**
- **Descriptive Names** - Use clear, descriptive names (e.g., "European_Roads_Dense", "Mountain_Trees_FS25")
- **Version Documentation** - Include version numbers or dates in names when managing iterations
- **Purpose Clarity** - Name settings based on their intended use case or geographic region

## Integration with Other Features

### 🔗 **Presets Integration**
Settings work seamlessly with the [Presets](presets.md) system:
- **Preset Application** - Presets can specify which settings to use
- **Consistent Workflow** - Similar management interface for both features
- **Complete Configuration** - Combine data presets with settings for full map control

### 🗂️ **Data Directory Integration**  
Settings are part of the [Data Directory](data_directory.md) structure:
- **Persistent Storage** - Settings survive container updates and restarts
- **File System Access** - Direct file manipulation when needed
- **Backup Inclusion** - Settings are included in data directory backups

### 🎨 **Schemas Editor Integration**
The [Schemas Editor](schemas_editor.md) complements Settings management:
- **Visual Editing** - Create and modify schemas through visual interface
- **Settings Export** - Export edited schemas to Settings for organization
- **Template Creation** - Develop new configurations for Settings library

## Future Enhancements

### 🔧 **General Settings** *(Coming Soon)*
Planned expansion to include software-wide configurations:
- **Performance Settings** - Memory usage, CPU optimization, cache management
- **Interface Preferences** - Theme selection, layout customization, language options
- **Generation Defaults** - Default map sizes, coordinate systems, output formats
- **Integration Settings** - External tool configurations, export preferences

### 📈 **Enhanced Management**
Future improvements planned:
- **Settings Validation** - Automatic compatibility checking and error detection
- **Bulk Operations** - Import/export multiple settings simultaneously
- **Settings Marketplace** - Community sharing platform for configurations
- **Advanced Filtering** - Search and filter settings by tags, compatibility, or creation date

## Troubleshooting

### ❌ **Common Issues**

**Settings not appearing:**
- Ensure files are in the correct directory structure
- Check file permissions in the Data Directory  
- Verify JSON syntax in configuration files

**Default settings not applying:**
- Confirm default is properly marked in the interface
- Check for conflicting manual selections during generation
- Verify settings compatibility with selected game version

**Performance issues:**
- Consider using simplified texture schemas for better performance
- Reduce tree variety in tree schemas if experiencing slowdowns
- Ensure map templates are appropriate for your hardware capabilities

## Related Documentation

- **[Texture Schema](texture_schema.md)** - Detailed texture configuration guide
- **[Tree Schema](tree_schema.md)** - Complete tree schema reference
- **[Data Directory](data_directory.md)** - Understanding the data structure  
- **[Presets](presets.md)** - Complementary data management system
- **[Schemas Editor](schemas_editor.md)** - Visual editing tools for schemas
- **[Local Deployment](local_deployment.md)** - Setting up your local environment

---

**Master your map generation workflow** with comprehensive Settings management. Organize your configurations, establish reliable defaults, and create maps with consistent, professional results every time!