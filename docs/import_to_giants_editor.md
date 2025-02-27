## How to import background terrain into the Giants Editor

📹 Check out the video version of this tutorial.  

[![YouTube tutorial](https://github.com/user-attachments/assets/0c0a205d-b41e-4bfb-ac75-27737bd8f1e9)](https://www.youtube.com/watch?v=j0_tmJgfdpw)


So, at this point, you should have the `*.i3d` files with the background terrain. Now, let's import them into the Giants Editor.

ℹ️ In this tutorials it's assumed that you have already generated the map, downloaded satellite images using this tutorial: [Download high-resolution satellite images](download_satellite_images.md), and created a background terrain as described in the previous tutorial: [Prepare the i3d files](create_background_terrain.md).

Here's what you need to do:

1. Download and install the Giants Editor from the official website: [https://gdn.giants-software.com/downloads.php](https://gdn.giants-software.com/downloads.php). Note that for working with a map for Farming Simulator 25, you need to use the Giants Editor 10.0.0 or later, while for Farming Simulator 22, you need to use the Giants Editor 9.0.0 or later. If you try to open the map for the editor of the wrong version, it will crash.

2. Open the main map file, for example for the Farming Simulator 25 it's a `map/map.i3d` file.

3. Click on the `File` menu and select `Import...` select the `*.i3d` file with the background terrain.

![Import](https://github.com/user-attachments/assets/32145805-6583-4147-ac04-4c69d041b554)

4. If after the import you can't see the texture on the terrain, you need to add the texture manually.
Open the `Material Editing` panel (if it's not visible click on the `Window` menu and select `Material Editing`) and ensure that you've selected the correct object in the `Scenegraph` panel. Find the `Albedo map` and click on the `...` button to select the texture for the terrain. 

![Albedo map](https://github.com/user-attachments/assets/20a197cd-dadf-4e61-8ad2-c6752d60fb17)

5. The new window will appear, click on the `...` button and select the texture for the terrain.

![Select the texture](https://github.com/user-attachments/assets/29940c6d-1c18-4077-a0f0-ce525a9bc503)

6. If you did not convert the textures to the `.dds` format, you will see the warning message asking you `Convert now?`. Click on the `Yes` button to convert the texture to the `.dds` format.

![Convert now](https://github.com/user-attachments/assets/1778363a-1701-4c49-9fc7-67a1e67b3257)

7. You should be able to see the texture on the terrain now.

8. If you have used the method of cutting out the center of the map from the previous tutorial, you only need to adjust the `Translate Y` and `Scale Y` values which will be different for each terrain.  

ℹ️ This examples were added later, so they will contain different untexutred terrain, don't be scared of it!  

![Adjust the terrain](https://github.com/user-attachments/assets/d5b6aec2-8e81-47e4-92f1-752a8df7fd69)

And it should be perfectly aligned with the rest of the map.  

![Aligned terrain](https://github.com/user-attachments/assets/e31e8f27-032c-4096-8043-20e94dfed6ac)

If you want, you can go back to the previous step: [Prepare the i3d files](create_background_terrain.md).<br>

Happy mapping! 🚜🌾