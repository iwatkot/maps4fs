## How to create a background terrain

To create a background terrain for the Farming Simulator map, you need to open the `*.obj` files with the terrain, obtain the satellite images as described in the [Download high-resolution satellite images](download_satellite_images.md) tutorial to use them as textures and export your results to the `*.i3d` format.<br>

ℹ️ In this tutorials it's assumed that you have already generated the map and downloaded satellite images from the previous step: [Download high-resolution satellite images](download_satellite_images.md).<br>

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

7. In the `Item` tab, change the `Location` [2] to `0, 0, 0` and the `Rotation` [3] to `0, 0, 0`.  
Set the `Dimensions` [4] of the background terrain in meters. It's calculated as map size + 2048 * 2. For example, if the map size is 4096x4096, the size of the terrain should be 8192x8192.

![Transformation](https://github.com/user-attachments/assets/bdd0be37-2a38-44e7-bbb8-21e1a0929756)

8. Switch to the `View` tab and change the `End` value to `100000` or something like that. It's just to make sure that the terrain is visible, otherwise it may partially disappear.

![Item end](https://github.com/user-attachments/assets/e838aa9c-09b7-4ede-b666-de83eb82fbbe)

9. Now we need to add a `Modifier` to the terrain. Click on the `Modifiers` tab, then click on the `Add Modifier`.

![Add modifier](https://github.com/user-attachments/assets/491c0d43-5f16-4a0e-b11c-a8e138107fbe)

10. In the dropdown menu, select the `Decimate` modifier.

![Select decimate](https://github.com/user-attachments/assets/1524ec71-a252-491e-8d39-84e7435980cd)

11. Now you need to adjust the `Ratio` value. The `Ratio` value will determine how much the terrain will be simplified. The lower the value, the more simplified the terrain will be. It depends on your actual terrain, but a good starting point is something like `0.05` and lower. Remember, that this is a background terrain, which almost not visible in the game, so it's quality doesn't really matter. And the more simplified the terrain is, the less resources it will consume.

![Apply decimate](https://github.com/user-attachments/assets/c7111d5d-a32a-4264-9810-bcfd948d8cd3)

12. Select the object, right-click on it, and select `Shade Smooth`. It will automatically smooth the terrain. Note that it may not work perfectly, so you may need to `Ctrl + Z` it, change the value of the `Decimate` modifier, and try again. And again: it's a background terrain, so it doesn't need to be perfect.

![Shade smooth](https://github.com/user-attachments/assets/b9b8f0ec-fea7-467e-8032-364c0d704efc)

The object should look more like a terrain now with the `Shade Smooth` applied.

![After shade smooth](https://github.com/user-attachments/assets/2128a862-7a9c-4fdc-ab2f-316eadd9496e)

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

### Cutting out the center of the map

Now the generator can remove the center from the mesh automatically, you need to ensure that the option **Background Settings** -> **Remove center** is turned on.  
So the approach above is not needed anymore, but it's still valid if you want to do it manually.

<details>
<summary>The manual approach</summary>

Now we will need to cut out the center of the map from the mesh. There are two aprroaches to do it. Using the `Boolean` modified and using the `Knife Project` tool. The `Boolean` modifier is more straightforward, and usually it works much better, so it's highly recommended to use it, not the second one.  

ℹ️ This tutorial was added after the main one, so it will contain different untexutred terrain, don't be scared of it!  

#### Using the Boolean modifier

1. Press `Shift + A` and add a `Cube` to the scene.  

![Add cube](https://github.com/user-attachments/assets/57732730-f388-42b9-960d-3ca668cdca27)

2. Set the size of the cube X and Y the same as a map size. For example, if the map size is 4096x4096, the size of the cube should be 4096x4096. The Z can be any value, but it should be bigger than the terrain itself!  

![Set cube size](https://github.com/user-attachments/assets/2bf22467-85ac-4b01-84fd-5dd74a6f58f6)

3. Make sure that the cube FULLY cuts through the terrain (higher and lower than the terrain).  

![Cuts through](https://github.com/user-attachments/assets/85361f53-e267-4892-86d2-d6db460f26f2)

4. Now select your background terrain, go to the `Modifiers` tab, click on the `Add Modifier`.  

![Add modifier](https://github.com/user-attachments/assets/6718a948-3353-4375-a569-07a4a1e5d8f8)

5. Type `Boolean` in the search bar and select the `Boolean` modifier.  

![Select boolean](https://github.com/user-attachments/assets/11b4be71-c4d7-431a-9e75-f7fe39368003)

6. Click on the `Dropper` icon.  

![Dropper](https://github.com/user-attachments/assets/292dcfaa-d6cc-4b42-be1f-1b83e03951c4)

7. Now click on the cube in the scene.  

![Click on cube](https://github.com/user-attachments/assets/9fc8272b-5d4f-4477-8460-506d1007116f)

8. Click on the `Fast` option.  

![Fast](https://github.com/user-attachments/assets/9e54b078-da25-471c-98e8-cd71c635cf91)

9. Now you can hide the cube by clicking on the eye icon and ensure that the terrain is cut out correctly.

![Hide cube](https://github.com/user-attachments/assets/6ee61673-bc35-4942-a31a-8e2b55883e83)

We are done! You can now move to the final step: [Export the object](#exporting-the-object).

#### Using the Knife Project tool

❌ This method is not recommended, as it's much more complicated and usually doesn't work as expected. Use it only if for some reason the `Boolean` modifier doesn't work for you.

<details>
<summary>Click to expand</summary>

1. Press `Shift + A` and add a `Plane` to the scene.

![Add plane](https://github.com/user-attachments/assets/7d66f878-24dc-4b83-aa44-949dc78a100b)

2. Set the size of the plane X and Y the same as a map size. For example, if the map size is 4096x4096, the size of the plane should be 4096x4096. The Z can be any value, but the plane must be well above the terrain.

![Set plane size](https://github.com/user-attachments/assets/89ac8cd5-a9de-4c46-b3d4-59e594d876b0)

3. Press `Tab` and then `A` to select all vertices of the plane. Press `U` and select `Project from View (Bounds)`. Switch to the `Top` view.

![Top view](https://github.com/user-attachments/assets/9cb1ce28-980b-4e02-b4cb-6fe89794927d)

4. Ensure that your terrain is selected, then `Ctrl + Click` on the plane.

![Ctrl click](https://github.com/user-attachments/assets/7c67713b-6346-4189-b595-3f5cfbbaaf40)

5. Now click on the `Mesh` and select `Knife Project`.

![Knife project](https://github.com/user-attachments/assets/eded9fba-af0e-44f0-948f-436ad06a8088)

6. After a while, you'll see that the central part of the terrain is selected.

![Selected](https://github.com/user-attachments/assets/33187de6-26ee-4d31-bf0b-a7809766a2cf)

7. Press `Delete` and select `Faces`.

![Delete faces](https://github.com/user-attachments/assets/76328118-03d7-48cc-a9fc-b845cfe8c9e6)

8. The central part of the terrain should be removed now.

![Removed](https://github.com/user-attachments/assets/bf787700-2e12-4b4b-96fc-3ec9042cd2ed)

Pay attention to the fact this method can produce artifacts. Remember that it's not recommended to use it, but if you have no other choice, you can try it.

![Artifacts](https://github.com/user-attachments/assets/e9df0436-54d7-474c-9cbe-76c950f31a53)

</details>
</details>

### Exporting the object

19. It's finally time to export our object as an `*.i3d` file. Open the side panel by pressing `N` and select the `GIANTS I3D Exporter` tab. If you can not see it here, that means you did not installed the `Blender Exporter Plugins` (step 2) or you did not activated it (step 3).
Now ensure that the object is selected [1], specify the path to the output file [3], and click on the `Export selected` button [4]. You can also use the `Export all` option, but ensure that you don't have any other objects in the scene, for example by default Blender adds a camera and a light source and a cube. 

![Export to i3d](https://github.com/user-attachments/assets/ad3913d7-a16e-47c0-a039-9f792e34ad4c)

Now we can go to the final section of the tutorial: [Import the i3d files to Giants Editor](import_to_giants_editor.md). Or you can go back to the previous step: [Download high-resolution satellite images](download_satellite_images.md).