#!/bin/bash
# setup.sh - Setup virtual environment and install dependencies

set -e

RESUME_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$RESUME_DIR"

echo "Setting up resume repository..."

# Check if venv exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate venv
source .venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Install pyyaml if not in requirements.txt
if ! pip list | grep -i pyyaml > /dev/null 2>&1; then
    pip install pyyaml
fi

echo "Setup complete! Activate with: source .venv/bin/activate"
