<a id="generator.background"></a>

# generator.background

This module contains the Background component, which generates 3D obj files based on DEM data
around the map.

<a id="generator.background.Background"></a>

## Background Objects

```python
class Background(Component)
```

Component for creating 3D obj files based on DEM data around the map.

**Arguments**:

- `coordinates` _tuple[float, float]_ - The latitude and longitude of the center of the map.
- `map_height` _int_ - The height of the map in pixels.
- `map_width` _int_ - The width of the map in pixels.
- `map_directory` _str_ - The directory where the map files are stored.
- `logger` _Any, optional_ - The logger to use. Must have at least three basic methods: debug,
  info, warning. If not provided, default logging will be used.

<a id="generator.background.Background.preprocess"></a>

#### preprocess

```python
def preprocess() -> None
```

Prepares the component for processing. Registers the tiles around the map by moving
clockwise from North, then clockwise.

<a id="generator.background.Background.process"></a>

#### process

```python
def process() -> None
```

Launches the component processing. Iterates over all tiles and processes them
as a result the DEM files will be saved, then based on them the obj files will be
generated.

<a id="generator.background.Background.info_sequence"></a>

#### info\_sequence

```python
def info_sequence() -> dict[str, dict[str, str | float | int]]
```

Returns a dictionary with information about the tiles around the map.
Adds the EPSG:3857 string to the data for convenient usage in QGIS.

**Returns**:

  dict[str, dict[str, float | int]] -- A dictionary with information about the tiles.

<a id="generator.background.Background.qgis_sequence"></a>

#### qgis\_sequence

```python
def qgis_sequence() -> None
```

Generates QGIS scripts for creating bounding box layers and rasterizing them.

<a id="generator.background.Background.generate_obj_files"></a>

#### generate\_obj\_files

```python
def generate_obj_files() -> None
```

Iterates over all tiles and generates 3D obj files based on DEM data.
If at least one DEM file is missing, the generation will be stopped at all.

<a id="generator.background.Background.plane_from_np"></a>

#### plane\_from\_np

```python
def plane_from_np(tile_code: str, dem_data: np.ndarray,
                  save_path: str) -> None
```

Generates a 3D obj file based on DEM data.

**Arguments**:

  tile_code (str) -- The code of the tile.
  dem_data (np.ndarray) -- The DEM data as a numpy array.
  save_path (str) -- The path where the obj file will be saved.

<a id="generator.background.Background.mesh_to_stl"></a>

#### mesh\_to\_stl

```python
def mesh_to_stl(mesh: trimesh.Trimesh) -> None
```

Converts the mesh to an STL file and saves it in the previews directory.
Uses powerful simplification to reduce the size of the file since it will be used
only for the preview.

**Arguments**:

  mesh (trimesh.Trimesh) -- The mesh to convert to an STL file.

<a id="generator.background.Background.previews"></a>

#### previews

```python
def previews() -> list[str]
```

Generates a preview by combining all tiles into one image.
NOTE: The map itself is not included in the preview, so it will be empty.

**Returns**:

- `list[str]` - A list of paths to the preview images.

<a id="generator.component"></a>

# generator.component

This module contains the base class for all map generation components.

<a id="generator.component.Component"></a>

## Component Objects

```python
class Component()
```

Base class for all map generation components.

**Arguments**:

- `game` _Game_ - The game instance for which the map is generated.
- `coordinates` _tuple[float, float]_ - The latitude and longitude of the center of the map.
- `map_height` _int_ - The height of the map in pixels.
- `map_width` _int_ - The width of the map in pixels.
- `map_directory` _str_ - The directory where the map files are stored.
- `logger` _Any, optional_ - The logger to use. Must have at least three basic methods: debug,
  info, warning. If not provided, default logging will be used.

<a id="generator.component.Component.preprocess"></a>

#### preprocess

```python
def preprocess() -> None
```

Prepares the component for processing. Must be implemented in the child class.

**Raises**:

- `NotImplementedError` - If the method is not implemented in the child class.

<a id="generator.component.Component.process"></a>

#### process

```python
def process() -> None
```

Launches the component processing. Must be implemented in the child class.

**Raises**:

- `NotImplementedError` - If the method is not implemented in the child class.

<a id="generator.component.Component.previews"></a>

#### previews

```python
def previews() -> list[str]
```

Returns a list of paths to the preview images. Must be implemented in the child class.

**Raises**:

