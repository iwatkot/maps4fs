```bash
# Backend API container
# Mounts:
# - %USERPROFILE%/maps4fs/mfsrootdir (shared with frontend)
# - %USERPROFILE%/maps4fs/data (API-only for data storage)
docker run -d -p 8000:8000 --name maps4fsapi -v %USERPROFILE%/maps4fs/mfsrootdir:/usr/src/app/mfsrootdir -v %USERPROFILE%/maps4fs/data:/usr/src/app/data iwatkot/maps4fsapi
```

```bash
# Frontend UI container
# Mounts:
# - %USERPROFILE%/maps4fs/mfsrootdir (shared with backend)
docker run -d -p 3000:3000 --name maps4fsui -v %USERPROFILE%/maps4fs/mfsrootdir:/usr/src/app/mfsrootdir iwatkot/maps4fsui
```

**These commands work out of the box on Windows!**
- `%USERPROFILE%` automatically resolves to `C:/Users/YourUsername`
- No manual path editing required

**Directory structure created:**
- `C:/Users/YourUsername/maps4fs/mfsrootdir` - Shared working directory between backend and frontend
- `C:/Users/YourUsername/maps4fs/data` - Templates and schemas directory for API