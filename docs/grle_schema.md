# GRLE Schema

The GRLE Schema defines technical specifications for Farming Simulator's internal image layers and rendering parameters. This configuration controls how Maps4FS generates various game-critical information layers that manage gameplay mechanics, collision detection, and visual effects.

## **⚠️ Farming Simulator 25 Only**

GRLE Schema is **only available for Farming Simulator 25**. FS22 does not use this configuration system.

## File Location

The GRLE schema is located in your **Data Directory**:

```
📁 Data Directory/
└── 📂 templates/
    └── 📄 fs25-grle-schema.json  ← GRLE layer definitions for FS25
```

## **🚨 Critical Warning: Do Not Modify**

### **Modification Risks**
- **GRLE schema cannot be safely customized** by end users
- **Changes will break map generation** and cause system failures
- **No customization benefits** - edits provide no meaningful improvements
- **Designed for internal use** by Farming Simulator engine, not user modification

### **Why Modifications Fail**
- **Engine dependencies**: FS25 expects exact specifications for proper rendering
- **Hardcoded relationships**: Layer parameters are tied to internal game systems  
- **Binary compatibility**: Generated files must match exact engine requirements
- **No user benefits**: Schema defines technical specs, not customizable features

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
- **Transparent operation** - users don't interact with GRLE generation
- **Automatic optimization** - Maps4FS handles all technical details
- **Built-in validation** - Schema ensures output meets FS25 standards

## Why This Schema Exists

### **FS25 Evolution**
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

### **Hands-Off Approach**
- **Never modify** the GRLE schema file
- **Trust automation** - Maps4FS handles all GRLE generation
- **Focus on inputs** - Customize DEMs, OSM data, textures instead
- **Report issues** - Contact developers if GRLE generation fails

### **Troubleshooting Strategy**
- **GRLE problems**: Check input data (DEM, OSM) for corruption
- **Generation failures**: Verify template integrity and file permissions
- **Compatibility issues**: Ensure using latest Maps4FS version for FS25

## ⚠️ Support Policy

### **No Support for Modifications**
- **Schema edits not supported** - modifications will break generation
- **No troubleshooting assistance** for custom GRLE configurations
- **Use at own risk** - any changes void support eligibility
- **Restore defaults** if experiencing issues after modifications

### **Recommended Approach**
- **Leave schema untouched** for reliable map generation
- **Customize other components** - focus on OSM, DEM, textures, trees
- **Trust the system** - GRLE generation is highly optimized already
- **Report bugs** - help improve default schema instead of modifying
