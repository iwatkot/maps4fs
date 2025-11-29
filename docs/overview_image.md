# Overview Image Configuration

> 🎉 **NEW for FS25**: Overview images are now fully automated! When **Download Satellite Images** is enabled, Maps4FS automatically generates perfect `overview.dds` files - no manual editing required!

## Purpose: Creating Your In-Game Map Display

The overview image serves as the **in-game map display** that players see when opening the map interface in Farming Simulator. This essential visual element provides context and navigation reference for your entire map area.

## Image Structure & Specifications

### Fixed Dimensions
**Final Format**: Always `4096×4096 pixels` regardless of your actual map size  
**File Format**: `.dds` (DirectDraw Surface) for optimal game engine compatibility

### Layout Architecture

![Overview Image Structure](https://github.com/iwatkot/maps4fsui/releases/download/0.0.1/overview.png)

**Playable Area**: `2048×2048 pixels` centered within the overview image  
**Border Region**: Surrounding area outside the playable zone

**Critical Understanding**: The playable map area occupies only the center quarter of the overview image. The remaining space provides visual context and immersive boundaries.

## Content Options & Strategies

## Content Options & Strategies

### Option 1: Automated Satellite Integration (FS25) ⭐ **RECOMMENDED**
**Fully Automated for Farming Simulator 25**

When **Download Satellite Images** is enabled in Maps4FS:
- 🚀 **Completely Automatic**: `overview.dds` generated without any manual work
- 🎯 **Perfect Dimensions**: Automatically sized to 4096×4096 pixels
- 🛰️ **High-Quality Satellite Imagery**: Uses actual satellite data for photorealistic results
- ✅ **Game-Ready Format**: Pre-compressed to DDS with optimal settings
- 🔄 **Seamless Integration**: Perfect alignment with your generated terrain

**For FS22 or Custom Designs**: Manual satellite integration still available (see below)
- **Seamless Integration**: Perfect alignment with your generated terrain
- **Realistic Context**: Actual satellite imagery showing surrounding geographic features  
- **Professional Results**: Consistent visual quality matching your map's real-world location

### Option 2: Custom Creative Content
**For Advanced Customization**

**Border Region Freedom**: Place any visual content outside the map borders:
- **Artistic Elements**: Custom graphics, logos, or themed imagery
- **Extended Landscape**: Hand-drawn terrain continuing beyond playable boundaries
- **Atmospheric Effects**: Weather patterns, lighting effects, or seasonal themes
- **Narrative Elements**: Story-related imagery or regional character

**Design Flexibility**: The border area has no gameplay impact—use it for pure visual enhancement.

## Implementation Workflow

### Standard Process
1. **Generation**: Maps4FS creates `overview.png` automatically during map generation
2. **Review**: Examine the generated image for quality and coverage
3. **Conversion**: Transform the PNG to DDS format for game compatibility
4. **Integration**: Place the final `overview.dds` in your map's root directory

### Custom Enhancement Process
1. **Base Image**: Start with the generated `overview.png` (provides perfect scale and alignment)
2. **Edit Borders**: Modify only the outer regions, preserving the central playable area
3. **Maintain Resolution**: Keep the exact `4096×4096` pixel dimensions
4. **Convert Format**: Export as DDS with appropriate compression settings
5. **Test Integration**: Verify the image displays correctly in Giants Editor

## Technical Requirements

**Resolution**: Exactly `4096×4096 pixels` (non-negotiable)  
**Format**: DDS with DXT compression for optimal performance  
**Color Space**: RGB with optional alpha channel for transparency effects  
**File Size**: Typically 2-8MB depending on compression and detail level

## Best Practices

**Preserve Scale**: Never resize the central playable area—maintain its exact proportions  
**Quality Balance**: Use sufficient detail for clarity without creating oversized files  
**Visual Consistency**: Match the overview's visual style with your map's terrain and atmosphere  
**Performance Optimization**: Apply appropriate DDS compression to minimize loading times

**Strategic Tip**: The overview image significantly impacts players' first impression of your map. Invest time in creating a polished, professional result that showcases your map's unique character and geographic setting.

## Attribution Pack (Optional)

Want to show that your map was created with Maps4FS? We've prepared an **optional attribution pack** with graphics like "Created with Maps4FS" and "Powered by Maps4FS" that you can use on your map images, websites, or promotional materials.

**📦 Download**: [Attribution Pack](https://1drv.ms/u/c/a4f172ed55b8f7e1/IQDVdINs6vmMQYzXqabkL3w6AaF8ePwYx423W9e4RftVzFc?e=c5BgvK) - *Completely optional, not required*

These graphics are provided for users who want to credit the tool, but there's **no obligation** to use them. Use them if you'd like to show support or let others know how your map was created!