- `NotImplementedError` - If the method is not implemented in the child class.

<a id="generator.component.Component.previews_directory"></a>

#### previews\_directory

```python
@property
def previews_directory() -> str
```

The directory where the preview images are stored.

**Returns**:

- `str` - The directory where the preview images are stored.

<a id="generator.component.Component.scripts_directory"></a>

#### scripts\_directory

```python
@property
def scripts_directory() -> str
```

The directory where the scripts are stored.

**Returns**:

- `str` - The directory where the scripts are stored.

<a id="generator.component.Component.generation_info_path"></a>

#### generation\_info\_path

```python
@property
def generation_info_path() -> str
```

The path to the generation info JSON file.

**Returns**:

- `str` - The path to the generation info JSON file.

<a id="generator.component.Component.info_sequence"></a>

#### info\_sequence

```python
def info_sequence() -> dict[Any, Any]
```

Returns the information sequence for the component. Must be implemented in the child
class. If the component does not have an information sequence, an empty dictionary must be
returned.

**Returns**:

  dict[Any, Any]: The information sequence for the component.

<a id="generator.component.Component.commit_generation_info"></a>

#### commit\_generation\_info

```python
def commit_generation_info() -> None
```

Commits the generation info to the generation info JSON file.

<a id="generator.component.Component.update_generation_info"></a>

#### update\_generation\_info

```python
def update_generation_info(data: dict[Any, Any]) -> None
```

Updates the generation info with the provided data.
If the generation info file does not exist, it will be created.

**Arguments**:

- `data` _dict[Any, Any]_ - The data to update the generation info with.

<a id="generator.component.Component.get_bbox"></a>

#### get\_bbox

```python
def get_bbox(coordinates: tuple[float, float] | None = None,
             height_distance: int | None = None,
             width_distance: int | None = None,
             project_utm: bool = False) -> tuple[int, int, int, int]
```

Calculates the bounding box of the map from the coordinates and the height and
width of the map.
If coordinates and distance are not provided, the instance variables are used.

**Arguments**:

- `coordinates` _tuple[float, float], optional_ - The latitude and longitude of the center of
  the map. Defaults to None.
- `height_distance` _int, optional_ - The distance from the center of the map to the edge of
  the map in the north-south direction. Defaults to None.
- `width_distance` _int, optional_ - The distance from the center of the map to the edge of
  the map in the east-west direction. Defaults to None.
- `project_utm` _bool, optional_ - Whether to project the bounding box to UTM.
  

**Returns**:

  tuple[int, int, int, int]: The bounding box of the map.

<a id="generator.component.Component.save_bbox"></a>

#### save\_bbox

```python
def save_bbox() -> None
```

Saves the bounding box of the map to the component instance from the coordinates and the
height and width of the map.

<a id="generator.component.Component.new_bbox"></a>

#### new\_bbox

```python
@property
def new_bbox() -> tuple[float, float, float, float]
```

This property is used for a new version of osmnx library, where the order of coordinates
has been changed to (left, bottom, right, top).

**Returns**:

  tuple[float, float, float, float]: The bounding box of the map in the new order:
  (left, bottom, right, top).

<a id="generator.component.Component.get_espg3857_bbox"></a>

#### get\_espg3857\_bbox

```python
def get_espg3857_bbox(
        bbox: tuple[float, float, float, float] | None = None,
        add_margin: bool = False) -> tuple[float, float, float, float]
```

Converts the bounding box to EPSG:3857.
If the bounding box is not provided, the instance variable is used.

**Arguments**:

- `bbox` _tuple[float, float, float, float], optional_ - The bounding box to convert.
- `add_margin` _bool, optional_ - Whether to add a margin to the bounding box.
  

**Returns**:

  tuple[float, float, float, float]: The bounding box in EPSG:3857.

<a id="generator.component.Component.get_epsg3857_string"></a>

#### get\_epsg3857\_string

```python
def get_epsg3857_string(bbox: tuple[float, float, float, float] | None = None,
                        add_margin: bool = False) -> str
```

Converts the bounding box to EPSG:3857 string.
If the bounding box is not provided, the instance variable is used.

**Arguments**:

- `bbox` _tuple[float, float, float, float], optional_ - The bounding box to convert.
- `add_margin` _bool, optional_ - Whether to add a margin to the bounding box.
  

**Returns**:

- `str` - The bounding box in EPSG:3857 string.

<a id="generator.component.Component.create_qgis_scripts"></a>

