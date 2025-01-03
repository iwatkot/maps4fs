## DTM Providers

The generator supports implementation of different DTM providers. The built-in DTM provider is a `SRTM 30 m` dataset, which available for the entire globe with a resolution of 30 m per pixel.

### What is a DTM?

First of all, it's important to understand what a DTM is.  
There are two main types of elevation models: Digital Terrain Model (DTM) and Digital Surface Model (DSM). The DTM represents the bare earth surface without any objects like buildings or vegetation. The DSM, on the other hand, represents the earth's surface including all objects.

![DTM vs DSM, example 1](https://github.com/user-attachments/assets/0bf691f3-6737-4663-86ca-c17a525ecda4)

![DTM vs DSM, example 2](https://github.com/user-attachments/assets/3ae1082c-1117-4073-ac98-a2bc1e22c1ba)

For obvious reasons, in our case we need the DTM and the DSM won't be useful, because it will contain the buildings and other objects that we want to avoid.

### What a DTM provider does?

A DTM provider is a service that provides elevation data for a given location. The generator will use this data to create a dem image for the map. While it's plenty of DTM providers available, only the ones that provide a free and open access to their data can be used by the generator.

### How to implement a DTM provider?

So the DTM provider is a simple class, that receives coordinate of the center point, the size of the region of interest and should return a 16-bit single channeled numpy array with the elevation data. The elevation data should be in meters above the sea level.

### Example of a DTM provider

➡️ Base class and existing providers can be found in the [dtm.py](../maps4fs/generator/dtm.py) file.

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

**Step 3 (optional):** use the `DTMProviderSetting` class to define your own settings (if needed).  

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

**Step 3:** implement the `get_tile_parameters` method.  

```python
    def get_tile_parameters(self, *args, **kwargs) -> dict[str, str]:
        """Returns latitude band and tile name for SRTM tile from coordinates.

        Arguments:
            lat (float): Latitude.
            lon (float): Longitude.

        Returns:
            dict: Tile parameters.
        """
        lat, lon = args

        tile_latitude = math.floor(lat)
        tile_longitude = math.floor(lon)

        latitude_band = f"N{abs(tile_latitude):02d}" if lat >= 0 else f"S{abs(tile_latitude):02d}"
        if lon < 0:
            tile_name = f"{latitude_band}W{abs(tile_longitude):03d}"
        else:
            tile_name = f"{latitude_band}E{abs(tile_longitude):03d}"

        self.logger.debug(
            "Detected tile name: %s for coordinates: lat %s, lon %s.", tile_name, lat, lon
        )
        return {"latitude_band": latitude_band, "tile_name": tile_name}
```

This method is required to understand how to format the download url. Of course different sources store data in different ways, so by default in the parent class this method is not implemented and you need to implement it in your provider. And if you're not using direct download, you obviously don't need this method.

**Step 4:** implement the `get_numpy` method.  

```python
    def get_numpy(self) -> np.ndarray:
        """Get numpy array of the tile.

        Returns:
            np.ndarray: Numpy array of the tile.
        """
        tile_parameters = self.get_tile_parameters(*self.coordinates)
        tile_name = tile_parameters["tile_name"]
        decompressed_tile_path = os.path.join(self.hgt_directory, f"{tile_name}.hgt")

        if not os.path.isfile(decompressed_tile_path):
            compressed_tile_path = os.path.join(self.gz_directory, f"{tile_name}.hgt.gz")
            if not self.get_or_download_tile(compressed_tile_path, **tile_parameters):
                raise FileNotFoundError(f"Tile {tile_name} not found.")

            with gzip.open(compressed_tile_path, "rb") as f_in:
                with open(decompressed_tile_path, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)

        return self.extract_roi(decompressed_tile_path)
```

As you can see, we're using the `get_tile_parameters` method, that we've implemented earlier. Then we're downloading the tile, decompressing it and extracting the region of interest. The `get_or_download_tile` and
`extract_roi` methods are implemented in the parent class, so you don't need to reimplement them if you're using the same approach.  

As you can see, it's pretty simple to implement a DTM provider. You can use any source of elevation data, as long as it's free and open.
NOTE: DTM Providers which require API keys, paid subscriptions, or any other form of payment will not be considered for implementation in the generator.

### I implemented a DTM provider, what's next?

If you've implemented a DTM provider, you just need to create a pull request to the repository with the generator. After the review, your provider will be added to the generator and will be available for everyone to use.