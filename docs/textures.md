## Texture files

Texture files in Farming Simulator maps are used to define the appearance of the terrain. This is crucial to understand how the textures work, if you're going to create a map.

### File description
**Image size:** (map height, map width), the same as the map size. For example, if the map size is 2048x2048, the texture size will be 2048x2048.  
**Channels:** 1  
**Data Type:** uint8  (unsigned 8-bit integer)  
**File Format:** .png  
**File Paths:** `map_directory/data/{texture name}{index}_weight.png`  

### File contents

The values in 8-bit images can range from 0 to 255, but in the meaning of how texturing works, only 0 and 255 values work. That means that in pixels with 0 value, the texture will not appear, and in pixels with 255 value, the texture will be visible.  
If the image is completely black, the texture will not appear at all. If the image is completely white, the texture will be visible everywhere.  
You can see the actual texture scheme in the corresponding files in the repo:
- [FS22 Texture Schema](https://github.com/iwatkot/maps4fs/blob/main/data/fs22-texture-schema.json)
- [FS25 Texture Schema](https://github.com/iwatkot/maps4fs/blob/main/data/fs25-texture-schema.json)

Pay attention to the fact, that FS22 and FS25 use completely different texture schemes and the textures themselves.

### Texture layers

Most of the textures consists of multiple images, for example: `gravel01_weight.png` and `gravel02_weight.png`. This is done to create a more realistic look. The actual in-game look will be a result of merging these images together.  
One more important thing: while in FS25 most of the textures have 2 layers, in FS22 most of the textures have 4 layers.  
And, of course, there are several exceptions from this rule:
- the `waterPuddle` texture from FS22 has only one layer (does not exist in FS25)
- the `forestRockRoots` texture from FS25 has no `weight` postifx in the file name. It's obviously just a bug, but it's still there and I guess it won't be fixed due to compatibility reasons (does not exist in FS22).