#### create\_qgis\_scripts

```python
def create_qgis_scripts(
        qgis_layers: list[tuple[str, float, float, float, float]]) -> None
```

Creates QGIS scripts from the given layers.
Each layer is a tuple where the first element is a name of the layer and the rest are the
bounding box coordinates in EPSG:3857.
For filenames, the class name is used as a prefix.

**Arguments**:

- `qgis_layers` _list[tuple[str, float, float, float, float]]_ - The list of layers to
  create scripts for.

<a id="generator.config"></a>

# generator.config

This module contains the Config class for map settings and configuration.

<a id="generator.config.Config"></a>

## Config Objects

```python
class Config(Component)
```

Component for map settings and configuration.

**Arguments**:

- `coordinates` _tuple[float, float]_ - The latitude and longitude of the center of the map.
- `map_height` _int_ - The height of the map in pixels.
- `map_width` _int_ - The width of the map in pixels.
- `map_directory` _str_ - The directory where the map files are stored.
- `logger` _Any, optional_ - The logger to use. Must have at least three basic methods: debug,
  info, warning. If not provided, default logging will be used.

<a id="generator.config.Config.preprocess"></a>

#### preprocess

```python
def preprocess() -> None
```

Gets the path to the map XML file and saves it to the instance variable.

<a id="generator.config.Config.process"></a>

#### process

```python
def process() -> None
```

Sets the map size in the map.xml file.

<a id="generator.config.Config.previews"></a>

#### previews

```python
def previews() -> list[str]
```

Returns a list of paths to the preview images (empty list).
The component does not generate any preview images so it returns an empty list.

**Returns**:

- `list[str]` - An empty list.

<a id="generator.config.Config.info_sequence"></a>

#### info\_sequence

```python
def info_sequence() -> dict[str, dict[str, str | float | int]]
```

Returns information about the component.
Overview section is needed to create the overview file (in-game map).

**Returns**:

  dict[str, dict[str, str | float | int]]: Information about the component.

<a id="generator.config.Config.qgis_sequence"></a>

#### qgis\_sequence

```python
def qgis_sequence() -> None
```

Generates QGIS scripts for creating bounding box layers and rasterizing them.

<a id="generator.dem"></a>

# generator.dem

This module contains DEM class for processing Digital Elevation Model data.

<a id="generator.dem.DEM"></a>

## DEM Objects

```python
class DEM(Component)
```

Component for processing Digital Elevation Model data.

**Arguments**:

- `coordinates` _tuple[float, float]_ - The latitude and longitude of the center of the map.
- `map_height` _int_ - The height of the map in pixels.
- `map_width` _int_ - The width of the map in pixels.
- `map_directory` _str_ - The directory where the map files are stored.
- `logger` _Any, optional_ - The logger to use. Must have at least three basic methods: debug,
  info, warning. If not provided, default logging will be used.

<a id="generator.dem.DEM.dem_path"></a>

#### dem\_path

```python
@property
def dem_path() -> str
```

Returns path to the DEM file.

**Returns**:

- `str` - Path to the DEM file.

<a id="generator.dem.DEM.get_output_resolution"></a>

#### get\_output\_resolution

```python
def get_output_resolution() -> tuple[int, int]
```

Get output resolution for DEM data.

**Returns**:

  tuple[int, int]: Output resolution for DEM data.

<a id="generator.dem.DEM.to_ground"></a>

#### to\_ground

```python
def to_ground(data: np.ndarray) -> np.ndarray
```

Receives the signed 16-bit integer array and converts it to the ground level.
If the min value is negative, it will become zero value and the rest of the values
will be shifted accordingly.

<a id="generator.dem.DEM.process"></a>

#### process

```python
def process() -> None
```

Reads SRTM file, crops it to map size, normalizes and blurs it,
saves to map directory.

<a id="generator.dem.DEM.make_copy"></a>

#### make\_copy

```python
def make_copy(dem_name: str) -> None
```

Copies DEM data to additional DEM file.

**Arguments**:

- `dem_name` _str_ - Name of the additional DEM file.

<a id="generator.dem.DEM.grayscale_preview"></a>

#### grayscale\_preview

```python
def grayscale_preview() -> str
```

Converts DEM image to grayscale RGB image and saves it to the map directory.
Returns path to the preview image.

**Returns**:

- `str` - Path to the preview image.

<a id="generator.dem.DEM.colored_preview"></a>

