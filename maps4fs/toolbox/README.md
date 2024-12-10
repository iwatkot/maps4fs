<a id="toolbox.dem"></a>

# toolbox.dem

This module contains functions for working with Digital Elevation Models (DEMs).

<a id="toolbox.dem.read_geo_tiff"></a>

#### read\_geo\_tiff

```python
def read_geo_tiff(file_path: str) -> DatasetReader
```

Read a GeoTIFF file and return the DatasetReader object.

**Arguments**:

- `file_path` _str_ - The path to the GeoTIFF file.
  

**Raises**:

- `FileNotFoundError` - If the file is not found.
- `RuntimeError` - If there is an error reading the file.
  

**Returns**:

- `DatasetReader` - The DatasetReader object for the GeoTIFF file.

<a id="toolbox.dem.get_geo_tiff_bbox"></a>

#### get\_geo\_tiff\_bbox

```python
def get_geo_tiff_bbox(
        src: DatasetReader,
        dst_crs: str | None = "EPSG:4326"
) -> tuple[float, float, float, float]
```

Return the bounding box of a GeoTIFF file in the destination CRS.

**Arguments**:

- `src` _DatasetReader_ - The DatasetReader object for the GeoTIFF file.
- `dst_crs` _str, optional_ - The destination CRS. Defaults to "EPSG:4326".
  

**Returns**:

  tuple[float, float, float, float]: The bounding box in the destination CRS
  as (north, south, east, west).

<a id="toolbox.dem.extract_roi"></a>

#### extract\_roi

```python
def extract_roi(file_path: str, bbox: tuple[float, float, float,
                                            float]) -> str
```

Extract a region of interest (ROI) from a GeoTIFF file and save it as a new file.

**Arguments**:

- `file_path` _str_ - The path to the GeoTIFF file.
- `bbox` _tuple[float, float, float, float]_ - The bounding box of the region of interest
  as (north, south, east, west).
  

**Raises**:

- `RuntimeError` - If there is no data in the selected region.
  

**Returns**:

- `str` - The path to the new GeoTIFF file containing the extracted ROI.

