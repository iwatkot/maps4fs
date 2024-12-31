## How to create a custom DEM file
If you got a better data model you might want to create your own DEM file for your generated map. Here are some steps that will help you to create a perfect matching DEM file for your generated map.

### Requirements
1. GeoTiff files that cover your map size
2. QGIS software - Download from their [official website](https://qgis.org/download/)
    * Follow steps 1-5 from [How to download satellite images using QGIS](download_satellite_images.md) to setup QGIS with the QuickMapServices plugin
3. Raster graphics editing software. I will use GIMP in this tutorial, because it is free. But other tools like Photoshop might be easier to use. Choose the tool that you are familiar with.
4. Your existing FS map


### Create the DEM file
1. Open QGIS and select a map as background layer (Web -> QuickMapServices) to have some orientation, preferable **OSM Standard** or **Google Hybrid**.
![Google Satellite](https://github.com/user-attachments/assets/944e7ffa-c8e8-4e8f-a2f6-ec48855ac822)
2. If you only have a single GeoTiff file, you can skip to step 3. Most likely you will have multiple GeoTiff files, which we have to merge together.
    * Drag and drop all GeoTiff files into QGIS. They should appear on the map.
    * Click on `Raster -> Miscellaneous -> Merge...`
    [TODO: Add image]
    Click the three dots at `Input layers`. Click `Select all` and **uncheck** your base map layer. Click on `Run` and wait until the process has finished.
    [TODO: Add image][TODO: Add image]
    You will see the new layer called "Merged" on the left side. To keep your project clean you can remove all layers except the "Merged" and base map layer.
    * Right click the "Merged" layer and select `Export -> Save As...`. Click on the three dots at file name and select a location where you want to store the GeoTiff file. Make sure the `Extent` is set to the **Merged** layer. Untick the `Add saved file to map` checkbox and click `Ok`. This will create a single GeoTiff file from this **Merged** layer.
3. Open maps4FS and go to "Modder Toolbox -> Textures and DEM"
    * Upload your single/merged GeoTiff file
    * Enter the center coordinates of your map
    * Enter the size of the ROI which should be the size of your map or background if you want to create the DEM for your background too. Add some additional meters to have some space to rotate and resize the image later.
    E.g.: For a 2048x2048m map with 4096x4096m background, I choose 5000 meters
    * Click on "Extract ROI" and "Download" once the process has finished.
    [TODO: Add image]
4. Drag and drop this new GeoTiff file (named "windowed" from now on in this guide) into QGIS. Make sure that the "windowed" layer is the top layer and hide or remove the "Merged" layer from step 4.
5. Right click the "windowed" layer, select `Properties...` and go to `Symbology`. Note down the **Min** and **Max** value from `Color gradient`. You should round down the min value and round up the max value to the next integer value. The difference between these two values will be your Height scale. You have to set this value in your map.i3d file. More about the Height scale is described in the [Height scale section in Digital Elevation Models (DEM)](dem.md#height-scale). 
[TODO: Add image]
6. Export the layer as a PNG image (File -> Import/Export -> Export Map to Image). Select the windowed layer in the Extent section. Increase the resolution to a value where the pixels would be enough to cover your desired size. **Do not touch the `Output width` and `Output height` numbers!** Only adjust the resolution. Click `Save` and select a location to save the PNG image (named **Windowed PNG** further on).
7. This step is optional, but it is highly recommended because it helps a lot in the following step. In the **Windowed PNG** file it is pretty hard to see structures like roads, fields, and so on. Therefore, create a Hillshade of your "windowed" layer (**Raster** -> **Analysis** -> **Hillshade...**). Select your "windowed" layer as `Input layer`, tick the `Compute edges` checkbox and click `Run`. Export the new Hillshade layer the same way as the windowed layer in the previous step.
[TODO: Add image][TODO: Add image]
8. Now comes the tricky part. We have to resize/rotate the PNG image to exactly fit to our FS map.
    * Create a new image in GIMP (**File** -> **New...**) with the required DEM width and height for your map. If you want it can also contain your background and we will crop it to the main map later. E.g.: In FS25 a 2048x2048m map requires a DEM file, that has 2049x2049 pixels. As I also want to create the background from that DEM I choose 4096x4096 pixels. You can learn more about DEM sizes in [Digital Elevation Models (DEM)](dem.md#height-scale). Expand the `Advanced Options` and select **Grayscale** as `Color space` with a `Precision` of **16-bit integer**.
    [TODO: Add image]
    * Go into your FS map -> data folder and select any image that contains a lot of data. Preferably the layer that contains your roads or your fields as they might the easiest to align our image to. E.g.: `asphaltDusty01_weight.png`. Import this image to GIMP and make sure it sits perfectly in the center. You could even lock the layer to make sure you do not move it by accident.
    * Import your PNG file(s) from step 6 (and 7) into GIMP. Make sure these layers are on top. Set the opacity to about 50%, in order to see the underlying `asphaltDusty01_weight` layer. [TODO: Add image]
    
        Windowed PNG file only from step 6:
        * Rotate and resize your **Windowed PNG layer** until its structures matches to the `asphaltDusty01_weight` layer. If it is to hard to see the structure of the PNG layer, you might want to consider creating the Hillshade in step 7.
        
        Windowed PNG and Hillshade from step 6 and 7:
        * Hide the **Windowed PNG layer** to focus on the **Hillshade layer**.
        * Rotate (**Layer** -> **Transform** -> **Arbitrary Rotation...**) and resize (**Layer** -> **Scale layer**) your **Hillshade layer** until its structures matches to the `asphaltDusty01_weight` layer. Note down the number of rotation, because you won't be able to get this number later again in GIMP (as far as I've seen). However the layer width & height and offset can be seen at any time. 
        * Once you've fitted the **Hillshade** perfectly you have to do the exact same changes to the **Windowed PNG layer**. Copy the rotation, width, height and offset from the **Hillshade** to the **Windowed PNG layer**
        [TODO: Add image]

    * Make sure the **Windowed PNG layer** is the top layer and set it's opacity back to 100%.
    * Save the Project file in case you want to make changes in the future if it doesn't fit as perfect as you'd liked it to be.
    * Export as PNG file (**File** -> **Export As...**). Make sure the profile is set to 16 bit integer Grayscale!
    * If your file also contains your background, you have to change the canvas size to your required DEM size. (**Image** -> **Canvas size...**). Do **not** use "Scale image" because this would scale down the whole image, but we only need the inner part of it.

        Make sure to hit `Center` after you set the required pixels, to get the exact center of your image.
        [TODO: Add image]
        
        Export the PNG (**File** -> **Export As...**) as `dem.png`.
9. And now you got your final dem file for your map. Replace it with your existing `dem.png` in the FS **map -> data** folder.
10. You have to set the proper Height scale from step 5 to your map.i3d. Either edit your map.i3d file or change the terrain in the Giants Editor.
[TODO: Add image]
11. Open the map in the Giants Editor and smooth the "steps" using the `Terrain sculpt mode`
[TODO: Add image]
