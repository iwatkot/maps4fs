# My Maps

My Maps transforms Maps4FS from a simple map generator into a complete map development workbench. Instead of generating maps and forgetting about them, you build a personal library where every map becomes a foundation for future projects.

## **📍 Local Deployment Only**

My Maps is exclusively available in local deployments. For setup instructions, see [Local Deployment Guide](local_deployment.md) and [Data Directory Overview](data_directory.md).

![My Maps Interface](https://github.com/iwatkot/maps4fsui/releases/download/2.6.0.1/screenshot-localhost-3000-1757595594033.png)

## **Why My Maps Changes Everything**

### **The Problem with Traditional Workflow**
Without My Maps, creating farming simulator maps follows this frustrating pattern:
1. Generate a map with specific settings
2. Discover it needs adjustments
3. Try to remember what settings you used
4. Re-enter everything manually
5. Generate again, hoping for better results
6. Repeat endlessly

### **The My Maps Solution**
My Maps breaks this cycle by turning every generation into a reusable template. When you find settings that work, they become permanent assets. When you need variations, you duplicate successful maps and adjust from there.

## **How It Actually Works**

### **Your Personal Map Library**
Every map you generate automatically appears in My Maps with complete information preserved. You see coordinates, size, rotation, game version, and creation date. More importantly, visual badges instantly show what each map contains - satellite imagery, background terrain, custom data, fields, forests, and water systems.

### **The Power of Duplication**
Here's where My Maps shines: the duplicate feature reads every setting from an existing map and loads them into the generator. This includes custom OSM files, custom elevation data, and all generation parameters. Click duplicate, make your adjustments, and generate - you're building on proven foundations instead of starting from scratch.

### **Visual Organization at Scale**
As your library grows, smart filtering keeps everything manageable. Search by name or coordinates to find specific locations. Filter by badges to show only maps with satellite imagery or background terrain. The interface handles hundreds of maps without slowing down your workflow.

## **Real-World Use Cases**

### **Iterative Map Development**
Start with basic settings for a new location. Generate, review, then duplicate and enhance. Maybe add satellite imagery to the second version, background terrain to the third. Each iteration builds on the previous success while preserving what works.

### **Client Work Management**
Map creators working for others can maintain separate projects easily. Generate variations for client review, keep successful configurations as templates, and duplicate proven settings for similar projects.

### **Learning and Experimentation**
New to Maps4FS? Generate maps with different settings and compare results side-by-side. The visual previews and detailed generation info help you understand how each parameter affects the final output.

## **Essential Features Explained**

### **🏷️ Smart Badges System**
Those colorful little icons aren't just pretty decorations - they're your visual workflow accelerators! Each map displays instant-recognition badges showing exactly what's inside:

| Badge | Feature | Why It Matters |
|-------|---------|----------------|
| 🛰️ | **Satellite Images** | High-resolution realistic textures |
| 🌐 | **Background Terrain** | 3D surrounding landscape for immersion |
| 🗺️ | **Custom OSM** | Personalized road/building data |
| 🌾 | **Fields** | Farmable areas ready for agriculture |
| 🌲 | **Forests** | Natural tree coverage and ecosystems |
| 🌊 | **Water** | Rivers, lakes, and water systems |
| 🛣️ | **Flattened Roads** | Smooth terrain under road networks |
| ✨ | **Dissolved** | Enhanced texture blending (less noisy) |

**🎯 Pro Tip:** Use these badges as filters! Need maps with stunning satellite textures for a showcase project? Filter by 🛰️. Want smooth road networks for realistic driving? Look for 🛣️ flattened roads. Need polished textures? Check for ✨ dissolved maps. It's like having a smart filing system that actually makes sense!

### **Complete Data Preservation**
My Maps stores everything in your Data Directory's mounted storage using this structure:

```
📁 Data Directory/
└── 📂 maps/
    ├── 📂 map_name_1/
    │   ├── 📄 generation_settings.json
    │   ├── 📄 generation_info.json
    │   ├── 📄 custom_data.osm (if used)
    │   ├── 📄 custom_dem.tif (if used)
    │   └── 📂 previews/
    └── 📂 map_name_2/
        └── ...
```

🆕 **Presets Integration**: My Maps now integrates with the [Presets](presets.md) system, allowing you to copy successful configurations from generated maps directly into your presets library for reuse.

This means maps survive container updates, restarts, and system changes. Your library becomes a permanent asset that grows more valuable over time.

### **🖼️ Professional Preview System**
Before downloading or duplicating, get a complete visual understanding of what each map contains. It's like having X-ray vision for your maps! 👀

**📸 Visual Feast:**
| Preview Type | What You See | Why It's Awesome |
|--------------|--------------|------------------|
| 🛰️ **Satellite Overview** | Bird's-eye real-world view | See actual terrain and landscape |
| 🗺️ **Layer Previews** | Individual feature visualization | Fields, forests, water separately |
| 📐 **Height Map** | 3D terrain visualization | Understand elevation and topology |
| 🎮 **Interactive 3D** | Rotatable mesh models | Inspect from every angle |
| 🌍 **Background Preview** | Surrounding landscape | See the bigger picture |

**🎯 Make Smart Decisions:** No more gambling with downloads! See exactly what you're getting before committing. Compare different versions side-by-side to pick the perfect foundation for your next project. It's like test-driving maps before you take them home! 🚗✨

### **🔍 Advanced Search and Filtering**
As your map library grows (and trust us, it will! 📈), these powerful search tools keep everything beautifully organized:

**🔤 Search Like a Pro:**
| Search Type | Perfect For | Example |
|-------------|-------------|---------|
| 📝 **Name Search** | Finding specific projects | "Client_Farm_Final" |
| 📍 **Coordinate Search** | Location-based lookup | "45.2866, -98.2315" |

**🎛️ Filter by Content Magic:**
- 🛰️ **Show only satellite imagery** → Perfect for high-quality presentation projects
- 🌐 **Find background terrain maps** → Ideal for immersive landscape work  
- 🗺️ **Locate custom data maps** → When you need that special OSM/DEM touch
- 🌾🌲🌊 **Filter by features** → Fields for farming, forests for aesthetics, water for realism

**💡 Smart Workflow:** Start broad with badge filters, then narrow down with name or coordinate search. It's like having a librarian who actually knows where everything is! 📚

## **Complete Action Reference**

### **📥 Download**
Get the complete map package ready for Giants Editor:
- All generated files in organized structure
- Textures, height maps, and configuration files included
- Original quality and settings preserved
- Direct import capability into Giants Editor

### **� Duplicate (Pre-fill Generator)**
**The game-changing feature that makes My Maps indispensable:**

Here's what makes duplication so powerful - it's not copying the map itself. Instead, it reads every single setting from your selected map and instantly pre-fills the Map Generator interface. Custom OSM file? Loaded. Custom DEM data? Ready to go. Every parameter, every checkbox, every slider - exactly as they were when that successful map was created.

**The Magic Workflow:**
1. 🎯 **Select any map** from your library that's close to what you want
2. ✨ **Click duplicate** - ALL settings instantly appear in the generator
3. 🎛️ **Adjust what you need** - maybe increase size, add satellite imagery, or tweak terrain
4. 🚀 **Generate immediately** - you're building on proven foundations, not starting from scratch

**What Gets Pre-filled:**
| Setting Category | What's Transferred |
|-----------------|-------------------|
| 📍 **Location** | Exact coordinates, map size, rotation |
| 🗺️ **Custom Data** | OSM files, DEM files automatically loaded |
| 🌍 **Terrain** | Elevation settings, water depth, foundations |
| 🌲 **Vegetation** | Tree density, forest species, grass types |
| 🌾 **Agriculture** | Field parameters, farmland margins, padding |
| 🎨 **Visual** | Texture resolution, satellite imagery options |

This transforms the painful "what settings did I use?" problem into "click and adjust." **No more guessing, no more starting over** - just intelligent iteration on what already works.

### **📊 Detailed Information Access**
Click any map to view comprehensive details:

**Generation Settings** - Every parameter used for creation including:
- Map size, rotation, and coordinate settings
- Terrain options (elevation, water depth, foundations)
- Vegetation settings (tree density, grass types, forest species)
- Field parameters (size, padding, farmland margins)
- Visual quality options (texture resolution, satellite imagery)

**Generation Info** - Performance and technical data:
- Processing time and performance metrics
- Data sources used (elevation providers, satellite sources)
- Field count, forest coverage, water area percentages
- File sizes and technical specifications
- Success/error status with detailed logs

### **🗑️ Delete**
Permanent removal with safeguards:
- Complete map deletion from library
- Confirmation dialog prevents accidental deletion
- Frees up Data Directory storage space
- Irreversible action - no recovery after deletion

### **📋 Map Library Display**
Each map shows essential information at a glance:
- **Coordinates** - Exact geographic location
- **Map Size** - Dimensions in meters (e.g., 3252m)
- **Output Size** - Final resolution (e.g., 2048px)
- **Rotation** - Applied rotation angle in degrees
- **Game Version** - Farming Simulator 22 or 25
- **Creation Date** - When the map was generated
- **Status Indicators** - Success/error states with details

## **Getting Started with My Maps**

### **Step 1: Generate Your First Maps**
Create a few maps with different settings to populate your library. Don't worry about perfection - you're building a foundation for future improvements.

### **Step 2: Use Badges for Organization**
Pay attention to the badges that appear on each map. They'll help you understand what different settings produce and find maps quickly later.

### **Step 3: Master the Duplicate Workflow**
When you find a map that's close to what you need, duplicate it instead of starting over. This single feature will save hours of repetitive configuration.

### **Step 4: Develop Your Library Strategy**
As your collection grows, develop naming conventions and organization strategies. Consider how you'll find maps months later when working on similar projects.

## **⚙️ Technical Considerations**

### **💾 Storage Reality Check**
Let's talk numbers! 📊 Maps with satellite imagery and background terrain are **gorgeous** but they're also storage-hungry beasts. A single high-quality map can easily consume 2-5 GB. That beautiful 4K satellite texture? Worth every byte, but plan accordingly!

**📈 Performance Sweet Spots:**
| Library Size | Loading Time | Performance | Recommendation |
|--------------|--------------|-------------|----------------|
| 🟢 **< 50 maps** | Lightning fast | Excellent | Perfect workflow |
| 🟡 **50-200 maps** | Quick | Great | Monitor storage |
| 🟠 **200+ maps** | Moderate | Good | Consider archiving |

### **🔧 System Performance**
- **🚀 Large libraries** may add a few seconds to interface loading (still totally worth it!)
- **⚡ Preview generation** happens during map creation - no waiting later
- **🔍 Search and filtering** stay snappy even with hundreds of maps
- **🎯 Background processing** never blocks your map generation workflow

### **🏠 Data Directory Magic**
My Maps leverages the mounted directory system like a boss! 💪

**✨ What This Means for You:**
- 🔄 **Auto-discovery** - New maps appear instantly after generation
- ⚡ **Real-time updates** - Changes show up immediately  
- 🛡️ **Update-proof** - Your library survives all Maps4FS container updates
- 💾 **Backup-friendly** - Standard file structure = easy backup/restore
- 🎛️ **Zero configuration** - Default setup is already optimized perfectly

**🔮 Future-Proof Design:**
Your investment in building a map library pays dividends! Updates enhance capabilities while keeping everything you've built. It's like having a map collection that gets better with age! 🍷

## **Best Practices for My Maps**

### **Organization Strategy**
Develop systems that scale with your growing library:
- **Descriptive naming** - Use clear, memorable map names that indicate location and purpose
- **Project grouping** - Consider naming conventions for related maps (e.g., "ClientName_Location_v1")
- **Badge utilization** - Leverage filters to organize by content type and features
- **Regular cleanup** - Remove experimental maps that didn't meet expectations

### **Experimentation Workflow**
Transform trial-and-error into systematic improvement:
1. **Generate conservative baseline** - Start with proven settings for new locations
2. **Use duplicate for variations** - Create enhanced versions rather than starting over
3. **Compare systematically** - Use preview system to evaluate different approaches
4. **Document successful patterns** - Keep maps that work well as templates for similar terrain
5. **Archive completed projects** - Move finished maps to external storage to manage space

### **Storage Management Strategy**
- **Monitor disk usage** - Large maps with background terrain consume significant storage
- **Selective retention** - Keep successful maps, delete failed experiments promptly
- **External archiving** - Export completed projects for long-term storage
- **Performance optimization** - Maintain reasonable library size for optimal interface performance

## **The Long-Term Value**

My Maps isn't just about current projects - it's about building expertise over time. Each successful map becomes a template for future work. Configurations that work well for specific terrain types become reusable assets. Your library becomes a knowledge base of what works, encoded in actual working examples rather than just notes.

This is why serious map creators find My Maps indispensable: it transforms map generation from repetitive manual work into a systematic process of building on proven successes.
