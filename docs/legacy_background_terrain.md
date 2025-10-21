# Background Terrain (Legacy Manual Process)

> ⚠️ **This is the legacy manual process for FS22 or users who prefer manual control**
> 
> For **Farming Simulator 25**, Maps4FS now automatically generates ready-to-use i3d files! 
> See the [new automated Background Terrain guide](background_terrain.md) instead.
> 
> **Use this guide only if:**
> - You're creating maps for **Farming Simulator 22**
> - You prefer manual control over the process
> - You need custom quality settings not available in automation

## How to create a background terrain

📹 Check out the video version of this tutorial.  

[![YouTube tutorial](https://github.com/user-attachments/assets/0c0a205d-b41e-4bfb-ac75-27737bd8f1e9)](https://www.youtube.com/watch?v=j0_tmJgfdpw)

To create a background terrain for your Farming Simulator map, you need to open the `*.obj` files containing the terrain data, apply the generated satellite images as textures, and export the results to the `*.i3d` format.

ℹ️ This tutorial assumes that you have already generated your map with satellite images.

Let's get straight to work:

1. Download and install [Blender](https://www.blender.org/download/).
2. Download and install the [Blender Exporter Plugins](https://gdn.giants-software.com/downloads.php) from the official Giants Software website.
3. Activate the `Blender Exporter Plugins` in Blender.
4. Now you can import the `*.obj` file. Go to `File` → `Import` → `Wavefront (.obj)` and select your `*.obj` file.

![Import obj](https://github.com/user-attachments/assets/0fea21f6-3f1e-40e1-9d3e-6844fbb9f0de)

5. Select the imported object, right-click on it, and click `Set Origin` → `Origin to Geometry`.

![Origin to geometry](https://github.com/user-attachments/assets/379fd7b3-3b27-4b45-b9cc-e39218fa7a6b)

6. Click on the arrow icon or press the `N` key.

![413003](https://github.com/user-attachments/assets/c3b74d01-624a-4c1f-b5ad-ef620cbb33d4)

7. In the `Item` tab, change the `Location` [2] to `0, 0, 0` and the `Rotation` [3] to `0, 0, 0`.  
Set the `Dimensions` [4] of the background terrain in meters. This is calculated as map size + 2048 × 2. For example, if your map size is 4096×4096, the terrain size should be 8192×8192.

![Transformation](https://github.com/user-attachments/assets/bdd0be37-2a38-44e7-bbb8-21e1a0929756)

8. Switch to the `View` tab and change the `End` value to `100000` or similar. This ensures the terrain remains visible and doesn't partially disappear.

![Item end](https://github.com/user-attachments/assets/e838aa9c-09b7-4ede-b666-de83eb82fbbe)

9. Now we need to add a `Modifier` to the terrain. Click on the `Modifiers` tab, then click `Add Modifier`.

![Add modifier](https://github.com/user-attachments/assets/491c0d43-5f16-4a0e-b11c-a8e138107fbe)

10. In the dropdown menu, select the `Decimate` modifier.

![Select decimate](https://github.com/user-attachments/assets/1524ec71-a252-491e-8d39-84e7435980cd)

11. Now adjust the `Ratio` value. This determines how much the terrain will be simplified. Lower values create more simplified terrain. Depending on your terrain, a good starting point is around `0.05` or lower. Remember, this is background terrain that's barely visible in-game, so quality doesn't matter much. More simplified terrain consumes fewer resources.

![Apply decimate](https://github.com/user-attachments/assets/c7111d5d-a32a-4264-9810-bcfd948d8cd3)

12. Select the object, right-click on it, and select `Shade Smooth`. This will automatically smooth the terrain. Note that it may not work perfectly, so you might need to undo (`Ctrl + Z`), adjust the `Decimate` modifier value, and try again. Remember: it's background terrain, so it doesn't need to be perfect.

![Shade smooth](https://github.com/user-attachments/assets/b9b8f0ec-fea7-467e-8032-364c0d704efc)

The object should now look more terrain-like with `Shade Smooth` applied.

![After shade smooth](https://github.com/user-attachments/assets/2128a862-7a9c-4fdc-ab2f-316eadd9496e)

13. It's time to add a material to the terrain. Click on the `Material Properties` tab, then click the `New` button.

![Material](https://github.com/user-attachments/assets/b4a5ae03-b9ce-441f-925c-70ed7085ed7e)

14. Go to the `Surface` section, click on the `Base Color` **CIRCLE** (not the color itself), and select the `Image Texture`. Provide the path to the satellite image you want to use as a texture.

![Image texture](https://github.com/user-attachments/assets/ecbd8c35-80c9-4bfb-b384-2545aa8f0f63)

15. Go to the `Emission` section, click on the `Color` **THE COLOR ITSELF** (not the circle), and select completely black. Otherwise, you won't be able to see the material in Giants Editor.

![Emission](https://github.com/user-attachments/assets/cd6350cf-e7da-40ef-9e6d-fc6c551ce4d1)

16. Open the `UV Editing` tab, and in the right viewport change the view to `Top` by pressing `7` on the numpad or holding the `Z` key and selecting `Top`.

![UV editing](https://github.com/user-attachments/assets/55694f85-74ea-438a-b7ed-0f6eea7c5655)

17. Ensure the texture has correct orientation relative to the terrain. If not, rotate the texture image before proceeding. After confirming the texture is correctly oriented, switch to the right viewport and select everything by pressing `A`. Everything on the right side should be selected (orange). Press the `U` key and select one of the `Unwrap` options. The recommended option is `Project from View (bounds)`, which projects the texture from your current view. Note: this should be done in `Top` view, otherwise the texture may be projected incorrectly.

![Unwrap](https://github.com/user-attachments/assets/34973898-75fb-4f37-ba47-db26fba965b9)

18. Return to the `Layout` tab, press and hold `Z`, and select `Material Preview`. You should see the terrain with the texture applied. You can now adjust the object scale in the `Transform` tab. Note that you can also do this later in Giants Editor.

![Material preview](https://github.com/user-attachments/assets/30f8434b-0e68-4b67-b39b-cdd91d2a68d1)

### Cutting Out the Map Center

The generator can now remove the center from the mesh automatically. Ensure that **Background Settings** → **Remove center** is enabled.  

### Exporting the Object

19. It's time to export our object as an `*.i3d` file. Open the side panel by pressing `N` and select the `GIANTS I3D Exporter` tab. If you can't see it, you either didn't install the `Blender Exporter Plugins` (step 2) or didn't activate them (step 3).

Ensure the object is selected [1], specify the output file path [3], and click the `Export selected` button [4]. You can also use `Export all`, but make sure you don't have other objects in the scene (Blender adds a camera, light source, and cube by default). 

![Export to i3d](https://github.com/user-attachments/assets/ad3913d7-a16e-47c0-a039-9f792e34ad4c)

## How to Import Background Terrain into Giants Editor

At this point, you should have `*.i3d` files with your background terrain. Now let's import them into Giants Editor.

ℹ️ This tutorial assumes you have already generated your map, downloaded satellite images, and created background terrain as described in the previous steps.

Here's what you need to do:

1. Download and install Giants Editor from the official website: [https://gdn.giants-software.com/downloads.php](https://gdn.giants-software.com/downloads.php). 
   
   **Important**: For Farming Simulator 25 maps, use Giants Editor 10.0.0 or later. For Farming Simulator 22 maps, use Giants Editor 9.0.0 or later. Using the wrong editor version will cause crashes.

2. Open your main map file (for Farming Simulator 25, this is the `map/map.i3d` file).

3. Click the `File` menu and select `Import...`, then choose your `*.i3d` file with the background terrain.

![Import](https://github.com/user-attachments/assets/32145805-6583-4147-ac04-4c69d041b554)

4. If you can't see the texture on the terrain after import, you need to add it manually.
   Open the `Material Editing` panel (if not visible, click `Window` menu and select `Material Editing`) and ensure you've selected the correct object in the `Scenegraph` panel. Find the `Albedo map` and click the `...` button to select the terrain texture. 

![Albedo map](https://github.com/user-attachments/assets/20a197cd-dadf-4e61-8ad2-c6752d60fb17)

5. The new window will appear, click on the `...` button and select the texture for the terrain.

![Select the texture](https://github.com/user-attachments/assets/29940c6d-1c18-4077-a0f0-ce525a9bc503)

6. If you haven't converted the textures to `.dds` format, you'll see a warning message asking `Convert now?`. Click `Yes` to convert the texture to `.dds` format.

![Convert now](https://github.com/user-attachments/assets/1778363a-1701-4c49-9fc7-67a1e67b3257)

7. You should now be able to see the texture on the terrain.

8. If you used the method to cut out the map center from the previous tutorial, you only need to adjust the `Translate Y` and `Scale Y` values, which will differ for each terrain.

ℹ️ These examples were added later, so they contain different untextured terrain - don't be alarmed!  

![Adjust the terrain](https://github.com/user-attachments/assets/d5b6aec2-8e81-47e4-92f1-752a8df7fd69)

And it should be perfectly aligned with the rest of the map.  

![Aligned terrain](https://github.com/user-attachments/assets/e31e8f27-032c-4096-8043-20e94dfed6ac)