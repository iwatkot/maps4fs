## Prerequisites
- Docker Desktop must be running
- Ensure Docker daemon is accessible

```bash
# Backend API container
docker run -d --pull=always -p 8000:8000 --name maps4fsapi -v $env:USERPROFILE/maps4fs/mfsrootdir:/usr/src/app/mfsrootdir -v $env:USERPROFILE/maps4fs/data:/usr/src/app/data iwatkot/maps4fsapi
```

```bash
# Frontend UI container
docker run -d --pull=always -p 3000:3000 --name maps4fsui -v $env:USERPROFILE/maps4fs/mfsrootdir:/usr/src/app/mfsrootdir iwatkot/maps4fsui
```

**These commands work out of the box on Windows PowerShell!**
- Frontend accessible at: `http://localhost:3000`
- Backend API accessible at: `http://localhost:8000`

**Directory structure created:**
- `C:/Users/YourUsername/maps4fs/mfsrootdir` - Shared working directory between backend and frontend
- `C:/Users/YourUsername/maps4fs/data` - Templates and schemas directory for API