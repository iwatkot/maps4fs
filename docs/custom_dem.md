# Custom DEM (Digital Elevation Model)

Custom DEM functionality allows you to use your own elevation data instead of relying on publicly available sources. This gives you complete control over terrain elevation for both the playable map area and surrounding background terrain.

💡 **New Feature**: The [Presets](presets.md) system now supports multiple DEM files, allowing you to maintain libraries of elevation data and switch between different terrain configurations easily.

## What is Custom DEM?

A Custom DEM is a user-provided elevation map that defines the terrain height data for your entire map region. Unlike standard DEM sources that Maps4FS downloads automatically, custom DEMs let you:

- **Use specialized elevation data** from surveying or LiDAR sources
- **Create fictional terrain** for fantasy or modified landscapes  
- **Enhance existing data** with higher resolution or accuracy
- **Match specific real-world locations** not well-covered by public sources

## When to Use Custom DEM

### **Ideal Use Cases**
- **High-precision mapping** - Survey-grade elevation data available
- **Fictional landscapes** - Creating non-existent terrain features
- **Enhanced realism** - Better elevation data than public sources
- **Specialized projects** - Racing tracks, custom farming areas, etc.

### **Consider Standard DEM When**
- Working with well-mapped regions (most populated areas)
- Prototyping or testing map concepts
- Limited access to specialized elevation data

## File Requirements

⚠️ **CRITICAL**: These requirements are mandatory. Generation will fail if not met exactly.

### **Image Format Specifications**
- **Format**: PNG image file
- **Color Mode**: Single-channel (grayscale) 
- **Bit Depth**: Unsigned 16-bit
- **Compression**: Standard PNG compression acceptable

### **Dimension Requirements**
The image size must be calculated precisely:

**Formula**: `Map Size + 4096 pixels` in each dimension

**Examples**:
- **2048×2048 map** → DEM image: `6144×6144` pixels
- **4096×4096 map** → DEM image: `8192×8192` pixels  
- **8192×8192 map** → DEM image: `12288×12288` pixels

### **Positioning Requirements**
- **Map center alignment**: Playable map area must be centered within the DEM image
- **Pre-rotation**: If map rotation is needed, rotate the DEM image beforehand
- **No runtime rotation**: Maps4FS will not rotate DEM data during generation

## Technical Implementation

### **Height Encoding**
- **0 (black)**: Represents minimum elevation in your region
- **65535 (white)**: Represents maximum elevation in your region
- **Linear mapping**: Elevation scales linearly between min/max values
- **Precision**: 16-bit provides 65,536 distinct elevation levels

### **Coverage Area**
```
┌─────────────────────────────────────┐
│           Background Terrain        │
│   ┌─────────────────────────────┐   │
│   │                             │   │
│   │      Playable Map Area      │   │ 
│   │        (Center)             │   │
│   │                             │   │
│   └─────────────────────────────┘   │
│           Background Terrain        │
└─────────────────────────────────────┘
```

The extra 4096 pixels provide background terrain data extending beyond the playable area.

## File Placement

### **Presets System (Local Deployment Only)**
⚠️ **Local Deployment Required**: This method requires [Local Deployment](local_deployment.md) and uses the [Presets](presets.md) feature.

For managing multiple DEM configurations:

```
📁 Data Directory/
└── 📂 defaults/
    └── 📂 dem/
        ├── 📄 alps_mountains_4x4.png     ← Alpine terrain
        ├── 📄 plains_midwest_8x8.png     ← Flat farmland
        ├── 📄 coastal_norway_2x2.png     ← Coastal terrain
        └── 📄 [your_files].png           ← Multiple DEM presets
```

**File Naming**: Use descriptive names that help identify the terrain type, region, and map size. Select your DEM preset in the Maps4FS interface during map generation.
- **Single file**: Only one custom DEM per Data Directory

## Creation Workflow

