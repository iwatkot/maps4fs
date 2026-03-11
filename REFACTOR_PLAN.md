# maps4fs Refactor Plan

## Context

maps4fs started as a small script and grew into a large codebase with legacy patterns:
- Components share data by writing/reading JSON files on disk (`info_layers/` directory)
- Significant amounts of intermediate files saved and never cleaned up
- Complex inheritance chains (e.g. `Road` inherits from `I3d, MeshComponent`)
- XML/i3d editing via raw `ElementTree` with magic XPath strings scattered everywhere
- FS22 is deprecated but still in the codebase
- QGIS scripting feature is deprecated but still in the codebase

The goal is a clean, simple rewrite targeting **FS25 only**, with architecture flexible enough to add future game support without major surgery.

---

## Step 1 — Improve Tests

**Goal:** Make the test suite meaningful enough to validate the refactor.

- Reduce the number of map generation test cases but make them substantially different (mostly, we check that different settings are working properly and validate they were applied)
- Move away from "generation didn't crash" as the primary assertion
- Tests should verify:
  - Generated file existence and correct paths for the target game
  - DEM file dimensions, dtype (`uint16`), and value range (non-trivial, non-flat)
  - Texture weight files existence and correct dimensions
  - I3D file structural validity (parseable XML, height scale element present and non-zero)
  - GRLE files existence, dimensions, and dtype
  - `generation_info.json` completeness (all expected component keys present)
  - Output size rescaling behaves correctly (output dimensions match `output_size`)
  - Map with rotation produces correctly-sized output
  - No FS22 test cases (deprecated)
- Keep tests runnable without network access where possible (mock DTM/OSM or provide cached fixtures)

---

## Step 2 — Audit Settings and Schemas

**Goal:** Ensure settings and schemas are 100% compatible with the new architecture and ready for multi-game support.

### Settings (`settings.py`)

- Review all settings classes: `DEMSettings`, `BackgroundSettings`, `GRLESettings`, `I3DSettings`, `TextureSettings`, `SatelliteSettings`, `BuildingSettings`
- Validate each field is actually used and named clearly
- Verify `GenerationSettings.to_json()` / `GenerationSettings.from_json()` round-trip correctly
- Consider renaming `I3DSettings` → `SceneSettings` (it handles trees, splines, license plates — not just i3d format)
- `GRLESettings.base_grass: tuple | str` — replace `tuple | str` with a plain `str` with a `Literal` type drawn from known FS25 plant names in the GRLE schema (same pattern as `BuildingSettings.region`); the tuple was a workaround for the now-removed `flattening` logic
- `SharedSettings` is a mutable bag used for DEM height scale propagation — document or redesign it
- `Parameters` class is a flat bag of string constants; audit for dead constants

### Schemas (JSON files in `templates/`)

- `fs25-texture-schema.json` — review all layers; ensure `usage`, `background`, `area_type`, `road_texture` fields are consistent
- `fs25-grle-schema.json` — verify layer names match actual FS25 game files
- `fs25-tree-schema.json` — verify tree type names match FS25
- `fs25-buildings-schema.json` — verify building entries have sane dimensions and valid categories/regions
- For each schema: define it in one place with a clear versioned structure, so adding an FS28 just means adding `fs28-*.json` files
- Remove `fs22-texture-schema.json` (FS22 deprecated)

---

## Step 3 — Document What's Changing and What's Not

**Goal:** Protect the stable public API.

The only guaranteed public entry points are:
1. `Map.__init__(...)` + `Map.generate()` — the core generation pipeline
2. `Game.from_code(code)` — game lookup
3. All `*Settings` classes — the configuration API
4. Schema JSON files — texture/grle/tree/buildings customization

Everything else (method names, internal class hierarchy, intermediate file formats) can change freely.

---

## Step 4 — Design the New Architecture

**Goal:** Create a clean, minimal design before writing code.

See `REFACTOR_SUGGESTIONS.md` for the detailed analysis. The designed architecture must address:

- **In-memory context** replacing info-layer JSON files for inter-component communication
- **Single DEM processing chain** (no scattered intermediate files)
- **Game config as data** (not a class hierarchy with path methods) to support future games
- **I3D/XML wrapper** replacing raw ElementTree usage — a fluent `XmlDocument` class with `get()`, `require()`, `set_attrs()`, `append_child()`, `find_all()`, and context-manager `save()`. No component should ever call `ET.parse()`, `.getroot()`, `.find()`, `.findall()`, or `ET.SubElement()` directly. Game-config-driven patches are handled by `XmlPatch` + `apply_xml_patches()`; dynamic node insertion (splines, fields, trees, buildings) uses `XmlDocument` directly.
- **QGIS removal** (deprecated feature)
- **FS22 removal** (deprecated game)
- **Water pipeline clarification** (which files are actually used)
- **Component dependency graph** made explicit and documented

---

## Step 5 — Save All Design Decisions

**Goal:** Capture everything before touching code.

- Write `REFACTOR_SUGGESTIONS.md` with:
  - Current architecture diagram (component order, data flow)
  - Per-component analysis (what it does, what it writes, what it reads)
  - Proposed new structure (module layout, class responsibilities)
  - Specific changes per component
  - Files/features to remove
  - Async verdict
  - Schema/settings changes
- Review and discuss with stakeholders before proceeding

---

## Step 6 — Analyze and Reorganize Helper Code

**Goal:** Keep core generation logic short and readable; push helpers out.

