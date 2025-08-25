# Maps4FS Python Package Deployment

The Python package deployment allows you to use Maps4FS directly from Python code with full programmatic control over map generation. This approach is recommended for developers who want to integrate Maps4FS into their own applications or need advanced customization.

## Features

🔴 **Skill level:** Advanced - Recommended for developers  
🗺️ **Supported map sizes:** 2x2, 4x4, 8x8, 16x16 km and any custom size  
✂️ **Map scaling:** Supported  
⚙️ **Advanced settings:** Enabled  
🖼️ **Texture dissolving:** Enabled  

## System Requirements

- Python 3.8 or later
- Git (for source code installation)
- 8 GB RAM for 2 km maps, 16 GB RAM for 4-8 km maps, 32 GB RAM for larger maps
- SSD storage (will work very slow on HDD)
- Windows 10/11 / Linux / MacOS

## Prerequisites

Before starting, make sure you have Python installed and working properly:

```bash
# Check Python version (should be 3.8 or later)
python --version

# Check if pip is available
pip --version
```

## Installation

There are two ways to install Maps4FS as a Python package:

### Option 1: Install from PyPI

**Skill level:** 🟡  
**Requires:** Python, pip

The easiest way is to install the package directly from PyPI:

```bash
pip install maps4fs
```

### Option 2: Install from Source Code

**Skill level:** 🔴  
**Requires:** Python, pip, Git

For developers who want the latest features or need to modify the source code:

```bash
# Clone the repository
git clone https://github.com/iwatkot/maps4fs.git
cd maps4fs

# Create virtual environment (Windows)
dev/create_venv.ps1

# Create virtual environment (Linux/Mac)
sh dev/create_venv.sh

# Activate the virtual environment (Windows)
./venv/scripts/activate

# Activate the virtual environment (Linux/Mac)
source venv/bin/activate

# Install dependencies and run demo
python demo.py
```

## Data Templates Setup

Maps4FS requires game templates and schemas to function properly. These should be placed in a `data` directory structure:

```text
📁 data
 ┣ 📄 fs22-map-template.zip
 ┣ 📄 fs25-map-template.zip
 ┗ 📄 fs22-texture-schema.json
```

**Important:** Download the `data` directory from the [Maps4FS repository](https://github.com/iwatkot/maps4fs/tree/main/data) and place it in the root of your project.

## Usage

### Basic Example

Here's a complete example of how to generate a map programmatically:

```python
import os
import maps4fs as mfs

# Configure game and providers
game_code = "fs25"  # or "fs22"
game = mfs.Game.from_code(game_code)
dtm_provider = mfs.dtm.SRTM30Provider

# Set map parameters
lat, lon = 45.28, 20.23  # Coordinates (latitude, longitude)
coordinates = (lat, lon)
size = 2048  # Map size in pixels
rotation = 25  # Map rotation in degrees

# Create output directory
map_directory = "generated_map"
os.makedirs(map_directory, exist_ok=True)

# Initialize map object
mp = mfs.Map(
    game,
    dtm_provider,
    None,  # Satellite provider (None for default)
    coordinates,
    size,
    rotation,
    map_directory,
)

# Generate the map with progress tracking
for component_name in mp.generate():
    print(f"Generating {component_name}...")

print(f"Map generation completed! Check the '{map_directory}' directory.")
```

### Advanced Configuration

You can customize various aspects of map generation:

```python
import maps4fs as mfs

# Use different DTM providers
dtm_provider = mfs.dtm.ASTER30Provider  # or SRTM30Provider, etc.

# Configure satellite imagery
satellite_provider = mfs.satellite.EsriProvider

# Custom map sizes and settings
size = 4096  # Larger map
rotation = 0  # No rotation

# Initialize with custom providers
mp = mfs.Map(
    game,
    dtm_provider,
    satellite_provider,
    coordinates,
    size,
    rotation,
    map_directory,
)
```

## Example Files

➡️ Check out the [demo.py](../demo.py) file in the repository for a complete working example.

The demo file includes:
- Basic map generation setup
- Parameter configuration examples  
- Progress tracking implementation
- Error handling examples

## Troubleshooting

### Common Issues

1. **Missing templates error:**
   - Ensure the `data` directory is present in your project root
   - Download templates from the official repository

2. **Memory errors during generation:**
   - Reduce map size or increase available RAM
   - Use smaller DTM providers for testing

3. **Import errors:**
   - Verify Maps4FS is installed: `pip list | grep maps4fs`
   - Check Python version compatibility

### Getting Help

For development-related questions and advanced usage:
- Check the [API documentation](https://github.com/iwatkot/maps4fs)
- Browse [example scripts](../demo.py) in the repository
- Report issues on [GitHub Issues](https://github.com/iwatkot/maps4fs/issues)