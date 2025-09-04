<p align="center">
<a href="https://github.com/iwatkot/maps4fs">maps4fs</a> •
<a href="https://github.com/iwatkot/maps4fsui">maps4fs UI</a> •
<a href="https://github.com/iwatkot/maps4fsdata">maps4fs Data</a> •
<a href="https://github.com/iwatkot/maps4fsapi">maps4fs API</a> •
<a href="https://github.com/iwatkot/maps4fsstats">maps4fs Stats</a> •
<a href="https://github.com/iwatkot/maps4fsbot">maps4fs Bot</a><br>
<a href="https://github.com/iwatkot/pygmdl">pygmdl</a> •
<a href="https://github.com/iwatkot/pydtmdl">pydtmdl</a>
</p>

<div align="center" markdown>
<a href="https://discord.gg/Sj5QKKyE42">
<img src="https://github.com/user-attachments/assets/37043333-d6ef-4ca3-9f3c-81323d9d0b71">
</a>

<p align="center">
  <a href="#overview">Overview</a> •
  <a href="docs/003_howtolaunch.md">How to Run</a> •
  <a href="docs/002_stepbystep.md">Step-by-Step Guide</a> •
  <a href="docs/009_workflow.md">Workflow Optimization</a><br>
  <a href="docs/FAQ.md">FAQ</a> •
  <a href="docs/get_help.md">Get Help</a> •
  <a href="docs/map_structure.md">Map Structure</a> •
  <a href="docs/010_mainsettings.md">Main Settings</a><br>
  <a href="docs/013_generationinfo.md">Generation info</a> •
  <a href="docs/012_textureschema.md">Texture schema</a><br>
  <a href="#DDS-conversion">DDS conversion</a> •
  <a href="docs/011_generationsettings.md">Generation settings</a> •
  <a href="#Resources">Resources</a> •
  <a href="#Bugs-and-feature-requests">Bugs and feature requests</a><br>
  <a href="docs/procedural_generation.md">Procedural Generation</a> •
  <a href="#Special-thanks">Special thanks</a>
</p>

