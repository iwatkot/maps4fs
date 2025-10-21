# Legacy Deployment (Deprecated)

⚠️ **This deployment method is deprecated and no longer supported.**

## What is Legacy Deployment?

The legacy version was a monolith application where both backend and frontend (using Streamlit) were bundled together in a single Docker container. This caused confusion for users and made the application harder to maintain.

## Legacy Docker Command

```bash
docker run -d -p 8501:8501 -p 8000:8000 --name maps4fs -v /c/maps4fs:/usr/src/app/mfsrootdir iwatkot/maps4fs:2.2.7
```

### Command Breakdown

- `-d` - Run container in detached mode (background)
- `-p 8501:8501` - Streamlit frontend port
- `-p 8000:8000` - Backend API port
- `--name maps4fs` - Container name
- `-v /c/maps4fs:/usr/src/app/mfsrootdir` - Volume mount for data directory

### Volume Mount Details

**Important:** Replace `/c/maps4fs` with your own local directory path where you want to store:
- Generated maps
- Cache data
- Configuration files
- Custom DEM and OSM files

**Examples for different operating systems:**
- **Windows:** `-v C:\your\maps\folder:/usr/src/app/mfsrootdir`
- **Linux/macOS:** `-v /home/user/maps4fs:/usr/src/app/mfsrootdir`

**What gets stored in the mounted folder:**
- `maps/` - Your generated maps
- `cache/` - Downloaded elevation and OSM data
- Custom files you want to use for map generation

**Latest available legacy tag:** `2.2.7`

Docker Hub: https://hub.docker.com/r/iwatkot/maps4fs

## Important Notice

- ❌ **No updates, new features, or support**
- ❌ **Deprecated architecture**
- ❌ **May have unresolved issues**
- ✅ **Still functional if you prefer it**

## Recommended Alternative

For the best experience with latest features and support, please use the **[Local Deployment](local_deployment.md)** method instead.