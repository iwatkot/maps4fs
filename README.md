<div align="center" markdown>

[![Maps4FS](https://img.shields.io/badge/maps4fs-gray?style=for-the-badge)](https://github.com/iwatkot/maps4fs)
[![PYDTMDL](https://img.shields.io/badge/pydtmdl-blue?style=for-the-badge)](https://github.com/iwatkot/pydtmdl)
[![PYGDMDL](https://img.shields.io/badge/pygmdl-teal?style=for-the-badge)](https://github.com/iwatkot/pygmdl)  
[![Maps4FS API](https://img.shields.io/badge/maps4fs-api-green?style=for-the-badge)](https://github.com/iwatkot/maps4fsapi)
[![Maps4FS UI](https://img.shields.io/badge/maps4fs-ui-blue?style=for-the-badge)](https://github.com/iwatkot/maps4fsui)
[![Maps4FS Data](https://img.shields.io/badge/maps4fs-data-orange?style=for-the-badge)](https://github.com/iwatkot/maps4fsdata)
[![Maps4FS ChromaDocs](https://img.shields.io/badge/maps4fs-chromadocs-orange?style=for-the-badge)](https://github.com/iwatkot/maps4fschromadocs)  
[![Maps4FS Upgrader](https://img.shields.io/badge/maps4fs-upgrader-yellow?style=for-the-badge)](https://github.com/iwatkot/maps4fsupgrader)
[![Maps4FS Stats](https://img.shields.io/badge/maps4fs-stats-red?style=for-the-badge)](https://github.com/iwatkot/maps4fsstats)
[![Maps4FS Bot](https://img.shields.io/badge/maps4fs-bot-teal?style=for-the-badge)](https://github.com/iwatkot/maps4fsbot)

</div>

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

🚜 **Farming Simulator 22 & 25** - Generate maps for both game versions<br>
🗺️ **Flexible Map Sizes** - 2x2, 4x4, 8x8, 16x16 km + custom sizes<br>
✂️ **Map Scaling & Rotation** - Perfect positioning and sizing control<br>
🏘️ **Adding buildings** - Automatic building placement system<br>

🌍 **Real-World Foundation** - Built from OpenStreetMap and satellite data<br>
🏞️ **Accurate Terrain** - SRTM elevation data with custom DTM support<br>
🛰️ **High-Resolution Imagery** - Automatic satellite texture downloads<br>

🌾 **Smart Field Generation** - Automatic farmable area detection<br>
🌳 **Intelligent Farmlands** - Property boundaries based on real data<br>
🌲 **Natural Forests** - Tree placement with customizable density<br>
🌊 **Water Systems** - Rivers, lakes, and water planes<br>
🌿 **Decorative Foliage** - Realistic vegetation and grass areas<br>
🏘️ **Intelligent Building Placement** - Automatic building placement in appropriate areas<br>

🚧 **3D Road Generation** - Automatic road mesh creation with custom textures<br>
🚧 **Complete Spline Networks** - Roads and infrastructure<br>
🔷 **Background Terrain** - 3D *.obj files for surrounding landscape<br>
📦 **Giants Editor Ready** - Import and start building immediately<br>

🗺️ **Advanced Customization** - [Custom OSM maps](https://maps4fs.gitbook.io/docs/advanced-topics/custom_osm) and elevation data<br>
📚 **Complete Documentation** - [Detailed guides](https://maps4fs.gitbook.io/docs) and video tutorials<br>

<p align="center">
<img src="https://github.com/iwatkot/maps4fs/releases/download/2.9.40/mfsg2.gif"><br>
<i>Example of map generated with Maps4FS with no manual edits.</i>
</p>

## Overview

The core idea originates from the excellent [maps4cim](https://github.com/klamann/maps4cim) project.<br>

The main goal of this project is to generate map templates based on real-world data for Farming Simulator. It's important to understand that **templates are not finished maps**. They serve as a foundation for map creation, using built-in textures to represent different terrain types and structures with accurate shapes and scales, along with generating realistic height maps. The detailed work of creating a complete, playable map remains with you. If you expected to simply run this tool and receive a ready-to-play map, this may not meet those expectations. However, if you're a map creator, this tool will significantly reduce your development time.<br>

![Maps4FS Interface](https://github.com/iwatkot/maps4fsapi/releases/download/2.6.0/screenshot-localhost-3000-1757595208136.png)

![My Maps Interface](https://github.com/iwatkot/maps4fsui/releases/download/2.6.0.1/screenshot-localhost-3000-1757595594033.png)

For newcomers to map creation, here's the typical workflow:

1. Generate a map template using this tool.
2. Download the Giants Editor.
3. Open the generated template in Giants Editor.
4. Begin detailed map development (adding roads, fields, buildings, etc.).

## Resources

This section lists essential tools required for Farming Simulator map creation.<br>
For basic map development, you only need Giants Editor. However, creating background terrain—the surrounding world that prevents your map from appearing to float in empty space—requires additional tools: Blender with the official exporter plugins.<br>

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
