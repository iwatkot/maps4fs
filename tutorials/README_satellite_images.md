## How to download satellite images using QGIS

To texture the background models on the map you map need to obtain satellite images. In this tutorial, I will show you how to download them using [QGIS](https://qgis.org) software.<br>
ℹ️ In this tutorials it's assumed that you have already generated the map. <br>

Now, let's start downloading the images:

1. Download and install QGIS software from the [official website](https://qgis.org/download/).
2. Open the QGIS software, go to the `Plugins` menu and click on `Manage and Install Plugins`.

![Manage and Install Plugins](https://github.com/user-attachments/assets/0b1c4374-58e8-48a7-aa10-04ccd100604d)

3. Enter `QuickMapServices` in the search bar, select it in the list and click on `Install plugin`.

![Install plugin](https://github.com/user-attachments/assets/236511dc-36a9-4305-b7d3-2d9a4e59d3dd)

4. Now, go to the `Web` menu and click on `QuickMapServices` and select `Settings`.

![Settings](https://github.com/user-attachments/assets/c79ce93f-f3a6-49ab-a4b8-a8250db38b7a)

5. Opetn the tab `More Services` and click on `Get contributed pack` and then click on `Save`.

![Get contributed pack](https://github.com/user-attachments/assets/a4fc7fe7-64b3-4815-ad9b-f885bf6d7a21)

6. Now in in the `QuickMapServices` you can see a lot of different sources. So open `Web` menu again and click on `QuickMapServices`, select `Google` and click on `Google Satellite`.<br>
ℹ️ In this tutorial we will use `Google` maps as an example, but you can use any other source just the same way.

![Google Satellite](https://github.com/user-attachments/assets/944e7ffa-c8e8-4e8f-a2f6-ec48855ac822)

ℹ️ Latest version of the `maps4fs` will generate QGIS scripts for you, so you can just copy-paste them and do everything automatically. Let's talk about how to use those scripts.

7. Open the `Python Console` by clicking on the corresponding icon in the toolbar or by pressing `Ctrl+Alt+P`.

![Python Console](https://github.com/user-attachments/assets/b9eefb07-b2bb-424f-99c5-7cc9f2abaefe)

8. Click on the `Show Editor` icon in the `Python Console` toolbar.

![Show Editor](https://github.com/user-attachments/assets/75490f86-5c0a-4ffa-aa9d-7e7924641b13)

9. Remove the default code from the editor if it's there.

10. You'll find the scripts in the `scripts` directory, they are grouped by the component of the generator:

```text
📁scripts
 ┣ 📄background_bbox.py
 ┣ 📄background_point.py
 ┣ 📄background_rasterize.py
 ┣ 📄config_bbox.py
 ┣ 📄config_point.py
 ┗ 📄config_rasterize.py
 ```

 So, the background scripts are for the background terrain and the config scripts are for the overview map.<br>
 The `bbox` scripts are used to set the bounds of the map, and the `rasterize` scripts are used to download the images. There are also `point` scripts,which can be used to add points to the cornders of tiles, so it may be helpful in some scenarios.<br>

⚡Remember that you should run them separately and remember to remove extra layers between the components, otherwise you'll get lines from the previous component on your images.<br>

11. For each component, first you need to add the bounding boxes to the map. So, open the `{component}_bbox.py` script and copy the code from it to the `Python Console` editor and press `Run script`.

![Run bbox](https://github.com/user-attachments/assets/c1bd102e-15ef-4bc9-a99a-6a18fdbaaca1)

12. You should be able to see the bounding box(es) on the map after it.<br>

![Background bounding boxes](https://github.com/user-attachments/assets/9f724ca8-9306-4764-87fb-f86979008987)

13. Now you can open the `{component}_rasterize.py` script.<br>
➡️ You must edit this script before running it. You need to specify the path to the directory, where the images will be saved.

```python

import processing

############################################################
####### ADD THE DIRECTORY FOR THE FILES TO SAVE HERE #######
############################################################
############### IT MUST END WITH A SLASH (/) ###############
############################################################

SAVE_DIR = "C:/Users/iwatk/OneDrive/Desktop/"

############################################################
```
So, set the path to the directory, remember that if you copy-paste it from the Windows Explorer, you need to replace the backslashes with the forward slashes, otherwise you'll get an error.

14. Copy the code from the `{component}_rasterize.py` script to the `Python Console` editor and press `Run script`.<br>
⚡QGIS will probably hangs for a several minutes, because it will be downloading high-resolution images, so be patient.

15. After the download is finished, all the images will be saved in the specified directory. You can now close the QGIS software.<br>
➡️ Pay attention to the fact that your images will contain small lines from bounding boxes, you need to crop them in the image editor. before using them as textures, you also need to resize them (make sure that proportions are preserved, for example 4096x2048, 2048x2048, etc.) and convert them to the `.png` or `.dds` format.

*️⃣ This approach does not guarantee that the map itself will be perfectly aligned with the background images as well as with the overview map, so you may need to adjust bounding boxes. You may consider those bounding boxes as a reference to help you get the right images, but you should not rely on them completely.<br>

If you want to images match the map perfectly, you may need to download the images with a small `EXTENT_BUFFER` and then manually adjust them in an image editor. To do it, change the value in the rasterize script:

```python
processing.run(
    "native:rasterize",
    {
        "EXTENT": epsg3857_string,
        "EXTENT_BUFFER": 0, # ⬅️ Make this value higher.
        "TILE_SIZE": 64,
        "MAP_UNITS_PER_PIXEL": 1,
        "MAKE_BACKGROUND_TRANSPARENT": False,
        "MAP_THEME": None,
        "LAYERS": None,
        "OUTPUT": file_path,
    },
)
```

⚠️ Below is an outdated method of manual downloading of images. It's highly recommended to use automatic scripts, that were generated by the software, but if you still want to do it manually, you can follow the steps below.<br>
<details>
<summary>Manual downloading</summary>

7. Now we need the `Processing Toolbox` to be shown. To do this, go to the `View` menu and click on `Panels` and select `Processing Toolbox`.

![Processing toolbox](https://github.com/user-attachments/assets/12cbc53b-3bcf-4009-b6d9-84bc8723cd25)

8. We are ready to save some images! You can navigate to the ROI (region of interest) or not, it's completely optional, but I guess it will be more convenient to do so.<br>
Now in the `Processing Toolbox` go to `Raster tools` and click on `Convert map to raster`.

![Convert map to raster](https://github.com/user-attachments/assets/8e2c7b48-6b36-426e-b9f9-51830ffdaf28)

9. Now we need to set the parameters.<br>
⚡Ok, I know that you've not been reading the text, just scrolling through the images, but now you need to do it, otherwise you probably download the images wrong.<br>
So, here's the deal:<br>
1️⃣ - Please paste the EPSG3857 string in this field, you can find it in the `generation_info.json` file.<br>
If you're downloading the images for the Background Terrain to texture them, you'll find them in the `Background` section:<br>

```json
"Background": {
    "N": {
        "center_latitude": 36.782024946489436,
        "center_longitude": 31.774572787591236,
        "epsg3857_string": "3534569.3402558295,3539689.185521097,4407487.386296577,4410047.308952553 [EPSG:3857]",
        "height": 2048,
        "width": 4096,
        "north": 36.79123398672488,
        "south": 36.77281590625399,
        "east": 31.79756896386182,
        "west": 31.75157661132065
    },
}
```

Pay attention to the `N` key here, you have 8 entries in your file, which one represents one tile around your map: North (N), North-East (NE), East (E), South-East (SE), South (S), South-West (SW), West (W), North-West (NW).<br>
So you need to download each one into the separate file.<br>

If you're downloading the images for the Overview (in-game map) file, you'll find the string in the `Config` section:<br>

```json
"Config": {
    "Overview": {
        "epsg3857_string": "2249906.6679576184,2255734.9033189337,5663700.389039194,5669528.6247056825 [EPSG:3857]",
        "south": 45.304132173367165,
        "west": 45.267296012425376,
        "north": 20.263611405732693,
        "east": 20.211255476687537,
        "height": 4096,
        "width": 4096
    }
},
```

➡️ So, you just copy the `epsg3857_string` value and paste it in the `Minimum extent to render` field.<br>

2️⃣ - Set the `Tile size` to the minimum possible value, in our case it's `64`. This is very important, because if you don't do it, the output images won't actually match your bounds.<br>

3️⃣ - Set the `Map units per pixel` value. The smaller the value, the better the quality of the image, so I recommend setting it to the minimum possible value, in our case it's `1`.<br>

4️⃣ - Set the `Output file` path. You can click on the `...` button and select the folder where you want to save the images. It's recommended to save them with the same name as the tile, e.g. `N.tif`, `NE.tif`, etc. This way it will be mauch easier to add the corresponding texture to the object in Blender.<br>

5️⃣ - Now you can finally click on the `Run` button and wait until the images are downloaded. Do not click on the `Close` button even after the download is finished, because you need to download the rest of the tiles.<br>

![Convert map to raster params](https://github.com/user-attachments/assets/48a611b7-d35d-43b7-8bef-41c77d187035)

10. As mentioned earlier, do not click on the `Close` button after the download is finished, because if you need to download the rest of the tiles you can just click on the `Change parameters` button, set a new value in the `Minimum extent to render` field and click on the `Run` button again. It will be much faster than setting all the parameters again.<br>

![Change parameters](https://github.com/user-attachments/assets/066c81a8-6d03-4efc-9db0-2d2c90c59341)

⚡Each time saving the image, ensure that on the left sidebar the correct layer (`Google Satellite`) is selected, otherwise you will save the image from another layer (probably from another tile).<br>

11. After you've downloaded everything you need, if you did not disable new layer creation and/or didn't delete the new layers, you can hide the `Google Satellite` layer by clicking on the eye icon next to it to see your own layers.<br>

![Your layers](https://github.com/user-attachments/assets/98f9c19f-032a-4119-9430-c99375facfbb)

You should see the square with a hole in the center, where your map is located. Now you can use these images to texture the background models in Blender.<br>

</details>

Go to the next section of the tutorial: [Prepare the i3d files](README_i3d.md).