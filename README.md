<div align="center" markdown>
<a href="https://discord.gg/Sj5QKKyE42">
<img src="https://github.com/user-attachments/assets/37043333-d6ef-4ca3-9f3c-81323d9d0b71">
</a>

<p align="center">
  <a href="#Quick-Start">Quick Start</a> •
  <a href="#Overview">Overview</a> • 
  <a href="docs/step_by_step.md">Create a map in 10 steps</a> •
  <a href="#How-To-Run">How-To-Run</a><br>
  <a href="docs/FAQ.md">FAQ</a> •
  <a href="docs/map_structure.md">Map Structure</a> •
  <a href="docs/tips_and_hints.md">Tips and Hints</a> •
  <a href="#Modder-Toolbox">Modder Toolbox</a><br>
  <a href="#Supported-objects">Supported objects</a> •
  <a href="#Generation-info">Generation info</a> •
  <a href="#Texture-schema">Texture schema</a> •
  <a href="#Background-terrain">Background terrain</a> •
  <a href="#Overview-image">Overview image</a><br>
  <a href="#DDS-conversion">DDS conversion</a> •
  <a href="#Advanced-settings">Advanced settings</a> •
  <a href="#Resources">Resources</a> •
  <a href="#Bugs-and-feature-requests">Bugs and feature requests</a><br>
  <a href="#Special-thanks">Special thanks</a>
</p>


