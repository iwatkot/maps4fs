# Map Templates

Map templates are pre-configured Farming Simulator map structures that serve as the foundation for generated maps. They contain essential game components, texture definitions, tree schemas, and other core elements that define how your generated content integrates with the game engine.

## What Are Map Templates?

Map templates are **incomplete Farming Simulator maps** - they contain the structural framework without the actual terrain, fields, or other procedurally generated components. Think of them as blueprints that define:

- **Available textures** and their properties
- **Tree species** and placement rules
- **Game-specific configurations** and settings
- **Core map structure** and file organization
- **Compatibility layers** for different FS versions

## Default Templates Location

Templates are stored in your **Data Directory** under the `templates/` folder:

```
📁 Data Directory/
└── 📂 templates/
    ├── 📄 fs25-map-template.zip     ← Farming Simulator 25
    ├── 📄 fs25-texture-schema.json
    ├── 📄 fs25-grle-schema.json
    └── 📄 fs25-tree-schema.json
```

## ⚠️ Important Warnings

### **Critical Risk: Template Corruption**
**Incorrectly prepared templates will break everything.** A malformed template can cause:
- **Complete generation failure** - Maps4FS unable to generate any maps
- **Corrupted output files** - Broken maps that crash Farming Simulator
- **System instability** - Potential issues requiring full Data Directory reset

### **No Support for Custom Templates**
- **Use at your own risk** - Custom templates are entirely user responsibility
- **No bug reports accepted** - Issues with custom templates will not be supported
- **No troubleshooting assistance** - Community and developers cannot help with custom template problems
- **You break it, you fix it** - Template modifications require your own expertise

**Recommendation**: Always maintain working backups of default templates before experimenting.

## Using Custom Templates

### **Step 1: Prepare Your Custom Template**
1. **Modify existing template** or create your own map structure
2. **Package as ZIP file** maintaining internal folder structure
3. **Test compatibility** with your target FS version
4. **Name appropriately** (e.g., `my-custom-fs25-template.zip`)

### **Step 2: Replace Default Template**
1. **Navigate to Data Directory**: `templates/` folder
2. **Backup original**: Rename existing template (e.g., `fs25-map-template-backup.zip`)
3. **Replace template**: Copy your custom template with **exact filename**:
   - For  `fs25-map-template.zip`
4. **Verify placement**: Ensure file is directly in `templates/` folder

### **Step 3: Generate Maps**
- **All future generations** will use your custom template automatically
- **No additional configuration** required in Maps4FS interface
- **Template applies** to all maps generated for that game version

## Template Customization Scope

Templates allow extensive customization of core game elements:

- **🎨 Texture Libraries** - Add custom ground textures, modify existing ones
- **🌲 Tree Collections** - Define available tree species and growth patterns
- **⚙️ Game Settings** - Modify core gameplay parameters and restrictions
- **🏗️ Map Structure** - Alter file organization and component relationships
- **🔧 Schema Definitions** - Customize data formats and validation rules

**Note**: Template customization requires understanding of Farming Simulator modding and map structure. Experiment responsibly and maintain backups.

## Default Data Repository

For the most up-to-date default templates, schemas, and data files, visit the official repository:

🔗 **[Maps4FS Data Repository](https://github.com/iwatkot/maps4fsdata)**

This repository contains:
- **Latest template versions** for all supported FS games
- **Updated schema files** with newest game features
- **Reference implementations** for custom modifications
- **Version history** and compatibility information

## Best Practices

### **Template Management**
- **Always backup** original templates before replacement
- **Version control** your custom templates with descriptive names
- **Document changes** for future reference and troubleshooting
- **Test thoroughly** before committing to large map projects

### **Compatibility Considerations**
- **Validate structure** - Ensure internal folder organization matches expected format
- **Check dependencies** - Verify all referenced assets are included
- **Monitor updates** - Keep templates current with game patches

### **Development Workflow**
- **Start small** - Test template changes with simple maps first
- **Iterate gradually** - Make incremental modifications rather than major overhauls
- **Maintain originals** - Keep unmodified templates for fallback options
- **Share responsibly** - Document custom templates for community benefit

## Troubleshooting

**Template Not Loading**: Verify exact filename matches expected pattern (`fs##-map-template.zip`)

**Generation Errors**: Check template internal structure and ensure all required files are present

**Missing Features**: Confirm your custom template includes all necessary schema definitions

**Version Conflicts**: Ensure template version matches your target Farming Simulator game version




