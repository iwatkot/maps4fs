## How to use splines?

After generation you'll see the `splines.i3d` file right next to the main map file. This file contains all the splines, that were extracted from the OSM data in ROI (region of interest).  

1. Add splines to the map. To add them you just need to click **File** -> **Import** and select the `splines.i3d` file and they should appear in the Giants Editor.
2. If the roads were convering all the region, then you probably won't need to translate they by X and Y axes. Because in this case the center of all splines will be the center of the map. But, if at least on one edge of the map were to roads, you probably will need to translate them.
3. It's recommended to create a TransformGroup for the splines. Just select all the splines, right click on them and select **Create Group**. This will allow you to transform all the splines at once (translate, rotate, scale).
4. Once you aligned splines by X and Y axes, you can start to align them by Z axis. Note that in Giants Editor the Z axis (height) is called Y axis, so we're talking about the height here.
5. You'll probably need to use Transform Y (Z) and Scale Y (Z) tools to align the splines by height.
6. Once your splines finally aligned you can use them for different purposes.

### Use splines for AI auto-drive

1. Select all the splines.
2. Create a new TransformGroup for them.
3. Select the TransformGroup, open **Attributes** panel, go to **User attributes** tab and add a new attribute as on the screenshot below. This attribute will be used to store the spline type.  
Select **Script callback**, enter **onCreate** as name and click **Add**. Then add **AISystem.onCreateAIRoadSpline** as a value.

![User attribute](https://github.com/user-attachments/assets/7602f8ff-bcbe-4abc-b360-487f0b6a6d55)