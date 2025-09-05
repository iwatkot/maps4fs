# Tree Schema

The Tree Schema defines which tree species are available for procedural placement on generated maps. This JSON configuration file controls the variety and characteristics of trees that Maps4FS can place across your landscape.

## **⚠️ Farming Simulator 25 Only**

Tree Schema is **only available for Farming Simulator 25**. FS22 does not support this customization feature.

## File Location

The tree schema is located in your **Data Directory**:

```
📁 Data Directory/
└── 📂 templates/
    └── 📄 fs25-tree-schema.json  ← Tree definitions for FS25
```

## Schema Structure

Each tree entry defines a specific tree variant with the following properties:

```json
{
  "name": "americanElm_stage03",
  "reference_id": 1003,
  "leaf_type": "broadleaved"
}
```

### **Properties Explained**

- **`name`**: Internal tree model identifier used by Farming Simulator
- **`reference_id`**: Unique numerical ID for Maps4FS processing (1001-1083)
- **`leaf_type`**: Tree category classification
  - `"broadleaved"`: Deciduous trees (oak, elm, maple, etc.)
  - *Note: All current trees are broadleaved; no coniferous trees in default schema*

## Available Tree Species

The default schema includes **81+ tree variants** across multiple species:

### **Common Tree Types**
- **American Elm** (5 growth stages)
- **Apple Trees** 
- **Aspen** (4 growth stages)
- **Beech** (4 growth stages)
- **Birch** (4 growth stages)
- **Cherry** (4 growth stages)
- **Oak** (4 growth stages)
- **Maple** (4 growth stages)
- **Linden** (4 growth stages)
- **Pine** (4 growth stages)
- **Willow** (4 growth stages)
- **And many more...**

### **Growth Stages**
Most species include multiple growth stages representing different maturity levels:
- `stage01` - Young/small trees
- `stage02` - Growing trees  
- `stage03` - Mature trees
- `stage04` - Fully grown trees
- `stage05` - Ancient/maximum size (rare)

## Customization Options

### **Adding Custom Trees**

**Prerequisites**: Custom trees must be included in your **custom map template**. See [Map Templates](map_templates.md) documentation.

1. **Create tree models** or obtain compatible FS25 tree assets
2. **Add to custom template** with proper naming and file structure
3. **Update tree schema** with new entries:

```json
{
  "name": "myCustomOak_stage01",
  "reference_id": 2001,
  "leaf_type": "broadleaved"
}
```

### **Reference ID Guidelines**
- **Default range**: 1001-1083 (reserved for standard trees)
- **Custom range**: 2001+ (recommended for custom additions)
- **Avoid conflicts**: Ensure unique IDs across all entries
- **Sequential numbering**: Keep custom IDs organized

### **Removing Trees**
Simply delete entries from the schema to prevent those trees from being placed:
- **Selective removal**: Remove specific growth stages
- **Species removal**: Remove entire species by deleting all stages
- **Backup first**: Save original schema before modifications

## Integration with Map Generation

### **Tree Placement Logic**
Maps4FS uses the tree schema to:
- **Select appropriate species** for different terrain types
- **Vary growth stages** for natural appearance
- **Respect density settings** from generation parameters
- **Match environmental conditions** to tree types

### **Performance Considerations**
- **More tree varieties** = more diverse landscapes
- **Fewer varieties** = potentially better performance
- **Growth stage distribution** affects visual complexity
- **Custom models** may impact game performance

## Best Practices

### **Schema Management**
- **Backup original** before making changes
- **Test incrementally** - add few trees at a time
- **Validate JSON** - ensure proper syntax after edits
- **Document changes** for future reference

### **Custom Tree Development**
- **Follow FS25 standards** for model compatibility
- **Include multiple stages** for natural progression
- **Test in-game** before finalizing additions
- **Consider performance** impact of complex models

### **Workflow Integration**
- **Coordinate with templates** - ensure tree assets are available
- **Version control** custom schemas alongside templates
- **Share responsibly** - document custom schemas for community

## Troubleshooting

**Trees not appearing**: Verify tree models exist in map template and reference IDs match

**JSON errors**: Validate syntax using online JSON validators

**Missing growth stages**: Check that all referenced stages are defined in template

**Performance issues**: Reduce tree variety or simplify custom models

**Template conflicts**: Ensure custom trees are properly integrated in map template files

## ⚠️ Important Limitations

- **Template dependency**: Custom trees require proper map template integration
- **FS25 exclusive**: No tree schema support for FS22
- **Model requirements**: Trees must follow FS25 asset standards and naming conventions
- **Reference ID limits**: Avoid conflicts with future default additions
