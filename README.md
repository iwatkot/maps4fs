<div align="center" markdown>
<img src="https://github.com/iwatkot/maps4fs/assets/118521851/ffd7f0a3-e317-4c3f-911f-2c2fb736fbfa">

<p align="center">
  <a href="#Quick-Start">Quick Start</a> •
  <a href="#Overview">Overview</a> • 
  <a href="#How-To-Run">How-To-Run</a> • 
  <a href="#Supported-objects">Supported objects</a> • 
  <a href="#For-advanced-users">For advanced users</a> • 
  <a href="#Bugs-and-feature-requests">Bugs and feature requests</a>
</p>


[![GitHub release (latest SemVer)](https://img.shields.io/github/v/release/iwatkot/maps4fs)](https://github.com/iwatkot/maps4fs/releases)
[![PyPI - Version](https://img.shields.io/pypi/v/maps4fs)](https://pypi.org/project/maps4fs)
[![Docker Pulls](https://img.shields.io/docker/pulls/iwatkot/maps4fs)](https://hub.docker.com/repository/docker/iwatkot/maps4fs/general)
[![GitHub issues](https://img.shields.io/github/issues/iwatkot/maps4fs)](https://github.com/iwatkot/maps4fs/issues)
[![Maintainability](https://api.codeclimate.com/v1/badges/b922fd0a7188d37e61de/maintainability)](https://codeclimate.com/github/iwatkot/maps4fs/maintainability)<br>
[![Checked with mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](https://mypy-lang.org/)
[![Build Status](https://github.com/iwatkot/maps4fs/actions/workflows/checks.yml/badge.svg)](https://github.com/iwatkot/maps4fs/actions)
[![Test Coverage](https://api.codeclimate.com/v1/badges/b922fd0a7188d37e61de/test_coverage)](https://codeclimate.com/github/iwatkot/maps4fs/test_coverage)
[![GitHub Repo stars](https://img.shields.io/github/stars/iwatkot/maps4fs)](https://github.com/iwatkot/maps4fs/stargazers)

</div>

🗺️ Supports 2x2, 4x4, 8x8, 16x16 and any custom size maps<br>
🌍 Based on real-world data from OpenStreetMap<br>
🏞️ Generates height using SRTM dataset<br>
📦 Provides a ready-to-use map template for the Giants Editor<br>
🚜 Supports Farming Simulator 22 and 25*<br>

\* changes in the library are ready, waiting for the Giants to release the Giants Editor v10. Meanwhile the option to generate a map for FS25 is disabled.

## Quick Start
There are several ways to use the tool. You obviously need the **first one**, but you can choose any of the others depending on your needs.<br>
### 🚜 For most users
**Option 1:** open the [maps4fs](https://maps4fs.streamlit.app) on StreamLit and generate a map template in a few clicks.<br>

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

![WebUI](https://github.com/user-attachments/assets/581e1206-2abd-4b3c-ad31-80554ad92d99)

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
```python
map.generate()
```

The map will be saved in the `map_directory` directory.

## Supported objects
The project is based on the [OpenStreetMap](https://www.openstreetmap.org/) data. So, refer to [this page](https://wiki.openstreetmap.org/wiki/Map_Features) to understand the list below.
- "building": True
- "highway": ["motorway", "trunk", "primary"]
- "highway": ["secondary", "tertiary", "road"]
- "highway": ["unclassified", "residential", "track"]
- "natural": "grassland"
- "landuse": "farmland"
- "natural": ["water"]
- "waterway": True
- "natural": ["wood", "tree_row"]

The list will be updated as the project develops.

## Info sequence
The script will also generate the `generation_info.json` file in the `output` folder. It contains the following keys: <br>
`"coordinates"` - the coordinates of the map center which you entered,<br>
`"bbox"` - the bounding box of the map in lat and lon,<br>
`"map_height"` - the height of the map in meters (this one is from the user input, e.g. 2048 and so on),<br>
`"map_width"` - the width of the map in meters (same as above),<br>
`"minimum_x"` - the minimum x coordinate of the map (UTM projection),<br>
`"minimum_y"` - the minimum y coordinate of the map (UTM projection),<br>
`"maximum_x"` - the maximum x coordinate of the map (UTM projection),<br>
`"maximum_y"` - the maximum y coordinate of the map (UTM projection),<br>
`"height"` - the height of the map in meters (it won't be equal to the parameters above since the Earth is not flat, sorry flat-earthers),<br>
`"width"` - the width of the map in meters (same as above),<br>
`"height_coef"` - since we need a texture of exact size, the height of the map is multiplied by this coefficient,<br>
`"width_coef"` - same as above but for the width,<br>
`"tile_name"` - the name of the SRTM tile which was used to generate the height map, e.g. "N52E013"<br>

You can use this information to adjust some other sources of data to the map, e.g. textures, height maps, etc.

## For advanced users
The tool supports the custom size of the map. To use this feature select `Custom` in the `Map size` dropdown and enter the desired size. The tool will generate a map with the size you entered.<br>

⛔️ Do not use this feature, if you don't know what you're doing. In most cases the Giants Editor will just crash on opening the file, because you need to enter a specific values for the map size.<br><br>

![Advanced settings and custom size](https://github.com/user-attachments/assets/327b6065-09ed-41d0-86a8-7d904025707c)

You can also apply some advanced settings to the map generation process. Note that they're ADVANCED, so you don't need to use them if you're not sure what they do.<br>

Here's the list of the advanced settings:

- DEM multiplier: the height of the map is multiplied by this value. So the DEM map is just a 16-bit grayscale image, which means that the maximum avaiable value there is 65535, while the actual difference between the deepest and the highest point on Earth is about 20 km. So, by default this value is set to 3. Just note that this setting mostly does not matter, because you can always adjust it in the Giants Editor, learn more about the [heightScale](https://www.farming-simulator.org/19/terrain-heightscale.php) parameter on the [PMC Farming Simulator](https://www.farming-simulator.org/) website.

- DEM Blur radius: the radius of the Gaussian blur filter applied to the DEM map. By default, it's set to 21. This filter just makes the DEM map smoother, so the height transitions will be more natural. You can set it to 1 to disable the filter, but it will result as a Minecraft-like map.

## Bugs and feature requests
If you find a bug or have an idea for a new feature, please create an issue [here](https://github.com/iwatkot/maps4fs/issues) or contact me directly on [Telegram](https://t.me/iwatkot).<br>
