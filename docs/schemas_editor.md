# Schemas Editor

The Schemas Editor is a powerful visual tool that allows you to edit and customize texture and tree schemas without manually editing JSON files. This intuitive interface makes it easy to modify how OpenStreetMap features are translated into Farming Simulator textures.

## 🎨 Textures Schema Editor

The Textures Schema Editor provides a visual interface for editing the [texture schema](texture_schema.md) - the foundational blueprint that transforms OpenStreetMap data into detailed Farming Simulator terrain.

![Textures Schema Editor](https://github.com/iwatkot/maps4fsui/releases/download/2.5.5/texture-schema-editor.png)

### What is the Textures Schema Editor?

Instead of manually editing complex JSON files, the Textures Schema Editor offers:

- **Visual texture preview** - See actual texture samples as you configure them
- **Interactive tag configuration** - Easy selection of OpenStreetMap tags
- **Real-time validation** - Immediate feedback on configuration errors
- **Category filtering** - Organize textures by type (roads, fields, forests, etc.)

### Key Features

#### 🖼️ Visual Texture Gallery
- Browse all available textures with visual previews
- Search and filter textures by name or category
- See texture count and variations at a glance

#### ⚙️ Interactive Configuration
- **Tag Editor**: Visual interface for selecting OpenStreetMap tags
- **Priority Management**: Drag-and-drop layer ordering
- **Color Picker**: Visual color selection for preview rendering
- **Width Adjustment**: Slider controls for line feature widths

#### 📊 Schema Management
- **Import/Export**: Load and save custom schema configurations
- **Template Library**: Pre-built configurations for common use cases
- **Validation**: Real-time error checking and warnings
- **Backup System**: Automatic schema versioning

### How It Works

1. **Browse Textures**: View the texture gallery with visual previews
2. **Select Texture**: Click on any texture to open its configuration
3. **Edit Properties**: Use the visual interface to modify:
   - OpenStreetMap tags that trigger this texture
   - Layer priority and rendering order
   - Width settings for linear features
   - Color coding for preview visualization
4. **Preview Changes**: See how your changes affect the texture application
5. **Save Schema**: Export your customized schema for map generation

### Benefits Over Manual JSON Editing

| Manual JSON Editing | Textures Schema Editor |
|---------------------|------------------------|
| Complex syntax requirements | Visual, intuitive interface |
| No texture previews | See actual texture samples |
| Easy to make syntax errors | Built-in validation |
| Hard to understand relationships | Visual tag relationships |
| No immediate feedback | Real-time preview |

### Common Use Cases

#### 🛣️ Road Customization
Modify how different road types appear in your maps:
- Adjust highway vs. residential road textures
- Change road widths for better realism
- Add custom textures for specific road types

#### 🌾 Agricultural Areas
Fine-tune farmland appearance:
- Customize field textures based on crop types
- Adjust meadow vs. farmland differentiation
- Create region-specific agricultural textures

#### 🌲 Forest Customization
Tailor forest rendering:
- Differentiate between forest types (mixed, broadleaved, needleleaved)
- Adjust forest edge transitions
- Create custom forestry textures

### Getting Started

1. **Open Schemas Editor**: Navigate to the "Schemas Editor" tab in Maps4FS
2. **Select Textures**: Choose "Textures Schema Editor" from the available options
3. **Choose Game Version**: Select FS25 schema to edit
4. **Start Editing**: Browse textures and begin customization
5. **Save to Settings**: Use "Save to Settings" to add your schema directly to [Settings](settings.md) management

### 🔗 Settings Integration

The Schemas Editor seamlessly integrates with the [Settings](settings.md) system:
- **Direct Save** - Save edited schemas directly to Settings with custom names
- **Organized Storage** - Schemas are automatically organized by game version in Settings
- **Default Assignment** - Set newly created schemas as default through Settings
- **Library Building** - Create multiple variations and organize them in Settings

---

*The Textures Schema Editor transforms the complex task of schema customization into an intuitive, visual experience. Whether you're a beginner looking to make simple adjustments or an advanced user creating completely custom configurations, this tool makes schema editing accessible to everyone.*

## 🌳 Tree Schema Editor

The Tree Schema Editor provides a visual interface for editing the [tree schema](tree_schema.md) - the configuration that defines which tree species are available for procedural placement on your generated maps.

![Tree Schema Editor](https://github.com/iwatkot/maps4fsui/releases/download/2.5.5/tree-schema-editor.png)

### What is the Tree Schema Editor?

Instead of manually editing JSON tree definitions, the Tree Schema Editor offers:

- **Visual tree gallery** - Browse all available tree species with 3D previews
- **Growth stage management** - See and select different maturity levels for each species
- **Species filtering** - Organize trees by type (broadleaved, coniferous, fruit trees, etc.)
- **Selection management** - Easy bulk selection and deselection of tree varieties
- **Real-time validation** - Immediate feedback on schema configuration

### Key Features

#### 🌲 Visual Tree Gallery
- Browse all tree species with detailed 3D model previews
- View different growth stages (stage01 through stage05)
- Search and filter trees by species name or characteristics
- See reference IDs and leaf types at a glance

#### 🎛️ Interactive Selection
- **Bulk Operations**: Select All / Deselect All for quick management
- **Species Grouping**: Trees organized by species with collapsible sections
- **Stage Selection**: Choose specific growth stages for natural variety
- **Type Filtering**: Filter by broadleaved, coniferous, or fruit trees

#### 📊 Schema Management
- **Import/Export**: Load and save custom tree schema configurations
- **Template Integration**: Ensure selected trees are available in your map template
- **Validation**: Check for missing tree models and reference ID conflicts
- **Preview**: See how tree selection affects landscape diversity

### How It Works

1. **Browse Tree Gallery**: View all available tree species with 3D previews
2. **Select Trees**: Click to select/deselect individual trees or growth stages
3. **Filter & Organize**: Use species filters and search to find specific trees
4. **Bulk Actions**: Use Select All/Deselect All for quick configuration
5. **Validate Selection**: Ensure selected trees are available in your template
6. **Save Schema**: Export your customized tree configuration

### Benefits Over Manual JSON Editing

| Manual JSON Editing | Tree Schema Editor |
|---------------------|-------------------|
| No visual tree previews | 3D tree model gallery |
| Complex reference ID management | Visual ID display and validation |
| Hard to understand growth stages | Clear stage progression view |
| Easy syntax errors | Built-in validation |
| No species organization | Organized by tree types |

### Common Use Cases

#### 🌿 Regional Customization
Create region-specific forests:
- Select trees native to your target geographic area
- Choose appropriate species for climate zones
- Remove non-native species for authenticity

#### 🍎 Agricultural Focus
Emphasize farming environments:
- Include fruit trees (apple, cherry) for orchards
- Select appropriate shade trees for farmyards
- Balance wild and cultivated tree varieties

#### 🎮 Performance Optimization
Optimize for game performance:
- Reduce total tree variety for better performance
- Select simpler tree models for lower-end hardware
- Focus on essential species for your map theme

#### 🌱 Growth Stage Management
Control tree maturity distribution:
- Include multiple growth stages for natural appearance
- Focus on specific stages for particular landscape themes
- Balance young and mature trees for realistic forests

### Available Features


**Advanced Capabilities:**
- **81+ tree variants** across multiple species
- **Growth stage progression** from young to ancient trees
- **Leaf type classification** for seasonal changes
- **Template integration** with custom map assets

### Getting Started

1. **Open Schemas Editor**: Navigate to the "Schemas Editor" tab in Maps4FS
2. **Select Trees**: Choose "Tree Schema Editor" from the available options
3. **Browse Gallery**: Explore available tree species and growth stages
4. **Make Selections**: Choose trees that fit your map's theme and requirements
5. **Validate**: Ensure selected trees are available in your map template
6. **Save to Settings**: Use "Save to Settings" to add your schema directly to [Settings](settings.md) management

### Template Integration

**Important**: Selected trees must be available in your [map template](map_templates.md). The Tree Schema Editor helps validate this:

- **Green indicators**: Trees available in current template
- **Warning indicators**: Trees missing from template
- **Validation messages**: Clear feedback on potential issues
- **Template suggestions**: Recommendations for compatible templates

### 🔗 Settings Integration

The Tree Schema Editor integrates seamlessly with the [Settings](settings.md) system:
- **Direct Save** - Save tree selections directly to Settings with descriptive names
- **Organization** - Tree schemas are automatically organized in Settings
- **Default Management** - Set your preferred tree schemas as default through Settings
- **Configuration Library** - Build collections of tree configurations for different map themes

---

*The Tree Schema Editor makes tree species selection intuitive and visual, allowing you to create diverse, authentic forests that match your map's geographic and thematic requirements. Whether building realistic regional landscapes or optimizing for performance, this tool puts complete control over your map's vegetation in your hands.*




