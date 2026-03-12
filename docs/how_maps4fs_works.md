# How Maps4FS Works

This page is a technical overview for developers integrating or extending Maps4FS.

It explains:
- core concepts,
- the generation pipeline,
- classes that are expected to be used as public API,
- important internal classes you may see while debugging.

## High-Level Mental Model

Maps4FS turns real-world geodata into a Farming Simulator 25 map template by running a fixed component pipeline.

At a high level:
1. You select a `Game` (FS25), map center coordinates, size, and generation settings.
2. A `Map` object prepares workspace state, input files, settings snapshots, and template files.
3. Components run in order (satellite, textures, DEM, water, background, GRLE, config, roads, scene, buildings).
4. Components exchange runtime data through `MapContext`.
5. Generated assets are written to the map directory and can be packed into a zip archive.

## Core Concepts

### 1. Game Definition

Game definitions provide game-specific paths, schema files, and XML/XPath config.

Primary classes:
- `maps4fs.Game`
- `maps4fs.FS25`
- `maps4fs.generator.game.GameConfig`

What this controls:
- where core files are stored (`map.i3d`, `map.xml`, farmlands/environment files),
- which schemas are used (texture/GRLE/tree/buildings),
- game-specific XML editing rules.

### 2. Map Session

`maps4fs.Map` is the orchestration object for one generation session.

It is responsible for:
- validating and storing inputs,
- preparing map directory and template,
- writing settings metadata files,
- running components in deterministic order,
- exposing utility operations (`previews()`, `pack()`, `self_clear()`).

### 3. Settings Models

Settings are strongly typed models used by API/UI layers and generation internals.

Primary classes:
- `maps4fs.GenerationSettings`
- `maps4fs.MainSettings`
- `maps4fs.settings.DEMSettings`
- `maps4fs.settings.BackgroundSettings`
- `maps4fs.settings.GRLESettings`
- `maps4fs.settings.I3DSettings`
- `maps4fs.settings.TextureSettings`
- `maps4fs.settings.SatelliteSettings`
- `maps4fs.settings.BuildingSettings`

Conceptually:
- `GenerationSettings` controls generation behavior.
- `MainSettings` captures run metadata (coordinates, game, provider, version, completion/error state).

### 4. Component Pipeline

Each generator step is implemented as a `Component` subclass.

Base class:
- `maps4fs.generator.component.base.Component`

A component generally:
1. reads source data and current context,
2. transforms or generates assets,
3. writes outputs,
4. publishes runtime values into `Map.context` for downstream components.

### 5. Runtime Data Exchange (MapContext)

`maps4fs.generator.context.MapContext` is the in-memory data contract between components.

Examples of shared data:
- extracted polygons/polylines (fields, roads, water, buildings),
- DEM/height scale values,
- water and satellite paths,
- mesh centroid positions used later by scene assembly.

Important: for internals, `MapContext` is the primary exchange mechanism during generation.

## Public API vs Internal API

Use these as stable integration entrypoints:
- `maps4fs.Game` / `maps4fs.Game.from_code(...)`
- `maps4fs.FS25`
- `maps4fs.Map`
- `maps4fs.GenerationSettings`
- `maps4fs.MainSettings`
- `maps4fs.settings.*`

Treat these as internal implementation details:
- `maps4fs.generator.component.*`
- `maps4fs.generator.osm_pipeline.*`
- most `maps4fs.generator.*` modules that are not re-exported from package root.

If you depend on internals, pin versions and re-test on every upgrade.

## End-to-End Flow (Practical)

Typical flow in wrappers/services:
1. Resolve game via `Game.from_code("FS25")`.
2. Build `GenerationSettings` from request payload.
3. Create `Map(...)` with game, provider, coordinates, size, rotation, and settings.
4. Iterate `Map.generate()` to execute pipeline and stream progress.
5. Call `Map.previews()` if preview assets are needed.
6. Call `Map.pack()` to produce distributable archive.

## Data Artifacts You Usually Consume

Most API services should consume only final artifacts:
- map files under generated `map/` directory,
- optional previews,
- packed archive from `Map.pack()`,
- run metadata in `main_settings.json` and `generation_settings.json`.

This keeps integrations resilient to internal refactors.

## Where to Look Next

- If you are upgrading from older versions: see [Migration to 3.0](migration_to_3_0.md).
- If you are integrating via Python package: see [Python Package Deployment](python_package_deployment.md).