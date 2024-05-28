<div align="center" markdown>
<img src="https://i.postimg.cc/N0Hvm4p4/maps4fs-poster.png">

<p align="center">
  <a href="#Overview">Overview</a> • 
  <a href="#Features">Features</a> • 
  <a href="#Supported-objects">Supported objects</a> • 
  <a href="#How-To-Run">How-To-Run</a> • 
  <a href="Settings">Settings</a> • 
  <a href="#Bugs-and-feature-requests">Bugs and feature requests</a>
</p>

![GitHub release (latest SemVer)](https://img.shields.io/github/v/release/iwatkot/maps4fs)
![GitHub downloads](https://img.shields.io/github/downloads/iwatkot/maps4fs/total)
![GitHub issues](https://img.shields.io/github/issues/iwatkot/maps4fs)
[![Maintainability](https://api.codeclimate.com/v1/badges/b922fd0a7188d37e61de/maintainability)](https://codeclimate.com/github/iwatkot/maps4fs/maintainability) 

</div>

## Overview
The core idea is coming from the awesome [maps4cim](https://github.com/klamann/maps4cim) project.<br>
The main goal of this project is to generate map templates, based on real-world data, for the Farming Simulator. It's important to mention that **templates are not maps**. They are just a starting point for creating a map. This tool just uses built-in textures to highlight different types of terrain and buildings with correct shapes and scales and to generate a height map. The rest of the work is up to you. So if you thought that you could just run this tool and get a playable map, then I'm sorry to disappoint you. But if you are a map maker, then this tool will save you a lot of time.<br>
So, if you're new to map making, here's a quick overview of the process:
1. Generate a map template using this tool.
2. Download the Giants Editor.
3. Open the map template in the Giants Editor.
4. Now you can start creating your map (adding roads, fields, buildings, etc.).

## Features
- Allows to enter a location by lat and lon (e.g. from Google Maps).
- Allows to select a size of the map (2x2, 4x4, 8x8 km, 16x16 km).
- Generates a map template (check the list of supported objects in [this section](#supported-objects)).
- Generates a height map.

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

## How-To-Run
**Option 1 (recommended):**<br>
Using Telegram bot [@maps4fs](https://t.me/maps4fsbot).<br>
Note: due to CPU and RAM limitations of the hosting, only 2x2 and 4x4 km maps are available. If you need bigger maps, use the [local version](#option-2).<br>
ℹ️ By the way, since I don't want to spend a lot of money on hosting, the bot may be unavailable from time to time or even be shut down. If you want to support this project, you can donate using [Buy me a coffee](https://www.buymeacoffee.com/iwatkot0).

![Telegram bot](https://i.postimg.cc/tJZC3YHg/Kapture-2024-01-24-at-02-19-03.gif)
<br>

Using it is easy and doesn't require any guides. Enjoy!

**Option 2:**<br>
Launch the project locally following these steps (or watch the [video tutorial](https://youtu.be/OUzCO7SWKyA)):

1. Navigate to the [releases](https://github.com/iwatkot/maps4fs/releases) page and download the latest version of the tool. If you are familiar with Git, you can clone the repository instead.
2. Unzip the archive.
3. Install [Python 3.12](https://www.python.org/downloads/release/python-3120/) for your OS.
4. Launch the script to create a virtual environment, install dependencies and run the tool:
    - Windows: right-click on the `run.ps1` and select **Run with PowerShell** (if an error occurs, run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` in PowerShell)
    - Linux / Mac: execute the `sh run.sh` in a terminal in the tool's folder (this one will work on Windows too, if you have bash installed)
5. Minimalistic GUI will appear.
6. Copy lat and lon from Google Maps and paste them into the corresponding fields. To do this, right-click on someplace on the map and click on the coordinates which look like this: `52.520008, 13.404954`. The first number is the latitude, the second one is the longitude. This point will be the center of the map.
7. Select the size of the map (2048, 4096, 8192 or 16384 meters). The bigger the map, the longer it takes to generate it. Warning: to open huge maps in Giants Editor, you need a powerful PC. I don't recommend generating maps bigger than 8192 meters. By the way, the default map sizes in the Farming Simulator are 2048x2048 meters.
9. Check the advanced settings if you want to change something. I **strongly recommend changing the `max_height` value** to which suits the map better. For more plain-like maps, set it to lower values (e.g. 200). For mountainous maps, set it to higher values (e.g. 800).
10. Click on the **Generate** button.
11. Wait until the map is generated. It may take a while.
12. The map will be saved in the `output` folder in the tool's folder. You can open `output/maps/map/map.i3d` in the Giants Editor to check if everything is ok. If you need to run the script again, start with step 4. The script will delete the previous map and generate a new one.
13. Now you can copy the `output` folder somewhere and start creating your map in the Giants Editor.

**Option 3:**<br>
Using command line (not available yet). I'll add this on demand.

**Option 4:**<br>
Using the web version (not available yet). I'll add this on demand. But at the moment, I just don't want to host it by myself. But it's not a problem to add a simple web app.

## Settings
Advanced settings are available in the tool's UI under the **Advanced Settings** tab. Here's the list of them:
- `max_height` - the maximum height of the map. The default value is 400. Select smaller values for plain-like maps and bigger values for mountainous maps. You may need to experiment with this value to get the desired result.
- `blur_seed` - the seed for the blur algorithm. The default value is 5, which means 5 meters. The bigger the value, the smoother the map will be. The smaller the value, the more detailed the map will be. Keep in mind that for some regions, where terrain is bumpy, disabling the blur algorithm may lead to a very rough map. So, I recommend leaving this value as it is.

## Info sequence
The script will also generate the `generation_info.json` file in the `output` folder. It contains the following keys: <br>
`"coordinates"` - the coordinates of the map center which you entered,<br>
`"bbox"` - the bounding box of the map in lat and lon,<br>
`"distance"` - the size of the map in meters,<br>
`"minimum_x"` - the minimum x coordinate of the map (UTM projection),<br>
`"minimum_y"` - the minimum y coordinate of the map (UTM projection),<br>
`"maximum_x"` - the maximum x coordinate of the map (UTM projection),<br>
`"maximum_y"` - the maximum y coordinate of the map (UTM projection),<br>
`"height"` - the height of the map in meters (it won't be equal to the distance since the Earth is not flat, sorry flat-earthers),<br>
`"width"` - the width of the map in meters,<br>
`"height_coef"` - since we need a texture of exact size, the height of the map is multiplied by this coefficient,<br>
`"width_coef"` - same as above but for the width,<br>
`"tile_name"` - the name of the SRTM tile which was used to generate the height map, e.g. "N52E013"<br>

You can use this information to adjust some other sources of data to the map, e.g. textures, height maps, etc.

## Bugs and feature requests
If you find a bug or have an idea for a new feature, please create an issue [here](https://github.com/iwatkot/maps4fs/issues) or contact me directly on [Telegram](https://t.me/iwatkot).<br>
ℹ️ Please, don't bother me if the Telegram bot is down. As I said before this is related to the hosting limitations, if you want you can always run the tool locally or support the project by donating, so maybe I'll be able to afford better hosting.