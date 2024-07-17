python -m venv .venv

. .\.venv\Scripts\Activate

pip install -r requirements.txt

$env:PYTHONPATH = "$(Get-Location)$([IO.Path]::PathSeparator)$env:PYTHONPATH"
python maps4fs\ui.py