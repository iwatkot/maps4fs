# Custom OSM Data

Custom OSM functionality allows you to use your own OpenStreetMap data instead of downloading from public OSM servers. This gives you complete control over map features, road networks, and geographic elements without community approval or modification restrictions.

## Why Use Custom OSM?

- **Complete Creative Control** - Add, modify, or remove any map features
- **No Community Restrictions** - No need to follow OSM community guidelines
- **Rapid Iteration** - Test different layouts and features quickly
- **Fictional Content** - Create maps that don't exist in the real world
- **Enhanced Detail** - Add specific features not present in public OSM data

## Methods for Using Custom OSM

### Method 1: Drag & Drop in UI (Recommended for Single Use)
The simplest approach for one-time map generation:

1. **Create your custom OSM file** (see creation guide below)
2. **Open Maps4FS interface**
3. **Drag and drop** your `.osm` file directly into the file upload area
4. **Generate your map** - the custom data will be used for this generation

**Best For**: Testing, single map projects, quick iterations

### Method 2: Data Directory Defaults (Recommended for Repeated Use)
For consistent use across multiple generations:

1. **Create your custom OSM file** (see creation guide below)
2. **Place file in Data Directory**: `defaults/osm/custom_osm.osm`
3. **File naming**: Must be exactly `custom_osm.osm`
4. **Generate maps** - all future generations will use this default data

**Best For**: Multiple maps from same region, consistent workflow, batch processing

**Data Directory Structure**:
```
📁 Data Directory/
└── 📂 defaults/
    └── 📂 osm/
        └── 📄 custom_osm.osm  ← Your custom OSM file here
```

## Creating Custom OSM Files

📹 **Video Tutorial**: Watch the complete creation process step-by-step.

<a href="https://www.youtube.com/watch?v=duTXvkIiECY" target="_blank"><img src="https://github.com/user-attachments/assets/8e130247-57f2-4d0a-9a9a-a13fa847c0d8"/></a>

### Step-by-Step Creation Process

1. **Download JOSM Editor** from the [official website](https://josm.openstreetmap.de/) or [Windows Store](https://apps.microsoft.com/detail/xpfcg1gv0wwgzx)

2. **Create New Layer** (Ctrl + N)

3. **Add Background Imagery** (Ctrl + Shift + N) - Choose any provider (Bing, Google, etc.)

![Add imagery](https://github.com/user-attachments/assets/8b6f0a68-821f-42d4-aff7-fda56485c175)

4. **Download OSM Data**: **File** → **Download data** (Ctrl + Shift + Down)

![Download OSM data](https://github.com/user-attachments/assets/35b78426-73f8-4332-94dc-952510e025f1)

5. **Select Your Region**: Draw area covering your region of interest, then click **Download**
   - **Tip**: If you get "Download area too large" error, download in smaller sections

![Draw the area](https://github.com/user-attachments/assets/ba033f1a-adcb-4215-9852-4f01dfe1e4ef)

6. **Remove Relations** (Required): Go to **Relations** tab, select all, and delete them
   - **Why**: Relations cause compatibility issues with Maps4FS processing
   - **Note**: Some areas may disappear - add them back manually if needed

![Remove relations](https://github.com/user-attachments/assets/65e1ef68-fdc2-4117-8032-2429cbaeb574)

7. **Edit Your Map**: Add, modify, or remove features as desired
   - No community approval needed
   - Complete creative freedom

8. **Proper Deletion Method**: Use **Purge** instead of **Delete**
   - **Enable Expert Mode** first in settings
   - **Why**: Simple deletion creates broken OSM files

![Enable expert mode](https://github.com/user-attachments/assets/eaee73df-76bb-48db-be6b-d4ddb7c5ea7c)

![Purge object](https://github.com/user-attachments/assets/75c90888-cf6d-437b-906f-89b029350044)

9. **Save Your File**: **File** → **Save as** (Ctrl + Shift + S)
   - Choose `.osm` format
   - Save with descriptive filename

### Post-Creation Steps

**For UI Drag & Drop**:
- File is ready to use immediately
- Drag into Maps4FS interface when generating

**For Data Directory Method**:
- Rename file to `custom_osm.osm` 
- Place in `defaults/osm/` folder
- All future generations use this data automatically

## File Management Best Practices

### **Version Control**
- **Backup original files** before major edits
- **Use descriptive filenames** during development
- **Consider Git** for tracking complex changes
- **Document modifications** for future reference

### **Testing Strategy**
- **Start small** - test with limited area first
- **Validate data** - ensure no broken elements
- **Generate test maps** before large projects
- **Iterate gradually** - make incremental improvements

## Troubleshooting

If your custom OSM file isn't working, throws errors, or generates a blank map, follow this diagnostic approach:

### Common Fix: Remove Delete Actions

1. **Open your OSM file** in any text editor
2. **Search for** `action='delete'` throughout the file
3. **Delete all XML elements** containing the `action='delete'` attribute
4. **Save the file** and try regenerating your map

### Root Causes and Solutions

**Problem: Deleting Elements in JOSM**
- **Issue**: Using standard **Delete** function creates broken references
- **Solution**: Always use **Purge** instead to completely remove elements
- **How**: Enable Expert Mode → Right-click → **Purge** (not Delete)

**Problem: Combining Ways**
- **Issue**: Using **Combine Way** (Ctrl+C) creates problematic merge artifacts  
- **Solution**: Manual cleanup required - locate and remove marked elements from OSM file
- **Prevention**: Avoid combining ways when possible, or prepare for manual fixes
