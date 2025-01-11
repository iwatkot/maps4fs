## DTM Providers

The generator supports implementation of different DTM providers. The built-in DTM provider is a `SRTM 30 m` dataset, which available for the entire globe with a resolution of 30 m per pixel.

### What is a DTM?

First of all, it's important to understand what a DTM is.  
There are two main types of elevation models: Digital Terrain Model (DTM) and Digital Surface Model (DSM). The DTM represents the bare earth surface without any objects like buildings or vegetation. The DSM, on the other hand, represents the earth's surface including all objects.

![DTM vs DSM, example 1](https://github.com/user-attachments/assets/0bf691f3-6737-4663-86ca-c17a525ecda4)

![DTM vs DSM, example 2](https://github.com/user-attachments/assets/3ae1082c-1117-4073-ac98-a2bc1e22c1ba)

For obvious reasons, in our case we need the DTM and the DSM won't be useful, because it will contain the buildings and other objects that we want to avoid.

### What a DTM provider does?

A DTM provider is a service that provides elevation data for a given location. The generator will use this data to create a dem image for the map. While there's plenty of DTM providers available, only the ones that provide a free and open access to their data can be used by the generator.

The base provider class, [DTMProvider](../mapsfs/generator/dtm/dtm.py) that all DTM providers inherit from, is responsible for all processing of DEM data. Individual DTM providers are responsible only for downloading the DTM tile(s) for the map area.

The process for generating the elevation data is:

- Download all DTM tiles for the desired map area (implemented by each DTM provider)
- If the DTM provider downloaded multiple tiles, merge these tiles into one
- If the tile uses a different projection, reproject it to EPSG:4326, which is used for all other data (like OSM)
- Extract the map area from the tile (some providers, like SRTM, return big tiles that are larger than just the desired area)
- Process the elevation data in the tile (optionally, using Easy Mode, the terrain is moved to ground level, so it appears at z=0 in Giants Editor, and processed so the elevation corresponds to real world meters using the default heightScale in your map, if the elevation of your terrain is more than 255 meters, the heightScale property of your map will automatically be adjusted to fit this elevation)

### How to implement a DTM provider?

So the DTM provider is a simple class, that receives coordinate of the center point, the size of the region of interest and should download all the needed DTM tiles and return a list of downloaded tiles for further processing by the base class.

### Example of a DTM provider

➡️ Base class and existing providers can be found in the [dtm](../maps4fs/generator/dtm) folder.

Let's take a look at an example of a DTM provider implementation.

**Step 1:** define description of the provider.

```python
class SRTM30Provider(DTMProvider):
    """Provider of Shuttle Radar Topography Mission (SRTM) 30m data."""

    _code = "srtm30"
    _name = "SRTM 30 m"
    _region = "Global"
    _icon = "🌎"
    _resolution = 30.0

    _url = "https://elevation-tiles-prod.s3.amazonaws.com/skadi/{latitude_band}/{tile_name}.hgt.gz"

    _author = "[iwatkot](https://github.com/iwatkot)"
    _is_community = True

    _instructions = "When working with SRTM provider..."
```

So, we inherit from the `DTMProvider` class, add some properties to identify the Provider (such as code and region). The most important part is the `_url` property, which is a template for the URL to download the elevation data. But if your provider uses some other approach, you can reimplement related methods.

Also, please provide MD-formatted author information, where in [] will be the name of the author and in () will be the link to the author's GitHub profile (or any other profile if you wish).

Please, set the `_is_community` property to `True`, it means that it was developed not by me, but by the community.

If you want some message to be displayed when the user selects your provider, you can set the `_instructions` property.

**Step 2 (optional):** use the `DTMProviderSetting` class to define your own settings (if needed).

```python
class SRTM30ProviderSettings(DTMProviderSettings):
    """Settings for the SRTM 30 m provider."""

    enable_something: bool = True
    input_something: int = 255
```

Also, you will need to add a new `_settings` property to the provider class.

```python
class SRTM30Provider(DTMProvider):
    ...
    _settings = SRTM30ProviderSettings
```

If those are provided you'll later be able to use the `user_settings` property to access the settings. In the example it would look like this:

```python
enable_something = self.user_settings.enable_something
input_something = self.user_settings.input_something
```

**Step 3:** implement the `download_tiles` method.

```python
    def download_tiles(self):
        """Download SRTM tiles."""
        north, south, east, west = self.get_bbox()

        tiles = []
        # Look at each corner of the bbox in case the bbox spans across multiple tiles
        for pair in [(north, east), (south, west), (south, east), (north, west)]:
            tile_parameters = self.get_tile_parameters(*pair)
            tile_name = tile_parameters["tile_name"]
            decompressed_tile_path = os.path.join(self.hgt_directory, f"{tile_name}.hgt")

            if not os.path.isfile(decompressed_tile_path):
                compressed_tile_path = os.path.join(self.gz_directory, f"{tile_name}.hgt.gz")
                if not self.get_or_download_tile(compressed_tile_path, **tile_parameters):
                    raise FileNotFoundError(f"Tile {tile_name} not found.")

                with gzip.open(compressed_tile_path, "rb") as f_in:
                    with open(decompressed_tile_path, "wb") as f_out:
                        shutil.copyfileobj(f_in, f_out)
            tiles.append(decompressed_tile_path)

        return tiles
```

This method uses the helper method `get_bbox` to get the coordinates of the bounding box of the map area. If your DTM provider requires you to provide the coordinates in a different projection, you need to make sure you convert. For an example of this, see the `transform_bbox` method in [nrw.py](../maps4fs/generator/dtm/nrw.py).
Then, it determines which tiles are needed, downloads them all to a temporary folder and extracts them. The base class provides a `_tile_directory` property for convenience that points to a temp folder for your provider.
Finally, it returns a list of file paths to the downloaded tiles.

As you can see, it's pretty simple to implement a DTM provider. You can use any source of elevation data, as long as it's free and open.
NOTE: DTM Providers which require API keys, paid subscriptions, or any other form of payment will not be considered for implementation in the generator.

### How DTM Provider can interact with the generator?

Sometimes the DTM providers needs a possibility to interact with other components of the generator. For this purpose use the `SharedSettings` class, which can be found in the [settings.py](../maps4fs/generator/settings.py) file.  
The instance if this class will be saved as a property of the `Map` object and will be available as a property of a DTM provider.

For example:

```python
mesh_z_scaling_factor = self.map.shared_settings.mesh_z_scaling_factor
```

Here's the list of the shared settings, which directly related to the DTM Provider:

- `mesh_z_scaling_factor`: the scaling factor for the background terrain and water mesh. The simple explanation would be the following: to 3D model work properly it's Z coordinates should match the meters from real world.
  Imagine the following: the highest point of your terrain is 200 meters, but in the 16-bit DEM file it's represented as 20000. So, the Z scaling factor should be 100.0.  
  Example of usage:

```python
data: np.ndarray
maximum_height = data.max()
... # Some processing here.
new_maximum_height = new_data.max()

z_scaling_factor = maximum_height / new_maximum_height
self.map.shared_settings.mesh_z_scaling_factor = z_scaling_factor
```

- `height_scale_multiplier`: the multiplier which supposed how the default multiplier of `255` should be changed to get the correct heights in the game.

Example of usage:

```python
data: np.ndarray
deviation = data.max() - data.min()
in_game_maximum_height = 65535 // 255

height_scale_multiplier = deviation / in_game_maximum_height
if height_scale_multiplier < 1.0:
    height_scale_multiplier = 1.0
# Since we do not need to lower the default multiplier, the multiplier will always should be >= 1.0.
self.map.shared_settings.height_scale_multiplier = height_scale_multiplier
```

- `height_scale_value`: the value which will be used to scale the height of the terrain. So it's simply a result of the multiplication of the `height_scale_multiplier` and the default multiplier of `255`.

Example of usage:

```python
height_scale_value = self.map.shared_settings.height_scale_multiplier * 255
self.map.shared_settings.height_scale_value = height_scale_value
```

- `change_height_scale`: the flag to indicate that the height scale in the i3d file should be updated with a new value.

Example of usage:

```python
if some_condition:
    self.map.shared_settings.change_height_scale = True
```

### Info sequence

If you want your provider to add some information to the `generation_info.json` file, you can use the `data_info` property of the `DTMProvider` class.

Note, that the `data_info` must me a correct JSON-serializable dictionary.

### Example of usage:

```python
def add_numpy_params(
    self,
    data: np.ndarray,
    prefix: str,
) -> None:
    """Add numpy array parameters to the data_info dictionary.

    Arguments:
        data (np.ndarray): Numpy array of the tile.
        prefix (str): Prefix for the parameters.
    """
    self.data_info[f"{prefix}_minimum_height"] = int(data.min())  # type: ignore
    self.data_info[f"{prefix}_maximum_height"] = int(data.max())  # type: ignore
    self.data_info[f"{prefix}_deviation"] = int(data.max() - data.min())  # type: ignore
    self.data_info[f"{prefix}_unique_values"] = int(np.unique(data).size)  # type: ignore
```

The method in the example adds some basic information about the DEM image to the `data_info` dictionary. You can add any information you want.

### I implemented a DTM provider, what's next?

If you've implemented a DTM provider, you just need to create a pull request to the repository with the generator. After the review, your provider will be added to the generator and will be available for everyone to use.
