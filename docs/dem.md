## Digital Elevation Models (DEM)
DEM is used in Farming Simulator maps to define the terrain height.  
Every hill, valley, and slope is defined by a DEM. While it may sounds complex, it's really just a 2D grid where each cell has a height value.
### File description
**Image size:** FS25 -> (map height + 1, map width + 1) FS22 -> (map height / 2 + 1, map width / 2 + 1)  
**Channels:** 1  
**Data Type:** uint16  (unsigned 16-bit integer)  
**File Format:** .png  
**File Path:** FS25 -> `map_directory/data/dem.png` FS22 -> `map_directory/data/map_dem.png`  
DEM image is a single channel unsigned 16-bit integer image, which means that each pixel can have an integer value between 0 and 2^16 (65535). So, if the image can have values from 0 to 65535, while the highest point on Earth is 8848 meters, how does it work?
### Height scale
And this, where the **heightScale** parameter comes in. It's a multiplier that converts the pixel value to it's in-game height.  By default, in Giants maps, it's value set to 255, but if you're working with DEMs, which contains real-world height values, you should make it much higher. The selection of the actual value is up to you, you can play around with it to get the best result.  
To set this value, you need to open the map.i3d file in Giants Editor, select the terrain on the **Scenegraph** tab, choose **Terrain** tab in the **Attributes** window, and set the **heightScale** parameter. After it you usually need to save the file and reload the map (**File** -> **Reload**).
### Units per pixel
In Farming Simulator 25 the size of the DEM image is usually the same as the map size but with an additional pixel in each dimension. For example, if the map size is 2048x2048, the DEM image size will be 2049x2049. But in Farming Simulator 22 the DEM image size is half of the map size. So, if the map size is 2048x2048, the DEM image size will be 1025x1025.  
But actually, it can be changed using the **unitsPerPixel** parameter in the map.i3d file. It defines how many in-game units (meters) each pixel of the DEM image represents. So, in the FS25 by default, it's set to 1, which means that each pixel of the DEM image represents 1 meter in the game. But in FS22 it's set to 2, and that's why the DEM image size is half of the map size.  
To set this value, you need to open the map.i3d file in Giants Editor, select the terrain on the **Scenegraph** tab, choose **Terrain** tab in the **Attributes** window, and set the **unitsPerPixel** parameter. Just a reminder, it should be an integer value. After it you usually need to save the file and reload the map (**File** -> **Reload**).