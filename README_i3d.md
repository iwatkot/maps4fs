## How to create a background terrain

To create a background terrain for the Farming Simulator map, you need to open the `*.obj` files with the terrain, obtain the satellite images as described in the [Download high-resolution satellite images](README_satellite_images.md) tutorial to use them as textures and export your results to the `*.i3d` format.<br>

ℹ️ In this tutorials it's assumed that you have already generated the map and downloaded satellite images from the previous step: [Download high-resolution satellite images](README_satellite_images.md).<br>

Let's go straight to the deal:

1. Download and install the [Blender](https://www.blender.org/download/) software.
2. Download and install the [Blender Exporter Plugins](https://gdn.giants-software.com/downloads.php) from the official Giants Software website.
3. Activate the `Blender Exporter Plugins` in the Blender.
4. Now, you can import the `*.obj`. Go to `File` -> `Import` -> `Wavefront (.obj)` and select the `*.obj` file.

![Import obj](https://github.com/user-attachments/assets/0fea21f6-3f1e-40e1-9d3e-6844fbb9f0de)

5. Select the imported object, right-click on it, click on `Set Origin` -> `Origin to Geometry`.

![Origin to geometry](https://github.com/user-attachments/assets/379fd7b3-3b27-4b45-b9cc-e39218fa7a6b)

6. Click on the arrow icon or press the `N` key.

![413003](https://github.com/user-attachments/assets/c3b74d01-624a-4c1f-b5ad-ef620cbb33d4)

7. In the `Item` tab, change the `Location` to `0, 0, 0` and the `Rotation` to `0, 0, 0`.

![Transformation](https://github.com/user-attachments/assets/3fa04f93-12c2-420d-9313-a5cf0186e686)

8. Swtich to the `View` tab and change the `End` value to `10000` or something like that. It's just to make sure that the terrain is visible, otherwise it may partially disappear.

![Item end](https://github.com/user-attachments/assets/e838aa9c-09b7-4ede-b666-de83eb82fbbe)

9. Now we need to add a `Modifier` to the terrain. Click on the `Modifiers` tab, then click on the `Add Modifier`.

![Add modifier](https://github.com/user-attachments/assets/491c0d43-5f16-4a0e-b11c-a8e138107fbe)

10. In the dropdown menu, select the `Decimate` modifier.

![Select decimate](https://github.com/user-attachments/assets/1524ec71-a252-491e-8d39-84e7435980cd)

11. Now you need to adjust the `Ratio` value. The `Ratio` value will determine how much the terrain will be simplified. The lower the value, the more simplified the terrain will be. It depends on your actual terrain, but a good starting point is something like `0.5` and lower. Remember, that this is a background terrain, which almost not visible in the game, so it's quality doesn't really matter. And the more simplified the terrain is, the less resources it will consume.

![Apply decimate](https://github.com/user-attachments/assets/c7111d5d-a32a-4264-9810-bcfd948d8cd3)

12. Select the object, right-click on it, and select `Shade Smooth`. It will automatically smooth the terrain. Note that it may not work perfectly, so you may need to `Ctrl + Z` it, change the value of the `Decimate` modifier, and try again. And again: it's a background terrain, so it doesn't need to be perfect.

![Shade smooth](https://github.com/user-attachments/assets/b9b8f0ec-fea7-467e-8032-364c0d704efc)

The object should look more like a terrain now with the `Shade Smooth` applied.

![After shade smooth](https://github.com/user-attachments/assets/c3006eba-0e5b-470f-88be-04cab9dd4139)

13. It's time to add a material to the terrain. Click on the `Material Properties` tab, then click on the `New` button.

![Material](https://github.com/user-attachments/assets/b4a5ae03-b9ce-441f-925c-70ed7085ed7e)

14. Go to the `Surface` section, click on the `Base Color` **CIRCLE** (not the color itself), and select the `Image Texture`. Provide the path to the satellite image you want to use as a texture.

![Image texture](https://github.com/user-attachments/assets/ecbd8c35-80c9-4bfb-b384-2545aa8f0f63)

15. Go to the `Emission` section, click on the `Color` **THE COLOR ITSELF** now (not the circle), and select completely black color. Otherise, you wont be able to see the material in the Giants Editor.

![Emission](https://github.com/user-attachments/assets/cd6350cf-e7da-40ef-9e6d-fc6c551ce4d1)

16. Open the `UV Editing` tab, and in the right tab change the view to `Top` by pressing `7` on the numpad or holding the `Z` key and selecting the `Top`.

![UV editing](https://github.com/user-attachments/assets/55694f85-74ea-438a-b7ed-0f6eea7c5655)

17. Now ensure that the texture has a correct orientation relative to the terrain. If it's not, you can rotate the texture image before moving on. After you ensured that the texture is correctly oriented, switch to the right tab and select everything by pressing `A`. Everything on the right side should be selected (orange). Now press the `U` key and select one of the `Unwrap` options. Recommended one is `Unwrap` -> `Angle Based`. It should work fine for the most cases. The second one is Project from View (bounds). It will project the texture from the view you are currently in. Note that it should be done in the `Top` view, otherwise the texture may be projected incorrectly.

![Unwrap](https://github.com/user-attachments/assets/34973898-75fb-4f37-ba47-db26fba965b9)

18. Now return to the `Layout` tab, press and hold `Z` and select `Material Preview`. You should see the terrain with the texture applied. Now you can adjust the scale of the object in the `Transform` tab. Note, that you can do it later in the Giants Editor as well.

![Materail preview](https://github.com/user-attachments/assets/30f8434b-0e68-4b67-b39b-cdd91d2a68d1)

19. It's finally time to export our object as an `*.i3d` file. Open the side panel by pressing `N` and select the `GIANTS I3D Exporter` tab. If you can not see it here, that means you did not installed the `Blender Exporter Plugins` (step 2) or you did not activated it (step 3).
Now ensure that the object is selected [1], specify the path to the output file [3], and click on the `Export selected` button [4]. You can also use the `Export all` option, but ensure that you don't have any other objects in the scene, for example by default Blender adds a camera and a light source and a cube. 

![Export to i3d](https://github.com/user-attachments/assets/ad3913d7-a16e-47c0-a039-9f792e34ad4c)

Now we can go to the final section of the tutorial: [Import the i3d files to Giants Editor](README_giants_editor.md). Or you can go back to the previous step: [Download high-resolution satellite images](README_satellite_images.md).