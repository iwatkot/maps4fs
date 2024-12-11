## Map Structure
In this section, we will discuss the structure of the map files and directories after using the generator.<br>
The name of the archive (folder) but default contains the following information:
- FS25: Game name (Farming Simulator 25 or Farming Simulator 22)
- Latitude: Latitude of the center of the map (45.28571)
- Longitude: Longitude of the center of the map (20.23743)
- Date: Date of the map creation (2024-12-10)
- Time: Time of the map creation (23-43-55)

### Background
This directory contains components for creating the background terrain of the map. PNG images are just DEM files and the OBJ files were generated based on these DEM files. You can safely remove the PNG files if you don't need them.<br>
The background directory contains of tiles, representing the cardinal directions (N, NE, E, SE, S, SW, W, NW) and the full tile. If you want to combine the background terrain from pieces, you can use them, or you can use the full tile for the whole map (in this case you probably need to cut out the center for the actual terrain).

### Info Layers
Thid directory mostly for internal use to store some data between different components. At the moment only one component - `Texture` stores here the generation data in JSON format.<br>
At the moment, it's completely safe to remove this directory if you don't need to store any generation data.

#### textures.json
This file contains a list of textures which associated with InfoLayers, so at the moment it's only for fields. It's a simple lists of coordinates of Polygons which represents the field on maps. This list is being used by the `I3d` component to generate the actual fields in the map.

```json
{
    "fields": [
        [
            [
                458,
                580
            ],
            [
                390,
                758
            ],
        ...
        ]
    ...
    ]
...
}
```
This file can be safely removed if you don't need to generate fields on the map.

### Map
This directory contains the actual map files. Let's talk about each component in more details.

#### Config
This directory contains XML files for the map configuration. We won't cover all of them here, but here are the most important one:<br>

`farmLands.xml`: Contains the information about the farm lands on the map.<br>
You MUST fill out this file with data corresponding to the `farmlands` InfoLayer in Giants Editor, otherwise you won't be able yo buy the lands in the game.<br>

```xml
    <farmlands infoLayer="farmlands" pricePerHa="60000">
        <farmland id="1" priceScale="1" npcName="FORESTER" />
        <farmland id="2" priceScale="1" npcName="GRANDPA" />
    </farmlands>
```

So, the keys here are kinda obvious, if you want to change the global price for the lands, you can do it in the `pricePerHa` attribute. The `farmland` tag contains the information about the lands. The `id` attribute is the ID of the land, the `priceScale` is the multiplier for the price of the land, and the `npcName` is the name of the NPC who owns the land.

### Data
This is the most important directory in the map structure. It contains all the textures, DEM and InfoLayer images. Basically, if any file is missing here, the map will crash when try opening it in the Giants Editor.<br>

#### Texture weight files
Those files represent the textures on the map, read more about them in the [Textures](./textures.md) section.

#### InfoLayer images
Those images represent the InfoLayers on the map, such as fields, farmlands, etc. Actually, you don't need to know anything about the files themvselves, since the generator will handle them for you, but you definetely need to edit those InfoLayers in the Giants Editor at least to create the [FarmLands](./farmlands.md).

