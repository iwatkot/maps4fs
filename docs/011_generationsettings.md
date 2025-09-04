# Generation Settings

This document describes the advanced settings available in **maps4fs** - a map generator for Farming Simulator. These settings allow you to fine-tune various aspects of the map generation process to achieve the best results for your specific terrain and requirements.

## DEM (Digital Elevation Model) Settings

These settings control the generation and processing of the DEM map image, which defines the terrain elevation and height data for your map.

### Blur Radius
**Units:** Integer value (pixels)  
DEM blur radius is used to blur the elevation map. Without blurring, the terrain may look too sharp and unrealistic. By default the blur radius is set to 3, which corresponds to a 3x3 pixel kernel. You can increase this value to make the terrain more smooth, or make it smaller to make the terrain more sharp.

![Blur Radius Example](https://github.com/user-attachments/assets/78e18ceb-b5b1-4a9d-b51b-4834effdaf9b)

⚠️ **Note:** This image represents the difference when using low quality DEM data with resolution of 30 meters per pixel. If you're using high quality DEM data, do not use high blur radius values, as it will destroy the details of the terrain.

### Plateau
**Units:** Meters from ground level  
DEM plateau value is used to make the whole map higher or lower. This value will be added to each pixel of the DEM image, making it higher. It can be useful if you're working on a plain area and need to add some negative height (to make rivers, for example).

### Ceiling
**Units:** Meters from the top of highest elevation  
DEM ceiling value is used to add padding in the DEM above the highest elevation in your map area. It can be useful if you plan to manually add some height to the map by sculpting the terrain in Giants Editor.

### Water Depth
**Units:** Meters  
Water depth value will be subtracted from the DEM image, making the water deeper. The pixel value used for this is calculated based on the heightScale value for your map.

![Water Depth Example](https://github.com/user-attachments/assets/22b99071-3169-4c02-9425-1e9fec0e27ec)

⚠️ **Note:** This image represents the difference when using low quality DEM data where there's no data about the water depth. If you're using high quality DEM data, you don't need to use this setting, or it will break the terrain.

### Add Foundations
If enabled, the terrain under buildings will be flattened to their average height.

![Add Foundations Example](https://github.com/user-attachments/assets/51cd6005-6971-49e5-a649-4ea31abac95d)

## Background Terrain Settings

These settings control the generation of background terrain, water planes, and other 3D elements that surround the playable map area.

### Generate Background
If enabled, the obj files for the background terrain will be generated. You can turn it off if you already have those files or don't need them. By default, it's set to True.

### Generate Water
If enabled, the water planes obj files will be generated. You can turn it off if you already have those files or don't need them. By default, it's set to True.

### Water Blurriness
**Units:** Integer value  
Used to reduce the roughness of the water planes. The higher the value, the more flat the surface of the water planes will be. However, too high values can lead to the water planes mesh not matching the terrain.

![Water Blurriness Example](https://i.postimg.cc/2jn8zgpP/water-blurriness.png)

### Flatten Roads
If enabled, the terrain under roads will be flattened. Do not use this option with high quality DTM providers that should already have flattened roads. Otherwise, it may lead to worse results.

![Flatten Roads Example](https://github.com/iwatkot/maps4fsuil/releases/download/2.1.2/flatten_roads.png)

⚠️ **Note:** This image represents the difference when using low quality DEM data with resolution of 30 meters per pixel. If you're using high quality DEM data, do not use this feature, as it may lead to unexpected results.

### Flatten Water
If enabled, the bottom of water resources will be set to the average height of all water resources for the whole map. This option is suitable for maps with water resources that don't differ too much in height. Do not use this option if your map terrain contains big hills or mountains, as it may lead to worse results.

### Remove Center
If enabled, the playable region (map terrain) will be removed from the background terrain. By default, it's set to True.

![Remove Center Example](https://github.com/user-attachments/assets/912864b7-c790-47a9-a001-dd1936d21c17)

## GRLE (Farmland & Vegetation) Settings

These settings control the generation of GRLE files (info layers) for the map, including farmlands, vegetation, and grass distribution.

### Farmland Margin
**Units:** Meters  
This value will be applied to each farmland, making it bigger. You can use this value to adjust how much the farmland should be bigger than the actual field. By default, it's set to 3. It's useful because without the margin, the farmland will end exactly at the same position as the field ends, which can cause gameplay issues.

![Farmland Margin Example](https://github.com/user-attachments/assets/c160bf6d-9217-455b-9655-462dc09b943c)

### Add Grass
If enabled, the tool will add grass to all empty areas (without roads, fields, buildings, etc.). By default, it's set to True.

![Add Grass Example](https://github.com/user-attachments/assets/49c0376a-b83b-46f0-9e25-2f11e03e16c0)

### Random Plants
When adding decorative foliage, enabling this option will add different species of plants to the map. If unchecked, only basic grass (smallDenseMix) will be added. Defaults to True.

![Random Plants Example](https://github.com/user-attachments/assets/e0dae979-21a8-4aa2-8281-ddcdcce3c582)

### Base Grass
You can select which plant will be used as base grass on the map. Note that the default smallDenseMix can be moved but can not be collected after it. If you want to mow the grass outside of the farmlands, select a meadow grass type.

### Add Farmyards
If enabled, the tool will create farmlands from regions marked as farmyards in the OSM data. Those farmlands will not have fields and will not be drawn on textures. By default, it's turned off.

### Base Price
**Units:** In-game currency (EUR or USD)  
The base price of farmland. It's used to calculate the price of farmland in the game. In default in-game maps this value equals 60000.

## I3D Settings

These settings control the generation of the main map I3D files, including trees, objects, and other 3D elements placed within the playable area.

### Add Trees
If enabled, the tool will add trees to the map in areas defined as forests in the OSM data. By default, it's set to True.

![Add Trees Example](https://github.com/user-attachments/assets/50dd8f82-f4f9-411e-a17a-ea10a0b95c20)

### Forest Density
**Units:** Meters between trees  
The density of the forest in meters. The lower the value, the lower the distance between trees, which makes the forest denser. Note that low values will lead to an enormous number of trees, which may cause Giants Editor to crash or lead to performance issues. By default, it's set to 10.

![Forest Density Example](https://github.com/user-attachments/assets/bf353ed6-f25c-4226-b0d6-105ada0f097b)

### Tree Limit
**Units:** Integer value (0 means no limit)  
This value will be used to adjust the forest density value. For example, if it's possible to place 100,000 trees from OSM data, and the forest density is set to 10, the expected number of trees on the map will be 10,000. If you set the tree limit to 5,000, the forest density will be adjusted to 20, meaning the distance between trees will be doubled.

This value is useful to prevent Giants Editor from crashing due to too many trees on the map. By default, it's set to 0 (disabled). Note that it will not lead to the exact number of trees, but will adjust the forest density to fit the tree limit.

## Texture Settings

These settings control the generation and processing of texture files and layers that define the visual appearance of different terrain types.

### Dissolve
If enabled, the values from one layer will be split between different layers of texture, making it look more natural. Warning: this is a time-consuming process. It's recommended to enable it when generating the final version of the map, not test versions.

![Dissolve Example](https://github.com/user-attachments/assets/b7da059b-eb35-4a4e-a656-168c31257b15)

### Fields Padding
**Units:** Meters  
This value will be applied to each field, making it smaller. It's useful when fields are too close to each other and you want to make them smaller. By default, it's set to 0.

![Fields Padding Example](https://github.com/user-attachments/assets/b88ebfb3-7afb-4012-a845-42a04fefa7d2)

### Skip Drains
If enabled, the tool will not generate drains and ditches on the map. By default, it's set to False. Use this if you don't need drains on the map.

### Use Cache
If enabled, the tool will use cached OSM data for generating the map. It's useful when you're generating the same map multiple times and don't want to download OSM data each time. But if you've made changes to the OSM data, you should disable this option to get updated data. By default, it's set to True. This option has no effect when using a custom OSM file.

### Use Precise Tags
If enabled, the tool will use precise tags from the texture schema and will ignore basic tags specified for the texture. With the default schema, this is used for specific types of forests: broadleaved, needleleaved, mixed, etc. Note that if enabled and the object does not have the precise tag, it will not be drawn on the map. By default, it's set to False.

By default the generator will use the `tags` from the texture schema:
```json
"tags": { "natural": ["wood", "tree_row"], "landuse": "forest" }
```

However, if this option is enabled, the generator will use the `precise_tags` instead:
```json
"precise_tags": { "leaf_type": "mixed" }
```

⚠️ **Note:** If an OSM object does not contain the precise tag (e.g., leaf_type), the generator will not draw the texture. Use this feature only if you ensure that the precise tags are present in the OSM data.additional splines will be generated around fields. It may not work for fields partially available on the map.

## Satellite Settings

These settings control the download and processing of satellite imagery used for textures and visual references.

### Download Images
If enabled, the tool will download satellite images for the background terrain and overview image. If you already have the images, you can turn it off.

### Zoom Level
**Units:** Integer value (maximum recommended: 18)  
The zoom level of satellite images. The higher the value, the more detailed the images will be. By default, it's set to 14. Be careful with high values, as they may result in very large images and extremely long download times. This option is disabled in the public version of the app.

