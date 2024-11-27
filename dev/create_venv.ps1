# Checking if .venv dir already exists.
if (Test-Path -Path ".venv") {
    Write-Host "VENV dir (.venv) already exists, it will be removed."
    Remove-Item -Recurse -Force .venv
}

Write-Host "VENV will be created"

# Creating VENV dir with selected python executable.
& python -m venv .venv

# Activating the virtual environment.
& .\.venv\Scripts\Activate.ps1

# Installing requirements from requirements.txt.
Write-Host "Installing dev/requirements..."
pip install -r dev/requirements.txt
Write-Host "Dev Requirements have been successfully installed, VENV ready."

# Deactivating the virtual environment.
deactivate