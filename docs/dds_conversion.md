# DDS File Conversion Guide

DDS (DirectDraw Surface) is the native texture format used throughout Farming Simulator for all visual assets including textures, icons, previews, and in-game maps. Understanding DDS conversion is essential for creating professional-quality map mods.

> 🎉 **NEW for FS25**: Maps4FS now automatically generates `overview.dds` files when **Download Satellite Images** is enabled! Manual conversion is only needed for custom overview maps or FS22.

## Why DDS Format?

**Performance Benefits:**
- **GPU-optimized** compression reduces memory usage
- **Faster loading times** compared to standard image formats
- **Built-in mipmapping** support for better rendering at distance
- **Hardware acceleration** compatibility with modern graphics cards

## Essential DDS Files for Maps

### Map Identity Files

| File | Dimensions | Purpose | Usage | FS25 Status |
|------|------------|---------|--------|-------------|
| `icon.dds` | 256×256 (FS22)<br>512×512 (FS25) | Mod icon | Displayed in mod browser | Manual conversion required |
| `preview.dds` | 2048×2048 | Loading screen preview | Shows during map loading | Manual conversion required |
| `overview.dds` | 4096×4096 | In-game minimap | Interactive map display | ✅ **Auto-generated** with satellite images |

> **FS25 Automation**: When **Download Satellite Images** is enabled, Maps4FS automatically creates `overview.dds` using satellite imagery - no manual conversion needed!

### Quality Requirements

**Compression Settings:**
- **Icon**: Use DXT1 or DXT5 compression for optimal file size
- **Preview**: DXT1 compression for photographic content
- **Overview**: DXT5 with alpha channel for transparency support

## Automated Overview Generation (FS25)

**Maps4FS now automatically handles overview.dds creation for Farming Simulator 25!**

### How It Works
When you enable **Download Satellite Images** in Maps4FS settings:
1. 🛰️ High-resolution satellite imagery is downloaded for your map area
2. 🎯 The image is automatically processed and optimized for in-game use
3. 📁 `overview.dds` is generated and saved in the correct format and dimensions
4. ✅ Ready to use immediately - no manual conversion required!

### Benefits
- **Perfect Quality**: Uses actual satellite imagery for photorealistic minimap
- **Correct Dimensions**: Automatically sized to 4096×4096 pixels
- **Optimal Compression**: Pre-configured with proper DXT5 settings
- **Time Saving**: Eliminates manual image editing and conversion steps

### When Manual Conversion is Still Needed
- **FS22 maps**: Automation only available for FS25
- **Custom overview designs**: If you prefer artistic or stylized minimaps
- **Icon and preview images**: These still require manual creation and conversion

## Conversion Tools & Methods

### Recommended Free Tools

#### 1. **GIMP with DDS Plugin** ⭐ *Most Popular*
- **Download:** [GIMP](https://www.gimp.org/) + [DDS Plugin](https://code.google.com/archive/p/gimp-dds/)
- **Pros:** Free, full control over compression settings
- **Best For:** Users comfortable with image editing software

#### 2. **Paint.NET with DDS Plugin**
- **Download:** [Paint.NET](https://www.getpaint.net/) + DDS Plugin from Plugin Pack
- **Pros:** User-friendly interface, good compression options
- **Best For:** Beginners seeking simplicity

#### 3. **Online Converters**
- **Convertio.co** - Supports PNG/JPG to DDS conversion
- **CloudConvert** - Batch processing capabilities
- **Best For:** Quick one-off conversions without software installation

### Professional Tools

#### **Adobe Photoshop with NVIDIA Plugin**
- **Download:** [NVIDIA Texture Tools Plugin](https://developer.nvidia.com/nvidia-texture-tools-adobe-photoshop)
- **Pros:** Professional-grade compression control, batch processing
- **Best For:** Professional mod developers with Photoshop access

#### **Intel Texture Works Plugin**
- **Compatible with:** Photoshop, After Effects
- **Features:** Advanced compression algorithms, real-time preview
- **Best For:** High-quality texture optimization

## Step-by-Step Conversion Process

### Using GIMP (Recommended)

1. **Prepare Your Image**
   - Ensure correct dimensions (see table above)
   - Optimize image quality and contrast
   - Save backup in original format

2. **Export to DDS**
   - File → Export As → Choose `.dds` extension
   - Select appropriate compression:
     - **DXT1** for images without transparency
     - **DXT5** for images with alpha channel
   - Enable **Generate Mipmaps** for better performance

3. **Verify Results**
   - Check file size (should be significantly smaller than PNG)
   - Test in-game to ensure visual quality

### Batch Conversion Tips

**For Multiple Files:**
- Use **ImageMagick** command-line tool for batch processing
- **XnConvert** provides GUI-based batch conversion
- **Photoshop Actions** automate repetitive conversions

## Optimization Best Practices

### Image Preparation
- **Start with high-quality source images** (PNG or TIFF recommended)
- **Use power-of-2 dimensions** when possible (512, 1024, 2048, 4096)
- **Avoid excessive compression** in source files before DDS conversion

### Compression Guidelines
- **Icons**: Prioritize clarity over file size
- **Previews**: Balance visual appeal with loading performance  
- **Overview Maps**: Ensure text and details remain readable

### File Size Management
- **Target Sizes:**
  - Icon: 50-200 KB
  - Preview: 500 KB - 2 MB
  - Overview: 2-8 MB

## Troubleshooting Common Issues

### **Problem:** DDS files appear corrupted in-game
**Solution:** Verify dimensions match exactly, check compression format compatibility

### **Problem:** Poor image quality after conversion
**Solution:** Use higher quality compression settings, start with better source images

### **Problem:** Large file sizes
**Solution:** Experiment with DXT1 vs DXT5, optimize source image before conversion

### **Problem:** Conversion software not recognizing DDS format
**Solution:** Ensure DDS plugin is properly installed and enabled

## Quality Verification

**Before finalizing your DDS files:**
1. **Visual Inspection:** Open converted files to check for artifacts
2. **Size Validation:** Confirm dimensions match requirements exactly
3. **In-Game Testing:** Load map to verify proper display
4. **Performance Check:** Monitor loading times and memory usage

## Advanced Techniques

### **Custom Compression Settings**
- Experiment with **BC7** compression for highest quality (if supported)
- Use **uncompressed DDS** for critical visual elements
- Consider **DXT1a** for single-bit alpha transparency

### **Mipmap Optimization**
- **Auto-generate mipmaps** for distant viewing quality
- **Custom mipmap chains** for specialized applications
- **Sharpening filters** to maintain detail at smaller sizes

---

**Pro Tip:** Always keep your original high-resolution source files. DDS conversion is lossy, so you'll want to re-convert from originals when making updates rather than editing DDS files directly.