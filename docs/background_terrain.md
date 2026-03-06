# Background Terrain (Automated)

Maps4FS now automatically generates ready-to-use i3d background terrain files for **Farming Simulator 25**, eliminating the need for manual Blender workflows!

## 🎯 Quick Overview

When you generate a map with the following settings enabled:
- **Download Satellite Images** ✅
- **Generate Background** ✅

Maps4FS will automatically create optimized i3d files that can be directly imported into Giants Editor.

## 📁 Generated Files

After generation, you'll find the following files in your map's `assets/background/` directory:

```
map_directory/
├── assets/
│   └── background/
│       ├── textured_mesh/
│       │   ├── background_textured_mesh.obj
│       │   ├── background_textured_mesh.mtl
│       │   └── background_texture.png
│       └── background_terrain.i3d  ← Ready to import!
```

## 🚀 How to Use (FS25)

> **Windows App users:** If you are using the Windows App and the i3dConverter is available (it is downloaded automatically on first run), all of the steps below — conversion to binary i3d, material setup, and positioning on the map — are done **automatically**. You can skip straight to opening the map in Giants Editor.

### Step 1: Generate Your Map
1. Enable **Download Satellite Images** in the Satellite component
2. Enable **Generate Background** in the Background Settings
3. Generate your map normally

### Step 2: Import into Giants Editor
1. Open your map in **Giants Editor 10.0.0+** (FS25)
2. Go to `File` → `Import...`
3. Navigate to `your_map/assets/background/`
4. Select `background_terrain.i3d`
5. Click `Import`

That's it! The background terrain is automatically:
- ✅ **Properly scaled** and positioned
- ✅ **Textured** with satellite imagery  
- ✅ **Decimated** for optimal performance
- ✅ **UV mapped** correctly
- ✅ **Center removed** (if enabled in settings)

## ⚙️ Settings Control

You can control the automated generation through these settings:

### Background Settings
- **Generate Background**: Enable/disable background terrain generation
- **Remove Center**: Automatically cuts out the map center
- **Background Texture Resolution**: Controls texture quality (auto-calculated based on map size)

### Advanced Settings
- **Decimation Factor**: Automatically calculated based on map size for optimal performance
- **Z-Scaling**: Matches your main terrain settings

## 🎮 Game Compatibility

| Game Version | Status | Method |
|--------------|---------|---------|
| **Farming Simulator 25** | ✅ **Fully Automated** | Use this guide |
| **Farming Simulator 22** | ⚠️ **Manual Process** | Use [Legacy Background Terrain](legacy_background_terrain.md) |

## 📊 Performance Benefits

The automated process includes several optimizations:

- **Smart Decimation**: Reduces polygon count based on map size
- **Texture Optimization**: Automatically resizes textures for background use
- **Memory Efficiency**: Optimized for minimal in-game impact
- **LOD Ready**: Pre-configured for distance rendering

## 🔧 Troubleshooting

### No background_terrain.i3d file generated?
- Ensure **Download Satellite Images** is enabled
- Ensure **Generate Background** is enabled
- Check that satellite images were successfully downloaded

### Import fails in Giants Editor?
- Use Giants Editor 10.0.0+ for FS25 maps
- Make sure the i3d file isn't corrupted
- Try importing the .obj files manually (see legacy docs)

### Terrain appears too high/low?
- Adjust the terrain position in Giants Editor
- Check Z-scaling settings match your main terrain

## 💡 Tips

- **Quality vs Performance**: The automated process balances quality and performance. For ultra-high quality backgrounds, consider the [legacy manual process](legacy_background_terrain.md)
- **Custom Textures**: You can replace the generated texture with your own if needed
- **Multiple Maps**: The automation works with any map size and automatically adjusts parameters

## 🔄 Upgrading from Manual Process

If you've been using the manual Blender workflow:

1. **Update your workflow**: Simply enable the automated settings
2. **No more Blender needed**: The i3d files are ready to import
3. **Same quality**: The automated process produces equivalent results
4. **Legacy docs available**: Manual process docs moved to [Legacy section](legacy_background_terrain.md) for reference

---

**Need the manual process?** Check out the [Legacy Background Terrain](legacy_background_terrain.md) documentation for the traditional Blender workflow (required for FS22).