# maps4fs Refactor Suggestions

> **Status:** Analysis only. No code has been changed. Review and discuss before proceeding.

---

## 1. Current Module Inventory

```
maps4fs/
  __init__.py                     # Public re-exports
  logger.py                       # (stub? empty or trivial)
  generator/
    map.py                        # Map class — orchestrates the pipeline
    game.py                       # Game base class + FS22, FS25 subclasses
    settings.py                   # All settings models (Pydantic + NamedTuple)
    config.py                     # Path constants + module-level setup side effects (messy — see §3.13)
    utils.py                      # OSM validation, geo utilities, JSON helpers, Singleton (misleading name — see §3.16)
    qgis.py                       # QGIS script generation (DEPRECATED)
    monitor.py                    # Logger, PerformanceMonitor (mostly good — see §3.14)
    statistics.py                 # Telemetry (technically blocking despite threads — see §3.15)
    component/
      __init__.py
      layer.py                    # Layer model (23-argument constructor nightmare — see §3.17)
      dem.py                      # DEM (elevation data) processing
      texture.py                  # OSM → texture weight images
      background.py               # Background terrain and water mesh generation
      grle.py                     # InfoLayer PNG generation (farmlands, plants, environment)
      i3d.py                      # map.i3d / splines.i3d editing + field/tree/spline injection
      config.py                   # map.xml editing, fog, overview, license plates
      road.py                     # Road surface mesh generation
      building.py                 # Building placement (extends I3d)
      satellite.py                # Satellite image download
      base/
        component.py              # Base class for all components
        component_image.py        # Image utility methods (blur, resize, rotate, etc.)
        component_xml.py          # XML/i3d read-write helpers
        component_mesh.py         # 3D mesh generation utilities
```

---

## 2. Current Data Flow

### 2.1 Component Execution Order

```
Satellite → Texture → Background → GRLE → Config → Road → I3d → Building
```

Order matters because several components read outputs from earlier ones.

### 2.2 Inter-Component Communication

The most problematic design pattern: components communicate by writing JSON files to the `info_layers/` directory, which later components read back from disk.

| Writer | File Written | Readers |
|--------|-------------|---------|
| `Texture` | `info_layers/textures.json` | `Background`, `GRLE`, `I3d`, `Road`, `Building` |
| `Background` | `info_layers/background.json` | (currently nothing reads it, future use) |

**What `textures.json` contains:**
```json
{
  "fields": [ [[x,y], ...], ... ],
  "buildings": [ [[x,y], ...], ... ],
  "roads_polylines": [ {"points": [[x,y], ...], "width": 8, "tags": "...", "road_texture": "asphalt"}, ... ],
  "water_polylines": [ {"points": [[x,y], ...], "width": 4, "tags": "..."}, ... ],
  "farmyards": [ [[x,y], ...], ... ],
  "forest": [ [[x,y], ...], ... ],
  "water": [ [[x,y], ...], ... ],
  "textures": { ... }
}
```

