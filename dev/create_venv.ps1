Write-Host "=================================================" -ForegroundColor Cyan
Write-Host "      Setting up Python Virtual Environment      " -ForegroundColor White
Write-Host "                   for maps4fs                   " -ForegroundColor White
Write-Host "=================================================" -ForegroundColor Cyan

# Checking if .venv dir already exists.
if (Test-Path -Path ".venv") {
    Write-Host "-------------------------------------------------" -ForegroundColor Cyan
    Write-Host "[WARNING] Virtual environment already exists...  " -ForegroundColor Yellow
    Write-Host "[CLEANUP] Removing existing .venv directory...   " -ForegroundColor Yellow
    
    Remove-Item -Recurse -Force .venv
    
    Write-Host "[SUCCESS] Cleanup completed                      " -ForegroundColor Green
}

Write-Host "-------------------------------------------------" -ForegroundColor Cyan
Write-Host "[CREATING] Setting up new virtual environment... " -ForegroundColor Blue

# Creating VENV dir with selected python executable.
& python -m venv .venv

Write-Host "[SUCCESS] Virtual environment created.           " -ForegroundColor Green
Write-Host "-------------------------------------------------" -ForegroundColor Cyan

# Activating the virtual environment.
Write-Host "[ACTIVATE] Activating virtual environment...     " -ForegroundColor Blue
& .\.venv\Scripts\Activate.ps1

# Installing requirements from requirements.txt.
Write-Host "-------------------------------------------------" -ForegroundColor Cyan
Write-Host "[INSTALL] Installing development requirements... " -ForegroundColor Blue
pip install -r dev/requirements.txt

Write-Host ""
Write-Host "=================================================" -ForegroundColor Green
Write-Host "     [COMPLETE] Setup completed successfully!    " -ForegroundColor Green
Write-Host "        Virtual environment is ready to use      " -ForegroundColor Green
Write-Host "=================================================" -ForegroundColor Green