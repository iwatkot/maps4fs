# Road Generation

maps4fs now includes automatic road generation from OpenStreetMap (OSM) data. Roads are generated as 3D meshes with proper UV mapping and texture application.

## Overview

The road generation system:
- Extracts road data from OSM based on texture schema configuration
- Creates 3D meshes with proper geometry and UV mapping
- Handles T-junctions automatically with patch generation
- Splits long roads to comply with Giants Engine UV coordinate limits
- Supports custom textures for different road types

## Configuration

### Texture Schema

Road generation is configured in the texture schema file (e.g., `fs25-texture-schema.json`). Add the `road_texture` property to any texture entry that should generate roads:

```json
{
  "name": "asphalt",
  "tags": {
    "highway": ["residential"]
  },
  "width": 6,
  "road_texture": "asphalt-white"
}
```

**Key Properties:**
- `road_texture`: Name of the texture file (without extension) to use for the road mesh
- `width`: Road width in meters (half-width from center line)
- `tags`: OSM tags that identify which roads should use this texture
- `info_layer`: Must be set to `"roads"` for road generation

### Texture Files

The generator searches for texture files in the `templates/` directory with the following supported formats:
- **DDS** (recommended for Giants Engine)
- PNG
- JPG/JPEG

**Example:**
If `road_texture` is `"asphalt-white"`, the generator will look for:
- `templates/asphalt-white.dds`
- `templates/asphalt-white.png`
- `templates/asphalt-white.jpg`

### Finding Road Textures