### **Step 1: Prepare Source Data**
1. Obtain elevation data (LiDAR, survey data, or heightmaps)
2. Determine elevation range (minimum to maximum heights)
3. Define your target map coordinates and size

### **Step 2: Image Processing**
1. **Scale to proper dimensions** using the formula above
2. **Convert to 16-bit grayscale** PNG format
3. **Map elevation values** linearly to 0-65535 range
4. **Apply any needed rotation** before saving
5. **Center the playable area** within the image

### **Step 3: Quality Verification**
1. **Check dimensions** match calculated requirements exactly
2. **Verify file format** (16-bit grayscale PNG)
3. **Validate elevation mapping** (smooth gradients, no artifacts)
4. **Test placement** in Data Directory

### **Step 4: Integration**
1. Place file with descriptive name in `defaults/dem/[your_filename].png`
2. Select your DEM preset in the Maps4FS interface during map generation
2. Run Maps4FS generation
3. Verify terrain appears correctly in generated map

## Common Issues & Solutions

### **Generation Failure**
**Symptoms**: Maps4FS fails during DEM processing

**Solutions**:
- Verify file appears in presets selection UI
- Check that file dimensions match your intended map size requirements
- Check image dimensions using the formula
- Confirm 16-bit grayscale PNG format
- Ensure file is not corrupted

### **Incorrect Terrain Heights**
**Symptoms**: Terrain too flat, too steep, or inverted

**Solutions**:
- Review elevation value mapping (0 = min, 65535 = max)
- Check for inverted heightmap (black = high instead of low)
- Verify elevation range represents realistic values

### **Misaligned Features**
**Symptoms**: Terrain doesn't match intended coordinates

**Solutions**:
- Confirm map area is centered in DEM image
- Check if rotation was applied correctly
- Verify coordinate system matches intended location

### **Performance Issues**
**Symptoms**: Slow generation or excessive memory usage

**Solutions**:
- Optimize PNG compression without changing bit depth
- Ensure image dimensions aren't excessive for map size
- Consider reducing unnecessary detail in background areas

## Best Practices

### **Data Preparation**
- **Start with high-quality source data** for best results
- **Maintain elevation accuracy** in critical playable areas
- **Smooth background transitions** to avoid visual artifacts
- **Test with smaller maps first** before large-scale projects

### **File Management**
- **Backup original elevation data** before processing
- **Document elevation ranges** and processing steps
- **Version control** for multiple DEM iterations
- **Validate changes** with test generations

### **Optimization**
- **Focus detail** on playable map areas
- **Simplify background terrain** where appropriate
- **Use consistent elevation scaling** across projects
- **Balance file size** with terrain detail needs

## Tools & Software

### **Professional Tools**
- **QGIS** - Free GIS software with DEM processing capabilities
- **Global Mapper** - Professional terrain processing software
- **ArcGIS** - Industry-standard GIS platform

### **Image Editors**
- **GIMP** - Free editor with 16-bit support
- **Photoshop** - Professional image editing with advanced bit depth
- **ImageMagick** - Command-line image processing

### **Specialized Software**
- **CloudCompare** - Point cloud and DEM processing
- **MeshLab** - 3D mesh processing and heightmap generation
- **Blender** - 3D modeling with terrain generation capabilities

## Integration with Maps4FS

Once your custom DEM is properly prepared and placed in the Data Directory:

1. **Standard generation process** applies - no special settings needed
2. **Background terrain** automatically uses your elevation data
3. **Playable area elevation** reflects your custom terrain
4. **Compatible with all other features** - fields, roads, textures work normally

## Related Documentation

- **[Data Directory](data_directory.md)** - Understanding the file structure and placement
- **[Background Terrain](background_terrain.md)** - How DEM data creates 3D terrain meshes
- **[DEM](dem.md)** - Standard DEM processing and options
- **[Local Deployment](local_deployment.md)** - Setting up your development environment

---

**Ready to create stunning custom terrain?** Prepare your elevation data following these specifications and unlock unlimited creative potential for your Maps4FS projects!
