Write-Host "=================================================" -ForegroundColor Cyan
Write-Host "         Downloading maps4fs Data Files          " -ForegroundColor White
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host ""

$tempDir = "tempdata"
$repoUrl = "https://github.com/iwatkot/maps4fsdata.git"

# Check if git is available
try {
    git --version | Out-Null
} catch {
    Write-Host "[ERROR] Git is not installed or not in PATH" -ForegroundColor Red
    Write-Host "[INFO] Please install Git and try again" -ForegroundColor Yellow
    exit 1
}

# Remove temp directory if it exists
if (Test-Path -Path $tempDir) {
    Write-Host "[CLEANUP] Removing existing temp directory..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force $tempDir
    Write-Host "[SUCCESS] Cleanup completed" -ForegroundColor Green
    Write-Host ""
}

# Clone the repository with depth 1
Write-Host "[CLONE] Cloning maps4fsdata repository..." -ForegroundColor Blue
git clone --depth 1 $repoUrl $tempDir

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Failed to clone repository" -ForegroundColor Red
    exit 1
}

Write-Host "[SUCCESS] Repository cloned successfully" -ForegroundColor Green
Write-Host ""

# Execute prepare_data.ps1 script
Write-Host "[EXECUTE] Running prepare_data.ps1 script..." -ForegroundColor Blue
$scriptPath = Join-Path $tempDir "prepare_data.ps1"

if (-not (Test-Path -Path $scriptPath)) {
    Write-Host "[ERROR] prepare_data.ps1 not found in repository" -ForegroundColor Red
    Remove-Item -Recurse -Force $tempDir
    exit 1
}

Set-Location $tempDir
& ".\prepare_data.ps1"

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] prepare_data.ps1 execution failed" -ForegroundColor Red
    Set-Location ..
    Remove-Item -Recurse -Force $tempDir
    exit 1
}

Set-Location ..
Write-Host "[SUCCESS] Data preparation completed" -ForegroundColor Green
Write-Host ""

# Copy data folder to current working directory
$dataSource = Join-Path $tempDir "data"
$dataDestination = "data"

if (-not (Test-Path -Path $dataSource)) {
    Write-Host "[ERROR] Data folder not found after script execution" -ForegroundColor Red
    Remove-Item -Recurse -Force $tempDir
    exit 1
}

Write-Host "[COPY] Copying data folder to current directory..." -ForegroundColor Blue

# Remove existing data folder if it exists
if (Test-Path -Path $dataDestination) {
    Write-Host "[INFO] Removing existing data folder..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force $dataDestination
}

Copy-Item -Recurse -Force $dataSource $dataDestination

if (-not (Test-Path -Path $dataDestination)) {
    Write-Host "[ERROR] Failed to copy data folder" -ForegroundColor Red
    Remove-Item -Recurse -Force $tempDir
    exit 1
}

Write-Host "[SUCCESS] Data folder copied successfully" -ForegroundColor Green
Write-Host ""

# Clean up temp directory
Write-Host "[CLEANUP] Removing temporary directory..." -ForegroundColor Blue
Remove-Item -Recurse -Force $tempDir

Write-Host "[SUCCESS] Cleanup completed" -ForegroundColor Green
Write-Host ""
Write-Host "=================================================" -ForegroundColor Green
Write-Host "     [COMPLETE] Data download completed!         " -ForegroundColor Green
Write-Host "        Data folder is ready to use              " -ForegroundColor Green
Write-Host "=================================================" -ForegroundColor Green