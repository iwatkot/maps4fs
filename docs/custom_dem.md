## How to create a custom DEM file
If you got a better data model you might want to create your own DEM file for your generated map. Here are some steps that will help you to create a perfect matching DEM file for your generated map.

### Requirements
1. Knowledge about DEM - Learn how [DEM](dem.md) works and what it is.
2. GeoTiff files that cover your map size. There might be some public websites or local services that provide these for your area.
3. QGIS software - Download from their [official website](https://qgis.org/download/).
    * Follow steps 1-5 from [How to download satellite images using QGIS](download_satellite_images.md) to setup QGIS with the QuickMapServices plugin.
4. Raster graphics editing software. I will use GIMP in this guide, because it is free. But other tools like Photoshop might be easier to use. Choose the tool that you are familiar with.
5. Your existing FS map files.


### Create the DEM file
1. Open QGIS and select a map as background layer (**Web** -> **QuickMapServices**) to have some orientation, preferable **OSM Standard** or **Google Hybrid**.
![Google Satellite](https://github.com/user-attachments/assets/944e7ffa-c8e8-4e8f-a2f6-ec48855ac822)
2. If you only have a single GeoTiff file, you can skip to step 3. Most likely you will have multiple GeoTiff files, which we have to merge together.
    * Drag and drop all GeoTiff files into QGIS. They should appear on the map.
    * Click on `Raster -> Miscellaneous -> Merge...`
    
    ![Raster merge menu](https://github.com/user-attachments/assets/1db61213-40d2-4c45-9058-180bfc68f394)

    Click the three dots next to `Input layers`. Click on `Select all` and **remove** the tick from your base map layer. Click on `Run` and wait until the process is complete.
   
    ![Raster merge settings](https://github.com/user-attachments/assets/42764ceb-cec8-4ee4-b600-ae6b496eb9bc) ![Raster merge settings2](https://github.com/user-attachments/assets/70e34aff-0455-4232-a80d-2c63bfcc7b83)

    You will see the new layer called "Merged" on the left side. To keep your project clean, you can remove all layers except the "Merged" and base map layer.
    * Right click the "Merged" layer and select `Export -> Save As...`. Click on the three dots next to the file name and select a location where you want to store the GeoTiff file. Make sure the `Extent` is set to the **Merged** layer. Remove the tick from the `Add saved file to map` checkbox and click on `Ok`. This will create a single GeoTiff file from this **Merged** layer.

   ![Export GeoTiff menu](https://github.com/user-attachments/assets/381c4afe-55a2-4c43-ad7d-550a0f8746db) ![Export GeoTiff settings](https://github.com/user-attachments/assets/d4f489ab-b14b-4a9e-a951-b8ae5b0d46ce)

   
3. Open maps4fs and go to "Modder Toolbox -> Textures and DEM"
    * Upload your single/merged GeoTiff file
    * Enter the center coordinates of your map
    * Enter the size of the ROI which should be the size of your map or background if you want to create the DEM for your background too. Add some additional meters to have some space to rotate and resize the image later.
    E.g.: For a 2048x2048m map with 4096x4096m background, I choose 5000 meters
    * Click on "Extract ROI" and "Download" once the process has finished.

    ![Modder Toolbox Windowing](https://github.com/user-attachments/assets/4de23e0b-ffa8-4ca4-923e-4e4cd47b7f57)

4. Drag and drop this new GeoTiff file (named "windowed" from now on in this guide) into QGIS. Make sure that the "windowed" layer is the top layer and hide or remove the "Merged" layer from step 4.
5. Check the layer menu and note down both numbers from the "windowed" layer. These are the lowest and highest points in this area. We will need those numbers in the next step. 

   ![Layer height values](https://github.com/user-attachments/assets/2b266df5-81a0-4f2d-8218-2855d055ba4f)

6. Convert the layer to a PNG image (**Raster** -> **Conversion** -> **Translate (Convert Format)...**). Select the **windowed layer** as `Input layer`. Set `-scale MIN MAX 0 65535 -outsize WIDTH HEIGHT` as `Additional command-line parameters`. Replace MIN, MAX, WIDTH & HEIGHT with your values:

   * **MIN** should be below the lower value from the previous step.
   * **MAX** should be above the higher value from the previous step. 
   * You can set the range (**MIN**, **MAX**) as you like, but make sure it covers both values from the previous step. The difference between **MIN** and **MAX** will be your Height scale. You have to set this value in your map.i3d file, which will be covered in step 10. More about the Height scale is described in the [Height scale section in Digital Elevation Models (DEM)](dem.md#height-scale).
   * **WIDTH** & **HEIGHT** is the value you've set as size of ROI from step 3.

   Set **UInt16** as `Output data type`. Click the three dots next to `Converted` and select a location where you want to store your PNG. Make sure to select PNG as file type and choose the right filename ending. Remove the tick from `Open output file after running algorithm` checkbox.

   Click on `Run` and wait until the process is complete. Check the log file for **Input file size is X, Y**. If those values are much lower as your set **WIDTH** & **HEIGHT** you might get better results when using lower **WIDTH** & **HEIGHT** values and upscaling the generated image afterwards. Make sure to preserve the 16bit Grayscale format!

   ![Translate menu](https://github.com/user-attachments/assets/140807a6-2338-4ca6-9eeb-2eccdbb6dfbb) ![Convert PNG config](https://github.com/user-attachments/assets/63e0828b-43ea-43fc-ae0f-4b638a7c2900)
 ![Convert PNG log](https://github.com/user-attachments/assets/82aed77a-f19f-415d-be48-5c17651bbe02)

7. This step is optional, but it is highly recommended because it helps a lot in the following step. In the **Windowed PNG** file it is hard to see structures like roads, fields and so on. Therefore, create a Hillshade of your "windowed" layer (**Raster** -> **Analysis** -> **Hillshade...**). Select your "windowed" layer as `Input layer`, tick the `Compute edges` checkbox and click `Run`. Convert the new Hillshade layer to PNG the same way as the windowed layer in the previous step, but remove the **-scale MIN MAX** part from `Additional command-line parameters` and set **Use Input Layer Data Type** as `Output data type`.

   ![Hillshade menu](https://github.com/user-attachments/assets/aa7122d3-fd46-46ce-91dd-842aeed24d97) ![Create Hillshade settings](https://github.com/user-attachments/assets/0045187e-0816-418d-be40-fff3d8004ecb) ![Hillshade PNG config](https://github.com/user-attachments/assets/85482ecf-4eb0-404f-8efa-c79f741518cc)

8. Now comes the tricky part. We have to resize/rotate the PNG image to exactly fit to our FS map.
    * Create a new image in GIMP (**File** -> **New...**) with the required DEM width and height for your map. If you wish, it can also contain your background, which we will later cut to fit the main map only. E.g.: In FS25 a 2048x2048m map requires a DEM file, that has 2049x2049 pixels. As I also want to create the background from that DEM I choose 4096x4096 pixels. You can learn more about DEM sizes in [Digital Elevation Models (DEM)](dem.md#height-scale). Expand the `Advanced Options` and select **Grayscale** as `Color space` with a `Precision` of **16-bit integer**.

      ![Create new image](https://github.com/user-attachments/assets/8bc88882-4939-4e86-93fb-f6529c25c0fd)

    * Go into your FS map -> data folder and select any image that contains a lot of data. Preferably the layer that contains your roads or your fields as they might the easiest to align our image to. E.g.: `asphaltDusty01_weight.png`. Import this image to GIMP and make sure it sits perfectly in the center. You could even lock the layer to make sure you do not move it by accident.
    * Import your PNG file(s) from step 6 (and 7) into GIMP. Make sure these layers are on top. Set the opacity to around 50% so that the `asphaltDusty01_weight` layer underneath is visible.
   
         ![Set opacity](https://github.com/user-attachments/assets/a4a24bd7-44a6-4f2a-857f-f851a70af211)
    
        Windowed PNG file only from step 6:
        * Rotate and resize your **Windowed PNG layer** until its structures matches to the `asphaltDusty01_weight` layer. If it is to hard to see the structure of the PNG layer, you might want to consider creating the Hillshade in step 7.
        
        Windowed PNG and Hillshade from step 6 and 7:
        * Hide the **Windowed PNG layer** to focus on the **Hillshade layer**.
        * Rotate (**Layer** -> **Transform** -> **Arbitrary Rotation...**) and resize (**Layer** -> **Scale layer**) your **Hillshade layer** until its structures matches to the `asphaltDusty01_weight` layer. Note down the number of rotation, because you won't be able to get this number later again in GIMP (as far as I've seen). However the layer width & height and offset can be seen at any time. Width & height can be found while resizing and the offset can be found when right-clicking the layer and selecting  `Edit Layer Attributes`
        * Once you've fitted the **Hillshade** perfectly you have to do the exact same changes to the **Windowed PNG layer**. Copy the rotation, width, height and offset from the **Hillshade** to the **Windowed PNG layer**

         ![Rotate & resize the image](https://github.com/user-attachments/assets/4d93f76e-970f-47bb-8f32-ba5949db9aa7)

    * Make sure the **Windowed PNG layer** is the top layer and set it's opacity back to 100%.
    * Save the Project file in case you want to make changes in the future if it doesn't fit as perfect as you'd liked it to be.
    * Export as PNG file (**File** -> **Export As...**). Make sure the profile is set to 16 bit integer Grayscale!
    * If your file also contains your background, you have to change the canvas size to your required DEM size. (**Image** -> **Canvas size...**). Do **not** use "Scale image" because this would scale down the whole image, but we only need the inner part of it.

      Make sure to hit `Center` after you set the required pixels, to get the exact center of your image.

      ![Change Canvas size](https://github.com/user-attachments/assets/4e20e4e2-d565-4b9b-86c2-c59c85e65793)

      Export the PNG (**File** -> **Export As...**) as `dem.png`.
9. And now you got your final dem file for your map. Replace it with your existing `dem.png` in the FS **map -> data** folder.
10. You have to set the proper Height scale from step 6 to your map.i3d. Either edit your map.i3d file or change the terrain in the Giants Editor.
![Map.i3d Height scale](https://github.com/user-attachments/assets/bc8d5a9b-e4a6-4fed-b591-dcabc1af2b14)![Giants Editor Height scale](https://github.com/user-attachments/assets/64f10e5b-4a6f-438e-b426-f1cbcf9c6bc1)