**Why this is bad:**
- Debugging is hard (need to open JSON files to understand state)
- Adds I/O overhead for every component
- Creates invisible coupling (a component silently fails if an earlier one didn't run)
- Makes unit testing a component in isolation very awkward

### 2.3 DEM File Pipeline (Current)

This is particularly messy. The `Background` component instantiates a `DEM` object internally and also manages all the DEM processing:

```
DTM Provider
  → background/FULL.png          (full DEM, map area + surrounding terrain)
  → background/not_substracted.png  (copy of FULL.png, before water depth)
  → background/not_resized.png    (center cutout, map-size only, unmodified)
  → background/not_resized_with_foundations.png  (+ building foundations)
  → background/not_resized_with_flattened_roads.png  (+ flattened roads)
  → map/data/dem.png              (resized to game DEM resolution, final output)
  → map/data/unprocessedHeightMap.png  (FS25: copy of dem.png)
```

Seven DEM-related files are created. Most exist only because data cannot be passed in-memory between components.

### 2.4 Water File Pipeline (Current)

```
Texture component
  → info_layers/textures.json     (water polygon coordinates)
  
Background component
  → water/water_resources.png     (polygon-based water mask, 8-bit grayscale)
  → water/line_based_water.obj    (line/polyline-based water mesh)
  → water/elevated_water.obj      (polygon-based water surface mesh on terrain)
  → water/plane_water.obj         (simplified flat water plane mesh)
  → assets/water/water_resources.i3d  (READY TO USE: line-based water i3d)
```

**Actually injected into the FS25 map:**
- `assets/water/water_resources.i3d` — YES (manual import by user into Giants Editor)
- `water_resources.png` — Only used internally for DEM subtraction masking
- `elevated_water.obj` and `plane_water.obj` — NOT directly used; these are intermediate artifacts of the polygon-water generation path
- `line_based_water.obj` — intermediate file; the i3d version is the deliverable

**Recommendation:** Remove `elevated_water.obj` and `plane_water.obj` generation. Keep only `water_resources.png` (internal mask) and `assets/water/water_resources.i3d` (deliverable).

---

## 3. Problems Identified

### 3.1 JSON File-Based Inter-Component Communication

See §2.2. All inter-component data should live in-memory in a context object attached to `Map`.

### 3.2 Scattered DEM Files

See §2.3. Result of passing data via filesystem. With in-memory context, most of these become unnecessary.

### 3.3 FS22 Is Deprecated But Still Present

- `FS22` class in `game.py`
- `templates/fs22-map-template.zip`
- `templates/fs22-texture-schema.json`
- `tests/test_generator.py` has `GAME_CODE_CASES = {"FS25": 3, "FS22": 1}` — FS22 test cases

### 3.4 QGIS Feature Is Deprecated But Still Present

- `generator/qgis.py` — 180-line module with QGIS script templates
- `Component.create_qgis_scripts()` called by `Config` and `Background`
- Creates `.py` script files in the `scripts/` directory
- These scripts were designed for a QGIS plugin workflow that was deprecated ~1 year ago
- No external callers depend on this feature any more

### 3.5 Complex Inheritance Chains

- `Road(I3d, MeshComponent)` — Road reads I3d's methods but conceptually Road is not an I3d editor
- `Building(I3d)` — similarly coupled to I3d for XML manipulation reasons
- `I3d(XMLComponent, ImageComponent)` — needs both because DEM z-coordinate lookup mixes in image reading

Root cause: `Component` base class has too many responsibilities. Helper methods for geometry, image processing, XML editing, and QGIS scripting are all mixed in.

### 3.6 Hard-Coded XPath Strings in Component Code

Examples in `i3d.py`:
```python
path = ".//Scene/TerrainTransformGroup"
sun_element_path = ".//Scene/Light[@name='sun']"
displacement_layer_path = ".//Scene/TerrainTransformGroup/Layers/DisplacementLayer"
```

Examples in `config.py`:
```python
latitude_element = root.find("./latitude")
max_height_element = season.find("./fog/heightFog/maxHeight")
```

These strings are game-version-specific. When FS28 changes the i3d structure, every component file needs to be hunted through.

### 3.7 `Game` Class as a Method Forest

`FS25.dem_file_path()`, `FS25.weights_dir_path()`, `FS25.i3d_file_path()`, `FS25.get_farmlands_xml_path()`, etc. — all of these are just `os.path.join(map_directory, "hardcoded/relative/path")`. There are 10+ such methods, all overridden per game version.

### 3.8 Texture Component Does Too Much

`texture.py` is responsible for:
1. Reading OSM features from a bounding box OR custom OSM file
2. Converting coordinates to pixel space
3. Drawing polygons and polylines to image buffers
4. Managing layer schemas
5. Scaling/rotating/dissolving images
6. Saving info-layer JSON
7. Saving procedural mask images
8. Scaling texture output sizes

Responsibilities 1–5 are pure OSM rendering and have no FS25 dependency. They could become a standalone library.

### 3.9 `SharedSettings` Is a Hidden Side Channel

`SharedSettings` on the `Map` object is mutated during DEM processing and read during I3D processing:

```python
# In DEM:
self.map.shared_settings.mesh_z_scaling_factor = ...
self.map.shared_settings.height_scale_multiplier = ...
self.map.shared_settings.height_scale_value = ...
self.map.shared_settings.change_height_scale = True

# In I3d:
if self.map.shared_settings.change_height_scale:
    value = self.map.shared_settings.height_scale_value
```

This is an undocumented cross-component dependency. It's another form of the info-layer problem but in memory.

### 3.10 `Parameters` Class Is Unbounded

`Parameters` is a flat bag of ~30 string constants with no grouping. Constants for file names, size limits, image layer names, and node ID offsets are mixed together.

### 3.11 Statistics Module Blocks Generation

`statistics.py` sends telemetry after generation. The `post()` function starts a non-daemon thread but then calls `thread.join(timeout=15)`, making it _synchronous_ with up to a 15-second block. This is a blocking operation in the generation pipeline that isn't communicated to the user.

### 3.12 `settings.py` — Fragile `__subclasses__()` Introspection

`SettingsModel` has three class methods (`all_settings_to_json`, `all_settings_from_json`, `all_settings`) that discover subclasses via `cls.__subclasses__()` at runtime. This is fragile:
- Import order can cause subclasses to be invisible
- Subclasses defined in un-imported modules will be silently skipped
- `camel_to_snake()` uses a regex hack: `re.split(r"(Settings)", camel_string)` to produce a snake_case key — difficult to maintain

Additionally, `MainSettings.to_json()` manually enumerates all 18 fields explicitly, even though `MainSettings` is a `NamedTuple` and `self._asdict()` would produce an identical result.

### 3.13 `config.py` Is a Side-Effect Module

`config.py` is not a configuration module — it is a _startup sequence_ disguised as one. At import time, it unconditionally runs:
- `ensure_templates()` — downloads a GitHub zip archive
- `ensure_template_subdirs()` — creates directories
- `ensure_locale()` — downloads another GitHub zip archive
- `ensure_executables()` — downloads Windows executables

This means **importing any maps4fs symbol can trigger 3 network requests and multiple filesystem operations**. Constants, directory paths, setup logic, and network download code are all in the same 400-line file.

The fix: split into `constants.py` (pure constants, zero side effects) and `bootstrap.py` (setup functions, called explicitly by the application entry point, not on import).

### 3.14 `monitor.py` — Level Override Bug

In `Logger.__init__`, the environment variable `MFS_LOG_LEVEL` is read into `log_level` but then `self.setLevel(level)` is called with the _constructor argument_ instead of `log_level`. The env var override never takes effect:

```python
log_level = os.getenv(MFS_LOG_LEVEL, level)  # reads env var...
...
self.setLevel(level)                          # ...then ignores it
```

Also, `group_by_level()` calls `pop_session_logs()` (destructive), consuming the logs as a side effect of grouping them. A non-destructive `peek` variant is missing.

### 3.15 `statistics.py` — Procedural Module-Level Functions

The four public functions (`send_main_settings`, `send_advanced_settings`, `send_survey`, `send_performance_report`) and the private `post()` are module-level functions that read `STATS_HOST` and `API_TOKEN` from module-level globals. This makes testing and configuration injection awkward. A simple `StatisticsClient` class that reads credentials once at construction, with private `_post()`, would be cleaner — without changing any endpoint paths or the external API contract.

### 3.16 `utils.py` — Name Does Not Describe Content

The module name `utils.py` communicates nothing. It currently contains at least five unrelated responsibilities:
1. OSM file validation (`check_osm_file`, `fix_osm_file`, `check_and_fix_osm`)
2. Geocoding / region lookup (`get_country_by_coordinates`, `get_region_by_coordinates`)
3. Timestamp formatting (`get_timestamp`)
4. Coordinate string formatting (`coordinate_to_string`)
5. JSON file writing (`dump_json`)
6. `Singleton` metaclass

Note: `check_osm_file` imports `from maps4fs.generator.game import FS25` — this ties OSM validation to a specific game class, which will become even more wrong once `FS22` is removed and `FS25` becomes `GameConfig`.

### 3.17 `layer.py` — 23-Argument Constructor

`Layer.__init__` accepts 23 explicit keyword arguments. This is unmanageable to read, call, mock, or extend. The class should be a `@dataclass` — all arguments already have defaults (except `name` and `count`), so the transition is straightforward. Additional issues:
- `paths()` has a hardcoded `inconsistent_names = ["forestRockRoots", "waterPuddle"]` list — game-specific exceptions baked into what should be generic logic
- `to_json()` manually builds a dict of every attribute and then filters `None` values — with `@dataclass` this would be `{k: v for k, v in dataclasses.asdict(self).items() if v is not None}`

---

## 4. Proposed New Architecture

### 4.1 Module Structure

```
maps4fs/
  __init__.py                     # Public API: Map, Game, GenerationSettings, etc.
  generator/
    map.py                        # Map class (simplified)
    game.py                       # Game + GameConfig dataclass (FS25 only)
    settings.py                   # Settings models (cleaned, backward-compatible interface)
    constants.py                  # RENAMED/SPLIT from config.py: pure path constants, no side effects
    bootstrap.py                  # SPLIT from config.py: setup/download functions, called explicitly
    context.py                    # NEW: MapContext — in-memory inter-component data
    monitor.py                    # Logger (bug fixed), PerformanceMonitor
    statistics.py                 # StatisticsClient class, truly non-blocking background thread
    osm.py                        # SPLIT from utils.py: OSM file validation/fixing
    geo.py                        # SPLIT from utils.py: geocoding, region lookup
    component/
      __init__.py
      layer.py                    # Layer model (refactored to @dataclass)
      dem.py                      # DEM processing (standalone, no background coupling)
      texture.py                  # OSM → textures (populates context, no JSON files)
      background.py               # Background terrain (reads context, uses DEM)
      grle.py                     # InfoLayer PNGs (reads context)
      scene.py                    # RENAMED from i3d.py (map.i3d/splines/fields/trees)
      config.py                   # map.xml, fog, overview, license plates
      road.py                     # Road mesh (reads context, uses LineSurface)
      building.py                 # Building placement (reads context, uses scene)
      satellite.py                # Satellite image download
      base/
        component.py              # Lifecycle only: preprocess, process, info_sequence, previews
        component_image.py        # Image utilities (unchanged)
        component_xml.py          # XML helpers + game-config-driven XPath (improved)
        component_mesh.py         # Mesh utilities (unchanged)
```

### 4.2 MapContext — Replacing JSON Files

A new `MapContext` class replaces all `info_layers/*.json` files as the inter-component communication mechanism:

```python
@dataclass
class MapContext:
    """In-memory store for data shared between components during generation."""
    
    # Populated by Texture component
    fields: list[list[tuple[int, int]]] = field(default_factory=list)
    buildings: list[list[tuple[int, int]]] = field(default_factory=list)
    roads_polylines: list[RoadPolylineInfo] = field(default_factory=list)
    water_polylines: list[WaterPolylineInfo] = field(default_factory=list)
    water_polygons: list[list[tuple[int, int]]] = field(default_factory=list)
    farmyards: list[list[tuple[int, int]]] = field(default_factory=list)
    
    # Populated by DEM/Background component
    height_scale_value: int | None = None
    mesh_z_scaling_factor: float | None = None
    
    # Asset paths populated by components (for consumer components to discover outputs)
    dem_path: str | None = None
    background_dem_path: str | None = None   # pre-subtraction copy
```

`Map` holds a `MapContext` instance. All components receive the map reference and read/write through `map.context`.

No more `SharedSettings` as a loose bag of mutable state. No more `info_layers/*.json` files created during generation (they may still be saved post-generation as debug output, but not as the communication channel).

### 4.3 GameConfig — Data-Driven Game Support

Replace the `FS22`/`FS25` class hierarchy with a data-driven `GameConfig`:

```python
@dataclass
class GameConfig:
    code: str
    dem_multiplier: int
    
    # File paths (relative to map_directory, so adding a new game = adding new paths)
    dem_path: str
    weights_dir: str
    i3d_path: str
    splines_path: str
    map_xml_path: str
    farmlands_xml_path: str | None
    environment_xml_path: str | None
    overview_path: str | None
    license_plates_dir: str | None
    additional_dem_name: str | None
    
    # Schema files (relative to templates/)
    texture_schema: str
    grle_schema: str | None
    tree_schema: str | None
    buildings_schema: str | None
    map_template: str
    
    # Feature flags
    i3d_processing: bool = True
    plants_processing: bool = True
    environment_processing: bool = True
    fog_processing: bool = True
    dissolve: bool = True
    mesh_processing: bool = True
    
    # XML patches: list of (xpath, attribute_name, value_template)
    # Value templates can use {map_size}, {height_scale}, etc.
    xml_patches: list[XmlPatch] = field(default_factory=list)
```

`FS25_CONFIG = GameConfig(code="FS25", dem_path="map/data/dem.png", ...)` — one declaration, no class inheritance.

Adding FS28 = adding `FS28_CONFIG = GameConfig(...)` + new schema JSON files. Zero changes to component code.

### 4.4 Simplified `Game` Class

```python
class Game:
    def __init__(self, config: GameConfig, map_template_path: str | None = None):
        self.config = config
    
    @classmethod
    def from_code(cls, code: str) -> Game:
        configs = {cfg.code: cfg for cfg in [FS25_CONFIG]}
        if code not in configs:
            raise ValueError(f"Unknown game: {code}")
        return cls(configs[code])
    
    # Path helpers become simple properties, not overridable methods
    def dem_file_path(self, map_directory: str) -> str:
        return os.path.join(map_directory, self.config.dem_path)
    
    def weights_dir_path(self, map_directory: str) -> str:
        return os.path.join(map_directory, self.config.weights_dir)
    
    # ... etc
```

### 4.5 I3D/XML Wrapper

There are two distinct XML interaction problems:

1. **Game-config-driven patches** — fixed attribute writes that happen at the end of every generation (height scale, map size, sun shadow bbox, fog, etc.). These are handled by `XmlPatch` + `GameConfig`:

```python
@dataclass
class XmlPatch:
    file: Literal["i3d", "map_xml", "environment_xml", "farmlands_xml"]
    xpath: str
    attributes: dict[str, str]  # attribute name → value template

FS25_CONFIG = GameConfig(
    ...
    xml_patches=[
        XmlPatch("i3d", ".//Scene/TerrainTransformGroup", {"heightScale": "{height_scale}"}),
        XmlPatch("i3d", ".//Scene/Light[@name='sun']", {
            "lastShadowMapSplitBboxMin": "-{half_map_size},-128,-{half_map_size}",
            "lastShadowMapSplitBboxMax": "{half_map_size},148,{half_map_size}",
        }),
        XmlPatch("map_xml", ".//map", {"width": "{scaled_size}", "height": "{scaled_size}"}),
        ...
    ]
)
```

A single `apply_xml_patches(game_config, map_directory, context)` function handles all of this at the end of generation.

2. **Dynamic XML manipulation** — components that _add_ nodes at runtime (splines, field markers, tree instances, building models, farmland entries). These currently call raw `ET.parse()` / `.getroot()` / `.find()` / `.findall()` / `.SubElement()` scattered throughout every component.

Both problems are solved by a single `XmlDocument` wrapper class that lives in `component_xml.py`:

```python
class XmlDocument:
    """Fluent, safe wrapper around ElementTree. Replaces direct tree/root/find usage."""

    def __init__(self, path: str):
        self._path = path
        self._tree = ET.parse(path)
        self._root = self._tree.getroot()

    # --- read ---

    def get(self, xpath: str) -> ET.Element | None:
        """Find one element; returns None if missing."""
        return self._root.find(xpath)

    def require(self, xpath: str) -> ET.Element:
        """Find one element; raises ValueError if missing."""
        element = self._root.find(xpath)
        if element is None:
            raise ValueError(f"Required XML element not found: {xpath!r}")
        return element

    def find_all(self, xpath: str) -> list[ET.Element]:
        return self._root.findall(xpath)

    # --- write ---

    def set_attrs(self, xpath: str, **attrs: str) -> XmlDocument:
        """Set attributes on the element at xpath. Fluent — returns self."""
        elem = self.require(xpath)
        for key, value in attrs.items():
            elem.set(key, value)
        return self

    def append_child(self, xpath: str, tag: str, **attrs: str) -> ET.Element:
        """Append a new child element to the element at xpath."""
        parent = self.require(xpath)
        child = ET.SubElement(parent, tag)
        for key, value in attrs.items():
            child.set(key, value)
        return child

    def remove_element(self, xpath: str) -> XmlDocument:
        """Remove all elements matching xpath from their parent."""
        for elem in self._root.findall(xpath):
            parent_xpath = xpath.rsplit("/", 1)[0] or "."
            parent = self._root.find(parent_xpath)
            if parent is not None:
                parent.remove(elem)
        return self

    # --- persistence ---

    def save(self) -> None:
        self._tree.write(self._path, encoding="unicode", xml_declaration=False)

    def __enter__(self) -> XmlDocument:
        return self

    def __exit__(self, *_) -> None:
        self.save()
```

**Usage example — before vs. after:**

```python
# Before (current code in i3d.py)
tree = ET.parse(i3d_path)
root = tree.getroot()
terrain = root.find(".//Scene/TerrainTransformGroup")
if terrain is not None:
    terrain.set("heightScale", str(height_scale))
tree.write(i3d_path)

# After
with XmlDocument(i3d_path) as doc:
    doc.set_attrs(".//Scene/TerrainTransformGroup", heightScale=str(height_scale))
```

```python
# Before (adding a spline node)
splines_root = ET.parse(splines_path).getroot()
scene = splines_root.find(".//Scene")
if scene is not None:
    spline_elem = ET.SubElement(scene, "NurbsCurve")
    for k, v in spline_attrs.items():
        spline_elem.set(k, v)
    ...

# After
with XmlDocument(splines_path) as doc:
    doc.append_child(".//Scene", "NurbsCurve", **spline_attrs)
```

All components receive `XmlDocument` instances (or construct them) — no component ever calls `ET.parse()`, `.getroot()`, `.find()`, `.findall()`, or `ET.SubElement()` directly. These are implementation details of `XmlDocument`.

---

## 5. Component-by-Component Analysis

### 5.1 `Satellite`

**Current:** Standalone download-only component with minimal coupling. Simple.

**Issues:** None significant.

**Proposed changes:**
- Extract `SatelliteImage` NamedTuple to a more appropriate location (it's just a task descriptor)
- Minor cleanup only

---

### 5.2 `Texture`

**Current:** Largest and most complex component. Handles OSM fetching, coordinate projection, polygon drawing, layer management, info-layer JSON writing, scaling, rotation, dissolve, procedural masks. The whole rendering pipeline.

**Issues:**
- Saves `info_layers/textures.json` — the root of the inter-component coupling problem
- Reads custom OSM schema via kwargs (`texture_custom_schema`) — this is passed through multiple layers and should be a first-class `Map` attribute
- `info_layer_path` is configurable via kwargs because Background creates a secondary Texture instance for background textures — this is a sign the design is fighting itself
- Geometry is drawn with `scale_factor` (map pixel ↔ meters) baked in, making the component tightly coupled to map size

**Proposed changes:**
- Replace `save_info_layer()` with writing to `map.context` (fields, buildings, roads, water, etc.)
- Remove `info_layer_path` kwarg — if Background needs a texture, it should call a shared OSM renderer utility, not instantiate a full `Texture` component
- Consider extracting the pure OSM-to-image drawing logic to a separate module or package (`osm_renderer`), leaving only the maps4fs-specific wiring in this component

**Important: OSM library must be schema-agnostic.** The future `osm_renderer` extract must not depend on maps4fs's `Layer` class, the FS25 texture schema JSON format, or any game-specific tag sets. Its interface should accept generic inputs — a bounding box or geometry source, a list of tag filters with associated draw parameters (width, color, fill), and a target image size — and return numpy arrays or write to image files. The maps4fs `Texture` component is the adapter layer that translates `Layer` objects and schema data into those generic draw parameters. Keeping this separation clean is what makes the OSM renderer reusable outside maps4fs.

**Multithreading in the OSM renderer.** The current Texture component processes layers sequentially. Since each OSM feature type (roads, fields, water, buildings, forest, etc.) is an independent draw call on a separate image buffer, they are embarrassingly parallel — subject to one constraint: the **base layer** (the fill-everything background texture) must be written first, because other layers are drawn on top of it. The proposed threading model:

```
1. Draw base layer (synchronous, blocks everything else)
2. Draw all non-base layers in a thread pool (concurrent, no inter-layer deps)
3. Merge results in priority order (synchronous, uses layer.priority)
```

The `merge_into` layer logic (where a layer's output is composited into another named layer) must be resolved after all threads finish — it cannot run concurrently with its target. The priority ordering for final compositing onto the shared canvas is already defined per-layer and is not affected by draw parallelism.

Implementation note: drawing uses `cv2` (OpenCV) and `numpy` operations. OpenCV releases the GIL for most pixel operations, so `ThreadPoolExecutor` provides real parallelism here without needing multiprocessing. Each layer draws into its own `numpy` array and the merge step is single-threaded, avoiding any shared-state races.

**General performance targets for the refactor.** Beyond the OSM renderer, the refactor should treat generation speed as a first-class concern:
- Eliminate all unnecessary disk I/O (intermediate files that only exist because context isn't in-memory)
- Profile with `PerformanceMonitor` before and after each refactoring step; do not regress on wall-clock time
- Prefer in-place `numpy` array mutation over creating copies where correctness allows
- Avoid re-reading files that were just written (e.g. DEM written then immediately re-read by the next component — context eliminates this)
- Cache OSM fetches (already done via `oxc` cache) and DTM fetches (already cached) — ensure the cache is preserved and not accidentally invalidated during refactor

---

### 5.3 `DEM`

**Current:** Creates the raw DEM from a DTM provider. But it's instantiated as a _sub-object_ inside `Background`, not run as its own pipeline stage. The `DEM` component in the game component list is absent — it does not appear in `game.components`. Background does all the DEM work internally.

Wait, actually checking the code: `DEM` is NOT in `game.components`:
```python
components = [Satellite, Texture, Background, GRLE, Config, Road, I3d, Building]
```

**The DEM component is not independently orchestrated at all.** `Background` instantiates it and calls `preprocess()` and `process()` itself. This means DEM is effectively a helper class for Background, not a standalone pipeline component.

**Issues:**
- Confusing architecture: `DEM` walks like a component but isn't treated as one
- All DEM state (paths, data, height scale) lives inside `Background`, making `Background` huge
- The height scale computed in DEM needs to propagate to `I3d` through `SharedSettings`, which is a hack

**Proposed changes:**
- Make `DEM` a true first-class component in the pipeline, running before `Background`
- `DEM` writes its outputs to `map.context`: `context.height_scale_value`, `context.dem_array`, `context.dem_path`
- `Background` reads the DEM array from context instead of re-running DEM internally
- `I3d` reads height scale from context instead of from `SharedSettings`

---

### 5.4 `Background`

**Current:** The heaviest component. Does:
1. Instantiates and runs `DEM` internally
2. Cuts the DEM to map size
3. Flattens roads in DEM (creating `not_resized_with_flattened_roads.png`)
4. Creates building foundations in DEM (requires buildings from `textures.json`)
5. Generates background terrain obj/i3d mesh
6. Generates water resources texture
7. Generates water meshes (line-based + polygon-based)
8. Processes road surface masks
9. Creates background texture images (by spinning up a secondary `Texture` instance)

**Issues:**
- Far too many responsibilities
- The secondary Texture instance it creates is an architectural oddity
- Multiple DEM intermediate files (§2.3)
- `mesh_info` is a mutable list accumulated during `generate_obj_files()` — not thread-safe, order-dependent
- Reads `textures.json` for buildings and water data

**Proposed changes:**
- Split into at most two responsibilities: (1) DEM cutout + modifications, (2) mesh generation
- After `DEM` becomes a first-class component, `Background` only handles: cut to map size → apply water depth → apply road flattening → apply foundations → save final DEM → optionally generate meshes
- Water mesh generation: keep `line_based_water_mesh` → `water_resources.i3d` pipeline; remove `elevated_water.obj` and `plane_water.obj` (they are not deliverables)
- Read road/water/building data from `map.context` instead of `textures.json`
- Background textures: extract the secondary `Texture` trick into a proper `create_mask_from_layers()` utility that the background component calls directly

---

### 5.5 `GRLE`

**Current:** Creates InfoLayer PNG files (farmlands, plants, environment, indoor mask). Reads fields and farmyards from `textures.json`. Also does XML editing for `farmlands.xml`.

**Issues:**
- Mixing two concerns: image file creation (PNG) and XML editing (`farmlands.xml`)
- The `plant_to_pixel_value()` and `area_type_to_pixel_value()` functions are module-level but game-specific — they should be in the GRLE schema or a config
- Reads `textures.json` for field/farmyard data

**Proposed changes:**
- Read field/farmyard data from `map.context` instead of `textures.json`
- Move `plant_to_pixel_value` and `area_type_to_pixel_value` into the GRLE schema JSON (extend schema format to include pixel value mappings)
- The XML part (farmlands.xml editing) stays — it's correctly an XML component

---

### 5.6 `Config`

**Current:** Sets map size in `map.xml`, adjusts fog in `environment.xml`, generates overview image DDS, updates license plates, saves QGIS scripts.

**Issues:**
- QGIS script saving is deprecated; calls `self.qgis_sequence()` and `self.create_qgis_scripts()` from several places
- `_set_overview()` calls `game.overview_file_path()` — this continues the method-per-path pattern
- `_adjust_fog()` has hardcoded XPath for environment XML

**Proposed changes:**
- Remove all QGIS-related methods and calls
- Move the hardcoded XPath fog adjustments to `GameConfig.xml_patches`
- Move map size XML patching to `GameConfig.xml_patches`
- `Config` component becomes responsible only for: overview image generation, license plates update

---

### 5.7 `Road`

**Current:** Inherits from `I3d, MeshComponent`. Reads road polylines from `textures.json`. Generates road surface meshes (OBJ → i3d via external converter).

**Issues:**
- Inherits from `I3d` only to reuse some mesh/coordinate helper methods, not because `Road` IS an `I3d` editor
- Reads from `textures.json`
- T-junction patch logic is complex but self-contained

**Proposed changes:**
- Change inheritance to `MeshComponent` only (stop inheriting from `I3d`)
- Move any shared helper methods needed by both to `component_mesh.py` or `component.py`
- Read road data from `map.context.roads_polylines` instead of `textures.json`

---

### 5.8 `I3d`

**Current:** Edits `map.i3d` (height scale, sun shadow, displacement layer), manages `splines.i3d` (road/water/field splines), places field markers, places trees.

**Issues:**
- Mixed concerns: map.i3d edits, splines.i3d management, field placement, tree placement
- Hardcoded XPath strings: `".//Scene/TerrainTransformGroup"`, `".//Scene/Light[@name='sun']"`, etc.
- Reads from `textures.json` for roads, water, and fields
- The `update_height_scale()` method reads from `SharedSettings` — indirect coupling to DEM

**Proposed changes:**
- Rename to `Scene` to avoid the confusing name (it manages the FS25 scene, not just i3d)
- Move all XPath-dependent XML edits to `GameConfig.xml_patches`, applied by a utility
- Read road/water/field data from `map.context` instead of `textures.json`
- Read height scale from `map.context.height_scale_value` instead of `SharedSettings`

---

### 5.9 `Building`

**Current:** Inherits from `I3d`. Reads building footprints from `textures.json`. Places building models in `map.i3d` based on footprint dimensions and categories.

**Issues:**
- Inherits from `I3d` but is conceptually a separate concern
- Reads from `textures.json`
- `BuildingEntryCollection` is a useful abstraction, but it and `BuildingEntry` could live in a separate `buildings.py` module

**Proposed changes:**
- Break inheritance from `I3d`; use `XMLComponent` directly
- Move `BuildingEntry`, `BuildingEntryCollection` to a `buildings.py` module (or keep in `building.py` — not a priority)
- Read building data from `map.context.buildings` instead of `textures.json`

---

### 5.10 `settings.py`

**Current:** All settings models live here: `Parameters`, `SharedSettings`, `SettingsModel` base + 7 component settings classes, `GenerationSettings`, and `MainSettings`. Backward compatibility is important — the public API (`GenerationSettings`, each component settings class) must not change.

**Issues:**
- `SettingsModel.all_settings_to_json()`, `all_settings_from_json()`, `all_settings()` use `cls.__subclasses__()` introspection (see §3.12) — fragile and non-obvious
- `MainSettings.to_json()` duplicates `self._asdict()` with 18 explicit lines; since `MainSettings` is a `NamedTuple`, `_asdict()` is identical
- `SharedSettings` is a mutable Pydantic model used as a side-channel between DEM and I3d (being removed)
- `Parameters` is a flat string-constants bag mixed with numeric constants

**Proposed changes (backward-compatible):**
- Replace `SettingsModel.all_settings_from_json()` with a direct mapping in `GenerationSettings.from_json()` — explicit is better than magic `__subclasses__()` scanning
- Remove `all_settings_to_json()` and `all_settings()` from `SettingsModel` base (not part of public API; `GenerationSettings.to_json()` is)
- Replace `MainSettings.to_json()` body with `return self._asdict()`
- Remove `SharedSettings` (replaced by `MapContext`)
- Group `Parameters` constants by domain: `DemParameters`, `WaterParameters`, `PlantsParameters`, etc. — or dissolve into the modules that actually use them
- `GRLESettings.base_grass: tuple | str = ("smallDenseMix", "meadow")` — the `tuple | str` union is a legacy artifact. The value is sent as a string by the UI, but the Pydantic default is a tuple; `all_settings_from_json` handled this via the `flattening` workaround that took `value[0]`. After removing that flattening hack, this field should be a simple `str` with a `Literal` annotation covering the known FS25 plant names (mirroring `BuildingSettings.region: Literal["auto", "all", "EU", "US"]`). Valid values should come from `fs25-grle-schema.json`, not be hardcoded in Python.

---

### 5.11 `config.py` (generator-level)

**Current:** 400-line file mixing path constants, directory creation, template download logic, locale download logic, and Windows executable download logic — all running at module import time.

**Issues:** See §3.13. Unusable for unit tests without triggering network calls. Any `import maps4fs` silently starts downloading files.

**Proposed changes:**
- **`constants.py`** (new name/file): pure constants only — `MFS_TEMPLATES_DIR`, `MFS_EXECUTABLES_DIR`, `MFS_ROOT_DIR`, `DTM_CACHE_DIR`, `I3D_CONVERTER_NAME`, `TEXCONV_REMOTE_URL`, etc. Zero side effects, zero imports beyond `os`.
- **`bootstrap.py`** (new name/file): `ensure_templates()`, `ensure_template_subdirs()`, `ensure_locale()`, `ensure_executables()`, `create_cache_dirs()`, `reload_templates()`. Called explicitly by the application (UI, Docker entrypoint, CLI), never on import.
- `get_map_bounds_file_paths()`, `get_windows_executable_path()`, `get_i3d_executable_path()`, `get_texconv_executable_path()` stay in `constants.py` or `bootstrap.py` as appropriate (they are pure lookups, no downloads).
- The `_urlopen_with_ssl_fallback()` helper moves into `bootstrap.py` (it is only used there).

---

### 5.12 `monitor.py`

**Current:** `Logger`, `PerformanceMonitor` (Singleton), `monitor_performance` decorator, `get_current_session()`, `performance_session()`. Well-structured overall.

**Issues:**
- Bug: env var `MFS_LOG_LEVEL` is read but then `self.setLevel(level)` is called with the constructor argument, ignoring the env var (see §3.14)
- `group_by_level(session_id)` calls `pop_session_logs()` internally — groups are returned but the logs are also consumed/removed as a side effect
- `Singleton` metaclass is imported from `utils.py`; after the utils split this dependency needs updating

**Proposed changes:**
- Fix `setLevel` bug: `self.setLevel(log_level)` not `self.setLevel(level)`
- Add `peek_session_logs(session_id)` that reads without consuming, or separate `group_by_level` from the consumption
- After `utils.py` split, move `Singleton` to `monitor.py` itself (it's only used there)

---

### 5.13 `statistics.py`

**Current:** 4 public module-level functions that build endpoint URLs and call `post()`, which starts a thread but then blocks for 15 seconds waiting for it.

**Issues:** See §3.15. The function signatures and endpoint paths are the public API contract with the remote statistics server — these must not change.

**Proposed changes:**
- Wrap in a `StatisticsClient` class:
  ```python
  class StatisticsClient:
      def __init__(self):
          self._host = os.getenv("STATS_HOST")
          self._token = os.getenv("API_TOKEN")
      
      def _post(self, endpoint: str, data: dict) -> None:
          """Fire-and-forget POST in a daemon thread."""
          def _thread():
              ...
          threading.Thread(target=_thread, daemon=True).start()
          # No join — truly non-blocking
      
      def send_main_settings(self, data: dict) -> None:
          self._post(f"{self._host}/receive_main_settings", data)
      
      # ... same for send_advanced_settings, send_survey, send_performance_report
  ```
- Keep the module-level shim functions for backward compatibility:
  ```python
  _client = StatisticsClient()
  def send_main_settings(data): _client.send_main_settings(data)
  def send_advanced_settings(data): _client.send_advanced_settings(data)
  # etc.
  ```
- Make `_post` use a daemon thread without joining — truly fire-and-forget. If the request doesn't complete before process exit, that's acceptable for telemetry.

---

### 5.14 `utils.py`

**Current:** Six responsibilities in one module with a generic name (see §3.16).

**Proposed changes — split into focused modules:**
- **`osm.py`**: `check_osm_file`, `fix_osm_file`, `check_and_fix_osm`. The `FS25` game import inside `check_osm_file` should be replaced — the function should accept a `schema` parameter (or this validation should move into the `Texture` component where it belongs with proper context).
- **`geo.py`**: `get_country_by_coordinates`, `get_region_by_coordinates`. These are only called from `settings.py` (`MainSettings.from_map()`) and potentially `building.py`; make the dependency explicit.
- Small utility functions (`get_timestamp`, `coordinate_to_string`, `dump_json`) can be inlined into their single callers or go into a minimal `helpers.py`.
- `Singleton` moves to `monitor.py` (its only consumer).

---

### 5.15 `layer.py`

**Current:** `Layer` has a 23-argument constructor, all wired up in `__init__` one by one, plus `to_json()`, `from_json()`, `path()`, `path_preview()`, `get_preview_or_path()`, `paths()`. Loaded from JSON schema files; `from_json()` uses `cls(**data)`.

**Issues:** See §3.17.

**Proposed changes:**
- Convert to `@dataclass`:
  ```python
  @dataclass
  class Layer:
      name: str
      count: int
      tags: dict[str, str | list[str] | bool] | None = None
      width: int | None = None
      color: tuple[int, int, int] | list[int] = field(default_factory=lambda: (255, 255, 255))
      exclude_weight: bool = False
      priority: int | None = None
      info_layer: str | None = None
      usage: str | None = None
      background: bool = False
      invisible: bool = False
      procedural: list[str] | None = None
      border: int | None = None
      precise_tags: dict[str, str | list[str] | bool] | None = None
      precise_usage: str | None = None
      area_type: str | None = None
      area_water: bool = False
      indoor: bool = False
      merge_into: str | None = None
      building_category: str | None = None
      external: bool = False
      road_texture: str | None = None
      save_tags: bool = False
  ```
- `from_json()` keeps `cls(**data)` — works identically with dataclass.
- `to_json()` becomes `{k: v for k, v in dataclasses.asdict(self).items() if v is not None}` — no manual dict.
- Remove hardcoded `inconsistent_names = ["forestRockRoots", "waterPuddle"]` in `paths()` — this list belongs in the texture schema JSON, not in the model.

---

## 6. Files and Features to Remove

| Item | Why |
|------|-----|
| `maps4fs/generator/qgis.py` | QGIS feature deprecated ~1 year ago |
| `Component.create_qgis_scripts()` | QGIS feature |
| `Component.qgis_sequence()` in Config and Background | QGIS feature |
| `templates/fs22-map-template.zip` | FS22 deprecated |
| `templates/fs22-texture-schema.json` | FS22 deprecated |
| `FS22` class in `game.py` | FS22 deprecated |
| FS22 test cases in `test_generator.py` | FS22 deprecated |
| `water/elevated_water.obj` generation | Not a deliverable, intermediate artifact |
| `water/plane_water.obj` generation | Not a deliverable, intermediate artifact |
| `background/not_resized.png` (intermediate) | Replaced by in-memory context |
| `background/not_resized_with_foundations.png` (intermediate) | Replaced by in-memory context |
| `background/not_resized_with_flattened_roads.png` (intermediate) | Replaced by in-memory context |
| `SharedSettings` (mesh_z_scaling_factor, height_scale_*) | Replaced by `MapContext` |
| `Map.get_texture_component()`, `Map.get_background_component()`, `Map.get_satellite_component()` | Replace with cleaner context API |

---

## 7. Files to Keep (and Why)

| File/Feature | Why Keep |
|-------------|----------|
| `water/line_based_water.obj` | Input to the water i3d converter |
| `assets/water/water_resources.i3d` | Deliverable for user to import into Giants Editor |
| `assets/background/background_terrain.i3d` | Deliverable |
| `map/overview.dds` | Required by FS25 map for in-game minimap; not optional |
| `generation_info.json` | Useful debug/info output |
| `generation_logs.json` | Useful debug output |
| `performance_report.json` | Useful profiling output |
| `texconv.exe` integration | Required for DDS conversion on Windows |
| `i3dConverter.exe` integration | Required for mesh-to-i3d conversion |

---

## 8. Async Verdict

**Verdict: Do NOT make the library async.**

Reasoning:
- The component pipeline is inherently sequential — each component depends on outputs of previous ones. This cannot be parallelized.
- The only significant async opportunity is network I/O (OSM download, DTM download, satellite images). These use blocking third-party libraries (`osmnx`, `pydtmdl`, `pygmdl`) that would need async rewrites to benefit from async.
- `Map.generate()` is already a generator (`yield component_name`) — callers can yield control between components for responsive UIs without needing the library to be async.
- Adding async throughout would roughly double the complexity of every component's code while providing no measurable user benefit in the typical use case.

If parallel external downloads are desired in the future, they can be added as `asyncio.gather()` at the network call sites in DTM/satellite components without making the entire pipeline async.

---

## 9. Settings and Schema Changes

### 9.1 Settings Changes

| Class / Method | Change | Reason |
|----------------|--------|--------|
| `SharedSettings` | Remove | Replaced by `MapContext` |
| `Parameters` | Split into domain-grouped constants or inline into callers | Flat bag of unrelated constants is hard to navigate |
| `SettingsModel.all_settings_to_json()` | Remove | Unused by `GenerationSettings.to_json()`; subclasses scanning is fragile |
| `SettingsModel.all_settings()` | Remove | Same reason; no external callers |
| `SettingsModel.all_settings_from_json()` | Replace with explicit mapping in `GenerationSettings.from_json()` | Fragile `__subclasses__()` introspection |
| `SettingsModel.camel_to_snake()` | Remove (used only inside `all_settings_from_json`) | Goes away with the above |
| `MainSettings.to_json()` | Simplify to `return self._asdict()` | NamedTuple already provides this; 18-line manual dict is redundant |

All `GenerationSettings`, component settings classes, and their public field names remain unchanged — this is the public API.

### 9.2 Schema Changes

- **Texture schema**: Add optional `pixel_value` to area type layers (currently hardcoded in `grle.py`)
- **GRLE schema**: Add `pixel_value_mappings` section with plant-to-pixel and area-type-to-pixel mappings (currently hardcoded in `grle.py`)
- **Remove**: `fs22-texture-schema.json` (FS22 deprecated)

No breaking changes to the FS25 texture schema are needed to support the refactor.

---

## 10. Tests Plan Skeleton

```python
# test_generator.py (new structure)

# Fixtures
COORDINATE_CASES = {
    "central_europe":  (50.0, 14.0),      # Farmland, roads, rivers
    "usa_midwest":     (41.0, -93.0),      # Flat terrain
    "mountain_region": (46.5, 8.5),        # High elevation variance
    "near_ocean":      (-34.0, 18.4),      # Coast, potential water
    "urban":           (48.8, 2.3),        # Dense buildings
}

SIZES = [512, 1024, 2048]

# For the refactor, FS25 only
def test_dem_file_created_and_valid(map_instance):
    dem_path = map_instance.game.dem_file_path(map_instance.map_directory)
    assert os.path.isfile(dem_path)
    dem = cv2.imread(dem_path, cv2.IMREAD_UNCHANGED)
    assert dem.dtype == np.uint16
    assert dem.shape[0] == dem.shape[1]  # square
    assert dem.max() > 0  # not all zeros

def test_texture_weights_exist(map_instance):
    weights_dir = map_instance.game.weights_dir_path(map_instance.map_directory)
    for layer in load_texture_schema(map_instance.game.texture_schema):
        if layer.get("exclude_weight"):
            continue
        weight_path = os.path.join(weights_dir, f"{layer['name']}01_weight.png")
        assert os.path.isfile(weight_path)

def test_i3d_height_scale_set(map_instance):
    i3d_path = map_instance.game.i3d_file_path(map_instance.map_directory)
    tree = ET.parse(i3d_path)
    element = tree.find(".//Scene/TerrainTransformGroup")
    assert element is not None
    height_scale = int(element.get("heightScale", 0))
    assert height_scale > 0

def test_generation_info_complete(map_instance):
    info_path = os.path.join(map_instance.map_directory, "generation_info.json")
    with open(info_path) as f:
        info = json.load(f)
    expected_keys = {"Texture", "Background", "GRLE", "Config"}
    assert expected_keys.issubset(info.keys())

def test_output_size_rescaling(map_instance_with_output_size):
    dem = cv2.imread(dem_path, cv2.IMREAD_UNCHANGED)
    expected_size = (output_size // 2) * 2 + 1
    assert dem.shape[0] == expected_size

def test_grle_farmlands_file_size(map_instance):
    # infoLayer_farmlands.png should exist and have correct dimensions
    ...

def test_overview_dds_exists(map_instance):
    overview_path = map_instance.game.overview_file_path(map_instance.map_directory)
    assert os.path.isfile(overview_path)
```

---

## 11. Proposed New Directory Layout for `generator/`

```
generator/
  map.py            ~200 lines  (was ~400; context + generate loop simplified)
  game.py           ~100 lines  (was ~550; GameConfig + single Game class)
  context.py         ~80 lines  (NEW: MapContext dataclass)
  settings.py       ~250 lines  (cleaned; fragile introspection removed, SharedSettings gone)
  constants.py       ~60 lines  (SPLIT from config.py: pure path constants, zero side effects)
  bootstrap.py      ~200 lines  (SPLIT from config.py: setup/download functions)
  monitor.py        ~200 lines  (bug-fixed Logger; Singleton moved here from utils)
  statistics.py     ~100 lines  (StatisticsClient class, truly non-blocking)
  osm.py             ~80 lines  (SPLIT from utils.py: OSM file validation/fixing)
  geo.py             ~40 lines  (SPLIT from utils.py: geocoding, region lookup)
  component/
    layer.py         ~100 lines  (refactored to @dataclass; was ~250 with boilerplate)
    dem.py            ~200 lines  (now a real pipeline component)
    texture.py        ~400 lines  (stripped of JSON I/O; writes to context)
    background.py     ~400 lines  (split: DEM cutout + mesh, no DEM instantiation)
    grle.py           ~250 lines  (reads context, schema-driven pixel values)
    scene.py          ~400 lines  (renamed from i3d.py; reads context)
    config.py         ~150 lines  (overview + license plates only)
    road.py           ~250 lines  (reads context, no I3d inheritance)
    building.py       ~300 lines  (reads context, no I3d inheritance)
    satellite.py      ~100 lines  (unchanged)
    base/
      component.py    ~200 lines  (lifecycle + context access only)
      component_image.py   ~200 lines  (unchanged)
      component_xml.py     ~100 lines  (simplified; XPaths moved to GameConfig)
      component_mesh.py    ~300 lines  (unchanged)
```

Target total: **~3500 lines** in generator (down from current ~6000+ across generator alone).

---

## 12. Summary of Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Inter-component data | In-memory `MapContext` | Eliminates I/O, makes testing easy |
| FS22 support | Remove | Deprecated, reduces complexity |
| FS28 support | `GameConfig` dataclass | Adding a game requires data, not code |
| I3D XPath management | `xml_patches` in `GameConfig` | Centralizes game-specific XML knowledge |
| QGIS scripts | Remove | Deprecated ~1 year ago |
| Async | No | Sequential pipeline, no net benefit |
| Texture as library | Evaluate but don't block on it | Extract only if it clearly simplifies maps4fs |
| DEM as pipeline component | Yes | Current hidden-subobject pattern is confusing |
| Intermediate DEM files | Remove most | All intermediate processing goes in-memory |
| Water meshes | Keep line-based i3d only | Polygon meshes are unused intermediates |
| `SharedSettings` | Remove | Replaced by `MapContext` |
| Test coverage | File presence + structure + values | Catches more real regressions |
