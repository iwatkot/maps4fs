## Frequently Asked Questions

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


If you think that some question should be added here, please, contact me in [Discord](https://discord.gg/Sj5QKKyE42) or open an issue on GitHub. Thank you! 