#### colored\_preview

```python
def colored_preview() -> str
```

Converts DEM image to colored RGB image and saves it to the map directory.
Returns path to the preview image.

**Returns**:

- `list[str]` - List with a single path to the DEM file

<a id="generator.dem.DEM.previews"></a>

#### previews

```python
def previews() -> list[str]
```

Get list of preview images.

**Returns**:

- `list[str]` - List of preview images.

<a id="generator.game"></a>

# generator.game

This module contains the Game class and its subclasses. Game class is used to define
different versions of the game for which the map is generated. Each game has its own map
template file and specific settings for map generation.

<a id="generator.game.Game"></a>

## Game Objects

```python
class Game()
```

Class used to define different versions of the game for which the map is generated.

**Arguments**:

- `map_template_path` _str, optional_ - Path to the map template file. Defaults to None.
  
  Attributes and Properties:
- `code` _str_ - The code of the game.
- `components` _list[Type[Component]]_ - List of components used for map generation.
- `map_template_path` _str_ - Path to the map template file.
  
  Public Methods:
  from_code(cls, code: str) -> Game: Returns the game instance based on the game code.

<a id="generator.game.Game.map_xml_path"></a>

#### map\_xml\_path

```python
def map_xml_path(map_directory: str) -> str
```

Returns the path to the map.xml file.

**Arguments**:

- `map_directory` _str_ - The path to the map directory.
  

**Returns**:

- `str` - The path to the map.xml file.

<a id="generator.game.Game.from_code"></a>

#### from\_code

```python
@classmethod
def from_code(cls, code: str) -> Game
```

Returns the game instance based on the game code.

**Arguments**:

- `code` _str_ - The code of the game.
  

**Returns**:

- `Game` - The game instance.

<a id="generator.game.Game.template_path"></a>

#### template\_path

```python
@property
def template_path() -> str
```

Returns the path to the map template file.

**Raises**:

- `ValueError` - If the map template path is not set.
  

**Returns**:

- `str` - The path to the map template file.

<a id="generator.game.Game.texture_schema"></a>

#### texture\_schema

```python
@property
def texture_schema() -> str
```

Returns the path to the texture layers schema file.

**Raises**:

- `ValueError` - If the texture layers schema path is not set.
  

**Returns**:

- `str` - The path to the texture layers schema file.

<a id="generator.game.Game.grle_schema"></a>

#### grle\_schema

```python
@property
def grle_schema() -> str
```

Returns the path to the GRLE layers schema file.

**Raises**:

- `ValueError` - If the GRLE layers schema path is not set.
  

**Returns**:

- `str` - The path to the GRLE layers schema file.

<a id="generator.game.Game.dem_file_path"></a>

#### dem\_file\_path

```python
def dem_file_path(map_directory: str) -> str
```

Returns the path to the DEM file.

**Arguments**:

- `map_directory` _str_ - The path to the map directory.
  

**Returns**:

- `str` - The path to the DEM file.

<a id="generator.game.Game.weights_dir_path"></a>

#### weights\_dir\_path

```python
def weights_dir_path(map_directory: str) -> str
```

Returns the path to the weights directory.

**Arguments**:

- `map_directory` _str_ - The path to the map directory.
  

**Returns**:

- `str` - The path to the weights directory.

<a id="generator.game.Game.i3d_file_path"></a>

#### i3d\_file\_path

```python
def i3d_file_path(map_directory: str) -> str
```

Returns the path to the i3d file.

**Arguments**:

- `map_directory` _str_ - The path to the map directory.
  

**Returns**:

- `str` - The path to the i3d file.

<a id="generator.game.Game.additional_dem_name"></a>

#### additional\_dem\_name

```python
@property
def additional_dem_name() -> str | None
```

Returns the name of the additional DEM file.

**Returns**:

  str | None: The name of the additional DEM file.

<a id="generator.game.FS22"></a>

## FS22 Objects

```python
class FS22(Game)
```

Class used to define the game version FS22.

<a id="generator.game.FS22.dem_file_path"></a>

#### dem\_file\_path

```python
def dem_file_path(map_directory: str) -> str
```

Returns the path to the DEM file.

**Arguments**:

- `map_directory` _str_ - The path to the map directory.
  

**Returns**:

- `str` - The path to the DEM file.

<a id="generator.game.FS22.weights_dir_path"></a>

#### weights\_dir\_path

```python
def weights_dir_path(map_directory: str) -> str
```

