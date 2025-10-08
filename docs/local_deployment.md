# How to deploy Maps4FS locally?

Local version of the tool allows you to use all the features, that may be disabled on the public version due to hosting limitations and large amount of users. If you deploy the tool locally, you can generate maps of any size with the highest speed limited only by your hardware.

## 🆕 **Exclusive Local Features**

### 🎛️ **Presets System** 
The revolutionary [Presets](presets.md) feature is **exclusively available in local deployment**, allowing you to:
- 📁 **Store Multiple Configurations** - OSM files, DEM files, Main Settings, and Generation Settings
- 🚀 **One-Click Apply** - Load complete map setups instantly
- 💾 **Save from My Maps** - Convert successful generations into reusable presets
- 🔄 **Build Template Libraries** - Create collections of proven configurations

### 🗂️ **Advanced Data Management**
- **[My Maps](my_maps.md)** - Complete map library management and organization
- **[Data Directory](data_directory.md)** - Full control over your map generation assets
- **Custom Resources** - Unlimited [Custom OSM](custom_osm.md) and [Custom DEM](custom_dem.md) files

## System Requirements

- CPU with at least 4 cores
- [Virtualization must be enabled](https://support.microsoft.com/en-us/windows/enable-virtualization-on-windows-c5578302-6e43-4b4b-a449-8ced115f58e1) in BIOS/UEFI settings
- Virtual Machine Platform feature must be enabled on Windows
- 8 GB RAM for 2 km maps, 16 GB RAM for 4-8 km maps, 32 GB RAM for larger maps
- SSD storage (will work very slow on HDD)
- Windows 10/11 22H2 or later / Linux / MacOS
- [Docker](https://docs.docker.com/desktop/setup/install/windows-install/) must be installed and running
- Either [Hyper-V](https://docs.docker.com/desktop/setup/install/windows-install/#system-requirements) (Windows Pro only) or [WSL 2](https://docs.docker.com/desktop/setup/install/windows-install/#wsl-verification-and-setup) must be enabled

## Prerequisites

Before deployment, make sure that the following components are in place:

1. Check that the Docker is installed and running properly:

```powershell
# Shows Docker version.
docker --version

# Launches a test container and removes it after execution.
docker run --rm hello-world
```

2. Make sure that you [increased the limit for Docker resources (CPU, Memory)](https://docs.docker.com/desktop/settings-and-maintenance/settings/) in Docker settings. Otherwise the containers will be stopped upon generation.  

3. Check that the [Powershell is installed](https://learn.microsoft.com/en-gb/powershell/scripting/install/installing-powershell-on-windows?view=powershell-7.5) and running properly:

```powershell
# Shows PowerShell version.
$PSVersionTable.PSVersion

# Launches a test PowerShell command.
Write-Host "Hello, World!"
```

*️⃣ PowerShell is required for automated deployment, but you still can launch the containers manually with basic terminal without PowerShell installed.

4. Install the corresponding version of the Giants Editor. 

*️⃣ Note: you must use the specific version that matches the game installation. Not just major versions, such as, GE 9.X for FS22 and GE 10.X for FS25, but also the exact minor versions, that matches the game version. Otherwise, the editor will crash or have errors and glitches.

## Deployment

There are different ways to deploy the tool locally, depending on your needs and preferences. For most users, it's recommended to use the automated [Setup Wizard](https://github.com/iwatkot/maps4fs/blob/main/setup-wizard.ps1). However, you can choose other approaches as well.

### Setup Wizard

**Skill level:** 🟢  
**Requires:** PowerShell

The easiest way to deploy Maps4FS locally is using our automated setup wizard. You can run it directly from PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -Command "iex (iwr 'https://raw.githubusercontent.com/iwatkot/maps4fs/main/setup-wizard.ps1' -UseBasicParsing).Content"
```

This command will:
- Download the latest setup wizard  
- Check that Docker is installed  
- Allows download and install Docker if not  
- Checks if the Docker daemon is running or launches it if not  
- Checks for the containers of old versions and removes them if necessary  
- Checks if required ports are available  
- Creates necessary directories and files  
- Deploys the containers with all the necessary configurations  
- Opens the web interface in your default browser

### Using Docker Compose

**Skill level:** 🟡  
**Requires:** Docker Compose

If you want better control of the deployment such as mounts to specific directories or whatever, you can use the Docker Compose. Download the latest `docker-compose.yml` file from the repository [here](https://github.com/iwatkot/maps4fs/blob/main/docker-compose.yml) manually or use this command to download it directly from PowerShell:

```powershell
# Download docker-compose.yml
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/iwatkot/maps4fs/main/docker-compose.yml" -OutFile "docker-compose.yml"

# Launch Docker Compose.
docker-compose -p maps4fs up -d
```

If you don't need to make any changes you can launch the docker compose file directly from the PowerShell:

```powershell
# Launch docker-compose directly from GitHub
powershell -ExecutionPolicy Bypass -Command "iwr 'https://raw.githubusercontent.com/iwatkot/maps4fs/main/docker-compose.yml' -OutFile 'docker-compose.yml'; docker-compose -p maps4fs up -d"
```

### Manual Deployment

**Skill level:** 🟡  
**Requires:** Docker  

If you prefer to set up the containers manually, you can use the following commands:

```powershell
# Backend API container
docker run -d --pull=always -p 8000:8000 --name maps4fsapi -e USERPROFILE="$env:USERPROFILE" -v $env:USERPROFILE/maps4fs/mfsrootdir:/usr/src/app/mfsrootdir -v $env:USERPROFILE/maps4fs/templates:/usr/src/app/templates -v $env:USERPROFILE/maps4fs/defaults:/usr/src/app/defaults -v /var/run/docker.sock:/var/run/docker.sock iwatkot/maps4fsapi
```

```powershell
# Frontend UI container  
docker run -d --pull=always -p 3000:3000 --name maps4fsui -e USERPROFILE="$env:USERPROFILE" -v $env:USERPROFILE/maps4fs/mfsrootdir:/usr/src/app/mfsrootdir -v $env:USERPROFILE/maps4fs/templates:/usr/src/app/templates -v $env:USERPROFILE/maps4fs/defaults:/usr/src/app/defaults -v /var/run/docker.sock:/var/run/docker.sock iwatkot/maps4fsui
```

*️⃣ Remember that you can set the preferable directory to mount as well as specify the needed port or even deploy the specific version of the container.

## Upgrade

To upgrade Maps4FS to the latest version, follow the method that matches your original deployment:

### Using Setup Wizard

The [Setup Wizard](#setup-wizard) automatically handles upgrades. Simply run the same command again:

```powershell
powershell -ExecutionPolicy Bypass -Command "iex (iwr 'https://raw.githubusercontent.com/iwatkot/maps4fs/main/setup-wizard.ps1' -UseBasicParsing).Content"
```

The wizard will detect existing containers, remove old versions, and deploy the latest release.

### Docker Compose or Manual Deployment

For [Docker Compose](#using-docker-compose) or [Manual Deployment](#manual-deployment), stop and remove existing containers first:

```powershell
# Stop and remove existing containers
docker stop maps4fsapi maps4fsui
docker rm maps4fsapi maps4fsui
```

Then follow your original deployment method to install the latest version.

## Usage

After deployment, you can access the web interface of Maps4FS by opening your browser and navigating to `http://localhost:3000`. The backend API will be accessible at `http://localhost:8000`.  

By default, the following directories are mounted and used:  
- `C:/Users/YourUsername/maps4fs/mfsrootdir` - Shared working directory between backend and frontend (maps and cache).  
- `C:/Users/YourUsername/maps4fs/templates` - Templates and schemas directory for API.  
- `C:/Users/YourUsername/maps4fs/defaults` - **🆕 Presets system** - Multiple OSM files, DEM files, and settings configurations.  

🎯 **New Presets Structure**: The `defaults` directory now supports the [Presets](presets.md) system with four subdirectories:
- `defaults/osm/` - Multiple OpenStreetMap data files
- `defaults/dem/` - Multiple Digital Elevation Model files
- `defaults/main_settings/` - Core map configuration presets
- `defaults/generation_settings/` - Advanced generation option presets

Learn more about the [Data Directory structure](data_directory.md), [Presets](presets.md), and [Map Templates](map_templates.md).

## Troubleshooting

If you encounter any issues during the deployment or usage of Maps4FS, follow the steps outlined below to understand what's wrong.

### Check Docker

Make sure Docker is installed and running properly on your machine.

```powershell
docker --version
```

As a result, you should see the installed version of Docker. Then, launch the sample container that will be removed automatically after a few seconds.

```powershell
docker run --rm hello-world
```

*️⃣ If any of the above commands fail, that means you have issues with Docker and need to ensure that is properly installed and configured.

### Check the containers

You need to ensure that both frontend and backend containers are exist and running properly.  The two containers being used are:

| Container name | Default port | Image name | Description |
|----------------|--------------|------------|-------------|
| maps4fsapi     | 8000         | iwatkot/maps4fsapi | Backend API container |
| maps4fsui      | 3000         | iwatkot/maps4fsui  | Frontend UI container |


Use the following commands to filter by specific container names or image names:

```powershell
# Filter by container name.
docker ps --filter "name=maps4fs"
```

The expected output should be something like:

```plaintext
CONTAINER ID   IMAGE                     COMMAND                  CREATED         STATUS         PORTS                    NAMES
abc123def456   iwatkot/maps4fsapi       "uvicorn app.main:app…"   5 minutes ago   Up 5 minutes   0.0.0.0:8000->8000/tcp   maps4fsapi
def456abc123   iwatkot/maps4fsui        "npm start"               5 minutes ago   Up 5 minutes   0.0.0.0:3000->3000/tcp   maps4fsui
```

*️⃣ If the command itself failed, that means you have issues with Docker and need to ensure that is properly installed and configured.

### If containers stopped

If you don't see both containers in the output, maybe they have stopped or failed to start. First of all, you need to know the exit code of the container.

```powershell
# Check exit code of backend API container
docker inspect maps4fsapi --format='{{.State.ExitCode}}'

# Check exit code of frontend UI container
docker inspect maps4fsui --format='{{.State.ExitCode}}'
```

Common exit codes include:

| Exit Code | Meaning |
|-----------|---------|
| 0         | Success |
| 1         | General error |
| [137](#docker-exit-code-137)       | Container killed (out of memory) |

Then, check the logs of the containers:

```powershell
# Check logs of backend API container
docker logs maps4fsapi

# Check logs of frontend UI container
docker logs maps4fsui
```

To save the logs into file, you can use the following commands:

```powershell
# Save logs of backend API container
docker logs maps4fsapi > maps4fsapi.log

# Save logs of frontend UI container
docker logs maps4fsui > maps4fsui.log
```

If the logs do not contain any errors, but simply indicate that the process was terminated, you may be facing a resource limitation issue and it's recommended to check the system resource usage (CPU, RAM) during the container runtime.  
If the logs contain errors, but they are unclear, it's recommended to ask for help in the [Discord](https://discord.gg/Sj5QKKyE42).

#### Docker events

You can monitor Docker events to get real-time information about container lifecycle changes. Use the following command:

```powershell
docker events
```

To save the events for last 24 hours into a file, you can use the following command:

```powershell
docker events --since 24h > docker_events.log
```

#### Docker exit code 137

The most common exit code indicating that the container was killed due to out of memory (OOM) issues. For large maps, the generator may be processing gigantic images and/or meshes, which may lead to high RAM usage.  
In this case, you need to increase the memory limit for the containers, refer to the official [Docker documentation](https://docs.docker.com/desktop/settings-and-maintenance/settings/) for more information on how to do this.

### If containers running

If both containers are running, but you still facing issues, please check that both of them are accessible.


```powershell
# Check if backend API is accessible and returns JSON response:
Invoke-WebRequest -Uri http://localhost:8000/info/version -UseBasicParsing
```

The expected response should be a JSON object like:

```json
{"version":"2.2.7"}
```

For the UI container use the following command:

```powershell
# Check if frontend UI is accessible and returns HTML response:
Invoke-WebRequest -Uri http://localhost:3000 -UseBasicParsing
```

The expected response should be the HTML content of the frontend UI.

*️⃣ If commands fail, that means that the backend API is not accessible or not running properly. Please check the container logs and status as described in the troubleshooting steps above.


### If you still have issues

Make sure that you've followed all the steps above, fill-out the following form and ask for help in the [Discord](https://discord.gg/Sj5QKKyE42) server.  
*️⃣ Requests without sufficient information may be ignored.

#### Checklist before asking for help

- [ ] My machine meets the system requirements.
- [ ] I am attaching the hardware specifications and information about the OS (including version) with this request.
- [ ] I have checked the Docker version and run the hello-world container.
- [ ] I am attaching outputs of both commands with this request.
- [ ] I have ensured that Docker is properly installed and configured.
- [ ] I have checked the status of both containers (API and UI) and they are running.
- [ ] I am attaching outputs of both commands with this request.
- [ ] I have checked the logs for both containers.
- [ ] I am attaching both log files with this request.
- [ ] I have checked the resource usage (CPU, RAM) during the container runtime.
- [ ] I have checked the Docker events for any relevant information.
- [ ] I am attaching the Docker events log file with this request.
- [ ] I have checked accessibility of both containers (API and UI).
- [ ] I am attaching the outputs of both accessibility checks with this request.
