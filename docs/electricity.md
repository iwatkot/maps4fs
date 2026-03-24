# Electricity: Powerlines and Lights

## Overview

Maps4FS electricity generation has two responsibilities:

1. Place electricity-related assets from OSM points (`power=pole`, `power=tower`, `highway=street_lamp`, `man_made=street_lamp`).
2. Build wire meshes for powerline networks from OSM lines (`power=minor_line`, `power=line`).

The system is schema-driven and uses two files together:

- `templates/fs25-texture-schema.json`
- `templates/fs25-electricity-schema.json`

## How the Pipeline Works

1. **Texture schema** matches OSM features and writes info-layer records.
2. **Electricity component** reads those records from map context.
3. Point records are mapped to categories, then to assets from electricity schema.
4. Assets are placed into `map.i3d` as `ReferenceNode` entries.
5. For wire-capable poles, line records are converted to connector-to-connector wires.
6. A combined wire network mesh is generated and referenced from `map.i3d`.

Lights are point assets only and do not generate wire meshes.

## Texture Schema: Electricity Entries

Electricity entries in texture schema are pseudo layers. They are typically `external: true` and `invisible: true`, used to collect OSM geometry into info layers.

### Typical Line Entries

Use these for OSM powerline ways:

```json
{
  "name": "PS_electricity_lines",
  "external": true,
  "invisible": true,
  "tags": { "power": ["minor_line"] },
  "info_layer": "electricity_lines",
  "electricity_category": "minor_line",
  "electricity_radius": 0.01,
  "save_tags": true
}
```

```json
{
  "name": "PS_electricity_lines_major",
  "external": true,
  "invisible": true,
  "tags": { "power": ["line"] },
  "info_layer": "electricity_lines",
  "electricity_category": "line",
  "electricity_radius": 0.05,
  "save_tags": true
}
```

`electricity_radius` controls wire cylinder thickness.

### Typical Point Entries

Use these for poles, towers, and street lights:

```json
{
  "name": "PS_electricity_poles",
  "external": true,
  "invisible": true,
  "tags": { "power": ["pole"] },
  "info_layer": "electricity_poles",
  "electricity_category": "default",
  "save_tags": true
}
```

```json
{
  "name": "PS_electricity_towers",
  "external": true,
  "invisible": true,
  "tags": { "power": ["tower"] },
  "info_layer": "electricity_poles",
  "electricity_category": "tower",
  "save_tags": true
}
```

```json
{
  "name": "PS_road_lights",
  "external": true,
  "invisible": true,
  "tags": { "highway": ["street_lamp"] },
  "info_layer": "electricity_poles",
  "electricity_category": "road_light",
  "save_tags": true
}
```

```json
{
  "name": "PS_residential_lights",
  "external": true,
  "invisible": true,
  "tags": { "man_made": ["street_lamp"] },
  "info_layer": "electricity_poles",
  "electricity_category": "residential_light",
  "save_tags": true
}
```

## Electricity Schema: Field Reference

Each entry in `fs25-electricity-schema.json` defines one placeable asset profile.

### Required fields

- `file` (string): Asset path used in i3d `File` entry.
- `name` (string): Base name used for placed nodes.
- `categories` (array of strings): Category match targets from texture schema (`electricity_category`).

### Common optional fields

- `type` (string): Logical role.
  - `pole`, `tower`: wire-capable if connectors are present.
  - `light`: light-only placement, excluded from wire topology.
- `rotation_offset_degrees` (number): Rotation offset used for connector orientation.
- `visual_rotation_offset_degrees` (number): Optional separate visual offset.
- `connectors` (array): Connector points for wire generation.
  - `side` (number): Horizontal offset in local pole right-axis.
  - `height` (number): Vertical offset above ground.
- `align_to_road` (bool): If true (typically lights), initial yaw faces nearest road.
- `align_to_road_max_distance` (number): Optional max distance to road for alignment.
  - If nearest road is farther than this, default yaw is kept.
- `template_file` (string): Source i3d to copy into map package before use.

## Connectors Deep Dive

Connectors are the most important part of wire generation. They define where each wire attaches on a pole/tower asset.

If connector values are wrong, wires may look too high/low, offset from insulators, crossed, or attached to empty space.

### What a connector is

A connector is one attachment point in pole-local coordinates:

```json
{
  "side": 0.8,
  "height": 10.2
}
```

- `side`: left/right offset from pole center on the local right axis.
- `height`: vertical offset above ground for wire attachment.

The system transforms these local offsets into world space using the pole's resolved yaw.

### Coordinate interpretation

For a placed pole:

- Pole center in world space: `(x_world, y_ground, z_world)`
- Connector world position:

  - `x = x_world + side * right_x`
  - `y = y_ground + height`
  - `z = z_world + side * right_z`

Where `(right_x, right_z)` is the pole-local right direction derived from pole yaw.

Practical meaning:

- Positive `side` puts connector on one side of the pole.
- Negative `side` mirrors it to the opposite side.
- Larger absolute `side` moves wires farther from center.
- Larger `height` moves wires higher.

### Field-by-field detail

`connectors` (array of objects)

- Purpose: list of wire attachment points for one asset profile.
- Order: important. Matching tries to preserve non-crossing pairs between neighbor poles.
- Minimum: for visible wires, use at least 2 connectors for typical distribution lines.

Connector object fields:

- `side` (number)
  - Unit: meters in asset/local pole scale.
  - Typical values:
    - small poles: `0.5` to `1.5`
    - large towers: `3.0` to `8.0`
  - Use symmetric pairs for balanced left/right lines: `+a`, `-a`.