```text
📦FS25_45_28571_20_23743_2024-12-10_23-43-55
 ┣ 📂background
 ┃ ┣ 📄E.obj
 ┃ ┣ 📄E.png
 ┃ ┣ 📄FULL.obj
 ┃ ┣ 📄FULL.png
 ┃ ┣ 📄N.obj
 ┃ ┣ 📄N.png
 ┃ ┣ 📄NE.obj
 ┃ ┣ 📄NE.png
 ┃ ┣ 📄NW.obj
 ┃ ┣ 📄NW.png
 ┃ ┣ 📄S.obj
 ┃ ┣ 📄S.png
 ┃ ┣ 📄SE.obj
 ┃ ┣ 📄SE.png
 ┃ ┣ 📄SW.obj
 ┃ ┣ 📄SW.png
 ┃ ┣ 📄W.obj
 ┃ ┗ 📄W.png
 ┣ 📂info_layers
 ┃ ┗ 📄textures.json
 ┣ 📂map
 ┃ ┣ 📂config
 ┃ ┃ ┣ 📄aiSystem.xml
 ┃ ┃ ┣ 📄collectibles.xml
 ┃ ┃ ┣ 📄colorGrading.xml
 ┃ ┃ ┣ 📄colorGradingNight.xml
 ┃ ┃ ┣ 📄environment.xml
 ┃ ┃ ┣ 📄farmlands.xml
 ┃ ┃ ┣ 📄fieldGround.xml
 ┃ ┃ ┣ 📄fields.xml
 ┃ ┃ ┣ 📄footballField.xml
 ┃ ┃ ┣ 📄handTools.xml
 ┃ ┃ ┣ 📄items.xml
 ┃ ┃ ┣ 📄pedestrianSystem.xml
 ┃ ┃ ┣ 📄placeables.xml
 ┃ ┃ ┣ 📄storeItems.xml
 ┃ ┃ ┣ 📄trafficSystem.xml
 ┃ ┃ ┣ 📄vehicles.xml
 ┃ ┃ ┗ 📄weed.xml
 ┃ ┣ 📂data
 ┃ ┃ ┣ 📄asphalt01_weight.png
 ┃ ┃ ┣ 📄asphalt02_weight.png
 ┃ ┃ ┣ 📄asphaltCracks01_weight.png
 ┃ ┃ ┣ 📄asphaltCracks02_weight.png
 ┃ ┃ ┣ 📄asphaltDirt01_weight.png
 ┃ ┃ ┣ 📄asphaltDirt02_weight.png
 ┃ ┃ ┣ 📄asphaltDusty01_weight.png
 ┃ ┃ ┣ 📄asphaltDusty02_weight.png
 ┃ ┃ ┣ 📄asphaltGravel01_weight.png
 ┃ ┃ ┣ 📄asphaltGravel02_weight.png
 ┃ ┃ ┣ 📄asphaltTwigs01_weight.png
 ┃ ┃ ┣ 📄asphaltTwigs02_weight.png
 ┃ ┃ ┣ 📄concrete01_weight.png
 ┃ ┃ ┣ 📄concrete02_weight.png
 ┃ ┃ ┣ 📄concreteGravelSand01_weight.png
 ┃ ┃ ┣ 📄concreteGravelSand02_weight.png
 ┃ ┃ ┣ 📄concretePebbles01_weight.png
 ┃ ┃ ┣ 📄concretePebbles02_weight.png
 ┃ ┃ ┣ 📄concreteShattered01_weight.png
 ┃ ┃ ┣ 📄concreteShattered02_weight.png
 ┃ ┃ ┣ 📄dem.png
 ┃ ┃ ┣ 📄densityMap_fruits.gdm
 ┃ ┃ ┣ 📄densityMap_ground.gdm
 ┃ ┃ ┣ 📄densityMap_groundFoliage.gdm
 ┃ ┃ ┣ 📄densityMap_height.gdm
 ┃ ┃ ┣ 📄densityMap_stones.gdm
 ┃ ┃ ┣ 📄densityMap_weed.gdm
 ┃ ┃ ┣ 📄forestGrass01_weight.png
 ┃ ┃ ┣ 📄forestGrass02_weight.png
 ┃ ┃ ┣ 📄forestLeaves01_weight.png
 ┃ ┃ ┣ 📄forestLeaves02_weight.png
 ┃ ┃ ┣ 📄forestNeedels01_weight.png
 ┃ ┃ ┣ 📄forestNeedels02_weight.png
 ┃ ┃ ┣ 📄forestRockRoots01.png
 ┃ ┃ ┣ 📄forestRockRoots02.png
 ┃ ┃ ┣ 📄grass01_weight.png
 ┃ ┃ ┣ 📄grass01_weight_preview.png
 ┃ ┃ ┣ 📄grass02_weight.png
 ┃ ┃ ┣ 📄grassClovers01_weight.png
 ┃ ┃ ┣ 📄grassClovers02_weight.png
 ┃ ┃ ┣ 📄grassCut01_weight.png
 ┃ ┃ ┣ 📄grassCut02_weight.png
 ┃ ┃ ┣ 📄grassDirtPatchy01_weight.png
 ┃ ┃ ┣ 📄grassDirtPatchy01_weight_preview.png
 ┃ ┃ ┣ 📄grassDirtPatchy02_weight.png
 ┃ ┃ ┣ 📄grassDirtPatchyDry01_weight.png
 ┃ ┃ ┣ 📄grassDirtPatchyDry02_weight.png
 ┃ ┃ ┣ 📄grassDirtStones01_weight.png
 ┃ ┃ ┣ 📄grassDirtStones02_weight.png
 ┃ ┃ ┣ 📄grassFreshMiddle01_weight.png
 ┃ ┃ ┣ 📄grassFreshMiddle02_weight.png
 ┃ ┃ ┣ 📄grassFreshShort01_weight.png
 ┃ ┃ ┣ 📄grassFreshShort02_weight.png
 ┃ ┃ ┣ 📄grassMoss01_weight.png
 ┃ ┃ ┣ 📄grassMoss02_weight.png
 ┃ ┃ ┣ 📄gravel01_weight.png
 ┃ ┃ ┣ 📄gravel02_weight.png
 ┃ ┃ ┣ 📄gravelDirtMoss01_weight.png
 ┃ ┃ ┣ 📄gravelDirtMoss02_weight.png
 ┃ ┃ ┣ 📄gravelPebblesMoss01_weight.png
 ┃ ┃ ┣ 📄gravelPebblesMoss02_weight.png
 ┃ ┃ ┣ 📄gravelPebblesMossPatchy01_weight.png
 ┃ ┃ ┣ 📄gravelPebblesMossPatchy02_weight.png
 ┃ ┃ ┣ 📄gravelSmall01_weight.png
 ┃ ┃ ┣ 📄gravelSmall02_weight.png
 ┃ ┃ ┣ 📄infoLayer_environment.png
 ┃ ┃ ┣ 📄infoLayer_farmlands.png
 ┃ ┃ ┣ 📄infoLayer_fieldType.png
 ┃ ┃ ┣ 📄infoLayer_indoorMask.png
 ┃ ┃ ┣ 📄infoLayer_limeLevel.png
 ┃ ┃ ┣ 📄infoLayer_navigationCollision.png
 ┃ ┃ ┣ 📄infoLayer_placementCollision.png
 ┃ ┃ ┣ 📄infoLayer_placementCollisionGenerated.png
 ┃ ┃ ┣ 📄infoLayer_plowLevel.png
 ┃ ┃ ┣ 📄infoLayer_rollerLevel.png
 ┃ ┃ ┣ 📄infoLayer_sprayLevel.png
 ┃ ┃ ┣ 📄infoLayer_stubbleShredLevel.png
 ┃ ┃ ┣ 📄infoLayer_tipCollision.png
 ┃ ┃ ┣ 📄infoLayer_tipCollisionGenerated.png
 ┃ ┃ ┣ 📄infoLayer_weed.png
 ┃ ┃ ┣ 📄mudDark01_weight.png
 ┃ ┃ ┣ 📄mudDark01_weight_preview.png
 ┃ ┃ ┣ 📄mudDark02_weight.png
 ┃ ┃ ┣ 📄mudDarkGrassPatchy01_weight.png
 ┃ ┃ ┣ 📄mudDarkGrassPatchy02_weight.png
 ┃ ┃ ┣ 📄mudDarkMossPatchy01_weight.png
 ┃ ┃ ┣ 📄mudDarkMossPatchy02_weight.png
 ┃ ┃ ┣ 📄mudLeaves01_weight.png
 ┃ ┃ ┣ 📄mudLeaves02_weight.png
 ┃ ┃ ┣ 📄mudLight01_weight.png
 ┃ ┃ ┣ 📄mudLight01_weight_preview.png
 ┃ ┃ ┣ 📄mudLight02_weight.png
 ┃ ┃ ┣ 📄mudPebbles01_weight.png
 ┃ ┃ ┣ 📄mudPebbles02_weight.png
 ┃ ┃ ┣ 📄mudPebblesLight01_weight.png
 ┃ ┃ ┣ 📄mudPebblesLight02_weight.png
 ┃ ┃ ┣ 📄mudTracks01_weight.png
 ┃ ┃ ┣ 📄mudTracks02_weight.png
 ┃ ┃ ┣ 📄pebblesForestGround01_weight.png
 ┃ ┃ ┣ 📄pebblesForestGround02_weight.png
 ┃ ┃ ┣ 📄rock01_weight.png
 ┃ ┃ ┣ 📄rock02_weight.png
 ┃ ┃ ┣ 📄rockFloorTiles01_weight.png
 ┃ ┃ ┣ 📄rockFloorTiles02_weight.png
 ┃ ┃ ┣ 📄rockFloorTilesPattern01_weight.png
 ┃ ┃ ┣ 📄rockFloorTilesPattern02_weight.png
 ┃ ┃ ┣ 📄rockForest01_weight.png
 ┃ ┃ ┣ 📄rockForest02_weight.png
 ┃ ┃ ┣ 📄rockyForestGround01_weight.png
 ┃ ┃ ┣ 📄rockyForestGround02_weight.png
 ┃ ┃ ┣ 📄sand01_weight.png
 ┃ ┃ ┣ 📄sand01_weight_preview.png
 ┃ ┃ ┣ 📄sand02_weight.png
 ┃ ┃ ┗ 📄unprocessedHeightMap.png
 ┃ ┣ 📄map.i3d
 ┃ ┣ 📄map.i3d.shapes
 ┃ ┣ 📄map.xml
 ┃ ┗ 📄overview.dds
 ┣ 📂previews
 ┃ ┣ 📄background_dem.png
 ┃ ┣ 📄background_dem.stl
 ┃ ┣ 📄dem_colored.png
 ┃ ┣ 📄dem_grayscale.png
 ┃ ┗ 📄textures_osm.png
 ┣ 📂scripts
 ┃ ┣ 📄background_bbox.py
 ┃ ┣ 📄background_point.py
 ┃ ┣ 📄background_rasterize.py
 ┃ ┣ 📄config_bbox.py
 ┃ ┣ 📄config_point.py
 ┃ ┗ 📄config_rasterize.py
 ┣ 📄generation_info.json
 ┣ 📄icon.dds
 ┣ 📄modDesc.xml
 ┗ 📄preview.dds
```