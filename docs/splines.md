# Splines

## What Are Splines

Splines are **3D paths** that follow roads, tracks, and other linear features from your OpenStreetMap data. They're essential for AI vehicle navigation and can also be used for decorative purposes like fencing or pipeline routes.

**File Output**: Maps4FS creates a `splines.i3d` file containing all the extracted spline paths from your map area.

## Adding Splines to Your Map

### Import Process

1. **Open Giants Editor**: Load your map project
2. **Import Splines**: Go to **File** → **Import** and select `splines.i3d`
3. **Verify Import**: Splines should appear as 3D paths following your roads

### Positioning and Alignment

**Initial Position**: If your map has roads covering the full area, splines should be centered correctly. If roads only exist on part of your map, you'll need to adjust their position.

**Create a Group**: 
1. Select all imported splines
2. Right-click and choose **Create Group**
3. This lets you move all splines together

### Height Adjustment

**Z-Axis Alignment** (called Y-axis in Giants Editor):
- **Transform Y**: Move splines up or down to match terrain height
- **Scale Y**: Adjust vertical scale if splines appear too tall or short
- **Follow Terrain**: Ensure splines sit properly on roads and don't float or sink underground

## Using Splines for AI Traffic

### Setup for Auto-Drive

1. **Select All Splines**: Choose your spline group
2. **Create TransformGroup**: Group them if not already grouped
3. **Add AI Attribute**: 
   - Select the TransformGroup
   - Open **Attributes** panel → **User Attributes** tab
   - Add new attribute:
     - **Type**: Script callback
     - **Name**: `onCreate`
     - **Value**: `AISystem.onCreateAIRoadSpline`

![AI Spline Configuration](https://github.com/user-attachments/assets/7602f8ff-bcbe-4abc-b360-487f0b6a6d55)

**Result**: AI vehicles will use these splines for autonomous driving on roads.

## Common Issues and Solutions

### Misaligned Splines
**Problem**: Splines don't follow roads correctly  
**Solution**: Check your OpenStreetMap data quality and regenerate if needed

### Height Problems
**Problem**: Splines float above or sink below terrain  
**Solution**: Use Transform Y tool to adjust height, or Scale Y to fix vertical proportions

### Missing Splines
**Problem**: Some roads don't have splines  
**Solution**: Improve OSM road data coverage in your area before regeneration

## Spline Quality Tips

**OSM Data Quality**: Better road data in OpenStreetMap = better splines
**Road Types**: Major roads (highways, primary) typically generate more reliable splines than minor paths
**Map Edges**: Roads that cut off at map boundaries may need manual adjustment