**Recommended Source:** [AmbientCG](https://ambientcg.com/)
- High-quality, free (CC0) textures
- Search for "asphalt", "road", "concrete", etc.
- Download seamless/tileable textures

**Important:** Make sure textures are **oriented vertically** (road lanes running up/down in the image). If the texture shows horizontal lanes, rotate it 90° before using, otherwise the lanes will be perpendicular to the road direction.

### Texture Tiling

The default texture tile size is **10 meters**. This means the texture repeats every 10 meters along the road length. The texture width always spans the full road width as specified in the schema.

## OSM Data Requirements

### Data Quality

The quality of generated roads depends heavily on OSM data quality:

✅ **Good OSM Data:**
- Simple, clean linestrings
- Proper road connections at intersections
- Consistent spacing between points
- No duplicate or overlapping segments

❌ **Problematic OSM Data:**
- Sharp curves with insufficient points
- Points too close together (< 1 meter)
- Overlapping road segments
- Artifacts from complex editing

**Best Practice:** Review and clean OSM data before generation. Use JOSM or similar OSM editors to simplify geometry and remove artifacts.

### Road Networks

Roads are extracted based on OSM highway tags defined in your texture schema. Common highway types:
- `motorway`, `trunk`, `primary` - Major roads
- `secondary`, `tertiary` - Medium roads
- `residential`, `service` - Local roads
- `track` - Unpaved roads

## Intersection Handling

### T-Junctions (Automatic)

T-junctions are handled automatically:
- The road that **ends** at another road is considered secondary
- A patch mesh is generated from the main (continuous) road
- The patch overlays the intersection to prevent z-fighting

**Example:**
```
Main Road: ═══════════════
               ║
Secondary:     ║ (ends at main)
```
The main road will generate a patch over the intersection point.

### X-Junctions (Manual Handling Required)

**X-junctions (crossroads) are NOT automatically handled** because OSM doesn't indicate which road is "main."

**Solutions:**

1. **Manual Intersection Mesh:** Create a custom intersection mesh in Giants Editor
2. **Split Secondary Road:** Edit the OSM data to split one road into two segments:
   ```
   Before (no patch):          After (patch generated):
   ═════╬═════                 ═════╬═════
        ║                           ║ ║
        ║                      (split into two)
   ```
   When split, both segments end at the main road and will be covered by patches.

### Height Differences

Intersections on **terrain with height differences** may not generate proper patches:
- The patch assumes roads are at similar elevations
- Steep slopes or elevation changes can cause gaps or z-fighting

**Solutions:**
- Flatten terrain around intersections in Giants Editor
- Edit OSM data to avoid intersections on steep terrain
- Create custom intersection meshes manually

## Technical Details

### Interpolation

Roads are automatically interpolated to create smooth, evenly-spaced geometry:
- **Target segment length:** 5 meters between points
- Curved roads skip interpolation to preserve shape
- Roads with sharp angles (> 30°) are not interpolated

**Note:** While increasing interpolation density can create smoother roads, it may lead to twisted or artifacted geometry, especially on complex terrain.

### UV Coordinate Limits

Giants Engine requires UV coordinates to be within the range **[-32, 32]**. Roads longer than **300 meters** (30 texture tiles × 10m) are automatically split into multiple segments to comply with this limit.

Each split segment:
- Has its own continuous UV mapping (0 to ~30)
- Is rendered as part of the same mesh
- Tiles seamlessly at split points

### Mesh Processing

The generation pipeline:
1. Extract road linestrings from OSM data
2. Apply smart interpolation for smooth geometry
3. Split long roads (> 300m) into segments
4. Generate 3D mesh with vertices, faces, and UVs
5. Create patches for T-junctions
6. Export to OBJ format
7. Convert to i3D format with texture references

## Terrain Fitting

Generated roads are automatically fitted to terrain elevation using DEM (Digital Elevation Model) data. However:

- **Complex terrain** may cause roads to not fit perfectly
- **Steep slopes** may create floating or sunken road segments
- **Interpolation artifacts** can occur on rapidly changing elevation

**Expected Workflow:**
1. Generate roads with maps4fs
2. Import map into Giants Editor
3. Manually adjust terrain sculpting around roads
4. Use terrain smoothing tools to blend roads with landscape

This is normal and expected - automatic road generation provides a starting point, with final adjustments done in Giants Editor.

## Troubleshooting

### Roads Not Generating

**Check:**
- Texture schema has `road_texture` property defined
- `info_layer` is set to `"roads"`
- Texture file exists in `templates/` directory
- OSM data contains roads with matching tags

### Texture Stretching or Artifacts

**Causes:**
- UV coordinates exceeded Giants Engine limits (roads too long)
- Texture not properly tiled/seamless
- OSM data has points too close together

**Solutions:**
- Use seamless textures from AmbientCG
- Clean OSM data to remove artifacts
- Check logs for UV coordinate warnings

### Intersection Issues

**Z-Fighting at Intersections:**
- T-junctions should generate patches automatically
- X-junctions need manual handling (split roads or custom mesh)
- Check for height differences in terrain

**Gaps or Overlaps:**
- Usually caused by OSM data quality issues
- Edit OSM to ensure roads properly connect
- Remove duplicate nodes at intersection points

### Mesh Artifacts

**Twisted or Malformed Geometry:**
- Check OSM data for sharp curves or close points
- Simplify road geometry in OSM editor
- Avoid very short segments (< 1 meter)

**Floating or Sunken Roads:**
- DEM resolution may not match road detail
- Manually adjust terrain in Giants Editor
- Smooth terrain around problem areas

## Best Practices

1. **Start with Clean OSM Data**
   - Review roads in JOSM before generation
   - Remove unnecessary nodes and simplify geometry
   - Ensure proper connections at intersections

2. **Choose Appropriate Textures**
   - Use seamless, tileable textures
   - Ensure vertical orientation (lanes up/down)
   - Prefer DDS format for Giants Engine

3. **Handle Intersections Deliberately**
   - Plan which roads should be "main" vs "secondary"
   - Split roads in OSM for automatic patch generation
   - Prepare to create custom meshes for complex junctions

4. **Expect Manual Refinement**
   - Generated roads are a starting point
   - Terrain sculpting in Giants Editor is normal
   - Complex areas may need custom meshes

5. **Test Iteratively**
   - Generate small areas first to test configuration
   - Adjust texture schema based on results
   - Refine OSM data based on generated output

## Example Configuration

```json
[
  {
    "name": "asphalt",
    "tags": {
      "highway": ["motorway", "trunk", "primary"]
    },
    "width": 8,
    "color": [70, 70, 70],
    "info_layer": "roads",
    "road_texture": "asphalt-main"
  },
  {
    "name": "asphaltResidential",
    "tags": {
      "highway": ["residential", "service"]
    },
    "width": 6,
    "color": [100, 100, 100],
    "info_layer": "roads",
    "road_texture": "asphalt-residential"
  },
  {
    "name": "gravel",
    "tags": {
      "highway": ["track", "path"]
    },
    "width": 4,
    "color": [140, 180, 210],
    "info_layer": "roads",
    "road_texture": "gravel-dirt"
  }
]
```

This configuration will generate:
- Wide (8m) main roads with `asphalt-main` texture
- Medium (6m) residential roads with `asphalt-residential` texture
- Narrow (4m) dirt tracks with `gravel-dirt` texture
