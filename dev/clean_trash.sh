#!/bin/sh

# Directories to be removed
dirs=".mypy_cache .pytest_cache htmlcov dist archives cache logs maps temp osmps map_directory tests/data"

# Files to be removed
files=".coverage queue.json"

# Loop through the directories
for dir in $dirs
do
  echo "Removing directory $dir"
  rm -rf $dir
done

# Loop through the files
for file in $files
do
  echo "Removing file $file"
  rm -f $file
done

echo "Removing __pycache__ directories"
find . -type d -name "__pycache__" -exec rm -rf {} +

echo "Cleanup completed."