Returns the path to the weights directory.

**Arguments**:

- `map_directory` _str_ - The path to the map directory.
  

**Returns**:

- `str` - The path to the weights directory.

<a id="generator.game.FS25"></a>

## FS25 Objects

```python
class FS25(Game)
```

Class used to define the game version FS25.

<a id="generator.game.FS25.dem_file_path"></a>

#### dem\_file\_path

```python
def dem_file_path(map_directory: str) -> str
```

Returns the path to the DEM file.

**Arguments**:

- `map_directory` _str_ - The path to the map directory.
  

**Returns**:

- `str` - The path to the DEM file.

<a id="generator.game.FS25.map_xml_path"></a>

#### map\_xml\_path

```python
def map_xml_path(map_directory: str) -> str
```

Returns the path to the map.xml file.

**Arguments**:

- `map_directory` _str_ - The path to the map directory.
  

**Returns**:

- `str` - The path to the map.xml file.

<a id="generator.game.FS25.weights_dir_path"></a>

#### weights\_dir\_path

```python
def weights_dir_path(map_directory: str) -> str
```

Returns the path to the weights directory.

**Arguments**:

- `map_directory` _str_ - The path to the map directory.
  

**Returns**:

- `str` - The path to the weights directory.

<a id="generator.game.FS25.i3d_file_path"></a>

#### i3d\_file\_path

```python
def i3d_file_path(map_directory: str) -> str
```

Returns the path to the i3d file.

**Arguments**:

- `map_directory` _str_ - The path to the map directory.
  

**Returns**:

- `str` - The path to the i3d file.

<a id="generator.grle"></a>

# generator.grle

This module contains the GRLE class for generating InfoLayer PNG files based on GRLE schema.

<a id="generator.grle.GRLE"></a>

## GRLE Objects

```python
class GRLE(Component)
```

Component for to generate InfoLayer PNG files based on GRLE schema.

**Arguments**:

- `coordinates` _tuple[float, float]_ - The latitude and longitude of the center of the map.
- `map_height` _int_ - The height of the map in pixels.
- `map_width` _int_ - The width of the map in pixels.
- `map_directory` _str_ - The directory where the map files are stored.
- `logger` _Any, optional_ - The logger to use. Must have at least three basic methods: debug,
  info, warning. If not provided, default logging will be used.

<a id="generator.grle.GRLE.preprocess"></a>

#### preprocess

```python
def preprocess() -> None
```

Gets the path to the map I3D file from the game instance and saves it to the instance
attribute. If the game does not support I3D files, the attribute is set to None.

<a id="generator.grle.GRLE.process"></a>

#### process

```python
def process() -> None
```

Generates InfoLayer PNG files based on the GRLE schema.

<a id="generator.i3d"></a>

# generator.i3d

This module contains the Config class for map settings and configuration.

<a id="generator.i3d.I3d"></a>

## I3d Objects

```python
class I3d(Component)
```

Component for map i3d file settings and configuration.

**Arguments**:

- `coordinates` _tuple[float, float]_ - The latitude and longitude of the center of the map.
- `map_height` _int_ - The height of the map in pixels.
- `map_width` _int_ - The width of the map in pixels.
- `map_directory` _str_ - The directory where the map files are stored.
- `logger` _Any, optional_ - The logger to use. Must have at least three basic methods: debug,
  info, warning. If not provided, default logging will be used.

<a id="generator.i3d.I3d.preprocess"></a>

#### preprocess

```python
def preprocess() -> None
```

Gets the path to the map I3D file from the game instance and saves it to the instance
attribute. If the game does not support I3D files, the attribute is set to None.

<a id="generator.i3d.I3d.process"></a>

#### process

```python
def process() -> None
```

Updates the map I3D file with the default settings.

<a id="generator.i3d.I3d.previews"></a>

#### previews

```python
def previews() -> list[str]
```

Returns a list of paths to the preview images (empty list).
The component does not generate any preview images so it returns an empty list.

**Returns**:

- `list[str]` - An empty list.

<a id="generator.map"></a>

# generator.map

This module contains Map class, which is used to generate map using all components.

<a id="generator.map.Map"></a>

## Map Objects

```python
class Map()
```

Class used to generate map using all components.

**Arguments**:

