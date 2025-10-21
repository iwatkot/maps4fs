# Water Planes (Automated)

Maps4FS now automatically generates ready-to-use i3d water plane files for **Farming Simulator 25**, eliminating the need for manual Blender workflows!

## 🎯 Quick Overview

When you generate a map with the following settings enabled:
- **Generate Water** ✅

Maps4FS will automatically create optimized i3d files that can be directly imported into Giants Editor.

## 📁 Generated Files

After generation, you'll find the following files in your map's `assets/water/` directory:

```
map_directory/
├── assets/
│   └── water/
│       └── water_resources.i3d  ← Ready to import!
└── water/
    ├── elevated_water.obj
    ├── plane_water.obj
    └── line_based_water.obj  (if applicable)
```

## 🚀 How to Use (FS25)

### Step 1: Generate Your Map
1. Enable **Generate Water** in the Background Settings
2. Generate your map normally

### Step 2: Import into Giants Editor
1. Open your map in **Giants Editor 10.0.0+** (FS25)
2. Go to `File` → `Import...`
3. Navigate to `your_map/assets/water/`
4. Select `water_resources.i3d`
5. Click `Import`

The water plane will appear black initially - this is normal and expected behavior.

### Step 3: Configure Water Properties in Giants Editor

After importing, you need to configure the water properties to make it display correctly:

#### Position the Water Plane
Position the water plane in the correct location within your map.

![Position the water plane](https://github.com/user-attachments/assets/c7257060-bd83-498f-a5dc-098e675540df)

#### Configure Material Properties
1. Open the **Material Editing** window and select your water plane
2. Change the **Variation** to **simple** 
3. Edit the values as shown in the screenshot (these are default values, but you can adjust them):

![Water plane values](https://github.com/user-attachments/assets/6624878c-818d-4371-bbf9-8bb6ace6589f)

4. Set **Smoothness** and **Metalness** to **1**

#### Set Normal Map
1. Click on the button near the **Normal map**

![Normal map](https://github.com/user-attachments/assets/95adc493-983a-46ae-bd20-7d1f4e998ba7)

2. Click the **...** button and provide the path to the **water_normal.dds** file  
   Location: `where-the-game-is-installed/data/maps/textures/shared/water_normal.dds`

![Water normal map](https://github.com/user-attachments/assets/515de60b-bc1a-4843-b548-2820107435af)

3. You should see the normal map in the window. Press the **OK** button

![Normal map window](https://github.com/user-attachments/assets/bee7955f-7f6c-4d94-978c-0ab7835b9e2b)

#### Configure User Attributes and Physics
1. Switch to the **UserAttributes** tab
2. Enter the name `onCreate`, select `Script callback`, and click **Add**
3. Set the **Attribute** value to `Environment.onCreateWater`

4. On the **Attributes** → **Transform** tab, check the `Rigid body` checkbox

5. Switch to the **Rigid body** tab and set the `Preset` to `WATER`

6. Go to the **Shape** tab and uncheck the `Cast shadowmap` checkbox (if it's checked)

The final result should look like this:

![Water plane in GE](https://github.com/user-attachments/assets/b246cf85-b044-4ceb-bff4-9b32a753b143)

## ⚙️ Settings Control

You can control the automated generation through these settings:

### Background Settings
- **Generate Water**: Enable/disable water plane generation
- **Water Blurriness**: Controls surface smoothness (higher = flatter)
- **Flatten Water**: Sets uniform water level across the map

## 🎮 Game Compatibility

| Game Version | Status | Method |
|--------------|---------|---------|
| **Farming Simulator 25** | ✅ **Fully Automated** | Use this guide |
| **Farming Simulator 22** | ⚠️ **Manual Process** | Use [Legacy Water Planes](legacy_water_planes.md) |

## 📊 Performance Benefits

The automated process includes several optimizations:

- **Smart Mesh Generation**: Optimized polygon count for water surfaces
- **Ocean Shader Ready**: Pre-configured with proper ocean shader materials
- **Memory Efficient**: Optimized for minimal in-game impact
- **Multiple Types**: Generates both elevated and plane water meshes

## 🔧 Troubleshooting

### No water_resources.i3d file generated?
- Ensure **Generate Water** is enabled
- Check that your map has water areas defined in OSM data

### Import fails in Giants Editor?
- Use Giants Editor 10.0.0+ for FS25 maps
- Make sure the i3d file isn't corrupted
- Try importing the .obj files manually (see legacy docs)

### Water appears black after import?
- This is normal! Follow the Giants Editor configuration steps above
- Set the proper normal map and material properties

### Water level too high/low?
- Adjust water position in Giants Editor
- Check **Flatten Water** setting for uniform levels

## 💡 Tips

- **Multiple Water Bodies**: The automated process handles multiple separate water areas
- **Custom Shapes**: Water follows the actual shape from your map data  
- **Quality Settings**: Use **Water Blurriness** to control surface detail
- **Performance**: Generated water planes are optimized for in-game performance

## 🔄 Upgrading from Manual Process

If you've been using the manual Blender workflow:

1. **Update your workflow**: Simply enable **Generate Water** setting
2. **No more Blender needed**: The i3d files are ready to import
3. **Same quality**: The automated process produces equivalent results
4. **Legacy docs available**: Manual process docs moved to [Legacy section](legacy_water_planes.md) for reference

---

**Need the manual process?** Check out the [Legacy Water Planes](legacy_water_planes.md) documentation for the traditional Blender workflow (required for FS22).