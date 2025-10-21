# Step-by-Step Guide: Create Your First Map

Transform any real-world location into a Farming Simulator map with this comprehensive guide. Maps4FS automates the complex terrain generation, letting you focus on the creative aspects of map making.

## 🛠️ Prerequisites

Before you begin, ensure you have the necessary tools and system requirements:

### Required Software
- **Giants Editor** ([Download here](https://gdn.giants-software.com/downloads.php))
  - For **Farming Simulator 25**: Use Giants Editor 10.0 or later
  - For **Farming Simulator 22**: Use Giants Editor 9.0 series
- **Maps4FS** - Either [web version](https://maps4fs.xyz) or [local installation](local_deployment.md)

### Optional Tools (for Advanced Features)
- **Image editing software** (for texture customization)
- **Blender** with Giants Exporter Plugin (for FS22 background terrain or advanced customization)

### System Requirements
- **RAM**: 8GB minimum, 16GB+ recommended for larger maps
- **Storage**: 5-10GB free space per map project
- **CPU**: Multi-core processor recommended for faster generation

## 🎯 Main Settings Overview

Understanding the core settings will help you make informed decisions during map generation:

### Game Selection
Choose between **Farming Simulator 22** and **Farming Simulator 25**:
- **FS25 (Recommended)**: Full feature support, active development
- **FS22**: Limited features, discontinued support

⚠️ **Important**: Match your Giants Editor version to your target game!

### Location Coordinates
- Use **decimal format**: `45.2673, 19.7925` ✅
- **NOT** degrees-minutes-seconds: `45°16'02.3"N 19°47'32.9"E` ❌
- Get coordinates from [Google Maps](https://www.google.com/maps) or [OpenStreetMap](https://www.openstreetmap.org)
- **Center point**: Coordinates mark the map center, not a corner

### Map Size Selection
Choose wisely based on your experience and hardware:

- **2x2 km**: Perfect for beginners, manageable scope
- **4x4 km**: Good balance of size and detail
- **8x8 km**: For experienced modders with powerful hardware
- **16x16 km**: Expert level, may have compatibility issues

💡 **Beginner Tip**: Start with 2x2 km! Large maps require exponentially more work to complete.

### DTM Provider
Select the best elevation data source for your region:
- **SRTM30Provider**: Global coverage, 30m resolution
- **Higher quality providers**: Available in some regions, better detail
- Maps4FS automatically shows available providers for your location

### Map Rotation
- Rotate to optimize the map orientation
- Consider prevailing wind direction and terrain features
- Useful for aligning fields with cardinal directions

## 📋 Step-by-Step Process

### Step 1: 📍 Choose Your Location
1. Open [Google Maps](https://www.google.com/maps) or [OpenStreetMap](https://www.openstreetmap.org)
2. Navigate to your desired farming area
3. Right-click and copy coordinates in decimal format
4. **Tip**: Look for areas with visible agricultural fields for best results

### Step 2: 📏 Configure Map Settings
1. **Set coordinates**: Paste your decimal coordinates
2. **Choose map size**: Start with 2x2 km for your first map
3. **Select game version**: FS25 recommended
4. **Pick DTM provider**: Use the highest quality available for your region
5. **Set rotation** (optional): Align fields optimally

### Step 3: ⚙️ Adjust Generation Settings
Configure key settings for your needs:

#### Essential Settings
- **Add Trees**: Enable for realistic forests
- **Add Grass**: Fill empty areas with vegetation
- **Farmland Margin**: Adjust farmlands boundaries
- **Fields Padding**: Space between fields
- **Forest Density**: Lower = denser forests
- **Generate Background**: Enable generation of background terrain
- **Generate Water**: Generate meshes for water planes

#### Quality vs. Performance
- **Dissolve Textures**: Enable for final maps (slower generation)
- **Random Plants**: Enable for natural-looking vegetation
- **Download Satellite Images**: Enable for background terrain

📖 **Learn More**: Check [Generation Settings](generation_settings.md) for detailed explanations.

### Step 4: 🚀 Generate Your Map
1. Review all settings one final time
2. Click **Generate** and wait for processing
3. **Processing time**: 1-5 minutes depending on size and settings
4. Monitor progress and check for any error messages

### Step 5: 📥 Download and Extract
1. Download the generated `.zip` file
2. Create a dedicated project folder on your computer
3. Extract all contents to this folder
4. **Map Structure**: Learn about included files in [Map Structure](map_structure.md)

### Step 6: 🌎 Background Terrain (Automated for FS25)
**For Farming Simulator 25**: Background terrain is now fully automated!
1. ✅ Enable **Download Satellite Images** in satellite settings
2. ✅ Enable **Generate Background** in background settings  
3. 🎯 Maps4FS automatically creates ready-to-use `background_terrain.i3d` files
4. 📁 Find them in `your_map/assets/background/` after generation
5. 🚀 Simply import the `.i3d` file directly into Giants Editor!

**For Farming Simulator 22**: Use the [Legacy Background Terrain](legacy_background_terrain.md) manual process.

### Step 7: ⛰️ Import Background Terrain (FS25)
No Blender needed for FS25!
1. Open your map in Giants Editor 10.0+
2. Go to `File` → `Import...`
3. Navigate to `your_map/assets/background/`
4. Select `background_terrain.i3d` and import
5. Done! The terrain is automatically textured and positioned

### Step 8: 🌊 Water Planes (Automated for FS25)
**For Farming Simulator 25**: Water planes are now fully automated!
1. ✅ Enable **Generate Water** in background settings
2. 🎯 Maps4FS automatically creates ready-to-use `water_resources.i3d` files
3. 📁 Find them in `your_map/assets/water/` after generation
4. 🚀 Import the `.i3d` file directly into Giants Editor
5. ⚙️ Configure water properties in Giants Editor (see [Water Planes guide](water_planes.md))

**For Farming Simulator 22**: Use the [Legacy Water Planes](legacy_water_planes.md) manual process.

### Step 9: 📂 Open in Giants Editor
1. Launch Giants Editor (correct version for your target game)
2. Open the main `.i3d` file from your extracted map
3. **First load**: May take several minutes for large maps
4. Save immediately as a Giants Editor project so the editor will create required files.

### Step 10: 🌾 Configure Fields
1. **Auto-generated fields**: Already placed based on real agricultural data
2. **One-click painting**: Use field info layer to paint terrain textures
3. **Adjust boundaries**: Modify field shapes if needed
4. **Learn more**: [Fields Documentation](fields.md)

### Step 11: 🏠 Add Farmlands
1. **Pre-configured farmlands**: Generated automatically around fields
2. **Ownership zones**: Set up buyable land areas
3. **Price configuration**: Adjust land values in farmlands.xml
4. **Detailed guide**: [Farmlands Documentation](farmlands.md)

### Step 12: 🗺️ Overview Map (Automated for FS25)
**For Farming Simulator 25**: Overview map is now fully automated!
- ✅ Automatically generated when **Download Satellite Images** is enabled
- 📁 Perfect `overview.dds` created with satellite imagery
- 🎯 Correct dimensions and compression applied automatically

**For Farming Simulator 22**: Manual creation required
- Use satellite imagery for overview.dds
- Resize and format according to game requirements  
- Follow [DDS Conversion Guide](dds_conversion.md) for proper formatting

### Step 13: ✨ Polish and Customize
Your map is now playable but needs finishing touches:
- **Add buildings**: Place farmhouses, shops, and industrial areas
- **Road network**: Connect fields and improve accessibility
- **Decorative objects**: Trees, rocks, and environmental details
- **Lighting**: Set up proper day/night lighting
- **Audio**: Add ambient sound zones
- **Ground collision map**: Create it via Giants Editor (Scripts -> Shared scripts -> Map -> Create Ground Collision Map)

## 🎮 Testing Your Map

### Initial Testing
1. **Load test**: Ensure map loads without crashes
2. **Performance check**: Monitor FPS in different areas
3. **Vehicle test**: Drive around with various equipment
4. **Field operations**: Test plowing, seeding, and harvesting

## 🚀 Next Steps

### Publishing Your Map
1. **Mod testing**: Ensure compatibility with popular mods
2. **Multiplayer testing**: Verify network performance
3. **Documentation**: Create user guides and changelogs
4. **Community**: Share on ModHub, farming forums, or Discord

### Advanced Features
- **🆕 Presets System** ([Local Deployment](local_deployment.md) only): Save and manage multiple configurations with the [Presets](presets.md) feature
- **Custom crops**: Add specialty farming options
- **Production chains**: Create unique economic systems
- **Seasonal content**: Weather-specific map variants
- **Scripted events**: Dynamic gameplay elements

## 📚 Additional Resources

### Video Tutorials
📹 [Complete YouTube Playlist](https://www.youtube.com/watch?v=hPbJZ0HoiDE&list=PLug0g7UYHX8D1Jik6NkJjQhdxqS-NOtB9) - Step-by-step video guides

### Documentation
- 📖 [FAQ](FAQ.md) - Common questions and troubleshooting
- 🔧 [Generation Settings](generation_settings.md) - Detailed setting explanations
- 🗺️ [Map Structure](map_structure.md) - Understanding generated files
- 💡 [Workflow Optimization](workflow_optimizations.md) - Best practices and tips

### Community Support
- 💬 [Discord Server](https://discord.gg/Sj5QKKyE42) - Get help and share your progress
- 🐛 [GitHub Issues](https://github.com/iwatkot/maps4fs/issues) - Report bugs or request features
- 🌐 [OpenStreetMap](https://www.openstreetmap.org) - Improve source data for better maps

---

**Congratulations!** You now have a complete, playable Farming Simulator map based on real-world terrain. The foundation is set – now let your creativity flourish as you build the farming paradise of your dreams!