- `game` _Type[Game]_ - Game for which the map is generated.
- `coordinates` _tuple[float, float]_ - Coordinates of the center of the map.
- `height` _int_ - Height of the map in pixels.
- `width` _int_ - Width of the map in pixels.
- `map_directory` _str_ - Path to the directory where map files will be stored.
- `logger` _Any_ - Logger instance

<a id="generator.map.Map.generate"></a>

#### generate

```python
def generate() -> Generator[str, None, None]
```

Launch map generation using all components. Yield component names during the process.

**Yields**:

  Generator[str, None, None]: Component names.

<a id="generator.map.Map.previews"></a>

#### previews

```python
def previews() -> list[str]
```

Get list of preview images.

**Returns**:

- `list[str]` - List of preview images.

<a id="generator.map.Map.pack"></a>

#### pack

```python
def pack(archive_path: str, remove_source: bool = True) -> str
```

Pack map directory to zip archive.

**Arguments**:

- `archive_path` _str_ - Path to the archive.
- `remove_source` _bool, optional_ - Remove source directory after packing.
  

**Returns**:

- `str` - Path to the archive.

<a id="generator.path_steps"></a>

# generator.path\_steps

This module contains functions and clas for generating path steps.

<a id="generator.path_steps.PathStep"></a>

## PathStep Objects

```python
class PathStep(NamedTuple)
```

Represents parameters of one step in the path.

**Attributes**:

- `code` _str_ - Tile code (N, NE, E, SE, S, SW, W, NW).
- `angle` _int_ - Angle in degrees (for example 0 for North, 90 for East).
  If None, the step is a full map with a center at the same coordinates as the
  map itself.
- `distance` _int_ - Distance in meters from previous step.
  If None, the step is a full map with a center at the same coordinates as the
  map itself.
  size {tuple[int, int]} -- Size of the tile in pixels (width, height).

<a id="generator.path_steps.PathStep.get_destination"></a>

#### get\_destination

```python
def get_destination(origin: tuple[float, float]) -> tuple[float, float]
```

Calculate destination coordinates based on origin and step parameters.

**Arguments**:

  origin {tuple[float, float]} -- Origin coordinates (latitude, longitude)
  

**Returns**:

  tuple[float, float] -- Destination coordinates (latitude, longitude)

<a id="generator.path_steps.get_steps"></a>

#### get\_steps

```python
def get_steps(map_height: int, map_width: int) -> list[PathStep]
```

Return a list of PathStep objects for each tile, which represent a step in the path.
Moving from the center of the map to North, then clockwise.

**Arguments**:

- `map_height` _int_ - Height of the map in pixels
- `map_width` _int_ - Width of the map in pixels
  

**Returns**:

- `list[PathStep]` - List of PathStep objects

<a id="generator.qgis"></a>

# generator.qgis

This module contains templates for generating QGIS scripts.

<a id="generator.qgis.get_bbox_template"></a>

#### get\_bbox\_template

```python
def get_bbox_template(
        layers: list[tuple[str, float, float, float, float]]) -> str
```

Returns a template for creating bounding box layers in QGIS.

**Arguments**:

- `layers` _list[tuple[str, float, float, float, float]]_ - A list of tuples containing the
  layer name and the bounding box coordinates.
  

**Returns**:

- `str` - The template for creating bounding box layers in QGIS.

<a id="generator.qgis.get_point_template"></a>

#### get\_point\_template

```python
def get_point_template(
        layers: list[tuple[str, float, float, float, float]]) -> str
```

Returns a template for creating point layers in QGIS.

**Arguments**:

- `layers` _list[tuple[str, float, float, float, float]]_ - A list of tuples containing the
  layer name and the bounding box coordinates.
  

**Returns**:

- `str` - The template for creating point layers in QGIS.

<a id="generator.qgis.get_rasterize_template"></a>

#### get\_rasterize\_template

```python
def get_rasterize_template(
        layers: list[tuple[str, float, float, float, float]]) -> str
```

Returns a template for rasterizing bounding box layers in QGIS.

**Arguments**:

- `layers` _list[tuple[str, float, float, float, float]]_ - A list of tuples containing the
  layer name and the bounding box coordinates.
  

**Returns**:

- `str` - The template for rasterizing bounding box layers in QGIS.

<a id="generator.qgis.save_scripts"></a>

#### save\_scripts

```python
def save_scripts(layers: list[tuple[str, float, float, float, float]],
                 file_prefix: str, save_directory: str) -> None
```

Saves QGIS scripts for creating bounding box, point, and raster layers.

**Arguments**:

