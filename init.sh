#!/bin/bash
set -e

cd "$(dirname "$0")"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install click packaging pytest

# Install the package in development mode if setup exists
if [ -f "setup.py" ] || [ -f "pyproject.toml" ]; then
    pip install -e . 2>/dev/null || true
fi

echo "Environment ready. Run: source venv/bin/activate"
echo "Then: python -m depdrift --help"
