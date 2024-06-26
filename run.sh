#!/bin/bash

echo "Starting VENV creation..."
if [ -d ".venv" ]; then
    echo "VENV dir (.venv) already exists, it will be removed."
    rm -rf .venv
fi

echo "VENV will be created..."

if command -v python &>/dev/null; then
    python_executable="python" && \
    echo "Found python in PATH, it will be used for creating VENV dir."
elif command -v python3 &>/dev/null; then
    python_executable="python3" && \
    echo "Found python3 in PATH, it will be used for creating VENV dir."
else
    echo "Python executable not found in PATH, please install it and try again." && \
    exit 1
fi

$python_executable -m venv .venv && \

if [[ "$OSTYPE" == "msys"* ]]; then
    echo "Windows OS detected..."
    .venv/Scripts/activate
else 
    source .venv/bin/activate
fi

echo "Requirements will be installed..." && \
pip3 install -r requirements.txt && \
echo "Requirements have been successfully installed, VENV ready." && \

export PYTHONPATH="${PWD}:${PYTHONPATH}"
$python_executable maps4fs/ui.py