- `height` (number)
  - Unit: meters above sampled terrain height at pole point.
  - Typical values:
    - distribution poles: `8` to `14`
    - high-voltage towers: `30`+
  - Use grouped heights for multi-level crossarms.

### Recommended patterns

#### 2-wire symmetric pattern (basic)

```json
"connectors": [
  { "side": 0.8, "height": 10.2 },
  { "side": -0.8, "height": 10.2 }
]
```

Use for simple medium-voltage style visuals.

#### 3-wire horizontal pattern

```json
"connectors": [
  { "side": 1.2, "height": 10.5 },
  { "side": 0.0, "height": 10.7 },
  { "side": -1.2, "height": 10.5 }
]
```

Use when center conductor is slightly higher.

#### Multi-level tower pattern

```json
"connectors": [
  { "side": 5.5, "height": 52.0 },
  { "side": -5.5, "height": 52.0 },
  { "side": 3.9, "height": 56.0 },
  { "side": -3.9, "height": 56.0 }
]
```

Use for high-voltage towers with separated circuits.

### How connector matching works between poles

For each linked pole pair:

1. Connector world positions are computed on both poles.
2. Connectors are ordered by projection on the pair right-axis.
3. Normal and reversed pairings are compared.
4. Lower total pairing cost is selected to reduce crossing.

This means connector ordering and side symmetry strongly influence visual quality.

### Tuning workflow (practical)

1. Start with symmetric two-connector setup.
2. Validate in Giants Editor using short and long spans.
3. Adjust `height` first (attachment realism).
4. Adjust `side` second (spacing and non-overlap).
5. Add extra connectors only after base pair looks correct.
6. If orientation seems wrong, adjust `rotation_offset_degrees` (not connectors).

### Common mistakes and fixes

- Wires too close to pole center:
  - Increase absolute `side`.

- Wires floating above insulators:
  - Decrease `height`.

- Wires clipping crossarm:
  - Increase `height` slightly and/or adjust `side`.

- Frequent crossing between neighbor poles:
  - Use symmetric `+side/-side` values and consistent heights.
  - Keep connector count consistent for all assets in the same category.

- Light assets unexpectedly creating wires:
  - Set `type` to `light` and omit connectors.

### Notes on wires

- Wires are created only from line records and wire-capable poles/towers.
- Light entries (`type: "light"`) are intentionally excluded from wire linking.

## Built-in Assets vs Custom Assets

### Built-in game assets (`$data/...`)

When `file` starts with `$data/...`, Maps4FS references game-provided assets directly. No copying is needed.

Examples:

- `$data/maps/mapAS/textures/props/highVoltageLinePole.i3d`
- `$data/placeables/mapEU/brandless/lightsResidential/streetLight01/streetLight01.i3d`
- `$data/placeables/brandless/lightsResidential/lightPole01/lightPole01.i3d`

### Custom assets (copied into map package)

Use this pattern when shipping custom i3d assets with your map:

```json
{
  "file": "assets/electricity/electricPolesSet.i3d",
  "template_file": "templates/shared/electricity/electricPolesSet.i3d",
  "name": "electricPolesSet",
  "categories": ["default"]
}
```

Behavior:

1. `template_file` is resolved from common roots (map dir, mod root, schema-relative paths).
2. Source i3d is copied to `file` path under mod root.
3. If a companion `.i3d.shapes` exists, it is copied too.
4. `map.i3d` stores the reference as a relative path from `map/map.i3d` directory.

## Path and Reference Rules

- Prefer forward slashes in schema paths.
- For custom assets, keep `file` under your mod package (for example `assets/electricity/...`).
- `map.i3d` references are written relative to `map/map.i3d`.
- `$data/...` paths should point to valid FS25 game files.

## Road-Facing Lights

For light entries:

- Set `type` to `light`.
- Set `align_to_road` to `true`.
- Optionally set `align_to_road_max_distance`.

Example:

```json
{
  "file": "$data/placeables/mapEU/brandless/lightsResidential/streetLight01/streetLight01.i3d",
  "name": "streetLight01",
  "type": "light",
  "rotation_offset_degrees": 90,
  "align_to_road": true,
  "align_to_road_max_distance": 96,
  "categories": ["road_light"]
}
```

Alignment behavior:

- Nearest point on fitted road segments is found.
- Light yaw is aimed toward that road point.
- Threshold is applied if `align_to_road_max_distance` is set.

If a light faces backward, tune `rotation_offset_degrees` by +90, -90, or 180 depending on the asset's local forward axis.

## Minimal End-to-End Setup Checklist

1. Add electricity point and line pseudo layers in texture schema.
2. Ensure categories in texture schema and electricity schema match.
3. Add wire-capable entries (`connectors`) for poles/towers.
4. Add light entries with `type: "light"` and optional road alignment fields.
5. Generate map and verify references in `map/map.i3d`.

## Troubleshooting

### No poles or lights appear

- Confirm point pseudo layers write into `info_layer: "electricity_poles"`.
- Ensure category names match between schemas.
- Ensure `file` path is valid.

### Wires do not appear

- Confirm line pseudo layers write into `info_layer: "electricity_lines"`.
- Confirm wire-capable entries have valid `connectors`.
- Confirm OSM includes matching `power=line`/`power=minor_line` ways.

### Light points get wires

- Ensure light entries use `type: "light"`.

### Lights do not face roads

- Ensure roads exist in texture schema and produce `roads_polylines` context.
- Enable `align_to_road`.
- Increase `align_to_road_max_distance` if roads are sparse.
- Tune `rotation_offset_degrees` for local model orientation.

## Related Docs

- [Texture Schema](texture_schema.md)
- [Textures](textures.md)
- [Roads](roads.md)
- [How Maps4FS Works](how_maps4fs_works.md)
