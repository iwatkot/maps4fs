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
  <a href="https://maps4fs.gitbook.io/docs/getting-started/how_to_launch">How to Launch</a> •
  <a href="https://maps4fs.gitbook.io/docs/getting-started/step_by_step_guide">Step-by-Step Guide</a> •
  <a href="https://maps4fs.gitbook.io/docs/getting-started/workflow_optimizations">Workflow Optimizations</a><br>
  <a href="https://maps4fs.gitbook.io/docs/getting-started/faq">FAQ</a> •
  <a href="https://maps4fs.gitbook.io/docs/setup-and-installation/get_help">Get Help</a> •
  <a href="#Resources">Resources</a> •
  <a href="#Special-thanks">Special thanks</a> •
  <a href="https://www.youtube.com/watch?v=hPbJZ0HoiDE&list=PLug0g7UYHX8D1Jik6NkJjQhdxqS-NOtB9">Video Tutorials</a>
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
🗺️ Supports [custom OSM maps](https://maps4fs.gitbook.io/docs/advanced-topics/custom_osm)<br>
🏞️ Generates height map using SRTM dataset<br>
📦 Provides a ready-to-use map template for the Giants Editor<br>
🚜 Supports Farming Simulator 22 and 25<br>
🔷 Generates \*.obj files for background terrain based on the real-world height map<br>
📕 Detailed [documentation](https://maps4fs.gitbook.io/docs) and tutorials <br>

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
<img src="https://github.com/user-attachments/assets/0b05b511-a595-48e7-a353-8298081314a4"><br>
📈 Automatically generates splines.<br><br>
<img width="480" src="https://github.com/user-attachments/assets/1a8802d2-6a3b-4bfa-af2b-7c09478e199b"><br>
🌾 Field generation with one click.<br><br>
<img width="480" src="https://github.com/user-attachments/assets/4d1fa879-5d60-438b-a84e-16883bcef0ec"><br>
🌽 Automatic farmlands generation based on the fields.<br><br>

## Overview

The core idea originates from the excellent [maps4cim](https://github.com/klamann/maps4cim) project.<br>

The main goal of this project is to generate map templates based on real-world data for Farming Simulator. It's important to understand that **templates are not finished maps**. They serve as a foundation for map creation, using built-in textures to represent different terrain types and structures with accurate shapes and scales, along with generating realistic height maps. The detailed work of creating a complete, playable map remains with you. If you expected to simply run this tool and receive a ready-to-play map, this may not meet those expectations. However, if you're a map creator, this tool will significantly reduce your development time.<br>

For newcomers to map creation, here's the typical workflow:

1. Generate a map template using this tool.
2. Download the Giants Editor.
3. Open the generated template in Giants Editor.
4. Begin detailed map development (adding roads, fields, buildings, etc.).

## Resources

This section lists essential tools required for Farming Simulator map creation.<br>
For basic map development, you only need Giants Editor. However, creating background terrain—the surrounding world that prevents your map from appearing to float in empty space—requires additional tools: Blender with the official exporter plugins. For realistic background terrain textures, QGIS is needed to obtain high-resolution satellite imagery.<br>

1. [Giants Editor](https://gdn.giants-software.com/downloads.php) - Official map creation tool for Farming Simulator
2. [Blender](https://www.blender.org/download/) - Open-source 3D modeling software for creating Farming Simulator assets
3. [Blender Exporter Plugins](https://gdn.giants-software.com/downloads.php) - Official plugins for exporting models from Blender to i3d format (Farming Simulator's native format)

## Special thanks

First and foremost, thanks to our direct [contributors](https://github.com/iwatkot/maps4fs/graphs/contributors) who have made code contributions to the project.

Additionally, we extend gratitude to community members who have supported the project through feedback, testing, and expertise, even without direct code contributions:

- [Ka5tis](https://github.com/Ka5tis) - Investigated the "spiky terrain" issue and discovered the solution: increasing `DisplacementLayer` size values
- [Kalderone](https://www.youtube.com/@Kalderone_FS22) - Provided valuable feedback, suggestions, and expert guidance on map-making processes, highlighting crucial Giants Editor settings
- [kirasolda](https://github.com/kirasolda) - Offered expert Blender advice, assisted with background terrain processing, and created detailed tutorials for preparing OBJ files for Giants Editor
- [BFernaesds](https://github.com/BFernaesds) - Conducted comprehensive manual application testing
- [gamerdesigns](https://github.com/gamerdesigns) - Performed thorough manual application testing
- [Tox3](https://github.com/Tox3) - Contributed extensive manual application testing
- [Lucandia](https://github.com/Lucandia) - Developed the excellent StreamLit [STL file preview widget](https://github.com/Lucandia/streamlit_stl)
- [H4rdB4se](https://github.com/H4rdB4se) - Investigated custom OSM file compatibility issues and established proper JOSM workflow procedures
- [kbrandwijk](https://github.com/kbrandwijk) - Created the [satellite image downloader tool](https://github.com/Paint-a-Farm/satmap_downloader) for Google Maps and granted permission for modification and Python package creation
- [Maaslandmods](https://github.com/Maaslandmods) - Conceived the UI tree schema editing feature and provided implementation images and code examples
- [StrauntMaunt](https://gitlab.com/StrauntMaunt) - Developed procedural generation scripts, provided essential Maps4FS updates, and authored procedural generation documentation
