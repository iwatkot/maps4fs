# Directories to be removed
$dirs = @(".mypy_cache", ".pytest_cache", "htmlcov", "dist", "archives", "cache", "logs", "maps", "temp", "map_directory","osmps", "tests/data")

# Files to be removed
$files = @(".coverage", "queue.json")

# Loop through the directories
foreach ($dir in $dirs) {
    Write-Host "Removing directory $dir"
    Remove-Item -Recurse -Force $dir -ErrorAction SilentlyContinue
}

# Loop through the files
foreach ($file in $files) {
    Write-Host "Removing file $file"
    Remove-Item -Force $file -ErrorAction SilentlyContinue
}

Write-Host "Removing __pycache__ directories"
Get-ChildItem -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "Cleanup completed."