[![Join Discord](https://img.shields.io/badge/join-discord-blue)](https://discord.gg/Sj5QKKyE42)
[![GitHub release (latest SemVer)](https://img.shields.io/github/v/release/iwatkot/maps4fs)](https://github.com/iwatkot/maps4fs/releases)
[![PyPI - Version](https://img.shields.io/pypi/v/maps4fs)](https://pypi.org/project/maps4fs)
[![Docker Pulls](https://img.shields.io/docker/pulls/iwatkot/maps4fs)](https://hub.docker.com/repository/docker/iwatkot/maps4fs/general)
[![GitHub issues](https://img.shields.io/github/issues/iwatkot/maps4fs)](https://github.com/iwatkot/maps4fs/issues)<br>
[![PyPI - Downloads](https://img.shields.io/pypi/dm/maps4fs)](https://pypi.org/project/maps4fs)
[![Checked with mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](https://mypy-lang.org/)
[![Build Status](https://github.com/iwatkot/maps4fs/actions/workflows/checks.yml/badge.svg)](https://github.com/iwatkot/maps4fs/actions)
[![codecov](https://codecov.io/gh/iwatkot/maps4fs/graph/badge.svg?token=NSKPFSKJXI)](https://codecov.io/gh/iwatkot/maps4fs)
[![GitHub Repo stars](https://img.shields.io/github/stars/iwatkot/maps4fs)](https://github.com/iwatkot/maps4fs/stargazers)<br>

</div>

🗺️ Supports 2x2, 4x4, 8x8, 16x16 and any custom size maps<br>
🔗 Generate maps using an [API](https://github.com/iwatkot/maps4fsapi)<br>
✂️ Supports map scaling<br>
🔄 Support map rotation<br>
🌐 Supports custom [DTM Providers](https://github.com/iwatkot/pydtmdl)<br>
🌾 Automatically generates fields<br>
🌽 Automatically generates farmlands<br>
🌿 Automatically generates decorative foliage<br>
🌲 Automatically generates forests<br>
🌊 Automatically generates water planes<br>
📈 Automatically generates splines<br>
🛰️ Automatically downloads high resolution satellite images<br>
🌍 Based on real-world data from OpenStreetMap<br>
🗺️ Supports [custom OSM maps](/docs/008_customosm.md)<br>
🏞️ Generates height map using SRTM dataset<br>
📦 Provides a ready-to-use map template for the Giants Editor<br>
🚜 Supports Farming Simulator 22 and 25<br>
🔷 Generates \*.obj files for background terrain based on the real-world height map<br>
📄 Generates scripts to download high-resolution satellite images from [QGIS](https://qgis.org/download/) in one click<br>
📕 Detailed [documentation](/docs) and tutorials <br>

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
<img src="https://github.com/user-attachments/assets/891911d7-081d-431e-a677-b4ae96870286"><br>
🌲 Allows to select trees for generation.<br><br>
<img src="https://github.com/user-attachments/assets/cce7d4e0-cba2-4dd2-b22d-03137fb2e860"><br>
🌊 Automatically generates water planes.<br><br>
<img src="https://github.com/user-attachments/assets/0b05b511-a595-48e7-a353-8298081314a4"><br>
📈 Automatically generates splines.<br><br>
<img src="https://github.com/user-attachments/assets/0957db9e-7b95-4951-969c-9d1edd9f073b"><br>
🖌️ Allows customization of the texture schema.<br><br>
<img src="https://github.com/user-attachments/assets/80e5923c-22c7-4dc0-8906-680902511f3a"><br>
🗒️ True-to-life blueprints for fast and precise modding.<br><br>
<img width="480" src="https://github.com/user-attachments/assets/1a8802d2-6a3b-4bfa-af2b-7c09478e199b"><br>
🌾 Field generation with one click.<br><br>
<img width="480" src="https://github.com/user-attachments/assets/4d1fa879-5d60-438b-a84e-16883bcef0ec"><br>
🌽 Automatic farmlands generation based on the fields.<br><br>

📹 Check out the complete playlist of video turorials on [YouTube](https://www.youtube.com/watch?v=hPbJZ0HoiDE&list=PLug0g7UYHX8D1Jik6NkJjQhdxqS-NOtB9). 🆕<br>

![Map example](https://github.com/user-attachments/assets/c46a3581-dd17-462f-b815-e36d4f724947)

<p align="center"><i>Map example generated with maps4fs.</i></p>

## Overview

The core idea is coming from the awesome [maps4cim](https://github.com/klamann/maps4cim) project.<br>

The main goal of this project is to generate map templates, based on real-world data, for the Farming Simulator. It's important to mention that **templates are not maps**. They are just a starting point for creating a map. This tool just uses built-in textures to highlight different types of terrain and buildings with correct shapes and scales and to generate a height map. The rest of the work is up to you. So if you thought that you could just run this tool and get a playable map, then I'm sorry to disappoint you. But if you are a map maker, then this tool will save you a lot of time.<br>
So, if you're new to map making, here's a quick overview of the process:

1. Generate a map template using this tool.
2. Download the Giants Editor.
3. Open the map template in the Giants Editor.
4. Now you can start creating your map (adding roads, fields, buildings, etc.).


## DDS conversion

The `.dds` format is the format used in the Farming Simulator for the textures, icons, overview, and preview images. There a plenty of options to convert the images to the `.dds` format, you can just google something like `png to dds`, and the first link probably will help you with it.<br>

List of the important DDS files:

- `icon.dds` - 256x256 pixels, the icon of the map,
- `preview.dds` - 2048x2048 pixels, the preview image of the map on the loading screen,
- `overview.dds` - 4096x4096 pixels, the overview image of the map (in-game map)

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

➡️ Please, before creating an issue or asking some questions, check the [FAQ](docs/FAQ.md) section and the follow the [docs/get_help.md](Get Help) instructions.

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
- [H4rdB4se](https://github.com/H4rdB4se) - for investigating the issue with custom OSM files and finding a proper way to work with the files in JOSM.
- [kbrandwijk](https://github.com/kbrandwijk) - for providing [awesome tool](https://github.com/Paint-a-Farm/satmap_downloader) to download the satellite images from the Google Maps and giving a permission to modify it and create a Python Package.
- [Maaslandmods](https://github.com/Maaslandmods) - for the awesome idea to edit the tree schema in UI, images and code snippets on how to do it.
- [StrauntMaunt](https://gitlab.com/StrauntMaunt) - for developing procedural generation scripts, providing with the required updates for maps4fs and preparing the docs on how to use procedural generation.
