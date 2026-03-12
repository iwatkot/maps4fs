# Frequently Asked Questions

📹 **Video Tutorial**: Learn where map data comes from in our comprehensive guide.

[![YouTube tutorial](https://github.com/user-attachments/assets/4e3e1e1a-7882-4673-87c4-f913775d178e)](https://www.youtube.com/watch?v=hPbJZ0HoiDE)

Welcome to the Maps4FS FAQ! Before asking questions or opening issues, please check if your answer is already here. This will help you get solutions faster and keeps our community focused on helping with unique challenges.

## 🗺️ Map Data & Objects

### Some objects don't appear on my map, why?

Maps4FS uses data from [OpenStreetMap](https://www.openstreetmap.org/), so if something exists in real life but isn't in OSM's database, it won't appear on your map. Here's how to troubleshoot:

1. **Check if the object exists on OSM** - Visit OpenStreetMap and search your area
2. **If it's on OSM but missing from your map** - See the next question about whitelisted objects
3. **If it's not on OSM** - See the question about adding missing objects

### I can see the object on OSM, but it doesn't appear on my map, why?

Maps4FS uses a curated whitelist of supported objects rather than importing everything from OSM. You can check which objects are supported in our [Texture Schema](texture_schema.md) documentation.

**Need a new object type added?** Contact us on [Discord](https://discord.gg/wemVfUUFRA) or open a GitHub issue. We'll review and add appropriate objects to the whitelist.

### There's no needed objects on OSM, what should I do?

You have two main options:

#### Option 1: Add to OpenStreetMap (Recommended for permanent additions)
You can contribute to OSM by adding missing objects yourself:
1. Visit [OpenStreetMap](https://www.openstreetmap.org/) and create an account
2. Add objects with correct tags following [OSM Wiki guidelines](https://wiki.openstreetmap.org/wiki/Main_Page)
3. Changes typically appear in Maps4FS within 5-30 minutes
4. **Important**: Only add real-world objects and follow [OSM Guidelines](https://wiki.openstreetmap.org/wiki/Good_practice)

#### Option 2: Use Custom OSM (Recommended for testing/personal use)
For complete control over your map data, use our [Custom OSM](custom_osm.md) approach:
- Create and edit your own OSM data
- Perfect for testing, iterations, or personal modifications
- No community approval needed
- Full creative control over your map content

## 🎮 Giants Editor Issues

### Purple terrain glitches in Giants Editor

**Issue**: Terrain appears purple at certain viewing angles.

**Solution**: Select the **terrain** object, open the **Terrain** tab in **Attributes**, scroll to the bottom and click **Reload material**.

### Black screen flickering in Giants Editor

**Issue**: Screen keeps flickering black during editing.

**Solution**:
1. Go to **Scripts** → **Create new script**
2. Name your script and paste this code:

```lua
setAudioCullingWorldProperties(-8192, -100, -8192, 8192, 500, 8192, 16, 0, 9000)
setLightCullingWorldProperties(-8192, -100, -8192, 8192, 500, 8192, 16, 0, 9000)
setShapeCullingWorldProperties(-8192, -100, -8192, 8192, 500, 8192, 16, 0, 9000)
```

3. Check **Always loaded** and execute the script

## 🚜 Game Loading & Installation

### Map loading hangs after installation

**Issue**: Placed the archive in mods directory but map won't load.

**Critical Steps**:
1. **Unpack the downloaded archive**
2. **Open in Giants Editor**
3. **Save the map**
4. **Repack as a new mod**

**Archive Naming**: Use simple names like `FS25_MyMap.zip`. Avoid special characters, spaces, or non-ASCII symbols.

### Crops destruction doesn't work / terrain glitches in-game

**Issue**: Gameplay problems with terrain interaction.

**Required Fix**: Create a ground collision map:
1. In Giants Editor: **Scripts** → **Shared scripts** → **Map** → **Create Ground Collision Map**
2. **Important**: Repeat this process every time you edit the map

## 🔧 Object Placement Issues

### Objects floating above terrain

**Issue**: Trees or other objects appear to hover above the ground.

**Solution**:
1. Select objects in **Scenegraph** (select each individual object, NOT groups)
2. **Pro tip**: Select first object, scroll to last, hold **Shift** and click last object
3. **Scripts** → **Shared scripts** → **Map** → **Terrain** → **Place objects on terrain**

![Select objects](https://github.com/user-attachments/assets/2afbea4e-6d0c-4ee5-a3c1-ce021926c9fd)

## 🐛 Troubleshooting Crashes

### Giants Editor crashes when opening map

**Troubleshooting Steps**:

1. **Check Console tab** for error messages if Editor loads partially
2. **If crashes on startup**, find the log file:
   ```
   C:/Users/<username>/AppData/Local/GIANTS Editor 64bit 10.0.3/editor_log.txt
   ```
   *Note: Folder name varies by Giants Editor version*

3. **Review latest log entries** for error patterns
4. **Need help?** Share relevant log sections in our [Discord](https://discord.gg/wemVfUUFRA)

### Game crashes or hangs when loading map

#### Enable Debug Mode
1. **Locate game.xml**:
   ```
   C:/Users/<username>/OneDrive/Documents/My Games/FarmingSimulator2025/game.xml
   ```
   *Note: OneDrive path may vary by system*

2. **Modify development section**:
   ```xml
   <development>
       <controls>true</controls>  <!-- Change false to true -->
       <openDevConsole onWarnings="false" onErrors="false"/>
   </development>
   ```

3. **In-game**: Press **~** to open console and check for errors

#### Check Game Logs
If game crashes before console access:
```
C:/Users/<username>/OneDrive/Documents/My Games/FarmingSimulator2025/log.txt
```

Focus on the latest entries and share relevant sections in [Discord](https://discord.gg/wemVfUUFRA) if needed.

## 📦 Mod Installation Issues

### Game can't see the map mod

**Common Issues & Solutions**:

#### ✅ Correct Archive Naming
```
FS25_Titelski_breg.zip           ← Correct
FS25_mod name _ kgjdfg.zip       ← Incorrect (spaces/special chars)
```

#### ✅ Proper Archive Structure
**Correct structure** (files at root level):
```
📦FS25_Titelski_breg.zip
 ┣ 📂 map
 ┃ ┣ 📂 config
 ┃ ┃ ┣ 📄 aiSystem.xml
 ┃ ┃ ┗ 📄 [other XML files]
 ┃ ┣ 📂 data
 ┃ ┃ ┣ 📄 dem.png
 ┃ ┃ ┗ 📄 [weight & info files]
 ┃ ┣ 📄 map.i3d
 ┃ ┣ 📄 map.xml
 ┃ ┗ 📄 overview.dds
 ┣ 📄 icon.dds
 ┣ 📄 modDesc.xml
 ┗ 📄 preview.dds
```

**❌ Incorrect structure** (extra folder level):
```
📦FS25_Titelski_breg.zip
 ┗ 📂 extra_folder          ← This breaks everything!
   ┣ 📂 map
   ┣ 📄 icon.dds
   ┗ 📄 modDesc.xml
```

---

**Need more help?** Join our [Discord community](https://discord.gg/wemVfUUFRA) for real-time support and troubleshooting assistance!



