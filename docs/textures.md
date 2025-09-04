# Texture Files

## What Are Texture Files

Texture files in Farming Simulator define **what the terrain looks like** - whether an area appears as grass, dirt, asphalt, gravel, or any other surface material. Understanding how these files work is essential for map creation.

**How It Works**: Each texture uses grayscale images called "weight maps" to control where that specific material appears on your map.

## File Specifications

### Basic Requirements

| Property | Value | Example |
|----------|-------|---------|
| **Image Size** | Same as map size | 2048×2048 map = 2048×2048 texture |
| **Color Type** | Grayscale (1 channel) | Black and white images |
| **File Format** | PNG | Uncompressed PNG files |
| **Data Type** | 8-bit (0-255 values) | Standard image format |
| **File Names** | `{texture_name}{number}_weight.png` | `grass01_weight.png` |
| **Location** | `map_directory/data/` | In your map's data folder |

## How Weight Maps Work

### Simple Black and White Logic

**The Rule**: Even though the files can have values from 0 to 255, in practice only two values matter:

- **Black pixels (0)**: Texture is invisible in this area
- **White pixels (255)**: Texture is fully visible in this area
- **Gray pixels (1-254)**: Rarely used, create partial visibility

**In Practice**: Most texture files are pure black and white for clear, sharp boundaries between different materials.

### Multiple Texture Layers

Most textures use **multiple files** to create realistic variation:

**FS25 Standard**: 2 files per texture
- `grass01_weight.png` + `grass02_weight.png`
- `gravel01_weight.png` + `gravel02_weight.png`

**FS22 Standard**: 4 files per texture
- `dirt01_weight.png` + `dirt02_weight.png` + `dirt03_weight.png` + `dirt04_weight.png`

**Why Multiple Files**: The game blends these together to create more natural-looking surfaces instead of repeating the same pattern.

## Texture Schemas

### Where Textures Come From

Maps4FS automatically creates all these texture files based on **texture schemas** - configuration files that define which textures to use for different map features.

**Important**: FS22 and FS25 use completely different texture schemas and textures.

**Schema Files**:
- **FS25**: [fs25-texture-schema.json](https://github.com/iwatkot/maps4fsdata/blob/main/fs25/fs25-texture-schema.json)
- **FS22**: [fs22-texture-schema.json](https://github.com/iwatkot/maps4fsdata/blob/main/fs22/fs22-texture-schema.json)

### How Generation Works

1. **OSM Data**: Maps4FS reads OpenStreetMap data (roads, fields, forests, etc.)
2. **Schema Mapping**: Each OSM feature gets matched to a texture type
3. **Weight Maps**: Black and white images are created showing where each texture appears
4. **File Export**: All texture weight files are saved to your map's data folder

## Special Cases

### Texture Exceptions

**FS22 Only**:
- `waterPuddle` texture has only 1 file instead of 4
- This texture doesn't exist in FS25

**FS25 Only**:
- `forestRockRoots` files don't have `_weight` in their names
- Files are named `forestRockRoots01.png` instead of `forestRockRoots01_weight.png`
- This is likely a bug, but it's maintained for compatibility

### Version Differences

**Cannot Mix Versions**: FS22 texture files won't work in FS25 maps and vice versa. Each game version has its own texture system and naming.

## Working with Texture Files

### What Maps4FS Does for You

**Automatic Generation**: Maps4FS creates all the texture weight files you need automatically. You don't need to create them manually.

**Complete Set**: You'll get all the necessary texture files for your map based on the OpenStreetMap data in your area.

### File Validation

**Check Your Files**:
- All texture files should be the same size as your map
- Files should be grayscale PNG format
- Black and white pixels should be clear and sharp
- File names should follow the `{texture}{number}_weight.png` pattern

### Common Issues

**Missing Textures**: If some areas look wrong, it's usually because the OpenStreetMap data for your area is incomplete. You can improve this by editing the OSM data for your region.

**Wrong File Sizes**: All texture files must exactly match your map dimensions. A 2048×2048 map needs 2048×2048 texture files.