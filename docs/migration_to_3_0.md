# Migration to 3.0

This page summarizes what changed in Maps4FS 3.0 and what to check if you integrate the library programmatically (for example in maps4fsapi).

## Support Policy Change

Starting from:
- **Maps4FS 3.0.0**
- **Maps4FS Windows 1.0.0**

Farming Simulator 22 support was removed. Maps4FS now targets FS25 only.

## What Stayed Stable

These areas were intentionally kept stable for integrators:
- Generation settings models and their core structure remain compatible.
- Core external classes/methods used by consumers remain available (for example `Game`, `Map`, `GenerationSettings`, `MainSettings`, and the main generation workflow).
- Typical public integration flow (create game, build map object, generate/pack) remains the same.

## Public API Surface (Reference)

When upgrading wrappers/services (for example maps4fsapi), treat these as the primary public surface:
- `maps4fs.Game` and `maps4fs.Game.from_code()`
- `maps4fs.FS25`
- `maps4fs.Map`
- `maps4fs.GenerationSettings`
- `maps4fs.MainSettings`
- `maps4fs.settings.*` models (`DEMSettings`, `BackgroundSettings`, `GRLESettings`, `I3DSettings`, `TextureSettings`, `SatelliteSettings`, `BuildingSettings`)

Everything under `maps4fs.generator.component.*` should be considered internal unless you intentionally maintain a deep integration.

## Breaking Changes (3.0)

### 1. FS22 support removed from runtime API

**Affected public classes/methods:**
- `Game.from_code(...)`
- game selection code in your API/UI
- direct imports/usages expecting `FS22`

**What changed:**
- Maps4FS 3.0 supports FS25 only.
- `Game.from_code("FS22")` no longer resolves and raises a `ValueError`.
- Public code paths should use `FS25` / `"FS25"` only.

**Upgrade action:**
- Remove FS22 values from request schemas, enum validators, and UI dropdowns.
- Replace fallback logic like `if game in ["FS22", "FS25"]` with FS25-only validation.

### 2. Internal cross-component JSON channel removed

**Affected classes/modules (for deep integrations):**
- `maps4fs.generator.component.base.Component.get_infolayer_data(...)`
- `maps4fs.generator.context.MapContext`

**What changed:**
- Legacy `info_layers/*.json` and `positions/*.json` exchange assumptions are no longer the runtime contract.
- Cross-component data is expected to be read from `map.context`.

**Upgrade action:**
- If your integration parsed intermediate JSON artifacts during generation, migrate to in-memory reads from `Map.context` fields.
- Keep using generated final outputs (`map/`, assets, packed archive) as the stable external artifact boundary.

### 3. Water/background mesh integration expects current asset keys

**Affected internal integration points:**
- scene/background/water coupling in custom adapters
- any code that matches mesh names/filenames

**Current keys/filenames to target:**
- `polygon_water` -> `polygon_water.obj`
- `polyline_water` -> `polyline_water.obj`

**Upgrade action:**
- Remove assumptions about legacy water mesh naming.
- If you post-process generated assets, key your logic to the current names above.

### 4. FS25 schema/template set is the supported baseline

**Affected classes/methods:**
- `FS25` (`texture_schema`, `grle_schema`, `tree_schema`, `buildings_schema`, `template_path`)
- custom template/schema selection logic in wrappers

**What changed:**
- Public game configuration resolves to FS25 schema/template files.
- Integrations should not expect FS22 template/schema compatibility in 3.x.

**Upgrade action:**
- Ensure your deployment bundles include FS25 schema/template assets only.
- Remove FS22 template selection branches.

## What Changed Internally

The following internal refactors are the most important for maintainers of wrappers and adapters:
- FS22-specific logic/assets were removed across generation and docs.
- Legacy QGIS scripts/workflows were removed.
- Cross-component JSON exchange artifacts were removed from runtime flow (for example old info-layer/positions intermediate JSON channels).
- In-memory runtime context became the primary cross-component exchange mechanism.
- Water/background generation pipeline was simplified and unified around current mesh/assets flow.
- Internal component orchestration and helper boundaries were refactored for maintainability and stricter typing/linting.

## If You Use Internal APIs

If your project imports internal modules (anything beyond documented public entrypoints), review:
- component internals and private helper methods,
- context field names/types used between components,
- assumptions about temporary/intermediate files,
- assumptions about legacy FS22 branches.

## Affected Classes: Quick Upgrade Notes

### `Game`
- Keep using `Game.from_code("FS25")`.
- Treat any non-FS25 game code as invalid input at your API boundary.

### `FS25`
- Use as the explicit supported game definition when you do not need dynamic lookup.
- Its paths/schemas are now the canonical game config for 3.x.

### `Map`
- Constructor and generation workflow remain stable for standard usage.
- If your code inspects intermediate files during generation, re-validate those assumptions against context-driven internals.

### `GenerationSettings` and `settings.*`
- Model structure stays compatible for normal integrations.
- Keep your JSON payload keys aligned with the existing model names/fields.

### `MainSettings`
- Continue using `MainSettings`/`main_settings.json` as your run metadata contract.
- Re-check any game-related validation in consumers to enforce FS25-only values.

## API Wrapper Migration Template

Use this as a practical checklist when updating a service layer:

1. Restrict incoming `game` to `FS25`.
2. Remove FS22-specific branching in handlers/services.
3. Update tests to assert `Game.from_code("FS22")` is rejected.
4. Verify generation endpoints still follow: create `Game` -> create `Map` -> iterate `generate()` -> `pack()`.
5. If you used internal component data, migrate from intermediate JSON parsing to `Map.context` usage.
6. Re-run end-to-end generation tests for at least one custom OSM and one default OSM flow.

## Quick Checklist for API Maintainers

Use this checklist when upgrading an API service that depends on maps4fs:

1. Verify you do not expose FS22 options in your API/UI.
2. Remove references to legacy QGIS/manual FS22 processing paths.
3. Validate any direct imports from `maps4fs.generator.component.*` internals.
4. Re-check data contracts if you previously parsed intermediate JSON artifacts.
5. Re-run integration tests for generation, previews, and packaging.
6. Confirm your deployment docs and examples now describe FS25-only behavior.

## Notes

For full usage and installation details, see [Python Package Deployment](python_package_deployment.md).
