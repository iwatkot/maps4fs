## Create a Farming Simulator map in 10 steps

📹 WIP: Check out the complete playlist of video turorials on [YouTube](https://www.youtube.com/watch?v=hPbJZ0HoiDE&list=PLug0g7UYHX8D1Jik6NkJjQhdxqS-NOtB9). 🆕<br>

📹 A complete step-by-step video tutorial is on [YouTube](https://www.youtube.com/watch?v=Nl_aqXJ5nAk&)!  

Hey, farmer!  
So, you're ready to create your own map for the Farming Simulator? Great, the `maps4fs` tool will save you a lot of time and effort. In this section, I'll guide you through the process of creating a map from scratch using the generator.  
This tutorial will contain a short description of each step, but you'll find detailed tutorials in the [docs](https://github.com/iwatkot/maps4fs/tree/main/docs) directory of the project.  
  
Just in case: remember to check the [FAQ](https://github.com/iwatkot/maps4fs/blob/main/docs/FAQ.md) if you have any questions when working with the generator. It's possible that the answer is already there.  

Let's roll!

### 1. 📍 Get the coordinates of the center of your map
It should be easy to do with [Google Maps](https://www.google.com/maps) or [OpenStreetMap](https://www.openstreetmap.org). The coordinates are latitude and longitude values, for example, `51.5074, -0.1278` for London.  
ℹ️ This point will be the center of your map, not the top, not the bottom, but the center.
*️⃣ Note, that the coordinates should not include any additional and should be decimal, not degrees-minutes-seconds. For example, these coordinates are wrong: `45°16'02.3"N 19°47'32.9"E`, but these are correct: `45.2673, 19.7925`.


### 2. 📏 Decide the size of your map
The default built-in maps in Farming Simulator are 2048x2048 meters, but you can choose any size you want as long as it's a power of 2 (e.g. 1024x1024, 2048x2048, 4096x4096, etc.).  
ℹ️ Many new-coming mappers choose large sizes like 16kx16k, but I want to warn you about some difficulties you may face with such a large map:
- To edit this map, you'll need a powerful computer. And still, it may crash even on high-end machines.
- You may (AND WILL) face performance issues in the game.
- And not the obvious one: it's very tough to create even a standard 2kx2k map, so you can imagine how hard it will be to create a 16kx16k map. It will take dozens (if not hundreds) of hours to create a map of this size.

Yeah, a 16-kilometer map sounds cool, but probably you'll never gonna make it to the end. So, if you're a beginner I strongly recommend starting with a 2kx2k map, or at least 4kx4k.

*️⃣ Note, that at the moment Giants Editor 10 does not support 16-kilometer maps, and will crash if you try to open it.

### 3. 🚀 Run the generator
Now all you need to do is just click on the `Generate` button and wait a little bit.  
ℹ️ There are also some advanced settings you can tweak, but from their name, you should get the idea that they are for the advanced users. Learn more about them in the [For advanced users](https://github.com/iwatkot/maps4fs?tab=readme-ov-file#For-advanced-users) section of the README. For experts the tool also offers a set of [Expert Settings](https://github.com/iwatkot/maps4fs?tab=readme-ov-file#Expert-settings) to fine-tune the map generation process and use some additional features.

### 4. 📥 Download and unpack the generated map
The generator will provide you with a `.zip` file that contains the map. Unpack it somewhere on your computer.  
ℹ️ Learn more about what's inside of the archive in the [Map Structure](https://github.com/iwatkot/maps4fs/blob/main/docs/map_structure.md) document.

### 5. 🌎 Download and align the satellite images
The tool can automatically download satellite images for the background terrain (and also for the overview.dds file). Refer to the Satellite Settings section in the generator.  
ℹ️ There's a detailed tutorial about it in the [How to download satellite images](https://github.com/iwatkot/maps4fs/blob/main/docs/download_satellite_images.md) document.

### 6. ⛰️ Create a background terrain
Once you obtained aligned satellite images, you can create a background terrain using the *.obj files that are included in the map archive.  
ℹ️ Learn how to do it in the [How to create a background terrain](https://github.com/iwatkot/maps4fs/blob/main/docs/create_background_terrain.md) document.

### 7. ⬇️ Import the background terrain to the Giants Editor
After you create the background terrain, textured it, and export it as a *.i3d file, you can import it to the Giants Editor.  
ℹ️ Learn how to do it in the [How to import the background terrain to the Giants Editor](https://github.com/iwatkot/maps4fs/blob/main/docs/import_to_giants_editor.md) tutorial.

### 8. 🗺️ Create the overview.dds file
After you aligned the satellite images, you can use it to create the overview.dds file.  
ℹ️ Learn more about it in the [Oveview image](https://github.com/iwatkot/maps4fs?tab=readme-ov-file#Overview-image) section of the README.

### 9. 🌾 Add fields
By default, the generator will add all the fields from the [OpenStreetMap](https://www.openstreetmap.org) data. After opening the map in the Giants Editor, you can repaint it only with one click.  
ℹ️ Learn more about it in the [Fields](https://github.com/iwatkot/maps4fs/blob/main/docs/fields.md) document.

### 10. 📚 Add farmlands
The generator will automatically add farmlands to the map. But if you need, you can add or adjust them manually in the Giants Editor.
ℹ️ Learn more about it in the [Farmlands](https://github.com/iwatkot/maps4fs/blob/main/docs/farmlands.md) document.  
  
So, that's it! Now, you can actually start creating your own map. Mostly, you need to add buildings, roads, and other objects to make it look like a real map. And the painted textures will help you to place them correctly, just like in the real world.  
But it's already fully playable, just without anything except the terrain, textures, fields, and farmlands.
