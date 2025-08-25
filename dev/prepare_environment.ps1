Write-Host "=================================================" -ForegroundColor Cyan
Write-Host "           maps4fs Environment Setup             " -ForegroundColor White
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host ""

# Get the directory where this script is located
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$downloadScript = Join-Path $scriptDir "download_data.ps1"
$venvScript = Join-Path $scriptDir "create_venv.ps1"

# Check if required scripts exist
if (-not (Test-Path -Path $downloadScript)) {
    Write-Host "[ERROR] download_data.ps1 not found in script directory" -ForegroundColor Red
    Write-Host "[INFO] Expected location: $downloadScript" -ForegroundColor Yellow
    exit 1
}

if (-not (Test-Path -Path $venvScript)) {
    Write-Host "[ERROR] create_venv.ps1 not found in script directory" -ForegroundColor Red
    Write-Host "[INFO] Expected location: $venvScript" -ForegroundColor Yellow
    exit 1
}

Write-Host "=================================================" -ForegroundColor Blue
Write-Host "              STEP 1: Download Data              " -ForegroundColor White
Write-Host "=================================================" -ForegroundColor Blue
Write-Host ""

# Execute download_data.ps1
& $downloadScript

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "=================================================" -ForegroundColor Red
    Write-Host "        [FAILED] Data download failed            " -ForegroundColor Red
    Write-Host "=================================================" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "=================================================" -ForegroundColor Blue
Write-Host "         STEP 2: Setup Virtual Environment       " -ForegroundColor White
Write-Host "=================================================" -ForegroundColor Blue
Write-Host ""

# Execute create_venv.ps1
& $venvScript

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "=================================================" -ForegroundColor Red
    Write-Host "      [FAILED] Virtual environment setup failed " -ForegroundColor Red
    Write-Host "=================================================" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "=================================================" -ForegroundColor Green
Write-Host "    [SUCCESS] Environment setup completed!       " -ForegroundColor Green
Write-Host "                                                 " -ForegroundColor Green
Write-Host "  Data files downloaded and ready                " -ForegroundColor Green
Write-Host "  Virtual environment created and activated      " -ForegroundColor Green
Write-Host "  Dependencies installed                         " -ForegroundColor Green
Write-Host "                                                 " -ForegroundColor Green
Write-Host "         Your maps4fs environment is ready!      " -ForegroundColor Green
Write-Host "=================================================" -ForegroundColor Green