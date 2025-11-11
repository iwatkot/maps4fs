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

## Step 1: Python Installation

### Windows

1. **Download Python:**
   - Go to [python.org](https://www.python.org/downloads/windows/)
   - Download the latest Python 3.8+ installer (recommended: Python 3.11 or newer)
   - Choose the "Windows installer (64-bit)" for most users

2. **Install Python:**
   - Run the downloaded installer
   - ⚠️ **IMPORTANT:** Check "Add Python to PATH" during installation
   - Choose "Install Now" or "Customize installation"
   - If customizing, ensure "pip" and "Add Python to environment variables" are selected

3. **Verify installation:**
   ```cmd
   python --version
   pip --version
   ```
   Both commands should return version information.

### macOS

1. **Option A: Official Installer (Recommended)**
   - Go to [python.org](https://www.python.org/downloads/mac-osx/)
   - Download the latest Python 3.8+ installer
   - Run the `.pkg` file and follow the installation wizard

2. **Option B: Using Homebrew**
   ```bash
   # Install Homebrew first if you don't have it
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   
   # Install Python
   brew install python
   ```

3. **Verify installation:**
   ```bash
   python3 --version
   pip3 --version
   ```

### Linux

#### Ubuntu/Debian:
```bash
# Update package list
sudo apt update

# Install Python and pip
sudo apt install python3 python3-pip python3-venv

# Verify installation
python3 --version
pip3 --version
```

#### CentOS/RHEL/Fedora:
```bash
# CentOS/RHEL
sudo yum install python3 python3-pip

# Fedora
sudo dnf install python3 python3-pip

# Verify installation
python3 --version
pip3 --version
```

## Step 2: Git Installation (Optional, for source installation)

### Windows
1. Go to [git-scm.com](https://git-scm.com/download/win)
2. Download and run the installer
3. Use default settings during installation
4. Verify: `git --version`

### macOS
```bash
# Option 1: Using Homebrew
brew install git

# Option 2: Using Xcode Command Line Tools
xcode-select --install
```

### Linux
```bash
# Ubuntu/Debian
sudo apt install git

# CentOS/RHEL
sudo yum install git

# Fedora
sudo dnf install git
```

## Step 3: Check Prerequisites

Before installing Maps4FS, verify your environment is ready:

### Windows Command Prompt or PowerShell:
```cmd
python --version
pip --version
git --version
```

### macOS/Linux Terminal:
```bash
python3 --version
pip3 --version
git --version
```

All commands should return version information without errors.

## Step 4: Create a Project Directory

It's recommended to create a dedicated directory for your Maps4FS project:

### Windows:
```cmd
mkdir C:\Maps4FS-Project
cd C:\Maps4FS-Project
```

### macOS/Linux:
```bash
mkdir ~/Maps4FS-Project
cd ~/Maps4FS-Project
```

## Step 5: Maps4FS Installation

There are two ways to install Maps4FS as a Python package:

### Option 1: Install from PyPI (Recommended for Beginners)

**Skill level:** 🟡 Beginner-friendly  
**Requires:** Python, pip

This is the easiest and most reliable method:

#### Windows:
```cmd
# Install Maps4FS
pip install maps4fs

# Verify installation
python -c "import maps4fs; print('Maps4FS installed successfully!')"
```

#### macOS/Linux:
```bash
# Install Maps4FS
pip3 install maps4fs

# Verify installation
python3 -c "import maps4fs; print('Maps4FS installed successfully!')"
```

### Option 2: Install from Source Code (Advanced)

**Skill level:** 🔴 Advanced developers  
**Requires:** Python, pip, Git

For developers who want the latest features or need to modify the source code:

#### Windows:
```cmd
# Clone the repository
git clone https://github.com/iwatkot/maps4fs.git
cd maps4fs

# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate

# Install dependencies
pip install -r dev/requirements.txt

# Install Maps4FS in development mode
pip install -e .

# Test installation
python demo.py
```

#### macOS/Linux:
```bash
# Clone the repository
git clone https://github.com/iwatkot/maps4fs.git
cd maps4fs

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r dev/requirements.txt

# Install Maps4FS in development mode
pip install -e .

# Test installation
python demo.py
```

#### 💡 **Even Easier: Automated Setup Scripts**

Maps4FS includes convenient automation scripts that handle all the setup for you:

**Windows (PowerShell):**
```cmd
# Clone the repository
git clone https://github.com/iwatkot/maps4fs.git
cd maps4fs

# Run the automated setup script
powershell -ExecutionPolicy Bypass -File dev/create_venv.ps1

# The script automatically:
# - Creates virtual environment
# - Activates it
# - Installs all dependencies
# - Sets up Maps4FS in development mode

# Test installation
python demo.py
```

**macOS/Linux (Bash):**
```bash
# Clone the repository
git clone https://github.com/iwatkot/maps4fs.git
cd maps4fs

# Run the automated setup script
bash dev/create_venv.sh

# The script automatically:
# - Creates virtual environment
# - Activates it  
# - Installs all dependencies
# - Sets up Maps4FS in development mode

# Test installation
python demo.py
```

**Benefits of automation scripts:**
- ✅ **One command setup** - No need to remember multiple steps
- ✅ **Error handling** - Scripts check for prerequisites and handle common issues
- ✅ **Consistent environment** - Same setup every time
- ✅ **Platform optimized** - Different scripts for Windows vs Unix systems
- ✅ **Time saving** - Perfect for quick setup or CI/CD

#### 💡 **Pro Tip: Using Visual Studio Code**

For the best development experience with source installation:

1. **Install VS Code:** Download from [code.visualstudio.com](https://code.visualstudio.com/)

2. **Open the project:**
   ```bash
   # After cloning the repository
   cd maps4fs
   code .  # Opens the project in VS Code
   ```

3. **Install recommended extensions** when prompted (Python extension)

4. **Edit and run easily:**
   - Open `demo.py` in VS Code
   - Modify coordinates, map size, or other parameters as needed
   - Press **F5** to run with debugger, or **Ctrl+F5** to run without debugger
   - The project includes pre-configured launch settings for easy debugging

This approach is perfect for:
- **Experimenting** with different settings
- **Learning** how Maps4FS works internally
- **Contributing** to the project
- **Debugging** generation issues

### Virtual Environment (Recommended)

Using a virtual environment is highly recommended to avoid conflicts with other Python packages:

#### Windows:
```cmd
# Create virtual environment
python -m venv maps4fs-env

# Activate it
maps4fs-env\Scripts\activate

# Install Maps4FS
pip install maps4fs

# When you're done, deactivate
deactivate
```

#### macOS/Linux:
```bash
# Create virtual environment
python3 -m venv maps4fs-env

# Activate it
source maps4fs-env/bin/activate

# Install Maps4FS
pip install maps4fs

# When you're done, deactivate
deactivate
```

## Step 6: Download Required Data Templates

Maps4FS requires game templates and schemas to function properly. You need to download these files manually:

### Download Method 1: Direct Download (Recommended)

1. **Go to the Maps4FS repository:** [https://github.com/iwatkot/maps4fs](https://github.com/iwatkot/maps4fs)

2. **Click the green "Code" button** → **"Download ZIP"**

3. **Extract the ZIP file** and copy the `templates` folder to your project directory

### Download Method 2: Using Git

```bash
# Clone just the templates (if you only need data files)
git clone --depth 1 https://github.com/iwatkot/maps4fs.git temp-repo
cp -r temp-repo/templates ./templates
rm -rf temp-repo  # Clean up
```

### Required Directory Structure

After downloading, your project directory should look like this:

```text
📁 Your-Project-Directory/
 ┣ 📁 templates/
 ┃  ┣ � fs22/
 ┃  ┃  ┣ 📄 map-template.zip
 ┃  ┃  ┗ 📄 texture-schema.json
 ┃  ┣ � fs25/
 ┃  ┃  ┣ 📄 map-template.zip
 ┃  ┃  ┣ 📄 texture-schema.json
 ┃  ┃  ┣ 📄 tree-schema.json
 ┃  ┃  ┗ 📄 buildings-schema.json
 ┃  ┗ 📄 [additional template files...]
 ┗ 📄 your-python-script.py
```

### Verify Templates

Create a simple test script to verify your setup:

**Windows (test_setup.py):**
```python
import os
import maps4fs as mfs

# Check if templates directory exists
if os.path.exists("templates"):
    print("✅ Templates directory found")
    
    # Check for required files
    fs25_template = "templates/fs25/map-template.zip"
    fs25_schema = "templates/fs25/texture-schema.json"
    
    if os.path.exists(fs25_template):
        print("✅ FS25 map template found")
    else:
        print("❌ FS25 map template missing")
        
    if os.path.exists(fs25_schema):
        print("✅ FS25 texture schema found")
    else:
        print("❌ FS25 texture schema missing")
        
    print("🎉 Setup appears to be working!")
else:
    print("❌ Templates directory not found")
    print("Please download the templates folder from the repository")
```

**Run the test:**
```cmd
python test_setup.py
```

## Step 7: Your First Map

Now let's create your first map! Create a new Python file called `my_first_map.py`:

### Complete Beginner Example

```python
import os
import maps4fs as mfs

# Step 1: Choose your game version
print("🎮 Setting up game...")
game_code = "fs25"  # Use "fs22" for Farming Simulator 22
game = mfs.Game.from_code(game_code)
print(f"✅ Game: {game_code.upper()}")

# Step 2: Choose location (latitude, longitude)
# Some example coordinates:
# Paris, France: (48.8566, 2.3522)
# New York, USA: (40.7128, -74.0060)
# Tokyo, Japan: (35.6762, 139.6503)
# Sydney, Australia: (-33.8688, 151.2093)

lat, lon = 48.8566, 2.3522  # Paris, France
coordinates = (lat, lon)
print(f"📍 Location: {lat}, {lon}")

# Step 3: Set map parameters
size = 2048  # Map size in pixels (2048 = 2x2 km map)
rotation = 0  # Map rotation in degrees (0 = no rotation)
print(f"🗺️ Map size: {size}x{size} pixels")

# Step 4: Choose terrain data provider
dtm_provider = mfs.dtm.SRTM30Provider  # Good global coverage
print("🏔️ Using SRTM30 terrain data")

# Step 5: Create output directory
map_directory = "my_first_map"
os.makedirs(map_directory, exist_ok=True)
print(f"📁 Output directory: {map_directory}")

# Step 6: Initialize the map
print("\n🚀 Initializing map generation...")
try:
    mp = mfs.Map(
        game,
        dtm_provider,
        None,  # dtm_provider_settings (None for default)
        coordinates,
        size,
        rotation,
        map_directory,
    )
    print("✅ Map initialized successfully!")
except Exception as e:
    print(f"❌ Error initializing map: {e}")
    print("💡 Make sure you have downloaded the templates folder!")
    exit(1)

# Step 7: Generate the map
print("\n🔄 Starting map generation...")
print("This may take several minutes depending on your computer...")

try:
    component_count = 0
    for component_name in mp.generate():
        component_count += 1
        print(f"[{component_count}/6] Generating {component_name}...")
    
    print(f"\n🎉 SUCCESS! Map generation completed!")
    print(f"📂 Your map is ready in the '{map_directory}' folder")
    print(f"🎮 You can now copy this folder to your Farming Simulator mods directory")
    
except Exception as e:
    print(f"\n❌ Error during generation: {e}")
    print("💡 Check the console output above for more details")
```

### Run Your First Map

Save the code above as `my_first_map.py` and run it:

#### Windows:
```cmd
python my_first_map.py
```

#### macOS/Linux:
```bash
python3 my_first_map.py
```

### Expected Output

You should see output like this:
```
🎮 Setting up game...
✅ Game: FS25
📍 Location: 48.8566, 2.3522
🗺️ Map size: 2048x2048 pixels
🏔️ Using SRTM30 terrain data
📁 Output directory: my_first_map

🚀 Initializing map generation...
✅ Map initialized successfully!

🔄 Starting map generation...
This may take several minutes depending on your computer...
[1/6] Generating Background...
[2/6] Generating Satellite...
[3/6] Generating Texture...
[4/6] Generating Buildings...
[5/6] Generating Config...
[6/6] Generating Package...

🎉 SUCCESS! Map generation completed!
📂 Your map is ready in the 'my_first_map' folder
🎮 You can now copy this folder to your Farming Simulator mods directory
```

## Advanced Examples

### Custom Map Sizes

```python
import maps4fs as mfs

# Different map sizes (larger = more detail, but takes longer)
size_options = {
    "2x2 km": 2048,    # Quick generation, small map
    "4x4 km": 4096,    # Medium generation time, medium map  
    "8x8 km": 8192,    # Slow generation, large map
    "16x16 km": 16384  # Very slow generation, huge map
}

# Choose your preferred size
size = size_options["4x4 km"]
```

### Different Terrain Providers

```python
# Global providers (work worldwide)
global_providers = {
    "SRTM30": mfs.dtm.SRTM30Provider,    # 30m resolution, good for most areas
    "ASTER30": mfs.dtm.ASTER30Provider,  # 30m resolution, alternative to SRTM
}

# High-resolution providers (specific regions only)
hires_providers = {
    "Germany": mfs.dtm.GermanyProvider,           # 1m resolution
    "Netherlands": mfs.dtm.NetherlandsProvider,   # 1m resolution  
    "USA": mfs.dtm.USGSProvider,                  # 10m resolution
    # Add more as available
}

# Example: Use high-res data for German coordinates
lat, lon = 52.5200, 13.4050  # Berlin, Germany
dtm_provider = hires_providers["Germany"]
```

### Map Rotation

```python
# Rotate your map to align with roads or features
rotation_examples = {
    "No rotation": 0,
    "Slight tilt": 15,
    "Quarter turn": 90,
    "Upside down": 180,
}

rotation = rotation_examples["Slight tilt"]
```

### Multiple Maps Generation

```python
import maps4fs as mfs

# Generate multiple maps from different locations
locations = {
    "Paris": (48.8566, 2.3522),
    "London": (51.5074, -0.1278),
    "Berlin": (52.5200, 13.4050),
    "Rome": (41.9028, 12.4964),
}

game = mfs.Game.from_code("fs25")
dtm_provider = mfs.dtm.SRTM30Provider

for city_name, (lat, lon) in locations.items():
    print(f"\n🌍 Generating map for {city_name}...")
    
    map_directory = f"map_{city_name.lower()}"
    
    mp = mfs.Map(
        game,
        dtm_provider,
        None,
        (lat, lon),
        2048,  # 2x2 km maps
        0,     # No rotation
        map_directory,
    )
    
    for component in mp.generate():
        print(f"  Generating {component}...")
    
    print(f"✅ {city_name} map completed!")

print("\n🎉 All maps generated successfully!")
```

## Example Files & Learning Resources

### 📝 **demo.py - Your Best Starting Point**

➡️ **Check out the [demo.py](../demo.py) file in the repository** - it's the perfect starting point for learning Maps4FS!

The demo file is a complete, real-world example that includes:

#### 🎯 **What's Inside:**
- **Complete map generation workflow** from start to finish
- **Parameter configuration examples** with explanations
- **Progress tracking implementation** to see generation status
- **Error handling examples** to deal with common issues
- **Multiple coordinate examples** for different locations
- **Commented code** explaining each step

#### 🚀 **How to Use It:**

**Method 1: Quick Start (PyPI Installation)**
```python
# Download just the demo.py file from GitHub
# https://github.com/iwatkot/maps4fs/blob/main/demo.py
# Save it to your project directory and run:
python demo.py
```

**Method 2: Full Source Access (Recommended for Learning)**
```bash
# Clone the repository to get demo.py and all resources
git clone https://github.com/iwatkot/maps4fs.git
cd maps4fs

# Set up environment (see installation steps above)
# Then simply run:
python demo.py
```

**Method 3: VS Code Development (Best for Experimentation)**
```bash
# Clone and open in VS Code
git clone https://github.com/iwatkot/maps4fs.git
cd maps4fs
code .

# Open demo.py and press F5 to run with debugger
# Perfect for experimenting and learning!
```

#### 🔧 **Customization Examples:**

The demo.py file is designed to be easily modified. Common customizations:

```python
# Change location (edit these lines in demo.py):
lat, lon = 48.8566, 2.3522  # Paris
# To:
lat, lon = 40.7128, -74.0060  # New York

# Change map size:
size = 2048  # 2x2 km
# To:
size = 4096  # 4x4 km

# Change game version:
game_code = "fs25"
# To:
game_code = "fs22"
```

#### 💡 **Why Start with demo.py?**
- **Tested & Working:** It's guaranteed to work if your environment is set up correctly
- **Real Example:** Shows actual production-ready code, not just snippets
- **Educational:** Learn best practices and proper error handling
- **Customizable:** Easy to modify for your specific needs
- **Debugging Ready:** If using VS Code, you can step through the code line by line

## Troubleshooting

### Common Installation Issues

#### ❌ "python is not recognized as an internal or external command"

**Problem:** Python is not installed or not in your PATH.

**Solutions:**
1. **Windows:** Reinstall Python and ensure "Add Python to PATH" is checked
2. **Alternative:** Use the full path: `C:\Users\YourName\AppData\Local\Programs\Python\Python311\python.exe`
3. **Check installation:** Open Control Panel → Programs → Look for Python

#### ❌ "pip is not recognized as an internal or external command"

**Problem:** pip is not installed or not in PATH.

**Solutions:**
1. **Windows:** Try `py -m pip install maps4fs` instead of `pip install maps4fs`
2. **Reinstall Python** with pip included
3. **Manual pip installation:** Download get-pip.py and run `python get-pip.py`

#### ❌ "Permission denied" or "Access denied" errors

**Problem:** Insufficient permissions to install packages.

**Solutions:**
1. **Windows:** Run Command Prompt as Administrator
2. **macOS/Linux:** Use `pip install --user maps4fs` to install for current user only
3. **Use virtual environment:** (Recommended) Create a virtual environment first

#### ❌ "No module named 'maps4fs'" after installation

**Problem:** Package installed in wrong Python environment.

**Solutions:**
1. **Check Python version:** Make sure you're using the same Python where you installed maps4fs
2. **Reinstall:** `pip uninstall maps4fs` then `pip install maps4fs`
3. **Use virtual environment:** Create a clean environment for the project

### Common Runtime Issues

#### ❌ "FileNotFoundError: Template file not found"

**Problem:** Missing game templates.

**Solutions:**
1. **Download templates:** Get the `templates` folder from the Maps4FS repository
2. **Check structure:** Ensure templates are in the correct directory structure
3. **Verify files:** Run the test_setup.py script from earlier

#### ❌ "ModuleNotFoundError: No module named 'gdal'" or similar

**Problem:** Missing system dependencies.

**Solutions:**

**Windows:**
```cmd
# Install GDAL and other dependencies
pip install GDAL-3.6.4-cp311-cp311-win_amd64.whl  # Adjust version
# Or use conda
conda install -c conda-forge gdal
```

**macOS:**
```bash
# Install using Homebrew
brew install gdal
pip install gdal
```

**Linux (Ubuntu/Debian):**
```bash
# Install GDAL system packages
sudo apt-get install gdal-bin libgdal-dev
pip install gdal
```

#### ❌ "Memory Error" or system freezing during generation

**Problem:** Insufficient RAM for map size.

**Solutions:**
1. **Reduce map size:** Start with 2048 (2x2 km) instead of larger sizes
2. **Close other applications:** Free up RAM before running
3. **Increase virtual memory:** (Windows) Increase page file size
4. **Use SSD storage:** HDD will be very slow and may cause timeouts

#### ❌ "HTTP Error" or "Connection failed" during DTM download

**Problem:** Network issues or provider temporarily unavailable.

**Solutions:**
1. **Check internet connection:** Ensure stable internet access
2. **Try different provider:** Switch from SRTM30 to ASTER30 or vice versa
3. **Retry later:** Providers may have temporary outages
4. **Use cached data:** If you've generated maps before, some data may be cached

#### ❌ Map generation takes forever or gets stuck

**Problem:** Various causes - insufficient resources, network issues, or corrupted data.

**Solutions:**
1. **Check console output:** Look for specific error messages
2. **Monitor resource usage:** Task Manager (Windows) or Activity Monitor (macOS)
3. **Restart generation:** Sometimes a fresh start helps
4. **Try smaller area:** Test with a smaller map size first

### Debugging Steps

#### Step 1: Verify Basic Setup
```python
# Create debug_setup.py
import sys
import os

print("=== Python Environment Debug ===")
print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")
print(f"Current directory: {os.getcwd()}")
print(f"Python path: {sys.path}")

try:
    import maps4fs
    print(f"✅ Maps4FS version: {maps4fs.__version__}")
except ImportError as e:
    print(f"❌ Maps4FS import failed: {e}")

print("\n=== File System Check ===")
if os.path.exists("templates"):
    print("✅ Templates directory found")
    for root, dirs, files in os.walk("templates"):
        level = root.replace("templates", "").count(os.sep)
        indent = " " * 2 * level
        print(f"{indent}{os.path.basename(root)}/")
        subindent = " " * 2 * (level + 1)
        for file in files:
            print(f"{subindent}{file}")
else:
    print("❌ Templates directory not found")
```

#### Step 2: Test Minimal Generation
```python
# Create test_minimal.py
import maps4fs as mfs

try:
    print("Testing game initialization...")
    game = mfs.Game.from_code("fs25")
    print("✅ Game initialized")
    
    print("Testing DTM provider...")
    dtm_provider = mfs.dtm.SRTM30Provider
    print("✅ DTM provider ready")
    
    print("Testing map initialization...")
    mp = mfs.Map(
        game,
        dtm_provider,
        None,
        (52.0, 8.0),  # Simple coordinates
        1024,         # Very small map for quick test
        0,
        "test_output"
    )
    print("✅ Map initialization successful")
    print("🎉 Basic setup is working!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
```

### Performance Optimization

#### For Faster Generation:
1. **Use smaller map sizes** for testing (1024 or 2048)
2. **Use SSD storage** instead of HDD
3. **Close unnecessary applications** to free up RAM
4. **Use local DTM providers** when available (faster than downloading)

#### For Large Maps:
1. **Ensure sufficient RAM** (32GB+ for 16x16 km maps)
2. **Use virtual memory/swap** as backup
3. **Generate during low-activity hours**
4. **Consider cloud computing** for very large maps

### Getting Help

#### Before Asking for Help:
1. **Run the debug scripts** above and share the output
2. **Include your system information:** OS, Python version, RAM, storage type
3. **Describe your exact steps** and what went wrong
4. **Share error messages** (full text, not just "it doesn't work")

#### Where to Get Help:
- **GitHub Issues:** [https://github.com/iwatkot/maps4fs/issues](https://github.com/iwatkot/maps4fs/issues) (recommended)
- **Include logs:** Copy any error messages or console output
- **Be specific:** Mention your OS, Python version, and exact steps you followed

### Quick Reference Commands

#### Windows:
```cmd
# Check installations
python --version && pip --version && git --version

# Install Maps4FS
pip install maps4fs

# Create and use virtual environment
python -m venv maps4fs-env
maps4fs-env\Scripts\activate
pip install maps4fs

# Run your script
python my_script.py
```

#### macOS/Linux:
```bash
# Check installations  
python3 --version && pip3 --version && git --version

# Install Maps4FS
pip3 install maps4fs

# Create and use virtual environment
python3 -m venv maps4fs-env
source maps4fs-env/bin/activate
pip install maps4fs

# Run your script
python3 my_script.py
```