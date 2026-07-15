#!/bin/bash
# setup.sh - Setup virtual environment and install dependencies
set -e

RESUME_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
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

echo "Setup complete! Activate with: source .venv/bin/activate"
