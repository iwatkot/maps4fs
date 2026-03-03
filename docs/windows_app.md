# Windows App

**Maps4FS Standalone Application for Windows**

The Windows App provides the easiest way to run Maps4FS on Windows without Docker or Python setup. It's a portable, standalone executable that you can download and run immediately.

## 🚨 CRITICAL SECURITY WARNING

**⚠️ ONLY DOWNLOAD FROM THE OFFICIAL SOURCE**

### Official Download Location
**[https://maps4fs.xyz/download](https://maps4fs.xyz/download)**

### ⛔ Security Guidelines
- **Carefully verify** every character in your browser's address bar
- If there are **ANY differences** in the URL (even one character), **LEAVE IMMEDIATELY**
- **NEVER download** from:
  - Any other domain or website
  - IP addresses
  - File sharing services
  - Forums or community posts
  - Discord attachments
  - Third-party download sites

### 🔐 Why This Matters
This is an **executable file** (.exe). Downloading executables from unofficial sources can lead to **catastrophic consequences** including:
- Malware infection
- Data theft
- System compromise
- Financial loss

**Please take this seriously.** When in doubt, don't download.

---

## 📦 What Is It?

Maps4FS for Windows is a **standalone portable application** that includes everything you need to generate Farming Simulator maps:
- No Docker required
- No Python installation needed
- No complex setup process
- Just download and run

## ⚡ Quick Start

1. **Download** from [https://maps4fs.xyz/download](https://maps4fs.xyz/download)
2. **Run** `maps4fs-0.0.1.exe` (or other version number)
3. **Generate** your maps!

## 🎯 Available Features

The Windows App includes all major Maps4FS features:
- **[Presets](presets.md)** - Store and manage complete map configurations
- **[Settings](settings.md)** - Customize your generation preferences
- **All Map Components** - Fields, forests, roads, buildings, and more
- **Custom Resources** - Use your own [OSM files](custom_osm.md) and [DEM data](custom_dem.md)
- **[Localization](localization.md)** - Want to see the app in your language? Community-driven translations are welcome!

## 📋 Requirements

### System Requirements
- **Operating System**: Windows 10 or Windows 11
- **RAM**: 8GB minimum (16GB+ recommended for large maps)
- **Disk Space**: 5GB minimum free space
- **Internet Connection**: Required for downloading map data

### Background Terrain Feature
For the **Background Terrain center removal** feature to work, you need:
- **Blender 4.3** or later installed on your machine
- Available from [blender.org](https://www.blender.org/download/)

Without Blender, all other features will work normally, but the Background Terrain center removal will be unavailable.

## ✅ Advantages

- **🛠️ No Complex Setup**: No Docker or Python required
- **📦 Portable**: Run from any folder, USB drive, or location
- **🚀 Quick Start**: Download and run in minutes
- **🎯 Beginner-Friendly**: Designed for users new to Maps4FS
- **💻 Windows Optimized**: Native performance on Windows

## ⚠️ Limitations

- **🪟 Windows Only**: Not available for Mac or Linux
- **🔄 Manual Updates**: Need to download new versions manually
- **🎨 Blender Required**: For Background Terrain center removal

## 📖 How to Use

After launching the app:

1. **Enter coordinates** or select a location
2. **Choose map size** and settings
3. **Configure features** you want to include
4. **Click Generate** and wait for processing
5. **Find your map** in the output directory

For detailed instructions on map generation settings, see:
- [Step by Step Guide](step_by_step_guide.md)
- [Main Settings](main_settings.md)
- [Generation Settings](generation_settings.md)

## 🐛 Known Issues & Troubleshooting

### Common Issues

**Q: Antivirus flags the executable**  
A: This is normal for new executables. The file is safe when downloaded from the official source. You may need to add an exception in your antivirus.

**Q: Background Terrain center removal not working**  
A: Install Blender 4.3+ from [blender.org](https://www.blender.org/download/)

**Q: App crashes on startup**  
A: Check Windows Event Viewer for details and report on GitHub with error logs

**Q: Generation fails**  
A: Ensure you have sufficient disk space and RAM. Try a smaller map size.

### Reporting Bugs

When reporting issues, please include:
- Windows version
- Error messages or crash logs
- Steps to reproduce
- Map size and settings used

Report issues at: [GitHub Issues](https://github.com/iwatkot/maps4fs/issues)

## 🔄 Updates

The Windows App does not auto-update. To get the latest version:
1. Visit [https://maps4fs.xyz/download](https://maps4fs.xyz/download)
2. Download the latest version
3. Extract and replace the old files

## 🆚 Comparison with Other Options

| Feature | Windows App | Web App | Docker |
|---------|-------------|---------|--------|
| **Setup Time** | 2 minutes | 0 minutes | 15-30 minutes |
| **Map Sizes** | All sizes | 2x2, 4x4 km | All sizes |
| **Portability** | ✅ | ✅ | ❌ |
| **Background Terrain** | ✅ (with Blender) | ❌ | ✅ |
| **Presets & Settings** | ✅ | ❌ | ✅ |

### When to Use Each Option

- **Windows App**: You're on Windows and want simplicity without Docker
- **Web App**: Testing or very small maps, no installation at all
- **Docker**: You need maximum stability, are comfortable with Docker, or use Mac/Linux

See [How to Launch](how_to_launch.md) for detailed comparison.

## 🆘 Get Help

- **Documentation**: [maps4fs.xyz/docs](https://maps4fs.xyz/docs)
- **Discord**: [Join our community](https://discord.gg/wemVfUUFRA)
- **GitHub**: [Report issues](https://github.com/iwatkot/maps4fs/issues)
- **FAQ**: [Frequently Asked Questions](FAQ.md)

---

**Remember**: Only download from [https://maps4fs.xyz/download](https://maps4fs.xyz/download) - your security depends on it!