- `layers` _list[tuple[str, float, float, float, float]]_ - A list of tuples containing the
  layer name and the bounding box coordinates.
- `save_dir` _str_ - The directory to save the scripts.

<a id="generator.texture"></a>

# generator.texture

Module with Texture class for generating textures for the map using OSM data.

<a id="generator.texture.Texture"></a>

## Texture Objects

```python
class Texture(Component)
```

Class which generates textures for the map using OSM data.

**Attributes**:

- `weights_dir` _str_ - Path to the directory with weights.
- `name` _str_ - Name of the texture.
- `tags` _dict[str, str | list[str] | bool]_ - Dictionary of tags to search for.
- `width` _int | None_ - Width of the polygon in meters (only for LineString).
- `color` _tuple[int, int, int]_ - Color of the layer in BGR format.

<a id="generator.texture.Texture.Layer"></a>

## Layer Objects

```python
class Layer()
```

Class which represents a layer with textures and tags.
It's using to obtain data from OSM using tags and make changes into corresponding textures.

**Arguments**:

- `name` _str_ - Name of the layer.
- `tags` _dict[str, str | list[str]]_ - Dictionary of tags to search for.
- `width` _int | None_ - Width of the polygon in meters (only for LineString).
- `color` _tuple[int, int, int]_ - Color of the layer in BGR format.
  

**Attributes**:

- `name` _str_ - Name of the layer.
- `tags` _dict[str, str | list[str]]_ - Dictionary of tags to search for.
- `width` _int | None_ - Width of the polygon in meters (only for LineString).

<a id="generator.texture.Texture.Layer.to_json"></a>

#### to\_json

```python
def to_json() -> dict[str, str | list[str] | bool]
```

Returns dictionary with layer data.

**Returns**:

- `dict` - Dictionary with layer data.

<a id="generator.texture.Texture.Layer.from_json"></a>

#### from\_json

```python
@classmethod
def from_json(cls, data: dict[str, str | list[str] | bool]) -> Texture.Layer
```

Creates a new instance of the class from dictionary.

**Arguments**:

- `data` _dict[str, str | list[str] | bool]_ - Dictionary with layer data.
  

**Returns**:

- `Layer` - New instance of the class.

<a id="generator.texture.Texture.Layer.path"></a>

#### path

```python
def path(weights_directory: str) -> str
```

Returns path to the first texture of the layer.

**Arguments**:

- `weights_directory` _str_ - Path to the directory with weights.
  

**Returns**:

- `str` - Path to the texture.

<a id="generator.texture.Texture.Layer.path_preview"></a>

#### path\_preview

```python
def path_preview(previews_directory: str) -> str
```

Returns path to the preview of the first texture of the layer.

**Arguments**:

- `previews_directory` _str_ - Path to the directory with previews.
  

**Returns**:

- `str` - Path to the preview.

<a id="generator.texture.Texture.Layer.get_preview_or_path"></a>

#### get\_preview\_or\_path

```python
def get_preview_or_path(previews_directory: str) -> str
```

Returns path to the preview of the first texture of the layer if it exists,
otherwise returns path to the texture.

**Arguments**:

- `previews_directory` _str_ - Path to the directory with previews.
  

**Returns**:

- `str` - Path to the preview or texture.

<a id="generator.texture.Texture.Layer.paths"></a>

#### paths

```python
def paths(weights_directory: str) -> list[str]
```

Returns a list of paths to the textures of the layer.
NOTE: Works only after the textures are generated, since it just lists the directory.

**Arguments**:

- `weights_directory` _str_ - Path to the directory with weights.
  

**Returns**:

- `list[str]` - List of paths to the textures.

<a id="generator.texture.Texture.get_base_layer"></a>

#### get\_base\_layer

```python
def get_base_layer() -> Layer | None
```

Returns base layer.

**Returns**:

  Layer | None: Base layer.

<a id="generator.texture.Texture.info_sequence"></a>

#### info\_sequence

```python
def info_sequence() -> dict[str, Any]
```

Returns the JSON representation of the generation info for textures.

<a id="generator.texture.Texture.layers"></a>

#### layers

```python
@property
def layers() -> list[Layer]
```

Returns list of layers with textures and tags from textures.json.

**Returns**:

- `list[Layer]` - List of layers.

<a id="generator.texture.Texture.layers"></a>

#### layers

```python
@layers.setter
def layers(layers: list[Layer]) -> None
```

