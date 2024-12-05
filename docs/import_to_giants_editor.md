## How to import background terrain into the Giants Editor

So, at this point, you should have the `*.i3d` files with the background terrain. Now, let's import them into the Giants Editor.

ℹ️ In this tutorials it's assumed that you have already generated the map, downloaded satellite images using this tutorial: [Download high-resolution satellite images](download_satellite_images.md), and created a background terrain as described in the previous tutorial: [Prepare the i3d files](create_background_terrain.md).

Here's what you need to do:

1. Download and install the Giants Editor from the official website: [https://gdn.giants-software.com/downloads.php](https://gdn.giants-software.com/downloads.php). Note that for working with a map for Farming Simulator 25, you need to use the Giants Editor 10.0.0 or later, while for Farming Simulator 22, you need to use the Giants Editor 9.0.0 or later. If you try to open the map for the editor of the wrong version, it will crash.

2. Open the main map file, for example for the Farming Simulator 25 it's a `map/map.i3d` file.

3. Click on the `File` menu and select `Import...` select the `*.i3d` file with the background terrain.

![Import](https://github.com/user-attachments/assets/32145805-6583-4147-ac04-4c69d041b554)

4. Postition the terrain in the correct place. You can use the `Transform` panel to move, rotate, and scale the terrain.

![Position](https://github.com/user-attachments/assets/8202b2f5-2286-4213-8785-c3779e9ad88a)

5. If after the import you can't see the texture on the terrain, you need to add the texture manually.
Open the `Material Editing` panel (if it's not visible click on the `Window` menu and select `Material Editing`) and ensure that you've selected the correct object in the `Scenegraph` panel. Find the `Albedo map` and click on the `...` button to select the texture for the terrain. 

![Albedo map](https://github.com/user-attachments/assets/20a197cd-dadf-4e61-8ad2-c6752d60fb17)

6. The new window will appear, click on the `...` button and select the texture for the terrain.

![Select the texture](https://github.com/user-attachments/assets/29940c6d-1c18-4077-a0f0-ce525a9bc503)

7. If you did not convert the textures to the `.dds` format, you will see the warning message asking you `Convert now?`. Click on the `Yes` button to convert the texture to the `.dds` format.

![Convert now](https://github.com/user-attachments/assets/1778363a-1701-4c49-9fc7-67a1e67b3257)

8. You should be able to see the texture on the terrain now. So now you only need to adjust the position of the terrain in the world.

![Terrain with texture](https://github.com/user-attachments/assets/a5da03a6-42b3-4010-997e-787c0d9bee38)

So, we'are done here.<br>
ℹ️ Please note, that is almost no way to align all background terrain with map perfectly without editing them in the 3D editor, Blender for example. You can find a lot of tutorials on YouTube on how to do it, this won't be covered here. Or you can just leave it as is and find the best possible position for the terrain, and maybe hiding the edges with some objects. It's up to you.<br>

If you want, you can go back to the previous step: [Prepare the i3d files](create_background_terrain.md).<br>

Happy mapping! 🚜🌾