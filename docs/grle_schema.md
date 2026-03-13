# GRLE Schema

The GRLE Schema defines technical specifications for Farming Simulator's internal image layers and rendering parameters. This configuration controls how Maps4FS generates various game-critical information layers that manage gameplay mechanics, collision detection, and visual effects.

## **⚠️ Farming Simulator 25**


## File Location

The GRLE schema is located in your **Data Directory**:

```
📁 Data Directory/
└── 📂 templates/
    └── 📄 fs25-grle-schema.json  ← GRLE layer definitions
```

## **⚠️ Customization Policy: Customize With Caution**

### **Customization Risks**
- **GRLE schema can be customized**, but only if you understand FS/GE layer requirements
- **Invalid values can break generation** or produce unusable maps
- **Not every layer should be changed** - many are engine-sensitive technical layers
- **Always back up** your schema before editing

### **When Customization Makes Sense**
- **Template-specific workflows** (for example custom multifruit templates)
- **Advanced compatibility adjustments** required by a specific map template
- **Controlled experiments** where you can validate results in Giants Editor

### **Extended Foliage Example (Supported Use Case)**
- If your template uses **extended foliage types**, `densityMap_fruits.png` may need `data_type: "uint16"`
- In this mode, Maps4FS can update `map.i3d` foliage layer channel settings to match extended foliage usage
- This enables values beyond uint8 limits for foliage states/types
- Use this only with templates that are prepared for extended foliage

## Schema Purpose

The GRLE schema serves as **Maps4FS internal configuration** for generating Farming Simulator-compatible layer files:

### **Information Layers Defined**
- **Environment data** - Environmental conditions and effects
- **Farmland boundaries** - Property and ownership definitions
- **Field types** - Crop compatibility and field classifications
- **Indoor masks** - Building and structure interior detection
- **Lime levels** - Soil acidity and treatment requirements
- **Navigation collision** - AI pathfinding and movement restrictions
- **Placement collision** - Object placement validation and constraints
- **And many more technical layers...**

## Schema Structure

Each layer definition includes precise technical parameters:

```json
{
  "name": "infoLayer_fieldType.png",
  "height_multiplier": 2.0,
  "width_multiplier": 2.0,
  "channels": 1,
  "data_type": "uint8"
}
```

### **Technical Parameters**
- **`name`**: Output filename for the generated layer
- **`height_multiplier`**: Vertical resolution scaling factor
- **`width_multiplier`**: Horizontal resolution scaling factor
- **`channels`**: Color channel count (1=grayscale, 3=RGB, 4=RGBA)
- **`data_type`**: Binary data format specification

### **Multiplier Impact**
- **2.0**: Double resolution (higher detail, larger files)
- **1.0**: Standard resolution (balanced quality/size)
- **0.5**: Half resolution (lower detail, smaller files)
- **0.25**: Quarter resolution (minimal detail, compact files)

## Layer Categories

### **Gameplay Mechanics**
- `infoLayer_farmlands.png` - Property and ownership boundaries
- `infoLayer_fieldType.png` - Crop planting restrictions and field types
- `infoLayer_limeLevel.png` - Soil pH and treatment requirements

### **Physics & Collision**
- `infoLayer_navigationCollision.png` - AI movement pathfinding data
- `infoLayer_placementCollision.png` - Object placement validation
- `infoLayer_indoorMask.png` - Interior space detection

### **Environmental Systems**
- `infoLayer_environment.png` - Weather and environmental effects
- Various seasonal and weather-related data layers

### **Technical Rendering**
- Multiple specialized layers for graphics engine optimization
- Internal FS25 rendering pipeline requirements
- Performance optimization parameters

## Integration with Maps4FS

### **Automatic Processing**
Maps4FS uses GRLE schema to:
- **Generate required layers** automatically during map creation
- **Apply correct resolutions** based on multiplier settings
- **Ensure compatibility** with FS25 engine requirements
- **Optimize file sizes** while maintaining quality standards

### **No User Intervention Required**
- **Transparent by default** - most users don't need to touch GRLE schema
- **Automatic optimization** - Maps4FS handles standard cases
- **Advanced mode available** - expert users can customize with caution

## Why This Schema Exists

### **Evolution**
- **New rendering engine** requires precise layer specifications
- **Enhanced gameplay features** need additional data layers
- **Performance optimization** demands exact technical parameters
- **Compatibility assurance** prevents game crashes and errors

### **Maps4FS Adaptation**
- **Engine compliance** - Ensures generated maps work with FS25
- **Quality consistency** - Maintains standard across all generated maps
- **Future-proofing** - Allows adaptation to FS25 updates and changes

## Technical Background

### **GRLE Format**
- **Proprietary format** used by Giants Engine (FS25's game engine)
- **Optimized compression** for game performance
- **Multi-channel support** for complex data storage
- **Resolution flexibility** for different detail requirements

### **Generation Pipeline**
1. **Maps4FS processes** terrain and feature data
2. **Schema defines** output specifications for each layer
3. **Engine converts** data to GRLE format with correct parameters
4. **FS25 loads** generated layers for gameplay functionality

## Best Practices

### **Safe Customization Approach**
- **Start from defaults** and modify only what you must
- **Change one field at a time** and test generation after each change
- **Validate output in Giants Editor** before using results in production
- **Keep schema backups** so rollback is immediate
- **Focus on inputs first** (DEM/OSM/textures), then adjust schema only when needed

### **Troubleshooting Strategy**
- **GRLE problems**: Check input data (DEM, OSM) for corruption
- **Generation failures**: Verify template integrity and file permissions
- **Compatibility issues**: Ensure using the latest Maps4FS version

## ⚠️ Support Policy

### **Support Scope for Custom Configurations**
- **Default schema path** has full support
- **Custom schema path** is supported on a best-effort basis
- **Template-specific customizations** may require user-side validation and iteration
- **If issues occur**, first retry with default schema to isolate the problem

### **Recommended Approach**
- **Use defaults first** for reliability
- **Customize with caution** only for clear use cases (e.g. extended foliage uint16)
- **Document your changes** so they can be reproduced and reviewed
- **Report bugs** with both default and customized behavior details




