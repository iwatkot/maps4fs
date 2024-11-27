<div align="center" markdown>
<img src="https://github.com/iwatkot/maps4fs/assets/118521851/ffd7f0a3-e317-4c3f-911f-2c2fb736fbfa">

<p align="center">
  <a href="#Quick-Start">Quick Start</a> •
  <a href="#Overview">Overview</a> • 
  <a href="#How-To-Run">How-To-Run</a><br>
  <a href="#Supported-objects">Supported objects</a> •
  <a href="#Generation-info">Generation info</a> •
  <a href="#Texture-schema">Texture schema</a> •
  <a href="#Background-terrain">Background terrain</a> •
  <a href="#Overview-image">Overview image</a><br>
  <a href="#DDS-conversion">DDS conversion</a> •
  <a href="#For-advanced-users">For advanced users</a> •
  <a href="#Resources">Resources</a> •
  <a href="#Bugs-and-feature-requests">Bugs and feature requests</a>
</p>


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
🌍 Based on real-world data from OpenStreetMap<br>
🏞️ Generates height using SRTM dataset<br>
📦 Provides a ready-to-use map template for the Giants Editor<br>
🚜 Supports Farming Simulator 22 and 25<br>
🔷 Generates *.obj files for background terrain based on the real-world height map 🆕<br>
📄 Generates commands to obtain high-resolution satellite images from [QGIS](https://qgis.org/download/) 🆕<br>

## Quick Start
There are several ways to use the tool. You obviously need the **first one**, but you can choose any of the others depending on your needs.<br>
### 🚜 For most users
**Option 1:** open the [maps4fs](https://maps4fs.streamlit.app) on StreamLit and generate a map template in a few clicks.<br>

![Basic WebUI](https://github.com/user-attachments/assets/14620044-9e92-47ae-8531-d61460740f58)

### 😎 For advanced users
**Option 2:** run the Docker version in your browser. Launch the following command in your terminal:
```bash
docker run -d -p 8501:8501 iwatkot/maps4fs
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

The generator also creates a multiple previews of the map. Here's the list of them:
1. General preview - merging all the layers into one image with different colors.
2. Grayscale DEM preview - a grayscale image of the height map (as it is).
3. Colored DEM preview - a colored image of the height map (from blue to red). The blue color represents the lowest point, and the red color represents the highest point.

![16 km map](https://github.com/user-attachments/assets/82543bcc-1289-479e-bd13-85a8890f0485)<br>
*Preview of a 16 km map with a 500-meter mountain in the middle of it.*<br>

Parameters:
- coordinates: 45.15, 19.71
- size: 16 x 16 km

## How-To-Run

You'll find detailed instructions on how to run the project below. But if you prefer video tutorials, here's one for you:
<a href="https://www.youtube.com/watch?v=ujwWKHVKsw8" target="_blank"><img src="https://github.com/user-attachments/assets/6dbbbc71-d04f-40b2-9fba-81e5e4857407"/></a>
<i>Video tutorial: How to generate a Farming Simulator 22 map from real-world data.</i>

### Option 1: StreamLit
🟢 Recommended for all users, you don't need to install anything.<br>
Using the [StreamLit](https://maps4fs.streamlit.app) version of the tool is the easiest way to generate a map template. Just open the link and follow the instructions.
Note: due to CPU and RAM limitations of the hosting, the generation may take some time. If you need faster processing, use the [Docker version](#option-2-docker-version).<br>

Using it is easy and doesn't require any guides. Enjoy!

### Option 2: Docker version
🟠 Recommended for users who want faster processing, very simple installation.<br>
You can launch the project with minimalistic UI in your browser using Docker. Follow these steps:

1. Install [Docker](https://docs.docker.com/get-docker/) for your OS.
2. Run the following command in your terminal:
```bash
docker run -d -p 8501:8501 iwatkot/maps4fs
```
3. Open your browser and go to [http://localhost:8501](http://localhost:8501).
4. Fill in the required fields and click on the `Generate` button.
5. When the map is generated click on the `Download` button to get the map.

### Option 3: Python package
🔴 Recommended for developers.<br>
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
In this case the library will use the default templates, which should be present in the `data` directory, which should be placed in the current working directory.<br>
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
The script will generate the `generation_info.json` file in the `output` folder. It splitted to the different sections, which represents the components of the map generator. You may need this information to use some other tools and services to obtain additional data for your map.<br>

List of components:
- `Config` - this component handles the `map.xml` file, where the basic description of the map is stored.
- `Texture` -  this component describes the textures, that were used to generate the map.
- `DEM` - this component describes the Digital Elevation Model (the one which creates terrain on your map), which was used to generate the height map and related to the `dem.png` file.
- `I3d` - this component describes the i3d file, where some specific attributes properties and path to the files are stored.
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
The `Overview` section contains information to create an overview image, which represents the in-game map. You can use the `epsg3857_string` to obtain the satellite images in the QGIS. So this section describes the region of the map plus the borders. Usually, it's exact 2X the size of the map.<br>
And here's the list of the fields:
- `"epsg3857_string"` - the string representation of the bounding box in the EPSG:3857 projection, it's required to obtain the satellite images in the QGIS,<br>
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
    "height": 2065.5342600671574,
    "width": 2072.295804702677,
    "height_coef": 1.0085616504234167,
    "width_coef": 1.011863185889979
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
- `"maximum_y"` - the maximum y coordinate of the map (UTM projection),<br>
- `"height"` - the height of the map in meters (it won't be equal to the parameters above since the Earth is not flat, sorry flat-earthers),<br>
- `"width"` - the width of the map in meters (same as above),<br>
- `"height_coef"` - since we need a texture of exact size, the height of the map is multiplied by this coefficient,<br>
- `"width_coef"` - same as above but for the width,<br>
- `"tile_name"` - the name of the SRTM tile which was used to generate the height map, e.g. "N52E013"<br>

### Background

The background component consist of the 8 tiles, each one represents the tile, that surrounds the map. The tiles are named as the cardinal points, e.g. "N", "NE", "E" and so on.<br>
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
- `"epsg3857_string"` - the string representation of the bounding box in the EPSG:3857 projection, it's required to obtain the satellite images in the QGIS,<br>
- `"height"` - the height of the tile in meters,<br>
- `"width"` - the width of the tile in meters,<br>
- `"north"` - the northern border of the tile,<br>
- `"south"` - the southern border of the tile,<br>
- `"east"` - the eastern border of the tile,<br>
- `"west"` - the western border of the tile,<br>

## Texture schema
maps4fs uses a simple JSON file to define the texture schema. For each of supported games this file has unique entries, but the structure is the same. Here's an example of the schema for Farming Simulator 25:

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
ℹ️ There's one texture that have count `0`, it's the waterPuddle texture from FS22, which not present in FS25.
- `tags` - the tags from the OpenStreetMap data. Refer to the section [Supported objects](#supported-objects) to see the list of supported tags. If there are no tags, the texture file will be generated empty and no objects will be placed on it.
- `width` - the width of the texture in meters. Some of the objects from OSM (roads, for example) are lines, not areas. So, to draw them correctly, the tool needs to know the width of the line.
- `color` - the color of the texture. It's used only in the preview images and have no effect on the map itself. But remember that previews are crucial for the map making process, so it's better to set the color to something that represents the texture.
- `priority` - the priority of the texture for overlapping. Textures with higher priorities will be drawn over the textures with lower priorities.
ℹ️ The texture with 0 priority considers the base layer, which means that all empty areas will be filled with this texture.
- `exclude_weight` - this only used for the forestRockRoots texture from FS25. It's just means that this texture has no `weight` postfix, that's all.

## Background terrain
The tool now supports the generation of the background terrain. If you don't know what it is, here's a brief explanation. The background terrain is the world around the map. It's important to create it, because if you don't, the map will look like it's floating in the void. The background terrain is a simple plane which can (and should) be texture to look fine.<br>
So, the tool generates the background terrain in the form of the 8 tiles, which surround the map. The tiles are named as the cardinal points, e.g. "N", "NE", "E" and so on. All those tiles will be saved in the `objects/tiles` directory with corresponding names: `N.obj`, `NE.obj`, `E.obj` and so on.<br>
If you're willing to create a background terrain, you will need: Blender, the Blender Exporter Plugins and the QGIS. You'll find the download links in the [Resources](#resources) section.<br>

If you're afraid of this task, please don't be. It's really simple and I've prepaired detailed step-by-step instructions for you, you'll find them in the separate README files. Here are the steps you need to follow:

1. [Download high-resolution satellite images](README_satellite_images.md).
2. [Prepare the i3d files](README_i3d.md).
3. [Import the i3d files to Giants Editor](README_giants_editor.md).

## Overview image
The overview image is an image that is used as in-game map. No matter what the size of the map, this file is always `4096x4096 pixels`, while the region of your map is `2048x2048 pixels` in center of this file. The rest of the image is just here for nice view, but you still may add satellite pictures to this region.<br>

<img width="400" src="https://github.com/user-attachments/assets/ede9ea81-ef97-4914-9dbf-9761ef1eb7ca">

Cool image by [@ZenJakey](https://github.com/ZenJakey).

So, the same way you've downloaded the satellite images for the background terrain, you can download them for the overview image. Just use the `epsg3857_string` from the `generation_info.json` file. You'll find the needed string in the `Config` component in the `Overview` section:

```json
"Config": {
    "Overview": {
        "epsg3857_string": "2249906.6679576184,2255734.9033189337,5663700.389039194,5669528.6247056825 [EPSG:3857]",
    }
},
```

After it you need to resize the image to 4096x4096 pixels and convert it to the `.dds` format.

## DDS conversion
The `.dds` format is the format used in the Farming Simulator for the textures, icons, overview and preview images. There's a plenty of options to convert the images to the `.dds` format, you can just google something like `png to dds` and the first link probably will help you with it.<br>

List of the important DDS files:
- `icon.dds` - 256x256 pixels, the icon of the map,
- `preview.dds` - 2048x2048 pixels, the preview image of the map on loading screen,
- `mapsUS/overview.dds` - 4096x4096 pixels, the overview image of the map (in-game map)

## For advanced users
The tool supports the custom size of the map. To use this feature select `Custom` in the `Map size` dropdown and enter the desired size. The tool will generate a map with the size you entered.<br>

⛔️ Do not use this feature, if you don't know what you're doing. In most cases the Giants Editor will just crash on opening the file, because you need to enter a specific values for the map size.<br><br>

![Advanced settings](https://github.com/user-attachments/assets/0446cdf2-f093-49ba-ba8f-9bef18a58b47)

You can also apply some advanced settings to the map generation process. Note that they're ADVANCED, so you don't need to use them if you're not sure what they do.<br>

Here's the list of the advanced settings:

- DEM multiplier: the height of the map is multiplied by this value. So the DEM map is just a 16-bit grayscale image, which means that the maximum avaiable value there is 65535, while the actual difference between the deepest and the highest point on Earth is about 20 km. So, by default this value is set to 3. Just note that this setting mostly does not matter, because you can always adjust it in the Giants Editor, learn more about the [heightScale](https://www.farming-simulator.org/19/terrain-heightscale.php) parameter on the [PMC Farming Simulator](https://www.farming-simulator.org/) website.

- DEM Blur radius: the radius of the Gaussian blur filter applied to the DEM map. By default, it's set to 21. This filter just makes the DEM map smoother, so the height transitions will be more natural. You can set it to 1 to disable the filter, but it will result as a Minecraft-like map.

## Resources
In this section you'll find a list of the resources that you need to create a map for the Farming Simulator.<br>
To create a basic map, you only need the Giants Editor. But if you want to create a background terrain - the world around the map, so it won't look like it's floating in the void - you also need Blender and the Blender Exporter Plugins. To create realistic textures for the background terrain, the QGIS is required to obtain high-resolution satellite images.<br>

1. [Giants Editor](https://gdn.giants-software.com/downloads.php) - the official tool for creating maps for the Farming Simulator.
2. [Blender](https://www.blender.org/download/) - the open-source 3D modeling software that you can use to create models for the Farming Simulator.
3. [Blender Exporter Plugins](https://gdn.giants-software.com/downloads.php) - the official plugins for exporting models from Blender to i3d format (the format used in the Farming Simulator).
4. [QGIS](https://qgis.org/download/) - the open-source GIS software that you can use to obtain high-resolution satellite images for your map.

## Bugs and feature requests
If you find a bug or have an idea for a new feature, please create an issue [here](https://github.com/iwatkot/maps4fs/issues) or contact me directly on [Telegram](https://t.me/iwatkot) or on Discord: `iwatkot`.
