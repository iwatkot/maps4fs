# Optimizing Your Maps4FS Workflow

Maps4FS revolutionizes map creation by automating tedious, time-consuming tasks so you can focus on what truly matters: creating engaging, high-quality content. The key to maximizing efficiency lies in understanding the distinction between **automated assets** and **custom assets**.

**Automated Assets**: Elements generated automatically by Maps4FS (terrain, roads, fields, basic structures) that require zero manual effort to create.

**Custom Assets**: Hand-crafted elements that add unique value and character to your map, requiring significant time investment.

**Golden Rule**: Never invest time in manual work until you're completely satisfied with the automated generation results. This simple principle can save you dozens of hours of wasted effort.

## Essential Preparation

### Optimizing OpenStreetMap Data

Your map's quality is fundamentally limited by the underlying OpenStreetMap (OSM) data quality. If your target region has incomplete or inaccurate OSM data, address this **before** beginning generation.

**Critical Recommendation**: Use the [custom OSM approach](008_customosm.md) rather than relying on public OSM data. This gives you complete control over your data without navigating OSM's community guidelines and approval processes. You can iterate freely, make region-specific adjustments, and maintain consistency across multiple generation cycles.

### Preserving Generation Parameters

Expect to generate your map multiple times before achieving optimal results. To ensure consistency and avoid configuration drift:

**Always save your `generation_info.json` file** after each satisfactory generation. This file contains all parameters needed to reproduce identical results, enabling you to:
- Maintain exact positioning, size, and rotation across iterations
- Preserve compatibility with existing custom assets when regenerating specific components
- Quickly revert to previous successful configurations

Learn more in the [Generation Info documentation](https://github.com/iwatkot/maps4fs?tab=readme-ov-file#generation-info).

## Phase 1: Automated Asset Validation

Once your OSM data meets your standards, begin the iterative generation process. This phase focuses exclusively on automated elements—resist any temptation to manually adjust content.

**Recommended Workflow:**

1. **Generate** → Load the map in Giants Editor
2. **Evaluate** → Assess automated elements: roads, fields, farmlands, terrain topology
3. **Resist Manual Edits** → No matter how minor the issue appears, avoid manual fixes
4. **Iterate Ruthlessly** → If results are unsatisfactory, delete everything except `generation_info.json` and regenerate
5. **Repeat** → Continue until automated assets meet your quality standards

**Why This Matters**: Every minute spent manually adjusting automated assets is wasted effort. These elements will be overwritten in your next generation cycle, destroying your manual work.

## Phase 2: Custom Asset Development

**Only proceed to this phase when automated assets are production-ready.** Your time investment begins here.

**Pre-Development Checklist:**
- ✅ Automated terrain topology is acceptable
- ✅ Road networks are properly positioned and connected
- ✅ Field boundaries and farmland divisions are logical
- ✅ Background terrain and water meshes render correctly
- ✅ Satellite imagery alignment is accurate
- ✅ Everything seems to be in its place

**Final Validation**: Before investing significant time in custom assets, perform one last comprehensive review of all automated elements. If you discover issues now, return to Phase 1—it's still cost-free to regenerate.

**Time Investment Begins**: Once you're confident in the automated foundation, you can begin creating custom buildings, decorative elements, unique landmarks, and other hand-crafted content that will differentiate your map.

Remember: Custom assets built on a solid automated foundation retain their value across minor regenerations, maximizing your return on time investment.