[![Join Discord](https://img.shields.io/badge/join-discord-blue)](https://discord.gg/Sj5QKKyE42)
[![GitHub release (latest SemVer)](https://img.shields.io/github/v/release/iwatkot/maps4fs)](https://github.com/iwatkot/maps4fs/releases)
[![PyPI - Version](https://img.shields.io/pypi/v/maps4fs)](https://pypi.org/project/maps4fs)
[![Docker Pulls](https://img.shields.io/docker/pulls/iwatkot/maps4fs)](https://hub.docker.com/repository/docker/iwatkot/maps4fs/general)
[![GitHub issues](https://img.shields.io/github/issues/iwatkot/maps4fs)](https://github.com/iwatkot/maps4fs/issues)
[![Maintainability](https://api.codeclimate.com/v1/badges/b922fd0a7188d37e61de/maintainability)](https://codeclimate.com/github/iwatkot/maps4fs/maintainability)<br>
[![PyPI - Downloads](https://img.shields.io/pypi/dm/maps4fs)](https://pypi.org/project/maps4fs)
[![Checked with mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](https://mypy-lang.org/)
[![Build Status](https://github.com/iwatkot/maps4fs/actions/workflows/checks.yml/badge.svg)](https://github.com/iwatkot/maps4fs/actions)
[![Test Coverage](https://api.codeclimate.com/v1/badges/b922fd0a7188d37e61de/test_coverage)](https://codeclimate.com/github/iwatkot/maps4fs/test_coverage)
[![GitHub Repo stars](https://img.shields.io/github/stars/iwatkot/maps4fs)](https://github.com/iwatkot/maps4fs/stargazers)

</div>

🗺️ Supports 2x2, 4x4, 8x8, 16x16 and any custom size maps<br>
🔄 Support map rotation 🆕<br>
🌾 Automatically generates fields 🆕<br>
🌽 Automatically generates farmlands 🆕<br>
🌿 Automatically generates decorative foliage 🆕<br>
🌲 Automatically generates forests 🆕<br>
🌊 Automatically generates water planes 🆕<br>
🌍 Based on real-world data from OpenStreetMap<br>
🗺️ Supports [custom OSM maps](/docs/custom_osm.md)<br>
🏞️ Generates height map using SRTM dataset<br>
📦 Provides a ready-to-use map template for the Giants Editor<br>
🚜 Supports Farming Simulator 22 and 25<br>
🔷 Generates *.obj files for background terrain based on the real-world height map<br>
📄 Generates scripts to download high-resolution satellite images from [QGIS](https://qgis.org/download/) in one click<br>
📕 Detailed [documentation](/docs) and tutorials <br>
🧰 Modder Toolbox to help you with various tasks <br>

<p align="center">
<img src="https://github.com/user-attachments/assets/cf8f5752-9c69-4018-bead-290f59ba6976"><br>
🌎 Detailed terrain based on real-world data.<br><br>
<img src="https://github.com/user-attachments/assets/dc40d0bb-c20b-411c-8833-9925d0389452"><br>
🛰️ Realistic background terrain with satellite images.<br><br>
<img src="https://github.com/user-attachments/assets/6e3c0e99-2cce-46ac-82db-5cb60bba7a30"><br>
📐 Perfectly aligned background terrain.<br><br>
<img src="https://github.com/user-attachments/assets/5764b2ec-e626-426f-9f5d-beb12ba95133"><br>
🌿 Automatically generates decorative foliage.<br><br>
<img src="https://github.com/user-attachments/assets/27a5e541-a9f5-4504-b8d2-64aae9fb3e52"><br>
🌲 Automatically generates forests.<br><br>
<img src="https://github.com/user-attachments/assets/cce7d4e0-cba2-4dd2-b22d-03137fb2e860"><br>
🌊 Automatically generates water planes.<br><br>
<img src="https://github.com/user-attachments/assets/80e5923c-22c7-4dc0-8906-680902511f3a"><br>
🗒️ True-to-life blueprints for fast and precise modding.<br><br>
<img width="480" src="https://github.com/user-attachments/assets/1a8802d2-6a3b-4bfa-af2b-7c09478e199b"><br>
🌾 Field generation with one click.<br><br>
<img width="480" src="https://github.com/user-attachments/assets/4d1fa879-5d60-438b-a84e-16883bcef0ec"><br>
🌽 Automatic farmlands generation based on the fields.<br><br>

📹 A complete step-by-step video tutorial is here!  
<a href="https://www.youtube.com/watch?v=Nl_aqXJ5nAk" target="_blank"><img src="https://github.com/user-attachments/assets/4845e030-0e73-47ab-a5a3-430308913060"/></a>
<p align="center"><i>How to Generate a Map for Farming Simulator 25 and 22 from a real place using maps4FS.</i></p>

![Map example](https://github.com/user-attachments/assets/c46a3581-dd17-462f-b815-e36d4f724947)
<p align="center"><i>Map example generated with maps4fs.</i></p>

## Quick Start
There are several ways to use the tool. You obviously need the **first one**, but you can choose any of the others depending on your needs.<br>
### 🚜 For most users
**Option 1:** Open the [maps4fs](https://maps4fs.xyz) and generate a map template in a few clicks.<br>

![Basic WebUI](https://github.com/user-attachments/assets/52f499cc-f28a-4da3-abef-0e818abe8dbe)

### 😎 For advanced users
**Option 2:** Run the Docker version in your browser. Launch the following command in your terminal:
```bash
docker run -d -p 8501:8501 --name maps4fs iwatkot/maps4fs
```
And open [http://localhost:8501](http://localhost:8501) in your browser.<br>
If you don't know how to use Docker, navigate to the [Docker version](#option-2-docker-version), it's really simple.<br>

### 🤯 For developers
**Option 3:** Python package. Install the package using the following command:
```bash
pip install maps4fs
```
And refer to the [Python package](#option-3-python-package) section to learn how to use it.<br>

## Overview
The core idea is coming from the awesome [maps4cim](https://github.com/klamann/maps4cim) project.<br>

The main goal of this project is to generate map templates, based on real-world data, for the Farming Simulator. It's important to mention that **templates are not maps**. They are just a starting point for creating a map. This tool just uses built-in textures to highlight different types of terrain and buildings with correct shapes and scales and to generate a height map. The rest of the work is up to you. So if you thought that you could just run this tool and get a playable map, then I'm sorry to disappoint you. But if you are a map maker, then this tool will save you a lot of time.<br>
So, if you're new to map making, here's a quick overview of the process:
1. Generate a map template using this tool.
2. Download the Giants Editor.
3. Open the map template in the Giants Editor.
4. Now you can start creating your map (adding roads, fields, buildings, etc.).

### Previews

The generator also creates multiple previews of the map. Here's the list of them:
1. General preview - merging all the layers into one image with different colors.
2. Grayscale DEM preview - a grayscale image of the height map (as it is).
3. Colored DEM preview - a colored image of the height map (from blue to red). The blue color represents the lowest point, and the red color represents the highest point.

![16 km map](https://github.com/user-attachments/assets/82543bcc-1289-479e-bd13-85a8890f0485)<br>
*Preview of a 16 km map with a 500-meter mountain in the middle of it.*<br>

Parameters:
- coordinates: 45.15, 19.71
- size: 16 x 16 km

## Step by step
Don't know where to start? Don't worry, just follow this [step-by-step guide](docs/step_by_step.md) to create your first map in 10 simple steps.<br>

## How-To-Run

### Option 1: Public version
🟢 Recommended for all users.  
🛠️ Don't need to install anything.  
🗺️ Supported map sizes: 2x2, 4x4, 8x8 km.  
⚙️ Advanced settings: enabled.  
🖼️ Texture dissolving: enabled.  
Using the public version on [maps4fs.xyz](https://maps4fs.xyz) is the easiest way to generate a map template. Just open the link and follow the instructions.
Note: due to CPU and RAM limitations of the hosting, the generation may take some time. If you need faster processing, use the [Docker version](#option-2-docker-version).<br>

Using it is easy and doesn't require any guides. Enjoy!

### Option 2: Docker version
🟠 Recommended for users who want bigger maps, fast generation, nice-looking textures, and advanced settings.  
🛠️ Launch with one single command.  
🗺️ Supported map sizes: 2x2, 4x4, 8x8, 16x16 km and any custom size.  
⚙️ Advanced settings: enabled.   
🖼️ Texture dissolving: enabled.  
You can launch the project with minimalistic UI in your browser using Docker. Follow these steps:

1. Install [Docker](https://docs.docker.com/get-docker/) for your OS.
2. Run the following command in your terminal:
```bash
docker run -d -p 8501:8501 --name maps4fs iwatkot/maps4fs
```
3. Open your browser and go to [http://localhost:8501](http://localhost:8501).
4. Fill in the required fields and click on the `Generate` button.
5. When the map is generated click on the `Download` button to get the map.

### Option 3: Python package
🔴 Recommended for developers.  
🗺️ Supported map sizes: 2x2, 4x4, 8x8, 16x16 km and any custom size.  
⚙️ Advanced settings: enabled.   
🖼️ Texture dissolving: enabled.  
You can use the Python package to generate maps. Follow these steps:

1. Install the package from PyPI:
```bash
pip install maps4fs
```
2. Import the Game class and create an instance of it:
```python
import maps4fs as mfs

game = mfs.Game.from_code("FS25")
```
In this case, the library will use the default templates, which should be present in the `data` directory, which should be placed in the current working directory.<br>
Structure example:<br>

```text
📁 data
 ┣ 📄 fs22-map-template.zip
 ┗ 📄 fs22-texture-schema.json
```

So it's recommended to download the `data` directory from the repository and place it in the root of your project.<br>

3. Create an instance of the Map class:
```python
import maps4fs as mfs

map = mfs.Map(
  game,
  (52.5200, 13.4050),  # Latitude and longitude of the map center.
  height=1024,  # The height of the map in meters.
  width=1024,  # The width of the map in meters.
  map_directory="path/to/your/map/directory",  # The directory where the map will be saved.
)
```

4. Generate the map:
The `generate` method returns a generator, which yields the active component of the map. You can use it to track the progress of the generation process.
```python
for active_component in map.generate():
    print(active_component)
```

The map will be saved in the `map_directory` directory.

## Modder Toolbox
The tool now has a Modder Toolbox, which is a set of tools to help you with various tasks. You can open the toolbox by switching to the `🧰 Modder Toolbox` tab in the StreamLit app.<br>

![Modder Toolbox](https://github.com/user-attachments/assets/dffb252f-f5c0-4021-9d45-31e5bccc0d9b)

### Tool Categories
Tools are divided into categories, which are listed below.
#### For Textures and DEM
- **GeoTIFF windowing** - allows you to upload your GeoTIFF file and select the region of interest to extract it from the image. It's useful when you have high-resolution DEM data and want to create a height map using it.

#### For Background terrain
- **Convert image to obj model** - allows you to convert the image to the obj model. You can use this tool to create the background terrain for your map. It can be extremely useful if you have access to the sources of high-resolution DEM data and want to create the background terrain using it.

## Supported objects
The project is based on the [OpenStreetMap](https://www.openstreetmap.org/) data. So, refer to [this page](https://wiki.openstreetmap.org/wiki/Map_Features) to understand the list below.
- "building": True
- "highway": ["motorway", "trunk", "primary"]
- "highway": ["secondary", "tertiary", "road", "service"]
- "highway": ["unclassified", "residential", "track"]
- "natural": ["grassland", "scrub"]
- "landuse": "farmland"
- "natural": ["water"]
- "waterway": True
- "natural": ["wood", "tree_row"]
- "railway": True

The list will be updated as the project develops.

## Generation info
The script will generate the `generation_info.json` file in the `output` folder. It is split into different sections, which represent the components of the map generator. You may need this information to use some other tools and services to obtain additional data for your map.<br>

List of components:
- `Config` - this component handles the `map.xml` file, where the basic description of the map is stored.
- `Texture` -  this component describes the textures, that were used to generate the map.
- `DEM` - this component describes the Digital Elevation Model (the one which creates terrain on your map), which was used to generate the height map and related to the `dem.png` file.
- `I3d` - this component describes the i3d file, where some specific attributes properties, and paths to the files are stored.
- `Background` - this component describes the 8 tiles, that surround the map.

Below you'll find descriptions of the components and the fields that they contain.<br>
ℹ️ If there's no information about the component, it means that at the moment it does not store any data in the `generation_info.json` file.

### Config
Example of the `Config` component:
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
The `Overview` section contains information to create an overview image, which represents the in-game map. You can use the `epsg3857_string` to obtain the satellite images in the QGIS. So this section describes the region of the map plus the borders. Usually, it's exactly 2X the size of the map.<br>
And here's the list of the fields:
- `"epsg3857_string"` - the string representation of the bounding box in the EPSG:3857 projection, it is required to obtain the satellite images in the QGIS,<br>
- `"south"` - the southern border of overview region,<br>
- `"west"` - the western border of overview region,<br>
- `"north"` - the northern border of overview region,<br>
- `"east"` - the eastern border of overview region,<br>
- `"height"` - the height of the overview region in meters (2X the size of the map),<br>
- `"width"` - the width of the overview region in meters,<br>

### Texture

Example of the `Texture` component:
```json
"Texture": {
    "coordinates": [
        45.28571409289627,
        20.237433441210115
    ],
    "bbox": [
        45.29492313313172,
        45.27650505266082,
        20.250522423471406,
        20.224344458948824
    ],
    "map_height": 2048,
    "map_width": 2048,
    "minimum_x": 439161.2439774908,
    "minimum_y": 5013940.540089059,
    "maximum_x": 441233.5397821935,
    "maximum_y": 5016006.074349126,
},
```

And here's the list of the fields:

- `"coordinates"` - the coordinates of the map center which you entered,<br>
- `"bbox"` - the bounding box of the map in lat and lon,<br>
- `"map_height"` - the height of the map in meters (this one is from the user input, e.g. 2048 and so on),<br>
- `"map_width"` - the width of the map in meters (same as above),<br>
- `"minimum_x"` - the minimum x coordinate of the map (UTM projection),<br>
- `"minimum_y"` - the minimum y coordinate of the map (UTM projection),<br>
- `"maximum_x"` - the maximum x coordinate of the map (UTM projection),<br>
- `"maximum_y"` - the maximum y coordinate of the map (UTM projection),

### Background

The background component consists of the 8 tiles, each one representing the tile, that surrounds the map. The tiles are named as the cardinal points, e.g. "N", "NE", "E" and so on.<br>
Example of the `Background` component:

```json
"Background": {
"N": {
    "center_latitude": 45.30414170952092,
    "center_longitude": 20.237433441210115,
    "epsg3857_string": "2251363.25324853,2254278.318028022,5668072.719985372,5670987.784803056 [EPSG:3857]",
    "height": 2048,
    "width": 2048,
    "north": 45.31335074975637,
    "south": 45.29493266928547,
    "east": 20.250526677438195,
    "west": 20.224340204982035
},
}
```

And here's the list of the fields:
- `"center_latitude"` - the latitude of the center of the tile,<br>
- `"center_longitude"` - the longitude of the center of the tile,<br>
- `"epsg3857_string"` - the string representation of the bounding box in the EPSG:3857 projection, it is required to obtain the satellite images in the QGIS,<br>
- `"height"` - the height of the tile in meters,<br>
- `"width"` - the width of the tile in meters,<br>
- `"north"` - the northern border of the tile,<br>
- `"south"` - the southern border of the tile,<br>
- `"east"` - the eastern border of the tile,<br>
- `"west"` - the western border of the tile,<br>

## Texture schema
maps4fs uses a simple JSON file to define the texture schema. For each ofthe  supported games, this file has unique entries, but the structure is the same. Here's an example of the schema for Farming Simulator 25:

```json
[
    {
    "name": "forestRockRoots",
    "count": 2,
    "exclude_weight": true
  },
  {
    "name": "grass",
    "count": 2,
    "tags": { "natural": "grassland" },
    "color": [34, 255, 34],
    "priority": 0
  },
  {
    "name": "grassClovers",
    "count": 2
  },
  {
    "name": "grassCut",
    "count": 2
  },
  {
    "name": "grassDirtPatchy",
    "count": 2,
    "tags": { "natural": ["wood", "tree_row"] },
    "width": 2,
    "color": [0, 252, 124]
  }
]
```
Let's have a closer look at the fields:
- `name` - the name of the texture. Just the way the file will be named.
- `count` - the number of textures of this type. For example, for the **dirtMedium** texture there will be two textures: **dirtMedium01_weight.png** and **dirtMedium02_weight.png**.
ℹ️ There's one texture that has count `0`, it's the waterPuddle texture from FS22, which is not present in FS25.
- `tags` - the tags from the OpenStreetMap data. Refer to the section [Supported objects](#supported-objects) to see the list of supported tags. If there are no tags, the texture file will be generated empty and no objects will be placed on it.
- `width` - the width of the texture in meters. Some of the objects from OSM (roads, for example) are lines, not areas. So, to draw them correctly, the tool needs to know the width of the line.
- `color` - the color of the texture. It's used only in the preview images and has no effect on the map itself. But remember that previews are crucial for the map-making process, so it's better to set the color to something that represents the texture.
- `priority` - the priority of the texture for overlapping. Textures with higher priorities will be drawn over the textures with lower priorities.
ℹ️ The texture with 0 priority considers the base layer, which means that all empty areas will be filled with this texture.
- `exclude_weight` - this is only used for the forestRockRoots texture from FS25. It just means that this texture has no `weight` postfix, that's all.

## Background terrain
The tool now supports the generation of the background terrain. If you don't know what it is, here's a brief explanation. The background terrain is the world around the map. It's important to create it because if you don't, the map will look like it's floating in the void. The background terrain is a simple plane that can (and should) be textured to look fine.<br>
So, the tool generates the background terrain in the form of the 8 tiles, which surround the map. The tiles are named as the cardinal points, e.g. "N", "NE", "E" and so on. All those tiles will be saved in the `background` directory with corresponding names: `N.obj`, `NE.obj`, `E.obj`, and so on.<br>
If you don't want to work with separate tiles, the tool also generates the `FULL.obj` file, which includes everything around the map and the map itself. It may be a convenient approach to work with one file, one texture, and then just cut the map from it.<br>

![Complete background terrain in Blender](https://github.com/user-attachments/assets/7266b8f1-bfa2-4c14-a740-1c84b1030a66)

➡️ *No matter which approach you choose, you still need to adjust the background terrain to connect it to the map without any gaps. But with a single file, it's much easier to do.*

If you're willing to create a background terrain, you will need Blender, the Blender Exporter Plugins, and the QGIS. You'll find the download links in the [Resources](#resources) section.<br>

If you're afraid of this task, please don't be. It's really simple and I've prepared detailed step-by-step instructions for you, you'll find them in the separate README files. Here are the steps you need to follow:

1. [Download high-resolution satellite images](docs/download_satellite_images.md).
2. [Prepare the i3d files](docs/create_background_terrain.md).
3. [Import the i3d files to Giants Editor](docs/import_to_giants_editor.md).

## Overview image
The overview image is an image that is used as an in-game map. No matter what the size of the map, this file is always `4096x4096 pixels`, while the region of your map is `2048x2048 pixels` in the center of this file. The rest of the image is just here for a nice view, but you still may add satellite pictures to this region.<br>

<img width="400" src="https://github.com/user-attachments/assets/ede9ea81-ef97-4914-9dbf-9761ef1eb7ca">

Cool image by [@ZenJakey](https://github.com/ZenJakey).

So, in the same way, you've downloaded the satellite images for the background terrain, you can download them for the overview image. Just use the `epsg3857_string` from the `generation_info.json` file. You'll find the needed string in the `Config` component in the `Overview` section:

```json
"Config": {
    "Overview": {
        "epsg3857_string": "2249906.6679576184,2255734.9033189337,5663700.389039194,5669528.6247056825 [EPSG:3857]",
    }
},
```

After that, you need to resize the image to 4096x4096 pixels and convert it to the `.dds` format.

## DDS conversion
The `.dds` format is the format used in the Farming Simulator for the textures, icons, overview, and preview images. There a plenty of options to convert the images to the `.dds` format, you can just google something like `png to dds`, and the first link probably will help you with it.<br>

List of the important DDS files:
- `icon.dds` - 256x256 pixels, the icon of the map,
- `preview.dds` - 2048x2048 pixels, the preview image of the map on the loading screen,
- `mapsUS/overview.dds` - 4096x4096 pixels, the overview image of the map (in-game map)

## Advanced settings
The tool supports the custom size of the map. To use this feature select `Custom` in the `Map size` dropdown and enter the desired size. The tool will generate a map with the size you entered.<br>

⛔️ Do not use this feature, if you don't know what you're doing. In most cases, the Giants Editor will just crash on opening the file, because you need to enter specific values for the map size.<br><br>

![Advanced settings](https://github.com/user-attachments/assets/9e8e178a-58d9-4aa6-aefd-4ed53408701d)

You can also apply some advanced settings to the map generation process. Note that they're ADVANCED, so you don't need to use them if you're not sure what they do.<br>

### DEM Advanced settings

- Multiplier: the height of the map is multiplied by this value. So the DEM map is just a 16-bit grayscale image, which means that the maximum available value there is 65535, while the actual difference between the deepest and the highest point on Earth is about 20 km. Just note that this setting mostly does not matter, because you can always adjust it in the Giants Editor, learn more about the DEM file and the heightScale parameter in [docs](docs/dem.md). By default, it's set to 1.

- Blur radius: the radius of the Gaussian blur filter applied to the DEM map. By default, it's set to 21. This filter just makes the DEM map smoother, so the height transitions will be more natural. You can set it to 1 to disable the filter, but it will result in a Minecraft-like map.

- Plateau height: this value will be added to each pixel of the DEM image, making it "higher". It's useful when you want to add some negative heights on the map, that appear to be in a "low" place. By default, it's set to 0.

- Water depth: this value will be subtracted from each pixel of the DEM image, where water resources are located. Pay attention that it's not in meters, instead it in the pixel value of DEM, which is 16 bit image with possible values from 0 to 65535. When this value is set, the same value will be added to the plateau setting to avoid negative heights.

### Texture Advanced settings

- Fields padding - this value (in meters) will be applied to each field, making it smaller. It's useful when the fields are too close to each other and you want to make them smaller. By default, it's set to 0.

- Texture dissolving - if enabled, the values from one layer will be splitted between different layers of texture, making it look more natural. By default, it's set to True. Can be turned of for faster processing.

- Skip drains - if enabled, the tool will not generate the drains and ditches on the map. By default, it's set to False. Use this if you don't need the drains on the map.

### Farmlands Advanced settings

- Farmlands margin - this value (in meters) will be applied to each farmland, making it bigger. You can use the value to adjust how much the farmland should be bigger than the actual field. By default, it's set to 3.

### Vegetation Advanced settings

- Forest density - the density of the forest in meters. The lower the value, the lower the distance between the trees, which makes the forest denser. Note, that low values will lead to enormous number of trees, which may cause the Giants Editor to crash or lead to performance issues. By default, it's set to 10.

- Random plants - when adding decorative foliage, enabling this option will add different species of plants to the map. If unchecked only basic grass (smallDenseMix) will be added. Defaults to True.

### Background terrain Advanced settings

- Generate background - if enabled, the obj files for the background terrain will be generated. You can turn it off if you already have those files or don't need them. By default, it's set to True.

- Generate water - if enabled, the water planes obj files will be generated. You can turn it off if you already have those files or don't need them. By default, it's set to True.

## Resources
In this section, you'll find a list of the resources that you need to create a map for the Farming Simulator.<br>
To create a basic map, you only need the Giants Editor. But if you want to create a background terrain - the world around the map, so it won't look like it's floating in the void - you also need Blender and the Blender Exporter Plugins. To create realistic textures for the background terrain, the QGIS is required to obtain high-resolution satellite images.<br>

1. [Giants Editor](https://gdn.giants-software.com/downloads.php) - the official tool for creating maps for the Farming Simulator.
2. [Blender](https://www.blender.org/download/) - the open-source 3D modeling software that you can use to create models for the Farming Simulator.
3. [Blender Exporter Plugins](https://gdn.giants-software.com/downloads.php) - the official plugins for exporting models from Blender to i3d format (the format used in the Farming Simulator).
4. [QGIS](https://qgis.org/download/) - the open-source GIS software that you can use to obtain high-resolution satellite images for your map.
5. [CompressPngCom](https://www.compresspng.com/) - the online tool to compress the PNG images. May be useful to reduce the size of the satellite images.
6. [AnyConv](https://anyconv.com/png-to-dds-converter/) - the online tool to convert the PNG images to the DDS format. You'll need this format for the textures, icons, overview, and preview images.

## Bugs and feature requests
➡️ Please, before creating an issue or asking some questions, check the [FAQ](docs/FAQ.md) section.<br>
If you find a bug or have an idea for a new feature, please create an issue [here](https://github.com/iwatkot/maps4fs/issues) or contact me directly on [Telegram](https://t.me/iwatkot) or on Discord: `iwatkot`.

## Special thanks

Of course, first of all, thanks to the direct [contributors](https://github.com/iwatkot/maps4fs/graphs/contributors) of the project.  

But also, I want to thank the people who helped me with the project in some way, even if they didn't contribute directly. Here's the list of them:

- [Ka5tis](https://github.com/Ka5tis) - for investigating the issue with a "spiky terrain" and finding a solution - changing the `DisplacementLayer` size to a higher value.
- [Kalderone](https://www.youtube.com/@Kalderone_FS22) - for useful feedback, suggestions, expert advice on the map-making process and highlihting some important settings in the Giants Editor.
- [OneSunnySunday](https://www.artstation.com/onesunnysunday) - for expert advice on Blender, help in processing background terrain, and compiling detailed tutorials on how to prepare the OBJ files for use in Giants Editor.
- [BFernaesds](https://github.com/BFernaesds) - for the manual tests of the app.
- [gamerdesigns](https://github.com/gamerdesigns) - for the manual tests of the app. 
- [Tox3](https://github.com/Tox3) - for the manual tests of the app. 
- [Lucandia](https://github.com/Lucandia) - for the awesome StreamLit [widget to preview STL files](https://github.com/Lucandia/streamlit_stl).