# How to Launch Maps4FS

Maps4FS offers multiple deployment options to suit different user needs, from quick online generation to full local control. Choose the method that best fits your requirements and technical expertise.

## 🪟 Option 1: Windows App (Easiest for Windows)

**Standalone portable application - no installation needed**

### 🎯 When to Use
- You're on Windows and want the simplest setup
- Don't want to deal with Docker or Python
- Want a portable app you can run from anywhere
- Need full features without complex installation

### ✅ Advantages
- **📦 Zero Setup**: Download and run immediately
- **🗺️ Full Map Sizes**: 2x2, 4x4, 8x8, 16x16 km + custom dimensions
- **💼 Portable**: Run from any folder or USB drive
- **⚡ Fast**: Native Windows performance
- **🔒 Privacy**: Everything runs locally

### ⚠️ Important Notes
- **🧪 Preview Version**: Expect bugs, features in development
- **🎨 Blender Required**: For Background Terrain center removal (install Blender 4.3+)
- **🪟 Windows Only**: Not available for Mac or Linux

### 🚀 Quick Start
1. Download from **[maps4fs.xyz/download](https://maps4fs.xyz/download)**
2. Extract and run `maps4fs.exe`
3. Start generating maps!

### 🚨 Security Warning
**ONLY download from the official website: maps4fs.xyz/download**  
Carefully verify the URL - downloading executables from unofficial sources can be extremely dangerous.

### 📖 Full Documentation
- 📚 [Complete Windows App Guide](windows_app.md)

---

## 🌐 Option 2: Public Web App (No Installation)

**Perfect for beginners and quick map generation**

### 🎯 When to Use
- First-time users exploring Maps4FS
- Small map projects (2x2, 4x4 km)
- No installation requirements
- Quick testing and experimentation

### ✅ Advantages
- **🛠️ Zero Installation**: Works directly in your browser
- **🚀 Instant Access**: No setup time required
- **📱 Cross-Platform**: Works on any device with a web browser
- **🔄 Always Updated**: Latest features automatically available

### ⚠️ Limitations
- **🗺️ Map Sizes**: 2x2, 4x4 km only (custom sizes not available)
- **✂️ Map Scaling**: Not supported
- **⚙️ Settings**: Some advanced features unavailable
- **🌐 Internet Required**: Must be online to use

### 🚀 How to Launch
1. Open your web browser
2. Navigate to **[maps4fs.xyz](https://maps4fs.xyz)**
3. Start generating maps immediately!

---

## 🐳 Option 3: Local Docker Deployment (For Advanced Users)

**Full features with containerized environment**

### 🎯 When to Use
- Want larger maps (up to 16x16 km)
- Need advanced settings and customization
- Faster generation times
- Working on serious map projects

### ✅ Advantages
- **🗺️ Full Map Sizes**: 2x2, 4x4, 8x8, 16x16 km + custom dimensions
- **✂️ Map Scaling**: Full scaling support
- **⚙️ Complete Features**: All advanced settings available
- **⚡ Faster Generation**: Local processing power
- **🔒 Privacy**: Your data stays on your machine
- **🌐 Offline Capable**: Works without internet (after initial setup)

### 📋 Requirements
- **Docker Desktop** installed on your system
- **8GB RAM minimum** (16GB+ recommended for large maps)
- **10GB free disk space** per project

### 🚀 Quick Launch (Windows)
Use the automated Setup Wizard:

```powershell
powershell -ExecutionPolicy Bypass -Command "iex (iwr 'https://raw.githubusercontent.com/iwatkot/maps4fs/main/setup-wizard.ps1' -UseBasicParsing).Content"
```

### 📖 Detailed Instructions
For complete setup guides including Docker installation:
- 📚 [Local Deployment Guide](local_deployment.md)

---

## 💻 Option 4: Python Package (Developers Only)

**Maximum control and performance for developers**

### 🎯 When to Use
- Software developers or advanced users
- Custom integrations needed
- Maximum performance required
- Contributing to Maps4FS development

### ✅ Advantages
- **🔧 Full Control**: Complete access to all functionality
- **⚡ Best Performance**: Direct Python execution, no containers
- **🛠️ Customizable**: Modify and extend the codebase
- **📦 API Access**: Programmatic map generation
- **🔄 Latest Features**: Access to cutting-edge development

### 📋 Requirements
- **Python 3.8+** installed
- **Git** for source code access
- **Command line familiarity**
- **Development environment** setup

### 🚀 Installation via pip
```bash
pip install maps4fs
```

### 🚀 Development Setup
```bash
git clone https://github.com/iwatkot/maps4fs.git
cd maps4fs
pip install -e .
```

### 📖 Developer Resources
- 📚 [Python Package Deployment](python_package_deployment.md)
- 🐙 [GitHub Repository](https://github.com/iwatkot/maps4fs)
- 📝 [API Documentation](https://github.com/iwatkot/maps4fsapi)

---

## 🤔 Which Option Should I Choose?

### 🪟 **On Windows?**
→ Start with **Option 1 (Windows App)** for the easiest experience

### 🆕 **Just Testing or Quick Maps?**
→ Use **Option 2 (Web App)** - zero installation, works anywhere

### 🎯 **Serious Map Making (Mac/Linux or prefer Docker)?**
→ Choose **Option 3 (Docker)** for full features and stability

### 💻 **Developer or Want to Contribute?**
→ Use **Option 4 (Python)** for maximum control and development access

## 📊 Feature Comparison

| Feature | Windows App | Web App | Docker | Python |
|---------|-------------|---------|--------|--------|
| **Setup Difficulty** | ⭐ Easiest | ⭐ Easy | ⭐⭐⭐ Advanced | ⭐⭐⭐⭐ Expert |
| **Platform** | Windows only | Any browser | Any OS | Any OS |
| **Map Sizes** | All sizes | 2x2, 4x4 km | All sizes | All sizes |
| **Custom Dimensions** | ✅ | ❌ | ✅ | ✅ |
| **Map Scaling** | ✅ | ❌ | ✅ | ✅ |
| **Advanced Settings** | Full | Partial | Full | Full |
| **Generation Speed** | Fast | Slower | Fast | Fastest |
| **Offline Usage** | ✅ | ❌ | ✅ | ✅ |
| **Stability** | Preview | Stable | Stable | Stable |
| **Updates** | Manual | Automatic | Manual | Manual |

## 🆘 Need Help?

### 💬 Community Support
- **Discord**: [Join our server](https://discord.gg/Sj5QKKyE42) for real-time help
- **GitHub Issues**: [Report problems](https://github.com/iwatkot/maps4fs/issues)
- **Documentation**: Check our [FAQ](FAQ.md) for common questions

### 📺 Video Tutorials
📹 [YouTube Playlist](https://www.youtube.com/watch?v=hPbJZ0HoiDE&list=PLug0g7UYHX8D1Jik6NkJjQhdxqS-NOtB9) - Complete setup and usage guides

---

**Ready to start?** Choose your preferred option above and begin creating amazing Farming Simulator maps from real-world locations!