Sets list of layers with textures and tags.

**Arguments**:

- `layers` _list[Layer]_ - List of layers.

<a id="generator.texture.Texture.layers_by_priority"></a>

#### layers\_by\_priority

```python
def layers_by_priority() -> list[Layer]
```

Returns list of layers sorted by priority: None priority layers are first,
then layers are sorted by priority (descending).

**Returns**:

- `list[Layer]` - List of layers sorted by priority.

<a id="generator.texture.Texture.draw"></a>

#### draw

```python
def draw() -> None
```

Iterates over layers and fills them with polygons from OSM data.

<a id="generator.texture.Texture.dissolve"></a>

#### dissolve

```python
def dissolve() -> None
```

Dissolves textures of the layers with tags into sublayers for them to look more
natural in the game.
Iterates over all layers with tags and reads the first texture, checks if the file
contains any non-zero values (255), splits those non-values between different weight
files of the corresponding layer and saves the changes to the files.

<a id="generator.texture.Texture.draw_base_layer"></a>

#### draw\_base\_layer

```python
def draw_base_layer(cumulative_image: np.ndarray) -> None
```

Draws base layer and saves it into the png file.
Base layer is the last layer to be drawn, it fills the remaining area of the map.

**Arguments**:

- `cumulative_image` _np.ndarray_ - Cumulative image with all layers.

<a id="generator.texture.Texture.get_relative_x"></a>

#### get\_relative\_x

```python
def get_relative_x(x: float) -> int
```

Converts UTM X coordinate to relative X coordinate in map image.

**Arguments**:

- `x` _float_ - UTM X coordinate.
  

**Returns**:

- `int` - Relative X coordinate in map image.

<a id="generator.texture.Texture.get_relative_y"></a>

#### get\_relative\_y

```python
def get_relative_y(y: float) -> int
```

Converts UTM Y coordinate to relative Y coordinate in map image.

**Arguments**:

- `y` _float_ - UTM Y coordinate.
  

**Returns**:

- `int` - Relative Y coordinate in map image.

<a id="generator.texture.Texture.polygons"></a>

#### polygons

```python
def polygons(tags: dict[str, str | list[str] | bool],
             width: int | None) -> Generator[np.ndarray, None, None]
```

Generator which yields numpy arrays of polygons from OSM data.

**Arguments**:

- `tags` _dict[str, str | list[str]]_ - Dictionary of tags to search for.
- `width` _int | None_ - Width of the polygon in meters (only for LineString).
  

**Yields**:

  Generator[np.ndarray, None, None]: Numpy array of polygon points.

<a id="generator.texture.Texture.previews"></a>

#### previews

```python
def previews() -> list[str]
```

Invokes methods to generate previews. Returns list of paths to previews.

**Returns**:

- `list[str]` - List of paths to previews.

<a id="generator.tile"></a>

# generator.tile

This module contains the Tile component, which is used to generate a tile of DEM data around
the map.

<a id="generator.tile.Tile"></a>

## Tile Objects

```python
class Tile(DEM)
```

Component for creating a tile of DEM data around the map.

**Arguments**:

- `coordinates` _tuple[float, float]_ - The latitude and longitude of the center of the map.
- `map_height` _int_ - The height of the map in pixels.
- `map_width` _int_ - The width of the map in pixels.
- `map_directory` _str_ - The directory where the map files are stored.
- `logger` _Any, optional_ - The logger to use. Must have at least three basic methods: debug,
  info, warning. If not provided, default logging will be used.
  

**Arguments**:

- `tile_code` _str_ - The code of the tile (N, NE, E, SE, S, SW, W, NW).
  
  Public Methods:
- `get_output_resolution` - Return the resolution of the output image.
- `process` - Launch the component processing.
- `make_copy` - Override the method to prevent copying the tile.

<a id="generator.tile.Tile.preprocess"></a>

#### preprocess

```python
def preprocess() -> None
```

Prepares the component for processing. Reads the tile code from the kwargs and sets the
DEM path for the tile.

<a id="generator.tile.Tile.get_output_resolution"></a>

#### get\_output\_resolution

```python
def get_output_resolution() -> tuple[int, int]
```

Return the resolution of the output image.

**Returns**:

  tuple[int, int]: The width and height of the output image.

<a id="generator.tile.Tile.make_copy"></a>

#### make\_copy

```python
def make_copy(*args, **kwargs) -> None
```

Override the method to prevent copying the tile.