- Audit `utils.py` — identify helpers that belong in a domain module vs. pure utilities
- Audit `config.py` — executable discovery, URL fetching, path constants
- Audit `monitor.py` — Logger, PerformanceMonitor (consider whether performance data is needed)
- Audit `statistics.py` — optional telemetry, should be clearly opt-in and non-blocking
- Move geometry helpers out of `component.py` base class (too many unrelated responsibilities)
- Target: `component.py` base should only handle lifecycle (`preprocess`, `process`, `info_sequence`, `previews`) and context access

---

## Step 7 — Consider Texture Component as a Separate Library

**Goal:** Evaluate extracting the OSM drawing logic.

The `Texture` component essentially does:
1. Fetch OSM features by tag queries
2. Convert geo coordinates to pixel space
3. Draw polygons and polylines onto images with configurable styles

This is purely OSM-to-image rendering. It has no fundamental dependency on FS25 or any game format. Candidates for extraction:
- `component/texture.py` (core drawing)
- `component/layer.py` (schema-driven layer model)
- The background texture sub-generation inside `background.py`

If extracted, the maps4fs generator would depend on this library and configure it via schemas.

**Decision criterion:** Extract if it simplifies maps4fs noticeably and if the extracted library is genuinely reusable outside FS25 map generation.

---

## Step 8 — Async Verdict

**Goal:** Decide definitively whether to make the library async.

Considerations:
- The pipeline is sequentially ordered (components depend on previous outputs)
- External I/O (OSM fetch, DTM download) uses blocking libraries under the hood
- `Map.generate()` is a generator — callers can yield control between components
- Adding async would require major refactoring of all component code and external library adapters
- No clear user-facing benefit: web UIs already run generation in a thread/worker

**Verdict:** Do not make the library async. The generator pattern already enables responsive UIs.

---

## Step 9 — Audit Generated Files vs. Files Actually Used by the Game

**Goal:** Remove any file generation that produces outputs which are never used.

Categories of generated files:
- **Used directly by FS25** — `dem.png`, `unprocessedHeightMap.png`, texture weight PNGs, GRLE PNGs, `map.xml`, `map.i3d`, `farmlands.xml`, `environment.xml`, `overview.dds`, splines i3d
- **Used as manual-use assets** — background terrain obj/i3d, water mesh obj/i3d (user imports into Giants Editor)
- **Intermediate files** — `not_resized.png`, `not_resized_with_foundations.png`, `not_resized_with_flattened_roads.png`, `water_resources.png`, STL previews
- **Legacy/unused** — `plane_water.obj`, `elevated_water.obj` (if the line-based water i3d already covers the use case)
- **Debug/info outputs** — `generation_info.json`, `generation_logs.json`, `performance_report.json`

For each generated file: either document it as required, or mark it for removal.

Water specifically:
- `line_based_water.obj` → `assets/water/water_resources.i3d` (ready-to-use; keep)
- `elevated_water.obj`, `plane_water.obj` — these polygon-based water files are not directly injected into FS25 map; evaluate removing them or keeping as optional manual-use meshes with clear documentation

---

## Step 10 — Handle overview.dds Correctly

**Note:** `overview.dds` is the in-game minimap texture. It is referenced by the map itself (in `map.xml`) and must be present. It is NOT just an extra file — it is required for the map to display correctly in FS25.

Ensure:
- The overview generation pipeline is documented as required
- The DDS conversion path (via `texconv.exe` on Windows) is clearly documented
- The `texconv` dependency is handled gracefully (warn if missing, don't crash)

---

## Step 11 — Remove FS22; Design for Future Games

**Goal:** Remove all FS22 code; ensure future games (e.g. FS28) can be added with data, not code.

### FS22 Removal
- Delete `FS22` class from `game.py`
- Delete `templates/fs22-map-template.zip`
- Delete `templates/fs22-texture-schema.json`
- Remove `FS22` from all test cases
- Update `__init__.py`, README, docs

### Future Game Support Design
Current `Game` class uses method overrides for every path (`dem_file_path`, `weights_dir_path`, etc.). For FS28, someone would have to:
- Subclass `Game`
- Override ~10 path methods
- Create new schema files

Better approach: make `Game` data-driven.
- Define a `GameConfig` dataclass with fields for all path templates:
  ```
  GameConfig(
      code="FS25",
      dem_path="map/data/dem.png",
      weights_dir="map/data",
      i3d_path="map/map.i3d",
      ...
      xml_patches=[...],  # XPath + value patches to apply
  )
  ```
- `Game` becomes a thin wrapper around `GameConfig`
- Adding FS28 = adding a `GameConfig` entry (possibly from a YAML/JSON file)
- The component code uses `game.config.dem_path` instead of `game.dem_file_path(map_directory)`

The FS25-specific i3d XPath patches (height scale, sun shadow, displacement layer, fog, etc.) should be moved from component code into the game config's `xml_patches` list.

---

## Step 12 — Write REFACTOR_SUGGESTIONS.md

**Goal:** Document all analysis and proposed changes before any code is touched.

`REFACTOR_SUGGESTIONS.md` must contain:
- Current module/class inventory
- Current data flow diagram (component order + what each reads/writes)
- Proposed module structure
- Proposed class responsibilities (simplified)  
- Specific changes for each component
- What gets removed (FS22, QGIS, redundant water files, etc.)
- What schemas change and how
- Settings model changes
- Test plan skeleton

**No code changes during this step.**

---

## Step 13 — STOP HERE

After `REFACTOR_SUGGESTIONS.md` is written, stop and review with the team before proceeding.

The next phases (actual code refactoring) will be planned after the suggestions are accepted.
