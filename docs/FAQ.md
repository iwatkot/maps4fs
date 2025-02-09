## Frequently Asked Questions

📹 Learn where the map data come from in this video.  

[![YouTube tutorial](https://github.com/user-attachments/assets/4e3e1e1a-7882-4673-87c4-f913775d178e)](https://www.youtube.com/watch?v=hPbJZ0HoiDE)


In this section, you will find anwers to the most frequently asked questions about the project. Please, before asking a question, or opening an issue, check if the answer is already here. Thank you!

### Some objects are not appear on the map, why?

First of all, you need to understand, that the project uses the data from the [OpenStreetMap](https://www.openstreetmap.org/) project. So, if some object exists in the real world, it doesn't mean that it was added to the OpenStreetMap database. Then, you need to go and check if that something is already there. If it's there but still doesn't appear on the map, check the second question. And if it's not, check the third one.

### I can see the object on OSM, but it doesn't appear on the map, why?

The `maps4fs` tool DOES NOT add everything from OSM to the map. Instead of projecting everything, it works with a whitelist of objects that are allowed to be displayed. And you, actually, can check this list in the [Supported Objects](../README.md#supported-objects) section of the main README file.  
It's really easy to add a new object to the whitelist, so if you think that something should be displayed, contact me in [Discord](https://discord.gg/Sj5QKKyE42) or open an issue on GitHub. I will check the object and add it to the whitelist if it's correct.

### There's no needed objects on OSM, what should I do?

The good news is that you can add them by yourself! The OpenStreetMap project is open for everyone, and you can add any object you want. Just go to the [OpenStreetMap](https://www.openstreetmap.org/) website, create an account, and start mapping. Ensure, that you're adding the correct objects with corresponding tags, and they will appear on the map, usually it taskes from 5 to 30 minutes.  
Please, while editing OSM, follow the [OSM Wiki](https://wiki.openstreetmap.org/wiki/Main_Page) and the [OSM Tags](https://wiki.openstreetmap.org/wiki/Map_Features) to add the correct objects. And also, respect the [OSM Guidelines](https://wiki.openstreetmap.org/wiki/Good_practice) and the community of this incredible project. Don't mess up with the data, and don't add anything that doesn't exist in the real world. It's just not cool.

### How can I download satellite images for the map?

You can find the detailed tutorial [here](https://github.com/iwatkot/maps4fs/blob/main/docs/download_satellite_images.md).

### How can I texture object and export it in the *.i3d format?

You can find the detailed tutorial [here](https://github.com/iwatkot/maps4fs/blob/main/docs/create_background_terrain.md).

### How can I import the *.i3d file to the map?

You can find the detailed tutorial [here](https://github.com/iwatkot/maps4fs/blob/main/docs/import_to_giants_editor.md).


### I have some graphic glitches in Giants Editor: the terrain become purple at some angles, what should I do?

To fix this issue, select the **terrain** object, open the **Terrain** tab in the **Attributes** window, scroll down to the end and press the **Reload material** button. It should help.

### I have some graphic glitches in Giants Editor: the screen keeps flickering black, what should I do?

To fix this issue, in the Giants Editor click on **Scripts** -> **Create new script**, give it a name and paste the code below:

```
setAudioCullingWorldProperties(-8192, -100, -8192, 8192, 500, 8192, 16, 0, 9000)
setLightCullingWorldProperties(-8192, -100, -8192, 8192, 500, 8192, 16, 0, 9000)
setShapeCullingWorldProperties(-8192, -100, -8192, 8192, 500, 8192, 16, 0, 9000)
```

Make sure that **Always loaded** checkbox is checked, then save it and execute. It should help.


### I launched the script to download satellite images from QGIS, but it's taking too long, what should I do?

The script is downloading a huge GeoTIFF image, so it can take a while depending on the region size and hardware. Some guys reported that on old CPUs it can take up to 30 minutes. Just wait, and it will finish eventually.

### I put the archive from the generator to the mods directory, but the map loading hangs, what should I do?

After downloading the archive from the generator it is a **mandatory** to unpack it, open in the Giants Editor, save and pack it back. Otherwise it won't work.  
Pay attention to the fact, that the archive name should be simple, like **FS25_MyMap.zip**. Avoid using special characters, spaces, and non-ASCII symbols in the archive name, or it won't work.

### I opened the map in the game, it works, but crops destruction is not work and also I see some glitches with the terrain, what's wrong?

At the end of the map creation process, you need to create a ground collision map. It's a very important step and without it you'll face a variety of issues in the game.
To do it, in Giants Editor go to **Scripts** -> **Shared scripts** -> **Map** -> **Create Ground Collision Map**. If you don't do this, you'll face some issues in the game.  
➡️ Any time you edit the map, you need to do it again.

### I opened the map and see that the trees (or any other object) are floating above the terrain, what should I do?

After generation, the trees (or any other object) may be floating above the terrain. To fix this, you need to put them on the terrain.  
1. Select the objects in the **Scenegraph**.
2. DO NOT ❌ Select the groups of objects, you need to select EACH OBJECT. Otherwise, it won't work. To make it easier, you can select and first one, scroll down to the last one, hold **Shift** and click on the last one.

![Select objects](https://github.com/user-attachments/assets/2afbea4e-6d0c-4ee5-a3c1-ce021926c9fd)

3. Click **Scripts** -> **Shared scripts** -> **Map** -> **Terrain** -> **Place objects on terrain**.

### Giants Editor crashes when I try to open the map, what should I do?

First of all, if it happens not on the loading, check out the **Console** tab if it contains any errors. If it does, try to fix them.

If it crahes on the loading and you can't use **Console** because of that, find the log file here:

```text
C:/Users/<username>/AppData/Local/GIANTS Editor 64bit 10.0.3/editor_log.txt
```

Pay attention that the folder name can be different, depending on the version of the Giants Editor.

Open the log file and check it for errors and pay attention to the latest lines. If you can't understand what's wrong, ask for help in our Discord server.

### Game is crashing or hangs when I try to load the map, what should I do?

#### Debug mode

First of all, enable the debug mode in the game. To do it, open the **game.xml** file in the following path:

```text
C:/Users/<username>/OneDrive/Documents/My Games/FarmingSimulator2025/game.xml
```

Pay attention that you may have or have not the **OneDrive** folder in the path depending on your system settings.

In this file, scroll down to the end and find the line:

```xml
<development>
    <controls>false</controls>
    <openDevConsole onWarnings="false" onErrors="false"/>
</development>
```

You need to change the **false** to **true** in the <controls> tag.

Now in the game you can use the **~** key to open the console. Check if there any errors or warnings in the console. If you can't understand what's wrong, ask for help in our Discord server.

#### Game log

If the game is crashing and you can't see the console, you can find the log file here:

```text
C:/Users/<username>/OneDrive/Documents/My Games/FarmingSimulator2025/log.txt
```

Pay attention that you may have or have not the **OneDrive** folder in the path depending on your system settings.

Open the log file and check it for errors and pay attention to the latest lines. If you can't understand what's wrong, ask for help in our Discord server.

### The game can't see the map mod, what should I do?

Ensure, that:

1. The archive with the map is named correctly.  
For example:

```text
FS25_Titelski_breg.zip ⬅️ This is a correct name.
FS25_mod name _ kgjdfg.zip ⬅️ This is an incorrect name.
```

2. The archive has a correct stucture inside of it.
For example, this is correct structure:

```text
📦FS25_Titelski_breg.zip
 ┣ 📂map
 ┃ ┣ 📂config
 ┃ ┃ ┣ 📄aiSystem.xml
 ┃ ┃ ┣ 📄... ⬅️ Other XML files there.
 ┃ ┃ ┗ 📄weed.xml
 ┃ ┣ 📂data
 ┃ ┃ ┣ 📄asphalt01_weight.png
 ┃ ┃ ┣ 📄... ⬅️ Other weights, infolayers and DEM files there.
 ┃ ┃ ┗ 📄unprocessedHeightMap.png
 ┃ ┣ 📄map.i3d
 ┃ ┣ 📄map.i3d.shapes
 ┃ ┣ 📄map.i3d.terrain.lod.type.cache
 ┃ ┣ 📄map.i3d.terrain.nmap.cache
 ┃ ┣ 📄map.i3d.terrain.occluders.cache
 ┃ ┣ 📄map.xml
 ┃ ┣ 📄overview.dds
 ┃ ┗ 📄splines.i3d
 ┣ 📄icon.dds
 ┣ 📄modDesc.xml
 ┗ 📄preview.dds
```

And this is incorrect structure:

```text
📦FS25_Titelski_breg
 ┗ 📂extra_folder
 ┃ ┣ 📂map
 ┃ ┃ ┣ 📂config
 ┃ ┃ ┃ ┣ 📜aiSystem.xml
 ┃ ┃ ┃ ┣ 📜⬅️ Other XML files there.
 ┃ ┃ ┃ ┗ 📜weed.xml
 ┃ ┃ ┣ 📂data
 ┃ ┃ ┃ ┣ 📜asphalt01_weight.png
 ┃ ┃ ┃ ┣ 📜 ⬅️ Other weights, infolayers and DEM files there.
 ┃ ┃ ┃ ┗ 📜unprocessedHeightMap.png
 ┃ ┃ ┣ 📜map.i3d
 ┃ ┃ ┣ 📜map.i3d.shapes
 ┃ ┃ ┣ 📜map.i3d.terrain.lod.type.cache
 ┃ ┃ ┣ 📜map.i3d.terrain.nmap.cache
 ┃ ┃ ┣ 📜map.i3d.terrain.occluders.cache
 ┃ ┃ ┣ 📜map.xml
 ┃ ┃ ┣ 📜overview.dds
 ┃ ┃ ┗ 📜splines.i3d
 ┃ ┣ 📜icon.dds
 ┃ ┣ 📜modDesc.xml
 ┃ ┗ 📜preview.dds
```

In the incorrect example above, pay attention that the files were placed in the **extra_folder** instead of the root of the archive.

If you think that some question should be added here, please, contact me in [Discord](https://discord.gg/Sj5QKKyE42) or open an issue on GitHub. Thank you! 