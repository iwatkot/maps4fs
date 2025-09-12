# Troubleshooting

This guide provides solutions for common issues you might encounter when using Maps4FS. For deployment-specific issues, please refer to the [Local Deployment](local_deployment.md) documentation which includes an extensive troubleshooting section.

## 🖥️ UI and Interface Issues

### Maps4FS Interface Errors or Blank Screen

If you experience issues with the Maps4FS interface (blank screen, features not working, errors):

1. **Check Browser Console for Errors**
   - **Chrome/Edge**: Press `F12` or `Ctrl+Shift+J` (Windows) / `Cmd+Option+J` (Mac)
   - **Firefox**: Press `F12` or `Ctrl+Shift+K` (Windows) / `Cmd+Option+K` (Mac)
   - Look for red error messages that indicate what's failing

2. **Obtain Complete UI Logs**
   ```bash
   # If using local deployment
   docker logs maps4fsui > maps4fsui.log
   
   # If using API container
   docker logs maps4fsapi > maps4fsapi.log
   ```

3. **Common UI Issues and Solutions**
   
   | Issue | Possible Solution |
   |-------|-------------------|
   | Network error | Check your internet connection and firewall settings |
   | API unavailable | Ensure API container is running (`docker ps`) |
   | Blank screen | Try clearing browser cache or use incognito/private mode |
   | Corrupted files | Try re-launching containers: `docker-compose restart` |
   | Browser incompatibility | Try a different browser (Chrome recommended) |

4. **Share Error Details**
   - When seeking help, always include:
     - Browser console errors (screenshot or text)
     - Container logs
     - Steps to reproduce the issue
     - Browser and OS information

## 🗺️ Map Data Issues

### Fields or Forests Missing from Generated Map

If your map is missing expected content (fields, forests, decorative foliage):

1. **Check Generation Settings**
   - Ensure the features were enabled in generation settings
   - Verify proper field/forest density settings
   - Check for filters that might exclude these elements

2. **Verify OSM Data Coverage**
   - Some areas have incomplete OpenStreetMap data
   - Visit [OpenStreetMap](https://www.openstreetmap.org/) to check your area's coverage
   - See [FAQ: Map Data & Objects](FAQ.md#️-map-data--objects) for detailed help

3. **Consider Custom OSM**
   - For complete control, use [Custom OSM](custom_osm.md)
   - Add missing farmland and forest areas manually
   - Create precise map data for your specific needs

4. **Terrain Type Impact**
   - Dense urban areas may have fewer detected fields
   - Remote regions might have incomplete OSM coverage
   - Consider adjusting the coordinates slightly to capture more agricultural areas

## 🔧 Giants Editor Issues

### Map Won't Open in Giants Editor

If your generated map fails to open in Giants Editor:

1. **Verify Correct Giants Editor Version**
   - **FS22 maps**: Require Giants Editor 9.x
   - **FS25 maps**: Require Giants Editor 10.x
   - **Important**: Not just major versions, but exact minor versions must match your game installation

2. **Check Editor Logs for Errors**
   - Find logs at: `C:/Users/<username>/AppData/Local/GIANTS Editor 64bit X.X.X/editor_log.txt`
   - The most recent entries will indicate why the map failed to load
   - Common causes: missing files, corrupted data, incompatible versions

3. **Purple Terrain or Black Screen**
   - See [FAQ: Giants Editor Issues](FAQ.md#-giants-editor-issues) for fixing purple terrain or black screen flickering
   - Follow the step-by-step solutions provided there

4. **Map Structure Issues**
   - Verify the map structure matches Giants Editor expectations
   - Don't modify the folder structure of the generated map
   - Keep file naming conventions intact

## 🎮 Game Loading Issues

### Map Does Not Open in Farming Simulator

If your map installs but won't load in the game:

1. **Enable Debug Console**
   - Locate `game.xml` at:
     ```
     C:/Users/<username>/OneDrive/Documents/My Games/FarmingSimulatorXX/game.xml
     ```
   - Modify development section:
     ```xml
     <development>
         <controls>true</controls>  <!-- Change false to true -->
         <openDevConsole onWarnings="false" onErrors="false"/>
     </development>
     ```
   - In-game, press `~` to open console and check for errors

2. **Check Game Logs**
   - If game crashes before console access:
     ```
     C:/Users/<username>/OneDrive/Documents/My Games/FarmingSimulatorXX/log.txt
     ```
   - Focus on the latest entries for error messages

3. **Verify Mod Installation**
   - Ensure proper archive naming: `FS25_MapName.zip` (no spaces/special characters)
   - Check correct archive structure (files at root level, not in subfolder)
   - See [FAQ: Mod Installation Issues](FAQ.md#-mod-installation-issues) for examples

4. **Fix Missing Ground Collision**
   - If crops can't be destroyed or terrain glitches occur
   - In Giants Editor: **Scripts** → **Shared scripts** → **Map** → **Create Ground Collision Map**
   - **Important**: Repeat this process every time you edit the map

## 📦 Common Data Issues

### Poor Map Quality or Missing Features

1. **Elevation Issues**
   - **Flat terrain**: Area might lack SRTM coverage; try a different location
   - **Spiky terrain**: Try increasing DisplacementLayer size in Giants Editor
   - **Consider [Custom DEM](custom_dem.md)** for higher-quality elevation data

2. **Road and Building Issues**
   - **Missing roads**: OSM data might be incomplete in your area
   - **Floating objects**: Select objects and place on terrain in Giants Editor
   - **See [FAQ: Object Placement Issues](FAQ.md#-object-placement-issues)** for detailed solutions

3. **Water Systems Problems**
   - **Missing rivers/lakes**: Check water settings in generation parameters
   - **Water appears above terrain**: Adjust water depth settings or edit manually in Giants Editor
   - **Water plane issues**: May require manual adjustment in Giants Editor

## 🆘 Getting Additional Help

If you've tried the solutions above and still have issues:

1. **Prepare Information**
   - Screenshots of the issue
   - Logs (UI, API, Giants Editor, or game)
   - Detailed description of the problem
   - Steps to reproduce

2. **Reach Out**
   - Join our [Discord community](https://discord.gg/Sj5QKKyE42) for real-time support
   - Open an issue on [GitHub](https://github.com/iwatkot/maps4fs/issues) with complete information
   - Follow the checklist in [Getting Help](get_help.md) to ensure your issue can be addressed quickly