#!/bin/bash
# activate.sh - Activate the virtual environment

RESUME_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
source "$RESUME_DIR/.venv/bin/activate"
echo "Virtual environment activated!"
